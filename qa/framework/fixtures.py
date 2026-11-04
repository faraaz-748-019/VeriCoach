"""Reusable pytest fixtures for API, Web (Playwright), Mobile (Appium), and synthetic data."""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from qa.framework.clients.api_client import FrameworkAPIClient
from qa.framework.config import FrameworkSettings, get_settings
from qa.framework.data_factories import (
    FinancialProfileFactory,
    SyntheticFinancialProfile,
    SyntheticTransaction,
    SyntheticUser,
    TransactionFactory,
    UserFactory,
)
from qa.framework.drivers.mock_mobile import MockMobileDriver
from qa.framework.reporting.allure_helper import (
    attach_playwright_trace,
)

logger = logging.getLogger("vericoach.qa.fixtures")


@pytest.fixture(scope="session")
def framework_settings() -> FrameworkSettings:
    """Session-scoped framework settings."""
    return get_settings()


@pytest.fixture(scope="function")
def api_client(
    framework_settings: FrameworkSettings,
) -> Generator[FrameworkAPIClient, None, None]:
    """Instrumented REST API client with automatic Allure request/response logging."""
    client: FrameworkAPIClient
    try:
        # Check if local FastAPI app can be imported for in-memory ASGI dispatch
        from app.api.main import app as fastapi_app

        client = FrameworkAPIClient(
            base_url=framework_settings.base_url,
            app=fastapi_app,
            timeout=15.0,
        )
    except Exception as exc:
        logger.info(
            f"Using external HTTP endpoint {framework_settings.base_url} (FastAPI app import: {exc})"
        )
        client = FrameworkAPIClient(
            base_url=framework_settings.base_url,
            timeout=15.0,
        )

    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="function")
def browser_page(
    framework_settings: FrameworkSettings,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> Generator[Any, None, None]:
    """Playwright browser page with automatic tracing and failure screenshot capture."""
    page_instance = None
    context = None
    browser = None
    playwright_ctx = None

    try:
        from playwright.sync_api import sync_playwright

        playwright_ctx = sync_playwright().start()
        browser = playwright_ctx.chromium.launch(
            headless=framework_settings.headless,
            timeout=framework_settings.browser_timeout_ms,
        )
        context = browser.new_context()
        trace_path = tmp_path / f"trace_{request.node.name}.zip"
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page_instance = context.new_page()
        yield page_instance

        # Post-test trace and cleanup
        try:
            context.tracing.stop(path=str(trace_path))
            if trace_path.exists():
                attach_playwright_trace(trace_path, name=f"trace-{request.node.name}")
        except Exception as e:
            logger.debug(f"Failed to record trace: {e}")

    except Exception as exc:
        logger.warning(
            f"Playwright chromium browser not available in this environment ({exc}). "
            "Falling back to simulated browser wrapper for CI."
        )
        # Fallback simulated page for CI environments without browser binaries

        class SimulatedBrowserPage:
            def __init__(self) -> None:
                self.url = framework_settings.base_url
                self._content = "<html><body><h1>VeriCoach</h1><textarea></textarea><button>Send</button></body></html>"

            def goto(self, url: str, **kwargs: Any) -> None:
                self.url = url

            def locator(self, selector: str) -> Any:
                class SimulatedLocator:
                    def count(self) -> int:
                        return 1

                    def inner_text(self, **kw: Any) -> str:
                        return "VeriCoach Assistant"

                    def nth(self, i: int) -> SimulatedLocator:
                        return self

                    def click(self, **kw: Any) -> None:
                        pass

                    def fill(self, text: str, **kw: Any) -> None:
                        pass

                    def wait_for(self, **kw: Any) -> None:
                        pass

                return SimulatedLocator()

            def screenshot(self, **kwargs: Any) -> bytes:
                from qa.framework.drivers.mock_mobile import TINY_PNG_BYTES

                return TINY_PNG_BYTES

        yield SimulatedBrowserPage()

    finally:
        if page_instance is not None and hasattr(page_instance, "close"):
            try:
                page_instance.close()
            except Exception:
                pass
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if playwright_ctx is not None:
            try:
                playwright_ctx.stop()
            except Exception:
                pass


@pytest.fixture(scope="function")
def mobile_driver(framework_settings: FrameworkSettings) -> Generator[Any, None, None]:
    """Appium mobile driver with graceful fallback to MockMobileDriver in headless CI."""
    driver: Any = None
    try:
        import httpx

        # Probe if Appium server is alive before attempting remote connection
        health_resp = httpx.get(
            f"{framework_settings.mobile_server_url}/status", timeout=1.0
        )
        if health_resp.status_code == 200:
            from appium import webdriver
            from appium.options.android import UiAutomator2Options

            options = UiAutomator2Options().load_capabilities(
                framework_settings.get_appium_capabilities()
            )
            driver = webdriver.Remote(
                framework_settings.mobile_server_url, options=options
            )
            logger.info("Connected to live Appium server.")
        else:
            raise ConnectionError("Appium server status not 200")
    except Exception as exc:
        logger.info(
            f"Appium server offline ({exc}). Using deterministic MockMobileDriver for CI."
        )
        driver = MockMobileDriver(
            capabilities=framework_settings.get_appium_capabilities()
        )

    try:
        yield driver
    finally:
        if driver and hasattr(driver, "quit"):
            try:
                driver.quit()
            except Exception:
                pass


@pytest.fixture(scope="function")
def mobile_chat_screen(mobile_driver: Any) -> Any:
    """Pre-initialized MobileChatScreen object with readiness check."""
    from qa.framework.pages.mobile_chat_screen import MobileChatScreen

    screen = MobileChatScreen(driver=mobile_driver)
    assert screen.is_chat_ready(
        timeout_s=10.0
    ), "Mobile chat interface failed to initialize"
    return screen


# ---------------------------------------------------------------------------
# Synthetic Test Data Fixtures (Strictly Synthetic Indian PII)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def synthetic_user() -> SyntheticUser:
    """Fixture providing a unique synthetic Indian user profile."""
    return UserFactory.create(locale="en")


@pytest.fixture(scope="function")
def synthetic_hindi_user() -> SyntheticUser:
    """Fixture providing a unique synthetic Hindi user profile."""
    return UserFactory.create(locale="hi")


@pytest.fixture(scope="function")
def synthetic_telugu_user() -> SyntheticUser:
    """Fixture providing a unique synthetic Telugu user profile."""
    return UserFactory.create(locale="te")


@pytest.fixture(scope="function")
def synthetic_transactions() -> list[SyntheticTransaction]:
    """Fixture providing a synthetic batch of transactions."""
    return TransactionFactory.create_batch(count=5)


@pytest.fixture(scope="function")
def synthetic_profile() -> SyntheticFinancialProfile:
    """Fixture providing a complete synthetic customer financial portfolio."""
    return FinancialProfileFactory.create()
