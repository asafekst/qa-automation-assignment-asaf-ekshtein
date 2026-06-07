# QA Automation Framework — Design Document

## 1. Overview

Single-repository test suite covering **Swag Labs** (browser UI) and **JSONPlaceholder** (HTTP API). The framework prioritizes readability, isolation, and CI reliability over abstraction depth.

| Dimension | Scope |
|-----------|--------|
| UI tests | 4 scenarios — login success/failure, cart, checkout |
| API tests | 6 runs (5 functions, 1 parametrized) — GET list/id, POST, PUT, DELETE |
| Trigger | Push and pull request to `main` |
| Philosophy | Minimal structure today; extension points documented for scale |

| System under test | Base URL |
|-------------------|----------|
| UI (Swag Labs) | https://www.saucedemo.com |
| API (JSONPlaceholder) | https://jsonplaceholder.typicode.com |

---

## 2. Test Strategy

### UI layer (`tests/ui/`)

**Responsibility:** Validate end-user journeys through the browser — navigation, visible state, and exact copy.

- Tests express **business flows** only; locators and waits live in page objects.
- Entry fixture: `login_page` (provided by root `conftest.py`).
- Marker: `@pytest.mark.ui` (module-level `pytestmark`).
- Failure signals: Playwright trace, screenshot, DOM snapshot, browser console (see §11).

### API layer (`tests/api/`)

**Responsibility:** Validate HTTP contracts — status codes, JSON shape, and field-level assertions.

- Tests call endpoints via a function-scoped `http` fixture (`requests.Session` with timeout).
- Shared logic: `tests/api/helpers.py` (URL builder, status/body/schema assertions).
- Test data: `tests/api/constants.py` (IDs, payloads).
- Marker: `@pytest.mark.api`.
- Each write scenario (POST, PUT, DELETE) is **atomic** — no shared server state between tests.

### Cross-cutting

| Marker | Purpose |
|--------|---------|
| `smoke` | Critical-path subset (all current tests) |
| `ui` / `api` | Suite filter for local runs and CI matrix jobs |

---

## 3. Technology Stack

| Tool | Role | Rationale |
|------|------|-----------|
| **pytest** | Runner, fixtures, markers, reporting hooks | De-facto Python standard; low ceremony |
| **Playwright** | UI automation | Built-in auto-wait, trace viewer, stable `data-test` support |
| **requests** | API calls | Sufficient for REST smoke/contract tests; no client framework required |
| **pytest-xdist** | Parallel UI execution | Validates isolation under concurrent browser contexts |
| **pytest-html** | HTML report | Self-contained artifact for CI triage |

No additional layers (BDD, custom runners, API client SDKs) until suite size justifies them.

---

## 4. Architecture

```
tests/ui/                 Test scenarios (UI)
tests/api/
  test_posts.py           Test scenarios (API)
  helpers.py              Assertion + URL helpers
  constants.py            API payloads and IDs
pages/                    Fluent page objects + shared Playwright assertions
constants.py              UI credentials, copy, products, checkout totals
conftest.py               Shared fixtures, env URLs, failure artifact hook
.github/workflows/tests.yml
scripts/check_anti_flake.py   Local guard (no sleeps / brittle waits)
```

### Layer responsibilities

| Layer | Owns | Does not own |
|-------|------|----------------|
| **Tests** | Scenario steps, business assertions | Selectors, waits, URL construction |
| **Page objects** | Locators, navigation, page-load verification | Test data, fixture lifecycle |
| **API helpers** | HTTP assertions, schema checks | Session creation (fixture) |
| **conftest.py** | Fixtures, base URLs, Playwright config, failure hooks | Business logic |
| **constants** | Static test data | Runtime state |

Structure is intentionally flat — no `clients/`, `config/`, or service objects until maintenance cost demands them.

---

## 5. Fluent Page Object Model (POM)

Page objects encapsulate **how** the UI is driven; tests describe **what** the user does.

**Pattern:** transition methods perform the action, assert the destination page is loaded, and return the next page object. Tests chain calls without re-instantiating pages or repeating load checks.

```python
inventory = login_page.open().login_as(STANDARD_USER, PASSWORD)
inventory.add_to_cart(BACKPACK)
cart = inventory.open_cart()
```

| Method | Returns | Load verification |
|--------|---------|-------------------|
| `LoginPage.open()` | `LoginPage` | Login page visible |
| `LoginPage.login_as()` | `InventoryPage` | Inventory URL, title, product list |
| `LoginPage.submit_credentials()` | — | Used for negative login (no success navigation) |
| `InventoryPage.open_cart()` | `CartPage` | Cart URL, title, cart list |

Playwright `expect()` assertions run inside page objects — tests remain free of low-level wait logic.

---

## 6. Fixtures & Isolation

