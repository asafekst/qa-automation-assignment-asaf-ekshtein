import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests
from playwright.sync_api import Playwright

from pages.login_page import LoginPage
from tests.api.constants import NEW_POST, UPDATED_POST

# --- UI (Swag Labs) ---

DEFAULT_UI_BASE_URL = "https://www.saucedemo.com"
UI_ACTION_TIMEOUT_MS = 10_000
UI_NAVIGATION_TIMEOUT_MS = 30_000

# --- API (JSONPlaceholder) ---

DEFAULT_API_BASE_URL = "https://jsonplaceholder.typicode.com"
API_REQUEST_TIMEOUT_SEC = 10

ARTIFACTS_ROOT = Path("test-results/artifacts")


def _resolve_base_url(env_var: str, default: str) -> str:
    raw = os.getenv(env_var, default).strip()
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"Invalid {env_var} '{raw}'. Expected http(s) URL, e.g. {default}"
        )
    return raw.rstrip("/")


UI_BASE_URL = _resolve_base_url("BASE_URL", DEFAULT_UI_BASE_URL)


class ApiSession(requests.Session):
    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", API_REQUEST_TIMEOUT_SEC)
        return super().request(method, url, **kwargs)


def pytest_sessionstart(session: pytest.Session) -> None:
    ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)


def _artifact_dir(nodeid: str) -> Path:
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    safe = re.sub(r"[^\w.-]+", "_", nodeid).strip("_")[:120]
    if worker:
        safe = f"{worker}_{safe}"
    return ARTIFACTS_ROOT / safe


def _save_ui_failure_artifacts(
    page, nodeid: str, out: Path, console_log: list[str]
) -> None:
    out.mkdir(parents=True, exist_ok=True)

    try:
        page.screenshot(path=str(out / "screenshot.png"), full_page=True)
    except Exception as exc:  # noqa: BLE001 — best-effort artifact
        (out / "screenshot.error.txt").write_text(str(exc), encoding="utf-8")

    try:
        (out / "page.html").write_text(page.content(), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        (out / "page.html").write_text(
            f"<!-- capture failed: {exc} -->", encoding="utf-8"
        )

    try:
        viewport = page.viewport_size or {}
        meta = {
            "test": nodeid,
            "captured_at": datetime.now(UTC).isoformat(),
            "url": page.url,
            "title": page.title(),
            "viewport": viewport,
        }
        (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        (out / "meta.json").write_text(
            json.dumps({"test": nodeid, "error": str(exc)}), encoding="utf-8"
        )

    (out / "console.log").write_text(
        "\n".join(console_log) if console_log else "(no browser console messages)",
        encoding="utf-8",
    )


# --- Playwright (UI only — browser fixtures load when UI tests request `page`) ---


@pytest.fixture(scope="session")
def _swag_labs_test_id(playwright: Playwright) -> None:
    """Swag Labs uses data-test, not the default data-testid. UI-only (via login_page)."""
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(scope="session")
def base_url() -> str:
    return UI_BASE_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    # Function-scoped context/page per test (pytest-playwright default) — safe for -n 2+.
    return {
        **browser_context_args,
        "base_url": UI_BASE_URL,
        "ignore_https_errors": False,
    }


@pytest.fixture(autouse=True)
def _ui_page_instrumentation(request: pytest.FixtureRequest):
    """Attach console capture and timeouts to the Playwright page for UI tests only."""
    if request.node.get_closest_marker("ui") is None:
        yield
        return

    page = request.getfixturevalue("page")
    console_log: list[str] = []

    def _on_console(msg) -> None:
        console_log.append(f"[{msg.type}] {msg.text}")

    def _on_page_error(exc: BaseException) -> None:
        console_log.append(f"[pageerror] {exc}")

    page.on("console", _on_console)
    page.on("pageerror", _on_page_error)
    page.set_default_timeout(UI_ACTION_TIMEOUT_MS)
    page.set_default_navigation_timeout(UI_NAVIGATION_TIMEOUT_MS)
    request.node._console_log = console_log  # type: ignore[attr-defined]
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    if item.get_closest_marker("ui") is None:
        return

    page = item.funcargs.get("page")
    if page is None:
        return

    _save_ui_failure_artifacts(
        page,
        item.nodeid,
        _artifact_dir(item.nodeid),
        getattr(item, "_console_log", []),
    )


@pytest.fixture
def login_page(page, _swag_labs_test_id: None) -> LoginPage:
    return LoginPage(page)


# --- API ---


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return _resolve_base_url("API_BASE_URL", DEFAULT_API_BASE_URL)


@pytest.fixture
def http() -> requests.Session:
    session = ApiSession()
    session.headers.update(
        {"Accept": "application/json", "Content-Type": "application/json"}
    )
    yield session
    session.close()


@pytest.fixture
def new_post() -> dict:
    return NEW_POST


@pytest.fixture
def updated_post() -> dict:
    return UPDATED_POST
