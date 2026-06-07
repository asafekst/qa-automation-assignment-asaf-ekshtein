# DESIGN.md — Test Automation Design Rationale

## 1. Language & Framework Choice

This project uses Python with Pytest as the test runner, Playwright for UI automation, and `requests` for API testing.

This stack was chosen because:

- Python + Pytest provides a simple, readable, and highly extensible testing framework with strong support for fixtures, parametrization, and plugins.
- Playwright was selected over Selenium due to:
  - Built-in auto-waiting (reduces flakiness significantly)
  - Faster execution and native parallelism support
  - Strong debugging tools (trace viewer, screenshots, video)
  - Cleaner API design that integrates well with Page Object Model (POM)

Selenium would be preferred in environments where:

- Existing Selenium/Grid infrastructure is already standardized
- Legacy browser support is required
- Organizational constraints enforce Selenium-based tooling

---

## 2. Anti-Flakiness Strategy

The framework is designed to minimize flaky tests and ensure deterministic execution.

Key strategies:

- No usage of `sleep()`, `wait_for_timeout()`, or `networkidle` — enforced by `scripts/check_anti_flake.py` in CI
- Playwright auto-waiting on actions; `expect()` for condition-based assertions (URL, text, visibility)
- Assertions based on application state, not timing
- Page Object Model (POM) with light fluent navigation (`login_as()` → `InventoryPage`, `open_cart()` → `CartPage`, etc.)
- Stable selectors: `data-test` via `get_by_test_id()` (configured in `conftest.py`); scoped text inside known containers; no brittle XPath chains
- Each UI test runs in a **fresh browser context**; each API test uses a **fresh `requests.Session`**

### Login strategy (current)

Each logged-in UI test performs login explicitly in the test via the Page Object:

```python
inventory = login_page.open().login_as(STANDARD_USER, PASSWORD)
inventory.expect_loaded()
```

This keeps tests self-contained and readable. The cost is acceptable for four UI scenarios.

**At scale (1000+ tests),** I would add Playwright `storageState`: log in once, save cookies/localStorage, then create a fresh browser context per test loaded from that state — faster runs with the same isolation model.

Other extensions at scale:

- Flakiness analytics (tracking unstable tests over time)
- Controlled CI retry only for known external instability (not masking real bugs)
- Stronger test data lifecycle (seeding/reset APIs or isolated environments)
- Optional network mocking for unstable dependencies

CI runs API and UI jobs **in parallel** on every push/PR to `main`; UI uses **2 workers** (`-n 2`) per run.

---

## 3. Test Data Strategy

The framework uses a single source of truth for test data:

- **UI:** `constants.py` — credentials, products, exact UI copy, checkout totals, shipping info
- **API:** `tests/api/constants.py` — post IDs and POST/PUT payloads

This ensures tests behave as strict contracts against the application.

- Static values are centralized in constants modules
- Exact UI messages are asserted explicitly to detect regressions early
- Non-deterministic content uses precise matching (e.g. order-complete body via regex)

JSONPlaceholder is stateless: PUT/DELETE are kept in one API test; DELETE asserts HTTP acceptance only, not persistence.

---

## 4. Parallelism & Isolation

All tests are designed to be fully independent and safe for parallel execution:

- Each UI test uses a fresh browser context (function-scoped `page`)
- Each API test uses a fresh HTTP session (function-scoped `http`)
- No shared mutable state between tests
- No dependency on execution order
- `standard_user` is a public demo credential; isolation is per browser context, not per username

Run parallel UI: `pytest tests/ui --browser=chromium -n 2`

### What breaks first at higher parallelism

- Live external targets (saucedemo.com, jsonplaceholder) — rate limits or slow responses
- Shared server-side session if the app ever stored cart state per user (not an issue on the current demo)
- CI runner resources (too many Chromium instances → timeout flakes)
- Improper session-scoped or global fixtures (none used here)

---

## 5. Reporting & Triage

On CI failure, the on-call engineer gets:

| Artifact | Purpose |
|----------|---------|
| `test-results/report.html` | pytest-html — failing test, traceback |
| `test-results/junit.xml` | CI / dashboard integration (one per matrix job artifact) |
| Screenshot, trace, video | pytest-playwright (`retain-on-failure` / `only-on-failure`) |
| `artifacts/<test>/page.html` | DOM snapshot |
| `artifacts/<test>/console.log` | Browser console + page errors |
| `artifacts/<test>/meta.json` | URL and title at failure |

All of `test-results/` is uploaded as a GitHub Actions artifact on every run.

### Debugging flow

1. Open the failed CI run → download `test-results` artifact
2. Open `report.html` → identify failing test and assertion
3. For UI: open trace (`playwright show-trace <file.zip>`) or screenshot + `page.html`
4. Reproduce locally: `pytest path::test_name --browser=chromium -v` (no `-n` while debugging)
5. For API: read traceback + response body snippet in helper assertion messages

---

## 6. What I Would Do Next

If given two more days:

**Day 1 — Determinism and API depth**

- Optional local mock for JSONPlaceholder so API tests run offline and parallel-safe at scale
- Negative API cases (malformed POST, invalid payloads) using the existing helper pattern

**Day 2 — CI and operability**

- Parallel CI jobs (lint + API ∥ UI) for faster feedback
- `storageState` for UI login once suite size justifies it
- Scheduled nightly against live targets; PRs run smoke only
- Pin a dependency lockfile

**Why this order:** The suite is stable and readable today. The next real pain is external dependency variance and CI latency — not more page objects. Bonus UI (sort, `problem_user`) comes after environment control.

---

## Architecture (intentionally small)

```
tests/ui/          → scenarios (entry: login_page fixture)
tests/api/         → scenarios + helpers.py
pages/             → page objects + shared assertions
constants.py       → UI test data
conftest.py        → login_page, http, failure artifacts
```

No `clients/`, `config/`, or BDD layer — add structure when pain appears, not ahead of it.