Defined in root `conftest.py`:

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `page` | function | Fresh browser context per UI test; console/error capture |
| `login_page` | function | UI test entry point |
| `http` | function | Fresh `requests.Session` with 10s timeout |
| `api_base_url` | session | Resolved from `API_BASE_URL` env var |
| `base_url` | session | Resolved from `BASE_URL` env var |

**Isolation guarantees:**

- No shared browser state, cookies, or cart between UI tests.
- No shared HTTP session between API tests.
- No test-order dependencies.
- `standard_user` is a public demo credential; parallel safety comes from **per-test browser contexts**, not unique usernames.

Playwright is configured globally to use Swag Labs `data-test` attributes via `get_by_test_id()`.

---

## 7. Test Data

| Layer | Location | Contents |
|-------|----------|----------|
| UI | `constants.py` | Credentials, exact UI strings, products, shipping, checkout totals |
| API | `tests/api/constants.py` | Post IDs, POST/PUT payloads |

**Principles:**

- Static values are centralized — tests do not hardcode copy or payloads.
- UI assertions use **exact strings** to detect copy regressions.
- JSONPlaceholder is stateless: DELETE verifies HTTP acceptance (200/204), not server-side removal.

---

## 8. Anti-Flakiness Strategy

| Rule | Implementation |
|------|----------------|
| No time-based waits | Prohibited: `time.sleep()`, `wait_for_timeout()`, `networkidle`. Enforced locally by `scripts/check_anti_flake.py` |
| Condition-based UI waits | Playwright action auto-wait + `expect()` on URL, visibility, text |
| Stable selectors | Priority: `data-test` → scoped text within known containers → avoid XPath/CSS chains |
| Timeouts | 10s action / 30s navigation ( `conftest.py` ) |
| Login per test | Explicit login in each UI scenario; at scale → Playwright `storageState` |
| External dependency risk | Live SaaS targets may introduce network variance; acceptable at current scale |

```bash
python scripts/check_anti_flake.py
```

---

## 9. Parallel Execution

All tests are safe for parallel runs.

```bash
pytest tests/ui --browser=chromium -n 2
pytest tests/api -m api
```

**First failure modes at scale:** external rate limits, runner CPU/memory under many Chromium workers, or fixtures accidentally scoped to session/module.

---

## 10. CI/CD

**Workflow:** `.github/workflows/tests.yml`

| Setting | Value |
|---------|-------|
| Trigger | `push`, `pull_request` → `main` |
| Runner | `ubuntu-latest` |
| Python | 3.14 |
| Strategy | Matrix: `api` ∥ `ui` |
| Job timeout | 15 minutes |

### Pipeline steps (per matrix job)

1. Checkout → setup Python (pip cache)
2. `pip install -r requirements.txt`
3. UI only: `python -m playwright install --with-deps chromium`
4. `mkdir -p test-results/artifacts`
5. Run pytest with suite marker
6. Upload artifact (`if: always()`)

| Job | Command | Env |
|-----|---------|-----|
| **api** | `pytest tests/api -m api` | `API_BASE_URL` |
| **ui** | `pytest tests/ui -m ui --browser=chromium -n 2` | `BASE_URL` |

Both jobs emit `test-results/report.html` and `test-results/junit.xml`.

---

## 11. Reporting & Triage

Artifacts: **`test-results-api`** and **`test-results-ui`** (14-day retention).

| Artifact | Source | Use |
|----------|--------|-----|
| `report.html` | pytest-html | Failing test, traceback, duration |
| `junit.xml` | pytest | CI dashboards, trend plugins |
| Trace, screenshot | pytest-playwright | UI failure replay (`playwright show-trace`) |
| `artifacts/<test>/page.html` | `conftest.py` hook | DOM at failure |
| `artifacts/<test>/console.log` | `conftest.py` hook | Browser console + page errors |
| `artifacts/<test>/meta.json` | `conftest.py` hook | URL and title at failure |

**Triage flow:**

1. Open failed run → download job artifact.
2. Read `report.html` → identify failing test and assertion.
3. UI: inspect trace/screenshot or `page.html` + `console.log`.
4. Reproduce locally: `pytest path::test_name --browser=chromium -v` (disable `-n` while debugging).
5. API: read traceback and helper assertion message (includes status/body context).

---

## 12. Evolution Path

Prioritized next steps if the suite grows:

1. **Environment control** — mock or staging endpoints for external targets (highest reliability ROI).
2. **API depth** — negative/malformed payload cases via existing helpers.
3. **UI performance** — `storageState` for login once scenario count justifies it.
4. **CI hardening** — optional `ruff` + anti-flake gate in pipeline; pinned dependency lockfile.

The current design is deliberately small. The next operational pain is **environment variance and CI signal quality**, not additional abstraction layers.
