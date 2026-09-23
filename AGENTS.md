# zpdatafetch

Python library + four CLIs (`zpdata`, `zrdata`, `zdata`, `zsdata`) fetching data from ZwiftPower, Zwiftracing.app, Zwift, and Zwift Status.

Project rules are in `.opencode/rules/` (environment, security, style, validation, workflow). Read them before every action. Mandatory parts summarized below.

## Environment

- uv-managed `.venv`. Activate first: `source .venv/bin/activate`. Never use pip.
- Python >= 3.10. CI tests 3.10–3.14 plus 3.14t; 3.13t is broken and unsupported.
- Local temporary files go in ./tmp

## Validation — run after every change, all three must pass

```sh
just test      # pytest (live API tests skip themselves without --live)
just check     # ruff check src test && ty check src test
```

- Direct equivalents: `python -m pytest`, `ruff check src test`, `ty check src test`.
- Live tests: `just test-live` (`pytest --live test/live`). They make real API calls using real system-keyring credentials (`zpdatafetch username/password`, `zrdatafetch authorization`). Never run them casually.
- CI runs ruff with `continue-on-error`, so lint failures will not fail CI — always run `just check` locally.
- Bug fixes need a regression test using the exact production data that triggered the bug. No made-up substitutes.

## Architecture

- src/ layout with 5 top-level packages (imported as `shared.*`, `zpdatafetch.*`, ...):
  - `shared/` — common HTTP client with retry, config, exceptions, validation, logging, CLI helpers. Used by every data package.
  - `zpdatafetch/` — ZwiftPower. Core session class `ZP`; data objects inherit `ZP_obj`.
  - `zrdatafetch/` — Zwiftracing. Has `rate_limiter.py` (standard/premium tiers).
  - `zdatafetch/` — Zwift (profiles, followers, rideons, activities, worlds).
  - `zsdatafetch/` — Zwift Status. Public API, no auth.
- Each package has `cli.py` (console-script entry: `zdata`/`zpdata`/`zrdata`/`zsdata`).
- Data classes support both sync `fetch()` and async `afetch()`. Async uses anyio; both asyncio and trio are tested via the `anyio_backend` fixture.
- HTTP library is `httpx2` (a fork, not `httpx`). Import `httpx2`.

## Tests

- `test/` mirrors `src/`: `test_zpdatafetch/`, `test_zrdatafetch/`, `test_zdatafetch/`, `test_zsdatafetch/`, `test_shared/`, `test/integration/`, `test/live/`.
- Root `test/conftest.py` auto-installs fake credentials (PlaintextKeyring + `_test_domain_override`) for the whole session — unit tests never touch the real keyring. Only `test/live/` restores the real system keyring.
- Raw JSON/HTML fixtures live in `test/fixtures/`.

## Style

- ruff: line length 80, indent width 2, single quotes, type hints required (ANN rules). Google-style docstrings.
- Per-file ruff ignores in `pyproject.toml` cover justified `Any`/long-line cases. Don't add new ones casually.
- Type checker is `ty` (configured under `[tool.ty]` in pyproject), not mypy or pyright.

## Security

- Never write passwords, tokens, or API keys into any file (source, docs, plans, comments). Credentials come from the system keyring at runtime only.

## Workflow

- Never start implementation without an explicit go-ahead. Write plans to `docs/planning/` with a checklist at the top and maintain it while working.
- Never ignore an issue or warning — fix it immediately or log it in `docs/planning/` with a proposed solution.
- GitHub issue workflow: work only existing issues. Pull with `gh issue view <N>`, plan in `docs/planning/issue_<N>_<slug>.md`, and complete by validating, marking the plan `DONE`, posting the final update via `gh issue comment <N>`, and closing the issue. Never create GitHub issues.
- Do not run `git commit`, `merge`, `rebase`, or `push`. Use `git add` / `git mv` / `git rm` so change history is tracked.
- Update `CHANGELOG.md` and `README.md` whenever functionality is added or changed.

## Release

- Bump version in `pyproject.toml`, update `CHANGELOG.md`, then push a tag starting with `release_` (e.g. `release_v2.3.2`). CI runs linux/windows/macos tests, then publishes to PyPI via trusted publishing. See `BUILD.md`.

## Gotchas

- `CONTRIBUTING.md`'s project-structure section is stale — actual source files use `zp*`/`zr*` prefixes (e.g. `zpcyclist.py`, not `cyclist.py`). Trust the tree.
- Plans go to `docs/planning/`. Root `planning/` holds older issue plans; `local/` is scratch session notes — don't add new content there.
