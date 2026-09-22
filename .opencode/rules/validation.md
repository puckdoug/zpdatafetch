---
description: Testing, linting, and type-checking validation after code changes
globs:
---

# Validation Rules

- Validate after each change that all three pass:
  - `python -m pytest`
  - `ruff check src test`
  - `ty check src test`
- When fixing a production bug, always add a regression test using the exact production data that triggered it. Do not substitute abstract or made-up values.
