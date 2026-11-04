"""Deterministic mock mobile driver for CI and headless testing without Appium daemon."""

from __future__ import annotations

import base64
from typing import Any

# 1x1 transparent PNG bytes for mock screenshots
TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
TINY_PNG_BYTES = base64.b64decode(TINY_PNG_B64)

# Minimal valid MP4 ftyp box for mock screen recordings
TINY_MP4_B64 = "AAAAHGZ0eXBtcDQyAAAAAG1wNDJpc29tYXZjMQ=="
TINY_MP4_BYTES = base64.b64decode(TINY_MP4_B64)


class MockMobileElement:
    """Mock UI element conforming to Appium WebElement interface."""

    def __init__(
        self,
        locator_value: str,
        initial_text: str = "",
        displayed: bool = True,
        attributes: dict[str, str] | None = None,
        driver_ref: MockMobileDriver | None = None,
    ) -> None:
        self.locator_value = locator_value
        self.text = initial_text
        self.clicked = False
        self._displayed = displayed
        self._attributes: dict[str, str] = attributes or {}
        self._driver_ref = driver_ref

    def click(self) -> None:
        self.clicked = True
        if self._driver_ref:
            self._driver_ref._handle_element_click(self)

    def send_keys(self, text: str) -> None:
        self.text += text
        if self._driver_ref:
            self._driver_ref._handle_element_input(self, text)

    def clear(self) -> None:
        self.text = ""

    def is_displayed(self) -> bool:
        return self._displayed

    def is_enabled(self) -> bool:
        return True

    def get_attribute(self, name: str) -> str | None:
        if name in ("content-desc", "accessibility-id"):
            return self._attributes.get("content-desc", self.locator_value)
        if name in ("resource-id", "id"):
            return self._attributes.get("id", self.locator_value)
        if name == "text":
            return self.text
        return self._attributes.get(name)


