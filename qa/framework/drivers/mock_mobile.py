"""Deterministic mock mobile driver for CI and headless testing without Appium daemon."""

from __future__ import annotations

import base64
from typing import Any

# 1x1 transparent PNG bytes for mock screenshots
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
TINY_PNG_BYTES = base64.b64decode(TINY_PNG_B64)


class MockMobileElement:
    """Mock UI element conforming to Appium WebElement interface."""

    def __init__(self, locator_value: str, initial_text: str = "") -> None:
        self.locator_value = locator_value
        self.text = initial_text
        self.clicked = False
        self._displayed = True

    def click(self) -> None:
        self.clicked = True

    def send_keys(self, text: str) -> None:
        self.text += text

    def clear(self) -> None:
        self.text = ""

    def is_displayed(self) -> bool:
        return self._displayed


class MockMobileDriver:
    """Mock Appium WebDriver providing deterministic mobile automation in CI."""

    def __init__(self, capabilities: dict[str, Any] | None = None) -> None:
        self.capabilities = capabilities or {}
        self.is_connected = True
        self.elements: dict[str, MockMobileElement] = {
            "chat_input": MockMobileElement("chat_input", initial_text=""),
            "send_button": MockMobileElement("send_button", initial_text="Send"),
            "chat_messages": MockMobileElement(
                "chat_messages",
                initial_text="Namaste! I am VeriCoach, your personal-finance assistant.",
            ),
            "language_picker": MockMobileElement("language_picker", initial_text="en"),
        }

    def find_element(self, by: str, value: str) -> MockMobileElement:
        clean_key = value.split("/")[-1].replace("@id=", "").replace("'", "")
        if clean_key not in self.elements:
            self.elements[clean_key] = MockMobileElement(value, initial_text="")
        return self.elements[clean_key]

    def find_elements(self, by: str, value: str) -> list[MockMobileElement]:
        elem = self.find_element(by, value)
        return [elem]

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 800,
    ) -> None:
        pass

    def get_screenshot_as_png(self) -> bytes:
        return TINY_PNG_BYTES

    def get_screenshot_as_base64(self) -> str:
        return TINY_PNG_B64

    def quit(self) -> None:
        self.is_connected = False
