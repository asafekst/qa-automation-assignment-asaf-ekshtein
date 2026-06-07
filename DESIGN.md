# Design Rationale

Minimal QA automation for **Swag Labs** (UI) and **JSONPlaceholder** (API): 4 UI tests, 5 API tests, one repo, CI on every push/PR to `main`.

| Target | URL |
|--------|-----|
| UI | https://www.saucedemo.com |
| API | https://jsonplaceholder.typicode.com |

---

## Stack

**Python · pytest · Playwright · requests**

- **pytest** — fixtures, markers (`ui`, `api`, `smoke`), parallel runs via `pytest-xdist`
- **Playwright** — auto-waiting, traces, `data-test` selectors; chosen over Selenium for speed, stability, and built-in debugging
- **requests** — enough for JSONPlaceholder without a heavy API client layer

---

## Architecture

```
tests/ui/          → 4 scenarios (entry: login_page fixture)
tests/api/         → scenarios + helpers.py
pages/             → page objects + shared assertions
constants.py       → UI credentials, copy, products, checkout totals
conftest.py        → fixtures, URLs, failure artifacts
.github/workflows/tests.yml
```

Thin Page Object Model with fluent navigation (`login_as()` → `InventoryPage`, `open_cart()` → `CartPage`). No extra `clients/`, `config/`, or BDD layer until the suite grows.

---

## Anti-flakiness

- **No** `sleep()`, `wait_for_timeout()`, or `networkidle` — guarded locally by `scripts/check_anti_flake.py`
- **Playwright auto-wait + `expect()`** only; assertions on application state, not timing
- **Selectors:** `data-test` via `get_by_test_id()` (set in `conftest.py`); scoped text in known containers; no brittle XPath chains
- **Isolation:** fresh browser context per UI test; fresh `requests.Session` per API test
- **Login:** each UI test logs in explicitly — readable and self-contained for four scenarios; at scale, use Playwright `storageState`

```python
inventory = login_page.open().login_as(STANDARD_USER, PASSWORD)
inventory.expect_loaded()
```

**Main flake risk:** live external sites (network latency, rate limits). Acceptable for this demo; mocks or staging would be the next step at scale.

---

## Test data

| Layer | Source |
|-------|--------|
| UI | `constants.py` — credentials, exact copy, products, checkout totals |
| API | `tests/api/constants.py` — post IDs and payloads |

Exact UI strings are asserted to catch regressions early. JSONPlaceholder is stateless — PUT/DELETE live in one test; DELETE checks HTTP acceptance only, not persistence.

---

## Parallelism

Safe to run in parallel — no shared state, no ordering assumptions.

```bash
pytest tests/ui --browser=chromium -n 2
pytest tests/api -m api
```

`standard_user` is a public demo account; isolation is per browser context, not per username.

---

## CI & reporting

**Workflow:** `.github/workflows/tests.yml` — matrix jobs **api** and **ui** in parallel (Python 3.14).

| Job | Command |
|-----|---------|
| API | `pytest tests/api -m api` |
| UI | `pytest tests/ui -m ui --browser=chromium -n 2` |

Each job uploads **`test-results-api`** or **`test-results-ui`** containing:

| Artifact | Purpose |
|----------|---------|
| `report.html` | pytest-html — failures and tracebacks |
| `junit.xml` | CI / dashboard integration |
| Trace, screenshot | pytest-playwright on UI failure |
| `artifacts/<test>/page.html`, `console.log`, `meta.json` | DOM + browser console (`conftest.py`) |

**On failure:** download the job artifact → open `report.html` → for UI, use trace/screenshot or `page.html`; reproduce locally with `pytest path::test_name --browser=chromium -v` (skip `-n` while debugging).

---

## What I would do next

1. Mock or pin staging for external targets (biggest reliability win)
2. Negative API cases via existing helpers
3. `storageState` for UI login once the suite grows
4. Optional: lint + anti-flake step in CI; dependency lockfile

The suite is intentionally small and stable today — the next pain is environment variance, not more abstractions.
