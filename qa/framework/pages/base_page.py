"""Base Page Object class for Web UI automation using Playwright."""

from __future__ import annotations

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from qa.framework.reporting.allure_helper import attach_screenshot, attach_text


class BaseWebPage:
    """Foundational Page Object encapsulating Playwright interactions and diagnostics."""

    def __init__(self, page: Page, base_url: str = "http://localhost:8000") -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str = "/") -> None:
        """Navigate to target path under base URL."""
        target_url = (
            f"{self.base_url}{path}"
            if path.startswith("/")
            else f"{self.base_url}/{path}"
        )
        try:
            self.page.goto(target_url, wait_until="domcontentloaded")
        except Exception as exc:
            self.take_screenshot("navigation_error")
            raise exc

    def locator(self, selector: str) -> Locator:
        """Resolve Playwright locator."""
        return self.page.locator(selector)

    def wait_for_selector(self, selector: str, timeout_ms: int = 10000) -> Locator:
        """Wait explicitly for selector to become visible."""
        try:
            loc = self.page.locator(selector)
            loc.wait_for(state="visible", timeout=timeout_ms)
            return loc
        except PlaywrightTimeoutError as exc:
            self.take_screenshot(f"timeout_waiting_{selector}")
            attach_text(
                f"Timed out waiting for visible selector: {selector}",
                name="selector_timeout",
            )
            raise exc

    def click(self, selector: str, timeout_ms: int = 10000) -> None:
        """Wait for selector and click."""
        try:
            self.page.locator(selector).click(timeout=timeout_ms)
        except Exception as exc:
            self.take_screenshot(f"click_error_{selector}")
            raise exc

    def fill(self, selector: str, text: str, timeout_ms: int = 10000) -> None:
        """Fill input field with text."""
        try:
            loc = self.page.locator(selector)
            loc.fill(text, timeout=timeout_ms)
        except Exception as exc:
            self.take_screenshot(f"fill_error_{selector}")
            raise exc

    def get_text(self, selector: str, timeout_ms: int = 5000) -> str:
        """Extract inner text from element."""
        try:
            return self.page.locator(selector).inner_text(timeout=timeout_ms).strip()
        except Exception as exc:
            self.take_screenshot(f"get_text_error_{selector}")
            raise exc

    def is_visible(self, selector: str, timeout_ms: int = 3000) -> bool:
        """Check if element is visible within timeout without throwing."""
        try:
            self.page.locator(selector).wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            return False

    def press_key(self, selector: str, key: str, timeout_ms: int = 10000) -> None:
        """Focus on selector and dispatch keyboard key press."""
        try:
            self.page.locator(selector).press(key, timeout=timeout_ms)
        except Exception as exc:
            self.take_screenshot(f"press_key_error_{key}")
            raise exc

    def select_option(self, selector: str, value: str, timeout_ms: int = 10000) -> None:
        """Select option by value in <select> dropdown."""
        try:
            self.page.locator(selector).select_option(value, timeout=timeout_ms)
        except Exception as exc:
            self.take_screenshot(f"select_option_error_{value}")
            raise exc

    def take_screenshot(self, name: str = "web_screenshot") -> bytes:
        """Capture browser screenshot and attach to Allure report."""
        try:
            screenshot_bytes = self.page.screenshot(full_page=True)
            attach_screenshot(screenshot_bytes, name=name)
            return screenshot_bytes
        except Exception:
            return b""
