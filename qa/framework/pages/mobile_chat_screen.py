"""Mobile Screen Object for the VeriCoach Android/iOS Application."""

from __future__ import annotations

from qa.framework.pages.base_mobile_page import BaseMobilePage


class MobileChatScreen(BaseMobilePage):
    """Screen Object modeling the VeriCoach mobile chat interface."""

    CHAT_INPUT = "chat_input"
    SEND_BUTTON = "send_button"
    CHAT_MESSAGES = "chat_messages"
    LANGUAGE_PICKER = "language_picker"

    def send_message(self, message: str) -> None:
        """Type and send a message via mobile UI."""
        self.input_text("id", self.CHAT_INPUT, message)
        self.tap("id", self.SEND_BUTTON)

    def get_latest_response(self) -> str:
        """Retrieve the latest assistant response text."""
        return self.get_text("id", self.CHAT_MESSAGES)

    def is_chat_ready(self) -> bool:
        """Verify whether chat input is displayed on screen."""
        return self.is_displayed("id", self.CHAT_INPUT)
