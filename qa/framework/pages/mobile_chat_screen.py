"""Mobile Screen Object for the VeriCoach Android Multilingual Chat Interface."""

from __future__ import annotations

import logging
import time

from qa.framework.pages.base_mobile_page import BaseMobilePage

logger = logging.getLogger("vericoach.qa.mobile.chat")


class MobileChatScreen(BaseMobilePage):
    """Screen Object modeling the VeriCoach Android mobile chat interface.

    Uses accessibility-id and resource-id locators with explicit waits.
    Supports English, Hindi, and Telugu multilingual queries, citations inspection,
    orientation changes, background/foreground state retention, and offline banners.
    """

    # Primary locators using accessibility id / resource-id
    ACC_CHAT_INPUT = "chat-input"
    ACC_SEND_BUTTON = "send-button"
    ACC_LANG_SELECT = "language-select"
    ACC_OFFLINE_BANNER = "offline-banner"
    ACC_CITATIONS_TOGGLE = "citations-toggle"
    ACC_CITATIONS_PANEL = "citations-panel"
    ACC_CITATION_ITEM = "citation-item"
    ACC_MESSAGE_ASSISTANT = "message-assistant"
    ACC_MESSAGE_USER = "message-user"
    ACC_MESSAGE_TEXT = "message-text"

    # Fallback IDs for alternate Android resource-id conventions
    ID_CHAT_INPUT = "chat_input"
    ID_SEND_BUTTON = "send_button"
    ID_CHAT_MESSAGES = "chat_messages"
    ID_LANG_PICKER = "language_picker"

    def is_chat_ready(self, timeout_s: float = 10.0) -> bool:
        """Verify chat input and send button are displayed and ready."""
        try:
            return self.is_displayed(
                "accessibility id", self.ACC_CHAT_INPUT, timeout_s=timeout_s
            ) or self.is_displayed("id", self.ID_CHAT_INPUT, timeout_s=2.0)
        except Exception:
            return False

    def send_message(self, message: str) -> None:
        """Type financial question into mobile input and submit."""
        # Locate chat input via accessibility id or resource-id
        input_locator = (
            ("accessibility id", self.ACC_CHAT_INPUT)
            if self.is_displayed("accessibility id", self.ACC_CHAT_INPUT, timeout_s=3.0)
            else ("id", self.ID_CHAT_INPUT)
        )
        self.input_text(input_locator[0], input_locator[1], message, clear_first=True)

        # Locate send button via accessibility id or resource-id
        send_locator = (
            ("accessibility id", self.ACC_SEND_BUTTON)
            if self.is_displayed(
                "accessibility id", self.ACC_SEND_BUTTON, timeout_s=3.0
            )
            else ("id", self.ID_SEND_BUTTON)
        )
        self.tap(send_locator[0], send_locator[1])

    def wait_for_response(self, timeout_s: float = 15.0) -> str:
        """Wait explicitly until assistant reply arrives and return its text."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            resp = self.get_latest_response()
            if (
                resp
                and resp != "Namaste! I am VeriCoach, your personal-finance assistant."
            ):
                return resp
            time.sleep(0.5)
        return self.get_latest_response()

    def get_latest_response(self) -> str:
        """Retrieve latest assistant response text."""
        # Check accessibility id
        if self.is_displayed(
            "accessibility id", self.ACC_MESSAGE_ASSISTANT, timeout_s=1.0
        ):
            return self.get_text("accessibility id", self.ACC_MESSAGE_ASSISTANT)
        if self.is_displayed("accessibility id", self.ACC_MESSAGE_TEXT, timeout_s=1.0):
            return self.get_text("accessibility id", self.ACC_MESSAGE_TEXT)
        # Check resource-id
        if self.is_displayed("id", self.ID_CHAT_MESSAGES, timeout_s=1.0):
            return self.get_text("id", self.ID_CHAT_MESSAGES)
        return ""

    def select_language(self, lang_code: str) -> None:
        """Switch application language ('en', 'hi', 'te')."""
        clean_code = lang_code.lower()
        # Direct helper if running on MockMobileDriver
        if hasattr(self.driver, "set_language"):
            self.driver.set_language(clean_code)
            return

        lang_locator = (
            ("accessibility id", self.ACC_LANG_SELECT)
            if self.is_displayed(
                "accessibility id", self.ACC_LANG_SELECT, timeout_s=2.0
            )
            else ("id", self.ID_LANG_PICKER)
        )
        self.tap(lang_locator[0], lang_locator[1])

        # If native dialog or options appear, select matching language option
        option_locators = [
            ("accessibility id", f"lang-option-{clean_code}"),
            (
                "xpath",
                f"//*[@text='{clean_code}' or contains(@text, '{clean_code.upper()}')]",
            ),
            (
                "xpath",
                f"//android.widget.CheckedTextView[contains(@text, '{clean_code}')]",
            ),
        ]
        for by, val in option_locators:
            if self.is_displayed(by, val, timeout_s=1.0):
                self.tap(by, val)
                break

    def scroll_to_citations(self) -> None:
        """Scroll downward to ensure citations section is in view."""
        self.scroll_to_element(
            "accessibility id", self.ACC_CITATIONS_TOGGLE, max_swipes=4
        )

    def is_citations_toggle_displayed(self) -> bool:
        """Verify citations toggle button is visible."""
        return self.is_displayed(
            "accessibility id", self.ACC_CITATIONS_TOGGLE, timeout_s=2.0
        )

    def expand_citations(self) -> None:
        """Tap citations toggle to open the citations drawer/panel."""
        if self.is_citations_toggle_displayed():
            self.tap("accessibility id", self.ACC_CITATIONS_TOGGLE)

    def is_citations_panel_displayed(self) -> bool:
        """Verify citations panel content is visible."""
        return self.is_displayed(
            "accessibility id", self.ACC_CITATIONS_PANEL, timeout_s=3.0
        ) or self.is_displayed(
            "accessibility id", self.ACC_CITATION_ITEM, timeout_s=2.0
        )

    def get_citation_items(self) -> list[str]:
        """Retrieve visible citation source titles."""
        elems = self.find_elements("accessibility id", self.ACC_CITATION_ITEM)
        titles: list[str] = []
        for e in elems:
            text = getattr(e, "text", "") or ""
            if not text and hasattr(e, "get_attribute"):
                text = e.get_attribute("text") or e.get_attribute("content-desc") or ""
            if text:
                titles.append(text.strip())
        return titles

    def background_and_resume(self, seconds: int = 2) -> None:
        """Send app to background for N seconds and resume."""
        self.background_app(seconds=seconds)

    def rotate_device(self, orientation: str) -> None:
        """Rotate device to LANDSCAPE or PORTRAIT."""
        self.rotate(orientation)

    def is_offline_banner_displayed(self) -> bool:
        """Check whether the offline warning banner is displayed."""
        return self.is_displayed(
            "accessibility id", self.ACC_OFFLINE_BANNER, timeout_s=3.0
        )

    def get_conversation_messages(self) -> list[str]:
        """Extract conversation messages to verify history preservation."""
        if hasattr(self.driver, "messages"):
            return [m["text"] for m in self.driver.messages]

        messages: list[str] = []
        for by, val in [
            ("accessibility id", self.ACC_MESSAGE_USER),
            ("accessibility id", self.ACC_MESSAGE_ASSISTANT),
        ]:
            for elem in self.find_elements(by, val):
                text = getattr(elem, "text", "")
                if text:
                    messages.append(text.strip())
        return messages
