#!/usr/bin/env python3
"""Validate catalog structure, editorial invariants, and generated files."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "tools.json"

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AI_ROLES = {"native", "features", "none"}
ACCESS_MODELS = {"free", "freemium", "paid", "pay-as-you-go", "institutional"}
STATUSES = {"active", "maintenance", "renamed"}
REQUIRED_TOOL_FIELDS = {
    "id",
    "name",
    "url",
    "description",
    "categories",
    "regions",
    "countries",
    "ai_role",
    "access",
    "platforms",
    "status",
    "maintainer_affiliated",
    "last_reviewed",
}
BANNED_MARKETING = re.compile(
    r"(?i)(world.s (?:best|most)|best-in-class|gold-standard|do not rely|"
    r"steep decline|absurdly|#1|most-used|pass rate|pre-ipo)"
)


def parse_date(value: str, context: str, errors: list[str]) -> date | None:
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{context}: expected an ISO date, got {value!r}")
        return None
    if parsed > date.today():
        errors.append(f"{context}: review date cannot be in the future")
    return parsed


def duplicate_values(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_taxonomy(items: object, label: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list) or not items:
        errors.append(f"{label}: expected a non-empty array")
        return set()
    ids = []
    for index, item in enumerate(items):
        context = f"{label}[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "name", "emoji"}:
            errors.append(f"{context}: expected exactly id, name, and emoji")
            continue
        if not ID_PATTERN.fullmatch(item["id"]):
            errors.append(f"{context}.id: invalid slug {item['id']!r}")
        if not item["name"].strip() or not item["emoji"].strip():
            errors.append(f"{context}: name and emoji must not be blank")
        ids.append(item["id"])
    duplicates = duplicate_values(ids)
    if duplicates:
        errors.append(f"{label}: duplicate ids: {', '.join(sorted(duplicates))}")
    return set(ids)


def validate_tool(
    tool: object,
    index: int,
    category_ids: set[str],
    region_ids: set[str],
    errors: list[str],
) -> None:
    context = f"tools[{index}]"
    if not isinstance(tool, dict):
        errors.append(f"{context}: expected an object")
        return
    missing = REQUIRED_TOOL_FIELDS - set(tool)
    extra = set(tool) - REQUIRED_TOOL_FIELDS
    if missing:
        errors.append(f"{context}: missing fields: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{context}: unexpected fields: {', '.join(sorted(extra))}")
    if missing:
        return

    tool_id = tool["id"]
    context = f"tool {tool_id!r}"
    if not isinstance(tool_id, str) or not ID_PATTERN.fullmatch(tool_id):
        errors.append(f"{context}: id must be a lowercase kebab-case slug")
    if not isinstance(tool["name"], str) or not 2 <= len(tool["name"]) <= 80:
        errors.append(f"{context}: name must be 2–80 characters")

    url = urlsplit(tool["url"] if isinstance(tool["url"], str) else "")
    if url.scheme != "https" or not url.netloc or url.fragment:
        errors.append(f"{context}: url must be a canonical HTTPS URL without a fragment")

    description = tool["description"]
    if not isinstance(description, str) or not 20 <= len(description) <= 180:
        errors.append(f"{context}: description must be 20–180 characters")
    elif not description.endswith("."):
        errors.append(f"{context}: description must end with a period")
    elif BANNED_MARKETING.search(description):
        errors.append(f"{context}: description contains promotional or volatile wording")

    categories = tool["categories"]
    if not isinstance(categories, list) or not categories:
        errors.append(f"{context}: at least one category is required")
    elif len(categories) != len(set(categories)) or not set(categories) <= category_ids:
        errors.append(f"{context}: categories must be unique known ids")

    regions = tool["regions"]
    if not isinstance(regions, list) or len(regions) != len(set(regions)) or not set(regions) <= region_ids:
        errors.append(f"{context}: regions must be unique known ids")

    for field in ("countries", "platforms"):
        values = tool[field]
        if not isinstance(values, list) or (field == "platforms" and not values):
            errors.append(f"{context}: {field} must be a{' non-empty' if field == 'platforms' else 'n'} array")
        elif not all(isinstance(value, str) and value.strip() for value in values):
            errors.append(f"{context}: {field} values must be non-empty strings")
        elif len(values) != len(set(values)):
            errors.append(f"{context}: {field} values must be unique")

    if tool["ai_role"] not in AI_ROLES:
        errors.append(f"{context}: unknown ai_role {tool['ai_role']!r}")
    if tool["access"] not in ACCESS_MODELS:
        errors.append(f"{context}: unknown access model {tool['access']!r}")
    if tool["status"] not in STATUSES:
        errors.append(f"{context}: unknown status {tool['status']!r}")
    if not isinstance(tool["maintainer_affiliated"], bool):
        errors.append(f"{context}: maintainer_affiliated must be boolean")
    parse_date(tool["last_reviewed"], f"{context}.last_reviewed", errors)


def main() -> int:
    errors: list[str] = []
    try:
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"catalog could not be read: {exc}", file=sys.stderr)
        return 1

    if set(catalog) != {"schema_version", "last_reviewed", "categories", "regions", "tools"}:
        errors.append("catalog root must contain exactly schema_version, last_reviewed, categories, regions, tools")
    if catalog.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    parse_date(catalog.get("last_reviewed"), "last_reviewed", errors)

    category_ids = validate_taxonomy(catalog.get("categories"), "categories", errors)
    region_ids = validate_taxonomy(catalog.get("regions"), "regions", errors)
    tools = catalog.get("tools")
    if not isinstance(tools, list) or len(tools) < 100:
        errors.append("tools must be an array containing at least 100 records")
        tools = []

    for index, tool in enumerate(tools):
        validate_tool(tool, index, category_ids, region_ids, errors)

    for field in ("id", "name", "url"):
        duplicates = duplicate_values([tool[field].casefold() for tool in tools if field in tool])
        if duplicates:
            errors.append(f"tools: duplicate {field} values: {', '.join(sorted(duplicates))}")

    expected_order = sorted(tools, key=lambda item: item["name"].casefold())
    if tools != expected_order:
        errors.append("tools must be sorted alphabetically by name")

    affiliated = [tool["id"] for tool in tools if tool.get("maintainer_affiliated")]
    if affiliated != ["studyarena"]:
        errors.append("known maintainer affiliation must be explicit for StudyArena only")

    rendered = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "render_catalog.py"), "--check"],
        cwd=ROOT,
        check=False,
    )
    if rendered.returncode:
        errors.append("generated catalog files are stale")

    if errors:
        print("Catalog validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Catalog valid: {len(tools)} tools, {len(category_ids)} categories, "
        f"{len(region_ids)} regional views"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
