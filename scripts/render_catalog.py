#!/usr/bin/env python3
"""Render the human-readable catalog and the GitHub Pages data export."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "tools.json"
TEMPLATE_PATH = ROOT / "scripts" / "README.template.md"
README_PATH = ROOT / "README.md"
SITE_DATA_PATH = ROOT / "docs" / "data" / "tools.json"

AI_LABELS = {
    "native": "AI-native",
    "features": "AI features",
    "none": "No AI",
}

ACCESS_LABELS = {
    "free": "Free",
    "freemium": "Freemium",
    "paid": "Paid",
    "pay-as-you-go": "Pay as you go",
    "institutional": "Institutional",
}


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def anchor(value: str) -> str:
    value = re.sub(r"[^a-z0-9 _-]", "", value.lower())
    return value.replace("_", "").replace(" ", "-")


def tool_link(tool: dict) -> str:
    suffix = " 🏠" if tool["maintainer_affiliated"] else ""
    return f"[{markdown_escape(tool['name'])}]({tool['url']}){suffix}"


def platform_label(tool: dict) -> str:
    values = tool["platforms"]
    if len(values) > 4:
        values = [*values[:3], f"+{len(values) - 3} more"]
    return " · ".join(markdown_escape(value) for value in values)


def render_categories(catalog: dict) -> str:
    sections = []
    tools = catalog["tools"]
    for category in catalog["categories"]:
        matching = [tool for tool in tools if category["id"] in tool["categories"]]
        rows = [
            f"- {tool_link(tool)} - {markdown_escape(tool['description'])} "
            f"_{ACCESS_LABELS[tool['access']]} · {AI_LABELS[tool['ai_role']]} · "
            f"{platform_label(tool)}_"
            for tool in matching
        ]
        sections.append(
            "\n".join(
                [
                    f"### {category['name']}",
                    "",
                    *rows,
                ]
            )
        )
    return "\n\n".join(sections)


def render_regions(catalog: dict) -> str:
    category_names = {item["id"]: item["name"] for item in catalog["categories"]}
    sections = []
    tools = catalog["tools"]
    for region in catalog["regions"]:
        matching = [tool for tool in tools if region["id"] in tool["regions"]]
        rows = []
        for tool in matching:
            categories = ", ".join(category_names[item] for item in tool["categories"])
            rows.append(
                f"- {tool_link(tool)} - {markdown_escape(tool['description'])} "
                f"_{markdown_escape(categories)} · {ACCESS_LABELS[tool['access']]}_"
            )
        sections.append(
            "\n".join(
                [
                    f"### {region['name']}",
                    "",
                    "_A selective regional view, not a claim of complete coverage._",
                    "",
                    *rows,
                ]
            )
        )
    return "\n\n".join(sections)


def render_toc(items: list[dict]) -> str:
    return "\n".join(
        f"  - [{item['emoji']} {item['name']}](#{anchor(item['name'])})"
        for item in items
    )


def expected_outputs() -> tuple[str, str]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    readme = (
        template.replace("{{TOOL_COUNT}}", str(len(catalog["tools"])))
        .replace("{{LAST_REVIEWED}}", catalog["last_reviewed"])
        .replace("{{CATEGORY_TOC}}", render_toc(catalog["categories"]))
        .replace("{{REGION_TOC}}", render_toc(catalog["regions"]))
        .replace("{{CATEGORY_SECTIONS}}", render_categories(catalog))
        .replace("{{REGION_SECTIONS}}", render_regions(catalog))
    )
    site_data = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    return readme, site_data


def check_file(path: Path, expected: str) -> bool:
    if not path.exists():
        print(f"missing generated file: {path.relative_to(ROOT)}", file=sys.stderr)
        return False
    if path.read_text(encoding="utf-8") != expected:
        print(f"generated file is stale: {path.relative_to(ROOT)}", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args()
    readme, site_data = expected_outputs()

    if args.check:
        valid = check_file(README_PATH, readme) & check_file(SITE_DATA_PATH, site_data)
        return 0 if valid else 1

    README_PATH.write_text(readme, encoding="utf-8")
    SITE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA_PATH.write_text(site_data, encoding="utf-8")
    print("Rendered README.md and docs/data/tools.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
