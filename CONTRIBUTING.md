# Contributing

Thanks for helping students find better learning tools. Corrections, regional context, accessibility notes, and missing open resources are as valuable as new listings.

## Quick paths

- To suggest a tool without editing JSON, use the **Add a tool** issue form.
- To report a broken, renamed, unsafe, or discontinued link, use the **Report a listing problem** form.
- For a ready correction, open a pull request against `main`.

Please search existing issues and `catalog/tools.json` before opening a duplicate.

## What belongs here

A tool should:

1. materially help people learn, practise, remember, research, write, plan, or collaborate;
2. be active and reachable at a canonical public HTTPS page;
3. be usable by individual learners or meaningfully encountered through an institution;
4. show sustained use, a distinctive learning benefit, or clear editorial merit beyond simply having launched; and
5. have a neutral description that can be verified from first-party material.

We usually exclude generic software with no meaningful study use, single-purpose marketing pages, referral links, prompt collections, thin wrappers, and products whose availability cannot be verified. Discontinued tools go to `ARCHIVE.md`.

## Edit the catalog

`catalog/tools.json` is the source of truth. Every tool uses this shape:

```json
{
  "id": "example-tool",
  "name": "Example Tool",
  "url": "https://example.com/",
  "description": "A neutral sentence describing the learning job it performs.",
  "categories": ["flashcards-spaced-repetition"],
  "regions": [],
  "countries": [],
  "ai_role": "none",
  "access": "freemium",
  "platforms": ["Web", "iOS", "Android"],
  "status": "active",
  "maintainer_affiliated": false,
  "last_reviewed": "2026-08-18"
}
```

Use existing taxonomy IDs from the top of the catalog. Valid AI roles are `native`, `features`, and `none`. Valid access models are `free`, `freemium`, `paid`, `pay-as-you-go`, and `institutional`.

Descriptions should say what the tool does. Do not include rankings, hype, exact prices, user or funding numbers, pass-rate claims, or unsupported safety claims. Link directly to the provider—never an affiliate, app-store tracking, or shortened URL.

After editing, run:

```console
python3 scripts/format_catalog.py
python3 scripts/render_catalog.py
python3 scripts/validate_catalog.py
```

Optionally check external links:

```console
python3 scripts/check_links.py
```

Commit the canonical catalog and both generated outputs (`README.md` and `docs/data/tools.json`). CI verifies that they agree.

## Evidence and affiliations

Link first-party documentation in the issue or pull-request description when changing AI capability, pricing model, ownership, status, or a regional claim. A reputable independent source is also welcome for lifecycle changes.

Disclose if you work for, advise, invest in, or otherwise benefit from a listed product. Affiliation does not prevent inclusion, but undisclosed promotion may be removed. Changes involving maintainer-affiliated products follow the additional review rule in `EDITORIAL_POLICY.md`.

## Pull requests

Keep each pull request focused. In the description, explain:

- what changed and why;
- how the tool meets the inclusion criteria;
- which links or sources you checked; and
- any relevant affiliation.

By contributing, you agree that your contribution is released under CC0 1.0 with the rest of the repository.
