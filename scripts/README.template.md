<!--
  This file is generated from catalog/tools.json.
  Edit the catalog or this template, then run: python3 scripts/render_catalog.py
-->

# Awesome Study Tools

[![Catalog validation](https://github.com/studyarena-com/awesome-study-tools/actions/workflows/validate.yml/badge.svg)](https://github.com/studyarena-com/awesome-study-tools/actions/workflows/validate.yml)
[![Link check](https://github.com/studyarena-com/awesome-study-tools/actions/workflows/links.yml/badge.svg)](https://github.com/studyarena-com/awesome-study-tools/actions/workflows/links.yml)
[![CC0 1.0](https://img.shields.io/badge/license-CC0--1.0-4a5568.svg)](LICENSE)
![{{TOOL_COUNT}} tools](https://img.shields.io/badge/tools-{{TOOL_COUNT}}-315c4c.svg)

A global, community-curated directory of study and learning tools. **The complete resource is the clickable Markdown list on this repository page**—no app or separate site required. Browse by category or region below, or use <kbd>Ctrl</kbd>/<kbd>⌘</kbd> + <kbd>F</kbd> to find a tool.

> [!NOTE]
> This project is maintained by [StudyArena](https://studyarena.com/). Maintainer-affiliated products are marked **🏠**, receive no ranking advantage, and follow the same inclusion rules as every other listing. There are no affiliate links or paid placements.

## Contents

- [Browse by study goal](#browse-by-study-goal)
{{CATEGORY_TOC}}
- [Browse by region](#browse-by-region)
{{REGION_TOC}}

## Browse by study goal

Every tool name below is a direct link. Entries are alphabetical within each section; the italic text shows access, AI role, and platforms. **AI-native** means AI is central to the product; **AI features** means AI augments a primarily non-AI product; **No AI** means no substantial AI feature was identified during the last review.

**🏠 Maintainer affiliated** · **Last editorial review:** {{LAST_REVIEWED}}

{{CATEGORY_SECTIONS}}

## Browse by region

These views highlight tools shaped by local curricula, exams, languages, or study habits. Global tools may still be available in every region. Coverage is intentionally selective and grows through contributions.

{{REGION_SECTIONS}}

## How this list is curated

This catalog is for students, educators, and families choosing software or online services that materially support learning. A listing should be active, have a canonical public page, offer clear learning value, and show meaningful adoption or editorial merit beyond simply having launched.

- Descriptions state observable capabilities, not rankings or vendor marketing claims.
- Entries are alphabetical; placement is not endorsement or a quality ranking.
- Exact prices, user counts, funding claims, and other fast-changing figures are omitted.
- Institutional tools are included when learners are likely to encounter them through a school or university.
- Discontinued tools belong in [the archive](ARCHIVE.md), not the active catalog.
- Maintainer affiliations and contributor conflicts must be disclosed.

Read the full [editorial policy](EDITORIAL_POLICY.md) for inclusion, evidence, removal, and conflict-of-interest rules.

## Data and extensibility

The catalog is maintained as structured, version-controlled data:

- [`catalog/tools.json`](catalog/tools.json) is the canonical dataset.
- [`catalog/schema.json`](catalog/schema.json) documents the data contract.
- [`docs/data/tools.json`](docs/data/tools.json) is the generated web export.
- `python3 scripts/validate_catalog.py` validates records and generated-file drift.
- `python3 scripts/render_catalog.py` rebuilds this README and the web export.

Everything runs on the Python standard library. No package install or API key is required.

## Responsible use

AI output can be incomplete or wrong. Check important claims against course materials and primary sources, protect personal or confidential data, and follow your school or university's academic-integrity rules. A tool's presence here is not an endorsement, safety certification, or guarantee of availability.

## Contributing

Found a useful tool, broken link, rebrand, or regional gap? Read [CONTRIBUTING.md](CONTRIBUTING.md), then use an issue form or open a pull request. Small, well-sourced corrections are especially welcome.

## Related lists

- [Awesome Student Resources](https://github.com/StudentSuite/awesome-student-resources) — student services, discounts, and broader resources.
- [Awesome Study Resources](https://github.com/StudentSuite/awesome-study-resources) — study techniques and learning resources.
- [Awesome Education](https://github.com/wowlusitong/awesome-education) — educational frameworks, datasets, and engineering resources.
