#!/usr/bin/env python3
"""Apply deterministic ordering and JSON formatting to the catalog."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "tools.json"


def ordered_unique(values: list[str], order: dict[str, int] | None = None) -> list[str]:
    unique = list(dict.fromkeys(values))
    if order is None:
        return sorted(unique, key=str.casefold)
    return sorted(unique, key=lambda item: order.get(item, len(order)))


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    category_order = {item["id"]: index for index, item in enumerate(catalog["categories"])}
    region_order = {item["id"]: index for index, item in enumerate(catalog["regions"])}

    for tool in catalog["tools"]:
        tool["categories"] = ordered_unique(tool["categories"], category_order)
        tool["regions"] = ordered_unique(tool["regions"], region_order)
        tool["countries"] = ordered_unique(tool["countries"])
        tool["platforms"] = list(dict.fromkeys(tool["platforms"]))

    catalog["tools"] = sorted(catalog["tools"], key=lambda item: item["name"].casefold())
    CATALOG_PATH.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Formatted {len(catalog['tools'])} catalog records")


if __name__ == "__main__":
    main()
