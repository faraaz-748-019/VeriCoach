"""Base Page Object class for Mobile application testing using Appium."""

from __future__ import annotations

import base64
from typing import Any

from qa.framework.reporting.allure_helper import attach_screenshot, attach_text


class BaseMobilePage:
    """Foundational Mobile Page/Screen Object for Appium and simulated mobile environments."""

    def __init__(self, driver: Any) -> None:
        self.driver = driver

    def find_element(self, by: str, value: str) -> Any:
        """Find single mobile element using locator strategy."""
        try:
            return self.driver.find_element(by=by, value=value)
        except Exception as exc:
            self.take_screenshot(f"element_not_found_{value}")
            attach_text(
                f"Mobile element not found: [{by}] {value}", name="mobile_error"
            )
            raise exc

    def tap(self, by: str, value: str) -> None:
        """Tap or click mobile element."""
        element = self.find_element(by, value)
        element.click()

    def input_text(self, by: str, value: str, text: str) -> None:
        """Input text into mobile element."""
        element = self.find_element(by, value)
        element.clear()
        element.send_keys(text)

    def get_text(self, by: str, value: str) -> str:
        """Get visible text from mobile element."""
        element = self.find_element(by, value)
        return str(getattr(element, "text", "")).strip()

    def is_displayed(self, by: str, value: str) -> bool:
        """Check if mobile element is displayed."""
        try:
            element = self.find_element(by, value)
            return bool(getattr(element, "is_displayed", lambda: True)())
        except Exception:
            return False

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 800,
    ) -> None:
        """Execute swipe gesture on mobile screen."""
        if hasattr(self.driver, "swipe"):
            self.driver.swipe(start_x, start_y, end_x, end_y, duration_ms)
        elif hasattr(self.driver, "execute_script"):
            self.driver.execute_script(
                "mobile: swipeGesture",
                {
                    "left": start_x,
                    "top": start_y,
                    "width": abs(end_x - start_x),
                    "height": abs(end_y - start_y),
                    "direction": "down" if end_y > start_y else "up",
                    "percent": 0.75,
                },
            )

    def take_screenshot(self, name: str = "mobile_screenshot") -> bytes:
        """Capture mobile screen and attach to Allure."""
        try:
            if hasattr(self.driver, "get_screenshot_as_png"):
                png_bytes = self.driver.get_screenshot_as_png()
            elif hasattr(self.driver, "get_screenshot_as_base64"):
                b64 = self.driver.get_screenshot_as_base64()
                png_bytes = base64.b64decode(b64)
            else:
                png_bytes = b""

            if png_bytes:
                attach_screenshot(png_bytes, name=name)
            return png_bytes
        except Exception:
            return b""
