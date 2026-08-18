#!/usr/bin/env python3
"""Check canonical catalog URLs with redirect and bot-block awareness."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "tools.json"
USER_AGENT = (
    "Mozilla/5.0 (compatible; AwesomeStudyToolsLinkCheck/1.0; "
    "+https://github.com/studyarena-com/awesome-study-tools)"
)
BOT_BLOCK_STATUSES = {401, 403, 418, 429, 451}


@dataclass(frozen=True)
class Result:
    tool_id: str
    name: str
    url: str
    final_url: str
    status: int | None
    outcome: str
    detail: str


def request(url: str, method: str, timeout: float) -> tuple[int, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }
    if method == "GET":
        headers["Range"] = "bytes=0-1023"
    req = urllib.request.Request(url, headers=headers, method=method)
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
        return response.status, response.geturl()


def attempt(url: str, timeout: float) -> tuple[int | None, str, str]:
    last_error = "unknown network error"
    for method in ("HEAD", "GET"):
        try:
            status, final_url = request(url, method, timeout)
            return status, final_url, ""
        except urllib.error.HTTPError as exc:
            status = exc.code
            final_url = exc.geturl() or url
            last_error = f"HTTP {status}"
            if status in BOT_BLOCK_STATUSES:
                return status, final_url, "site blocks automated checks"
            if method == "HEAD" and status in {400, 404, 405, 406, 500, 501}:
                continue
            return status, final_url, last_error
        except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
            reason = getattr(exc, "reason", exc)
            last_error = str(reason)
            if method == "HEAD":
                continue
    return None, url, last_error


def check(tool: dict, timeout: float, retries: int) -> Result:
    status = None
    final_url = tool["url"]
    detail = ""
    for attempt_number in range(retries + 1):
        status, final_url, detail = attempt(tool["url"], timeout)
        if status is not None:
            break
        if attempt_number < retries:
            time.sleep(0.25 * (attempt_number + 1))

    if status in BOT_BLOCK_STATUSES:
        outcome = "blocked"
    elif status is None:
        outcome = "broken"
    elif 200 <= status < 400:
        outcome = "redirect" if final_url.rstrip("/") != tool["url"].rstrip("/") else "ok"
        if outcome == "redirect":
            detail = f"redirects to {final_url}"
    elif status in {404, 410}:
        outcome = "broken"
    else:
        outcome = "warning"

    return Result(
        tool_id=tool["id"],
        name=tool["name"],
        url=tool["url"],
        final_url=final_url,
        status=status,
        outcome=outcome,
        detail=detail,
    )


def markdown_report(results: list[Result]) -> str:
    problems = [result for result in results if result.outcome in {"broken", "warning"}]
    lines = ["# Catalog link report", ""]
    if not problems:
        lines.append("No broken or warning-status catalog links were found.")
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "| Tool | Outcome | Status | URL | Detail |",
            "|---|---|---:|---|---|",
        ]
    )
    for result in problems:
        status = str(result.status) if result.status is not None else "network"
        detail = result.detail.replace("|", "\\|")
        lines.append(
            f"| {result.name} | {result.outcome} | {status} | {result.url} | {detail} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    tools = catalog["tools"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(check, tool, args.timeout, args.retries) for tool in tools]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda item: item.name.casefold())

    counts = {
        outcome: sum(result.outcome == outcome for result in results)
        for outcome in ("ok", "redirect", "blocked", "warning", "broken")
    }
    for result in results:
        if result.outcome != "ok":
            status = result.status if result.status is not None else "network"
            print(f"{result.outcome:8} {status!s:>7}  {result.name}: {result.detail}")
    print(
        "Checked {total} links: {ok} ok, {redirect} redirects, {blocked} bot-blocked, "
        "{warning} warnings, {broken} broken".format(total=len(results), **counts)
    )

    if args.json_output:
        payload = {"summary": counts, "results": [asdict(result) for result in results]}
        args.json_output.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    if args.markdown_output:
        args.markdown_output.write_text(markdown_report(results), encoding="utf-8")

    return 1 if counts["broken"] or counts["warning"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
