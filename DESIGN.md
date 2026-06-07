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
| `ui` / `api` | Suite filter for local runs and CI parallel jobs |

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
pages/
  login_page.py           Fluent POM — login
  inventory_page.py       Fluent POM — catalog / cart badge
  cart_page.py            Fluent POM — cart lines
  checkout_page.py        Fluent POM — checkout funnel
  assertions.py           Shared Playwright assertions
tests/
  ui/                     4 UI scenarios
  api/
    test_posts.py         API scenarios
    helpers.py            URL builder + HTTP assertions
    constants.py          Post IDs and payloads
constants.py              UI credentials, copy, products, checkout totals
conftest.py               Fixtures, env URLs, failure artifact hook
pytest.ini                Markers, strict mode, report defaults
pyproject.toml            Ruff lint config
requirements.txt
README.md
DESIGN.md
.env.example
.github/workflows/tests.yml
scripts/check_anti_flake.py
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
| Strategy | Parallel jobs: `api` ∥ `ui` |
| Job timeout | 15 minutes |

### Pipeline steps (per job)

1. Checkout → setup Python 3.14 (pip cache)
2. `pip install -r requirements.txt` + anti-flake guard
3. UI only: `python -m playwright install --with-deps chromium`
4. `mkdir -p test-results/artifacts`
5. **Single non-duplicative run** — if no `api/ui and not smoke` tests exist, one `-m "smoke and …"` run with `--maxfail=1` and reports; otherwise smoke gate then regression slice only
6. Upload artifact (`if: always()`)

| Job | When all tests are smoke (today) | When regressions exist | Env |
|-----|----------------------------------|------------------------|-----|
| **api** | `pytest tests/api -m "smoke and api" --maxfail=1` (once) | smoke gate → `pytest -m "api and not smoke"` | `API_BASE_URL` |
| **ui** | `pytest tests/ui -m "smoke and ui" -n 2 --maxfail=1` (once) | smoke gate → `pytest -m "ui and not smoke" -n 2` | `BASE_URL` |

Playwright artifact options live in `pytest.ini` (not duplicated on the CLI).

Both jobs emit `test-results/report.html` and `test-results/junit.xml`.

---

## 11. Reporting & Triage

Artifacts: **`test-results-api`** and **`test-results-ui`** (14-day retention).

| Artifact | Source | Use |
|----------|--------|-----|
| `report.html` | pytest-html | Failing test, traceback, duration |
| `junit.xml` | pytest | CI dashboards, trend plugins |
| Trace (`.zip`), screenshot (`.png`), video | pytest-playwright (`retain-on-failure` / `only-on-failure`) | UI failure replay (`playwright show-trace <trace.zip>`) |
| `artifacts/<test>/page.html` | `conftest.py` hook | HTML DOM snapshot at failure |
| `artifacts/<test>/console.log` | `conftest.py` hook | Browser console + page errors |
| `artifacts/<test>/meta.json` | `conftest.py` hook | URL, title, viewport, timestamp |
| `artifacts/<test>/screenshot.png` | `conftest.py` hook | Full-page screenshot at failure |

**Triage flow:**

1. Open failed run → download job artifact.
2. Read `report.html` → identify failing test and assertion.
3. UI: inspect trace/screenshot or `page.html` + `console.log`.
4. Reproduce locally: `pytest path::test_name --browser=chromium -v` (disable `-n` while debugging).
5. API: read traceback and helper assertion message (includes status/body context).

---

## 12. AI Tooling (Cursor)

| Use | How |
|-----|-----|
| Scaffolding | Initial pytest + Playwright layout, page objects, and API helpers |
| CI debugging | Identified `pipefail` + pytest exit-code 5 interaction in smoke detection |
| Documentation | README/DESIGN alignment with actual workflow and artifact layout |
| Review discipline | Architecture, assertions, and trade-offs remain human-owned; AI output is verified by local runs + CI |

Cursor accelerated boilerplate and cross-file consistency; it did not replace judgment on anti-flakiness rules, test isolation, or what belongs in page objects vs tests.

---

## 13. Next 48 Hours

If the suite had two more working days, priority order:

1. **Staging / mocks** — remove live-network variance for Swag Labs and JSONPlaceholder (highest stability ROI).
2. **Regression slice** — add `@pytest.mark.api` / `@pytest.mark.ui` tests *without* `smoke` (negative API payloads, sort/filter UI bonus).
3. **`storageState` login** — cut UI runtime once scenario count exceeds ~10.
4. **Lockfile + scheduled CI** — `pip-tools` pin file; nightly workflow against live targets for drift detection.
5. **Allure or trend dashboard** — only if stakeholders need historical charts beyond pytest-html + JUnit.

---

## 14. Longer-Term Evolution

1. **Environment control** — mock or staging endpoints for external targets.
2. **API depth** — malformed payload and auth-edge cases via existing helpers.
3. **UI performance** — parallel worker tuning and runner resource limits documented from real CI metrics.
4. **CI hardening** — dependency lockfile; optional `ruff` gate in pipeline.

The current design is deliberately small. The next operational pain is **environment variance and CI signal quality**, not additional abstraction layers.
