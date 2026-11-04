"""Web Page Object for the VeriCoach Multilingual Chat Interface."""

from __future__ import annotations

from qa.framework.pages.base_page import BaseWebPage


class WebChatPage(BaseWebPage):
    """Page Object modeling the VeriCoach frontend chat application."""

    CHAT_INPUT = "textarea, input[type='text']"
    SEND_BUTTON = "button[type='submit'], button:has-text('Send')"
    MESSAGE_ITEMS = ".message, [data-testid='message-item']"
    CITATIONS_PANEL = "[data-testid='citations-panel'], .citations"
    LANGUAGE_SELECTOR = "select, [data-testid='language-selector']"

    def open(self) -> None:
        """Open chat home page."""
        self.navigate("/")

    def send_chat_message(self, message: str) -> None:
        """Input query into chat box and submit."""
        self.fill(self.CHAT_INPUT, message)
        self.click(self.SEND_BUTTON)

    def is_input_ready(self) -> bool:
        """Check if chat input is visible and interactive."""
        return self.is_visible(self.CHAT_INPUT)

    def get_messages(self) -> list[str]:
        """Extract all message texts visible on screen."""
        loc = self.locator(self.MESSAGE_ITEMS)
        count = loc.count()
        return [loc.nth(i).inner_text().strip() for i in range(count)]
