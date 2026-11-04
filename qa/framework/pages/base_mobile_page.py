"""Base Page Object class for Mobile application testing using Appium."""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from qa.framework.reporting.allure_helper import (
    attach_screenshot,
    attach_text,
    attach_video,
)

logger = logging.getLogger("vericoach.qa.mobile.page")


class BaseMobilePage:
    """Foundational Mobile Page/Screen Object for Appium and Android testing."""

    def __init__(self, driver: Any, default_timeout_s: float = 15.0) -> None:
        self.driver = driver
        self.default_timeout_s = default_timeout_s

    def _normalize_locator(self, by: str, value: str) -> tuple[str, str]:
        """Map shorthand strategies ('accessibility id', 'id', 'xpath', 'uiautomator') to AppiumBy."""
        by_clean = by.lower().replace("_", " ").strip()
        if by_clean in ("accessibility id", "accessibility-id", "accessibility_id"):
            return AppiumBy.ACCESSIBILITY_ID, value
        if by_clean in ("id", "resource-id", "resource_id"):
            return AppiumBy.ID, value
        if by_clean == "xpath":
            return AppiumBy.XPATH, value
        if by_clean in ("uiautomator", "android uiautomator"):
            return AppiumBy.ANDROID_UIAUTOMATOR, value
        if by_clean == "class name":
            return AppiumBy.CLASS_NAME, value
        return by, value

    def find_element(self, by: str, value: str, timeout_s: float | None = None) -> Any:
        """Find a single mobile element using explicit wait."""
        timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        mapped_by, mapped_value = self._normalize_locator(by, value)

        # Direct fast lookup for MockMobileDriver in offline CI
        if hasattr(self.driver, "find_element") and not hasattr(
            self.driver, "session_id"
        ):
            try:
                return self.driver.find_element(mapped_by, mapped_value)
            except Exception:
                pass

        try:
            wait = WebDriverWait(
                self.driver,
                timeout=timeout,
                poll_frequency=0.3,
                ignored_exceptions=(
                    NoSuchElementException,
                    StaleElementReferenceException,
                ),
            )
            return wait.until(EC.presence_of_element_located((mapped_by, mapped_value)))
        except (TimeoutException, Exception) as exc:
            self.take_screenshot(f"element_not_found_{value}")
            attach_text(
                f"Mobile element not found within {timeout}s: [{mapped_by}] {mapped_value}",
                name="mobile_locator_error",
            )
            raise NoSuchElementException(
                f"Element [{mapped_by}]='{mapped_value}' not located within {timeout}s."
            ) from exc

    def find_elements(self, by: str, value: str) -> list[Any]:
        """Find multiple mobile elements matching the locator."""
        mapped_by, mapped_value = self._normalize_locator(by, value)
        try:
            return self.driver.find_elements(mapped_by, mapped_value)
        except Exception:
            return []

    def tap(self, by: str, value: str, timeout_s: float | None = None) -> None:
        """Wait explicitly until element is clickable and tap it."""
        timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        mapped_by, mapped_value = self._normalize_locator(by, value)

        if hasattr(self.driver, "session_id"):
            wait = WebDriverWait(self.driver, timeout=timeout, poll_frequency=0.3)
            elem = wait.until(EC.element_to_be_clickable((mapped_by, mapped_value)))
            elem.click()
        else:
            element = self.find_element(by, value, timeout_s=timeout)
            element.click()

    def input_text(
        self,
        by: str,
        value: str,
        text: str,
        clear_first: bool = True,
        timeout_s: float | None = None,
    ) -> None:
        """Wait for element and enter text."""
        element = self.find_element(by, value, timeout_s=timeout_s)
        if clear_first:
            try:
                element.clear()
            except Exception:
                pass
        element.send_keys(text)

    def get_text(self, by: str, value: str, timeout_s: float | None = None) -> str:
        """Retrieve visible text from mobile element."""
        element = self.find_element(by, value, timeout_s=timeout_s)
        text = getattr(element, "text", "")
        if not text and hasattr(element, "get_attribute"):
            text = (
                element.get_attribute("text")
                or element.get_attribute("content-desc")
                or ""
            )
        return str(text).strip()

    def is_displayed(self, by: str, value: str, timeout_s: float = 2.0) -> bool:
        """Check if mobile element is displayed on screen within short timeout."""
        try:
            element = self.find_element(by, value, timeout_s=timeout_s)
            if hasattr(element, "is_displayed"):
                return bool(element.is_displayed())
            return True
        except Exception:
            return False

    def scroll_to_element(self, by: str, value: str, max_swipes: int = 5) -> Any:
        """Scroll downward until the targeted element becomes displayed."""
        for _attempt in range(max_swipes):
            if self.is_displayed(by, value, timeout_s=1.0):
                return self.find_element(by, value, timeout_s=1.0)
            self.scroll_down(percent=0.6)
            time.sleep(0.3)

        if self.is_displayed(by, value, timeout_s=2.0):
            return self.find_element(by, value)
        raise NoSuchElementException(
            f"Could not scroll to element [{by}] {value} after {max_swipes} swipes."
        )

    def scroll_down(self, percent: float = 0.6) -> None:
        """Execute downward vertical scroll gesture."""
        if hasattr(self.driver, "session_id") and hasattr(
            self.driver, "get_window_size"
        ):
            try:
                size = self.driver.get_window_size()
                width = size["width"]
                height = size["height"]
                start_x = width // 2
                start_y = int(height * 0.8)
                end_y = int(height * (0.8 - percent))

                self.driver.swipe(start_x, start_y, start_x, end_y, duration=600)
                return
            except Exception as exc:
                logger.debug(f"Native swipe fallback: {exc}")

        if hasattr(self.driver, "swipe"):
            self.driver.swipe(500, 1400, 500, 600, duration=600)

    def rotate(self, orientation: str) -> None:
        """Rotate device to LANDSCAPE or PORTRAIT."""
        clean_orient = orientation.upper()
        if hasattr(self.driver, "orientation"):
            self.driver.orientation = clean_orient
        elif hasattr(self.driver, "_orientation"):
            self.driver._orientation = clean_orient

    def get_orientation(self) -> str:
        """Query current orientation."""
        if hasattr(self.driver, "orientation"):
            return str(self.driver.orientation).upper()
        return "PORTRAIT"

    def background_app(self, seconds: int = 2) -> None:
        """Put app in background for specified seconds, then restore."""
        if hasattr(self.driver, "background_app"):
            self.driver.background_app(seconds)
        time.sleep(0.5)

    def set_airplane_mode(self, enabled: bool) -> None:
        """Toggle airplane mode using Appium network connection or adb broadcast."""
        # Appium ConnectionType: 1 = AIRPLANE_MODE, 6 = ALL_NETWORK_ON
        conn_type = 1 if enabled else 6

        if hasattr(self.driver, "set_network_connection"):
            try:
                self.driver.set_network_connection(conn_type)
                time.sleep(1.0)
                return
            except Exception as exc:
                logger.debug(f"driver.set_network_connection failed: {exc}")

        # Fallback for Android via adb shell broadcast if supported
        if hasattr(self.driver, "execute_script"):
            try:
                self.driver.execute_script(
                    "mobile: shell",
                    {
                        "command": "cmd",
                        "args": [
                            "connectivity",
                            "airplane-mode",
                            "enable" if enabled else "disable",
                        ],
                    },
                )
            except Exception:
                pass

    def start_recording(self) -> None:
        """Begin video screen capture."""
        if hasattr(self.driver, "start_recording_screen"):
            try:
                self.driver.start_recording_screen()
            except Exception as exc:
                logger.debug(f"Failed to start screen recording: {exc}")

    def stop_recording(
        self, attach_to_allure: bool = True, name: str = "failure_video"
    ) -> bytes:
        """Stop video screen capture and optionally attach MP4 to Allure."""
        if hasattr(self.driver, "stop_recording_screen"):
            try:
                b64_str = self.driver.stop_recording_screen()
                if b64_str:
                    video_bytes = base64.b64decode(b64_str)
                    if attach_to_allure and video_bytes:
                        attach_video(video_bytes, name=name)
                    return video_bytes
            except Exception as exc:
                logger.debug(f"Failed to stop screen recording: {exc}")
        return b""

    def take_screenshot(self, name: str = "mobile_screenshot") -> bytes:
        """Capture mobile screenshot and attach to Allure."""
        try:
            png_bytes = b""
            if hasattr(self.driver, "get_screenshot_as_png"):
                png_bytes = self.driver.get_screenshot_as_png()
            elif hasattr(self.driver, "get_screenshot_as_base64"):
                b64 = self.driver.get_screenshot_as_base64()
                png_bytes = base64.b64decode(b64)

            if png_bytes:
                attach_screenshot(png_bytes, name=name)
            return png_bytes
        except Exception as exc:
            logger.debug(f"Failed to capture mobile screenshot: {exc}")
            return b""
