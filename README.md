# QA Automation Framework (Python + pytest)

Minimal UI and API test suite in one project.

| Target | URL |
|--------|-----|
| **UI** | https://www.saucedemo.com/ |
| **API** | https://jsonplaceholder.typicode.com/ |

## Structure

```
pages/                 # UI page objects (Playwright)
tests/
  ui/                  # 4 Swag Labs scenarios
  api/                 # 5 API test functions + helpers
conftest.py            # Shared fixtures (UI + API)
constants.py           # UI credentials and exact copy
requirements.txt
.github/workflows/tests.yml
```

## Setup (< 5 minutes)

**Prerequisites:** Python 3.14, pip, Git

```bash
git clone https://github.com/asafekst/qa-automation-assignment-asaf-ekshtein.git
cd qa-automation-assignment-asaf-ekshtein
python -m venv .venv

# Windows
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium

# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Optional: copy `.env.example` → `.env` for custom URLs.

## Run tests

```bash
# All (UI needs browser flag)
pytest tests/ui --browser=chromium
pytest tests/api

# Smoke (fail fast — same subset CI runs first)
pytest tests/api -m "smoke and api" --maxfail=1 -q
pytest tests/ui -m "smoke and ui" --browser=chromium -n 2 --maxfail=1 -q

# Full suites
pytest tests/api -m api
pytest tests/ui -m ui --browser=chromium -n 2 \
  --tracing=retain-on-failure --screenshot=only-on-failure --output=test-results

# Parallel UI (required: at least 2 workers; tests are isolated per browser context)
pytest tests/ui --browser=chromium -n 2

# Parallel — auto worker count
pytest tests/ui --browser=chromium -n auto
pytest tests/api -n auto

# Lint
ruff check .
```

### Anti-flakiness

- **No** `time.sleep`, `wait_for_timeout()`, or `networkidle` waits — enforced by `scripts/check_anti_flake.py` in CI and `ruff` banned-api rules.
- **No** implicit waits — only Playwright **auto-wait** on actions and **`expect()`** for assertions.
- **Selectors (priority order):**
  1. `data-test` via `get_by_test_id()` (Swag Labs; attribute set in `conftest.py`)
  2. Scoped text inside a `data-test` container (e.g. cart line names under `inventory-item-name`)
  3. No brittle XPath / long CSS chains
- Each UI test gets a **fresh browser context** (function-scoped). `standard_user` is the public demo account; parallel tests do not share browser state — only the username string is reused.

```bash
python scripts/check_anti_flake.py
```

### Reporting

| Artifact | Location |
|----------|----------|
| HTML report | `test-results/report.html` (open in browser) |
| JUnit | `test-results/junit.xml` |
| Failed UI: screenshot | `test-results/` (pytest-playwright, `--screenshot=only-on-failure`) |
| Failed UI: trace | `test-results/` (`--tracing=retain-on-failure`; view with `playwright show-trace <file.zip>`) |
| Failed UI: DOM + console | `test-results/artifacts/<test>/page.html`, `console.log`, `meta.json`, `screenshot.png` |
| Failed UI: video | `test-results/` (`--video=retain-on-failure`) |

CI runs API and UI jobs **in parallel** on every push/PR to `main`. Each job uploads its `test-results/` folder (HTML report, JUnit, and UI failure traces/screenshots).

See [DESIGN.md](DESIGN.md) for architecture and trade-offs.

## UI scenarios (`tests/ui/`)

| # | Test | What it checks |
|---|------|----------------|
| 1 | Login success | `standard_user` → inventory with products |
| 2 | Login failure | Exact error text + still on login page |
| 3 | Cart | 2 items, badge count, line names/prices |
| 4 | Checkout | Shipping → overview totals → confirmation |

- Playwright auto-waiting, `data-test` selectors, no sleeps  
- Fresh browser context per test  

## API scenarios (`tests/api/`)

| # | Test | What it checks |
|---|------|----------------|
| 1 | GET `/posts` | 200, JSON array, post schema |
| 2 | GET `/posts/{id}` | id `1` → 200; `99999` → 404 |
| 3 | POST `/posts` | 201, echoed payload, generated `id` |
| 4 | PUT `/posts/{id}` | 200, updated fields echoed |
| 5 | DELETE `/posts/{id}` | 200/204 accepted (no persistence check) |

- `requests` session per test, shared assertion helpers in `tests/api/helpers.py`  

## Configuration

| Variable | Default | Used by |
|----------|---------|---------|
| `BASE_URL` | `https://www.saucedemo.com` | UI |
| `API_BASE_URL` | `https://jsonplaceholder.typicode.com` | API |

## Design principles

- **Simple** — one root `conftest.py`, thin page objects, small API helpers  
- **Independent** — no shared login state, sessions, or ordering assumptions  
- **Explicit** — strict UI copy in `constants.py`; HTTP/body assertions with clear messages  
- **CI-ready** — GitHub Actions runs API and UI in parallel on every push/PR

## CI

[![Tests](https://github.com/asafekst/qa-automation-assignment-asaf-ekshtein/actions/workflows/tests.yml/badge.svg)](https://github.com/asafekst/qa-automation-assignment-asaf-ekshtein/actions/workflows/tests.yml)

`.github/workflows/tests.yml` runs on push/PR/`workflow_dispatch` to `main`: parallel jobs **API** and **UI** (Python 3.14). Each job runs **once** when all tests are smoke (`--maxfail=1`); when non-smoke regressions are added, smoke gate runs first, then only the regression slice (no overlap). Artifacts: `test-results-api`, `test-results-ui`.

**Latest green CI run:** [Tests #14 on `main`](https://github.com/asafekst/qa-automation-assignment-asaf-ekshtein/actions/runs/27101290358) (11+ consecutive green runs on `main`; both **API tests** and **UI tests** jobs passed).