class MockMobileDriver:
    """Mock Appium WebDriver providing deterministic mobile automation in CI."""

    def __init__(self, capabilities: dict[str, Any] | None = None) -> None:
        self.capabilities = capabilities or {}
        self.is_connected = True
        self._orientation = "PORTRAIT"
        self._network_connection = 6  # ALL_NETWORK_ON
        self._recording = False
        self._current_language = "en"
        self._last_input_text = ""

        # Conversation history state
        self.messages: list[dict[str, Any]] = [
            {
                "sender": "assistant",
                "text": "Namaste! I am VeriCoach, your personal-finance assistant.",
                "language": "en",
                "sources": [
                    {
                        "doc_id": "tax-80c",
                        "title": "Income Tax Act 1961 - Sec 80C",
                        "score": 0.94,
                    }
                ],
            }
        ]

        self._init_elements()

    def _init_elements(self) -> None:
        """Initialize mock UI elements corresponding to app components."""
        self.elements: dict[str, MockMobileElement] = {
            "chat-input": MockMobileElement(
                "chat-input",
                initial_text="",
                displayed=True,
                attributes={"id": "chat-input", "content-desc": "chat-input"},
                driver_ref=self,
            ),
            "chat_input": MockMobileElement(
                "chat_input",
                initial_text="",
                displayed=True,
                attributes={"id": "chat_input", "content-desc": "chat_input"},
                driver_ref=self,
            ),
            "send-button": MockMobileElement(
                "send-button",
                initial_text="Send",
                displayed=True,
                attributes={"id": "send-button", "content-desc": "send-button"},
                driver_ref=self,
            ),
            "send_button": MockMobileElement(
                "send_button",
                initial_text="Send",
                displayed=True,
                attributes={"id": "send_button", "content-desc": "send_button"},
                driver_ref=self,
            ),
            "language-select": MockMobileElement(
                "language-select",
                initial_text="en",
                displayed=True,
                attributes={"id": "language-select", "content-desc": "language-select"},
                driver_ref=self,
            ),
            "language_picker": MockMobileElement(
                "language_picker",
                initial_text="en",
                displayed=True,
                attributes={"id": "language_picker", "content-desc": "language_picker"},
                driver_ref=self,
            ),
            "offline-banner": MockMobileElement(
                "offline-banner",
                initial_text="Offline: You are offline. Check connection.",
                displayed=(self._network_connection == 1),
                attributes={"id": "offline-banner", "content-desc": "offline-banner"},
                driver_ref=self,
            ),
            "citations-toggle": MockMobileElement(
                "citations-toggle",
                initial_text="View Sources (1)",
                displayed=True,
                attributes={
                    "id": "citations-toggle",
                    "content-desc": "citations-toggle",
                },
                driver_ref=self,
            ),
            "citations-panel": MockMobileElement(
                "citations-panel",
                initial_text="Income Tax Act 1961 - Sec 80C (Score: 0.94)",
                displayed=False,
                attributes={"id": "citations-panel", "content-desc": "citations-panel"},
                driver_ref=self,
            ),
            "citation-item": MockMobileElement(
                "citation-item",
                initial_text="Income Tax Act 1961 - Sec 80C",
                displayed=False,
                attributes={"id": "citation-item", "content-desc": "citation-item"},
                driver_ref=self,
            ),
            "chat_messages": MockMobileElement(
                "chat_messages",
                initial_text=self.messages[-1]["text"],
                displayed=True,
                attributes={"id": "chat_messages", "content-desc": "chat_messages"},
                driver_ref=self,
            ),
            "message-assistant": MockMobileElement(
                "message-assistant",
                initial_text=self.messages[-1]["text"],
                displayed=True,
                attributes={
                    "id": "message-assistant",
                    "content-desc": "message-assistant",
                },
                driver_ref=self,
            ),
            "message-text": MockMobileElement(
                "message-text",
                initial_text=self.messages[-1]["text"],
                displayed=True,
                attributes={"id": "message-text", "content-desc": "message-text"},
                driver_ref=self,
            ),
        }

    def _handle_element_input(self, elem: MockMobileElement, text: str) -> None:
        """Handle typing into input elements."""
        if "input" in elem.locator_value:
            self._last_input_text = elem.text

    def _handle_element_click(self, elem: MockMobileElement) -> None:
        """Handle tap interactions on buttons."""
        clean = elem.locator_value.lower()
        if "send" in clean and self._last_input_text.strip():
            user_msg = self._last_input_text.strip()
            self.messages.append(
                {
                    "sender": "user",
                    "text": user_msg,
                    "language": self._current_language,
                }
            )
            # Generate assistant answer based on current language
            if self._current_language == "hi":
                resp_text = (
                    "नमस्ते! मैं वेरीकोच हूँ। धारा 80सी (Section 80C) के तहत आप पीपीएफ, "
                    "ईएलएसएस और जीवन बीमा में प्रति वर्ष ₹1.5 लाख तक निवेश करके कर छूट प्राप्त कर सकते हैं।"
                )
            elif self._current_language == "te":
                resp_text = (
                    "నమస్కారం! నేను వెరికోచ్. సెక్షన్ 80సి కింద మీరు పీపీఎఫ్, ఈఎల్ఎస్ఎస్ "
                    "మరియు జీవిత బీమాలో సంవత్సరానికి ₹1.5 లక్షల వరకు పెట్టుబడి చేసి పన్ను ఆదా చేసుకోవచ్చు."
                )
            else:
                resp_text = (
                    "Section 80C of the Income Tax Act allows deductions up to ₹1.5 Lakh per financial year "
                    "for investments in ELSS mutual funds, PPF, and life insurance."
                )

            self.messages.append(
                {
                    "sender": "assistant",
                    "text": resp_text,
                    "language": self._current_language,
                    "sources": [
                        {
                            "doc_id": "tax-80c",
                            "title": "Income Tax Act 1961 - Sec 80C",
                            "score": 0.94,
                        }
                    ],
                }
            )

            # Update latest response element
            self.elements["message-assistant"].text = resp_text
            self.elements["message-text"].text = resp_text
            self.elements["chat_messages"].text = resp_text
            self.elements["citations-toggle"]._displayed = True

            # Clear inputs
            self._last_input_text = ""
            if "chat-input" in self.elements:
                self.elements["chat-input"].text = ""
            if "chat_input" in self.elements:
                self.elements["chat_input"].text = ""

        elif "citations-toggle" in clean:
            # Toggle citations visibility
            is_shown = self.elements["citations-panel"]._displayed
            self.elements["citations-panel"]._displayed = not is_shown
            self.elements["citation-item"]._displayed = not is_shown
            self.elements["citations-toggle"].text = (
                "Hide Sources (1)" if not is_shown else "View Sources (1)"
            )

    def set_language(self, lang_code: str) -> None:
        """Helper to switch application language."""
        self._current_language = lang_code
        if "language-select" in self.elements:
            self.elements["language-select"].text = lang_code
        if "language_picker" in self.elements:
            self.elements["language_picker"].text = lang_code

        # If switching language, set initial greeting according to language
        if lang_code == "hi":
            greeting = "नमस्ते! मैं वेरीकोच हूँ, आपका व्यक्तिगत वित्तीय सहायक। मैं आपकी क्या मदद कर सकता हूँ?"
        elif lang_code == "te":
            greeting = "నమస్కారం! నేను వెరికోచ్, మీ వ్యక్తిగత ఆర్థిక సహాయకుడిని. నేను మీకు ఎలా సహాయపడగలను?"
        else:
            greeting = "Namaste! I am VeriCoach, your personal-finance assistant."

        self.messages.append(
            {
                "sender": "assistant",
                "text": greeting,
                "language": lang_code,
                "sources": [
                    {
                        "doc_id": "tax-80c",
                        "title": "Income Tax Act 1961 - Sec 80C",
                        "score": 0.94,
                    }
                ],
            }
        )
        self.elements["message-assistant"].text = greeting
        self.elements["message-text"].text = greeting
        self.elements["chat_messages"].text = greeting

    @property
    def orientation(self) -> str:
        return self._orientation

    @orientation.setter
    def orientation(self, value: str) -> None:
        self._orientation = value.upper()

    @property
    def network_connection(self) -> int:
        return self._network_connection

    def set_network_connection(self, connection_type: int) -> None:
        """Appium ConnectionType: 1 is AIRPLANE_MODE, 6 is ALL_NETWORK_ON."""
        self._network_connection = connection_type
        # When airplane mode (1), offline banner is displayed
        is_offline = connection_type == 1
        if "offline-banner" in self.elements:
            self.elements["offline-banner"]._displayed = is_offline

    def start_recording_screen(self, **kwargs: Any) -> None:
        self._recording = True

    def stop_recording_screen(self, **kwargs: Any) -> str:
        self._recording = False
        return TINY_MP4_B64

    def background_app(self, seconds: int) -> None:
        """Simulate backgrounding and resuming app; conversation history is preserved."""
        pass

    def activate_app(self, app_id: str) -> None:
        pass

    def find_element(self, by: str, value: str) -> MockMobileElement:
        clean_key = (
            value.split("/")[-1]
            .replace("@id=", "")
            .replace("@data-accessibility-id=", "")
            .replace("@content-desc=", "")
            .replace("'", "")
            .replace('"', "")
            .replace("[", "")
            .replace("]", "")
        )
        for key in (clean_key, value):
            if key in self.elements:
                return self.elements[key]

        # Auto-match substring
        for k, elem in self.elements.items():
            if k in clean_key or clean_key in k:
                return elem

        # Create dynamically if not found
        elem = MockMobileElement(value, initial_text="", driver_ref=self)
        self.elements[clean_key] = elem
        return elem

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
        # Scrolling makes citations panel visible if toggle was clicked
        pass

    def get_screenshot_as_png(self) -> bytes:
        return TINY_PNG_BYTES

    def get_screenshot_as_base64(self) -> str:
        return TINY_PNG_B64

    def quit(self) -> None:
        self.is_connected = False
