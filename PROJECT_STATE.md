# QA Automation Project State

## Goal

Build a minimal, production-quality QA automation framework with:

- UI tests (Playwright)
- API tests (requests)
- pytest-based structure

## Current Scope

**UI** (https://www.saucedemo.com/):

- Login success
- Login failure (strict assertion)
- Cart validation (2 items)
- Checkout E2E

**API** (https://jsonplaceholder.typicode.com/):

- GET /posts
- GET /posts/{id} (valid + invalid)
- POST /posts
- PUT + DELETE /posts/{id}

## Architecture Decisions

- Simple Page Object Model (no heavy abstractions)
- pytest as test runner
- Playwright auto-waiting (no sleeps)
- requests for API tests
- Each test is independent and stateless
- Single root `conftest.py` for UI + API fixtures
- UI copy and checkout totals in `constants.py`; API helpers in `tests/api/helpers.py`
- `data-test` attribute configured globally for Swag Labs (`data-test`, not `data-testid`)
- Markers: `@pytest.mark.ui`, `@pytest.mark.api`, `@pytest.mark.smoke`

## Project Layout

```
pages/                 # UI page objects
constants.py           # UI credentials, exact strings, products, checkout totals
conftest.py            # Fixtures: page objects, http session, base URLs
tests/
  ui/                  # 4 Playwright tests
  api/
    constants.py       # Post IDs for API scenarios
    helpers.py         # URL builder + assertion helpers
    test_posts.py      # 5 test functions (6 runs with parametrize)
requirements.txt
pytest.ini
README.md
.github/workflows/tests.yml
.env.example
```

## What is already done

- **UI framework** — Playwright + pytest; page objects for login, inventory, cart, checkout
- **4 UI tests** — `tests/ui/` covering login success/failure, cart (badge + 2 line items), checkout with overview totals
- **API framework** — `requests` session per test; `tests/api/helpers.py` for status, JSON, schema, and field assertions
- **5 API test functions (6 runs)** — list + schema, GET by id (200/404), POST, PUT, DELETE (isolated; no persistence check)
- **Isolation** — fresh browser context per UI test; fresh `requests.Session` per API test; UI entry via `login_page` fixture only
- **Strict assertions** — exact login error text, page titles, checkout header; API failures include HTTP status and field diffs
- **No sleeps** — Playwright `expect` / auto-wait; API uses request timeouts only
- **Parallel-ready** — `pytest-xdist` in requirements; safe to run `pytest tests/ui tests/api -n auto` (UI needs `--browser=chromium`)
- **Lint** — `ruff` configured in `pyproject.toml`
- **CI** — GitHub Actions (`tests.yml`): parallel API (`-m api`) + UI (`-m ui`, `-n 2`); HTML report, JUnit, traces/screenshots on failure; artifacts per job
- **Reporting** — `pytest-html` (`test-results/report.html`); failed UI: screenshot, trace, DOM (`page.html`), console log
- **Docs & DX** — `README.md`, `.env.example`, VS Code `launch.json` / `tasks.json` for UI and API runs
- **Local verification** — 10 tests passing (4 UI + 6 API) on Windows with `.venv`

## What is next

- **Publish repo** — push to public GitHub (assignment deliverable)
- **Confirm remote CI** — ensure Actions pass on `main` after push
- **Optional expansion** — bonus UI (sort/filter, badge add/remove); other Swag Labs users (`problem_user`, `locked_out_user`); API negative POST cases
- **Optional hardening** — pin full dependency lockfile; scheduled CI against live targets; retry policy for UI flakiness in CI only

## Recent polish (done)

- `DESIGN.md` — one-page architecture and trade-offs
- CI — separate JUnit files per suite; upload `test-results/` on every run
- Assignment: anti-flakiness (no sleep, `data-test`, `expect` only), UI `-n 2`, 10-run stability gate, HTML report + failure artifacts
- POST create — assert generated `id` > 0
- `.gitignore` — `.env`, `.ruff_cache/`

## Quick Commands

```bash
pip install -r requirements.txt
playwright install chromium

pytest tests/api -v
pytest tests/ui --browser=chromium -v
pytest tests/ui tests/api --browser=chromium -n auto
ruff check .
```

## Configuration

| Variable       | Default                                      |
|------------------|----------------------------------------------|
| `BASE_URL`       | `https://www.saucedemo.com`                  |
| `API_BASE_URL`   | `https://jsonplaceholder.typicode.com`       |
