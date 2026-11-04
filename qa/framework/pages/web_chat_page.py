"""Web Page Object for the VeriCoach Multilingual Chat Interface."""

from __future__ import annotations

from qa.framework.pages.base_page import BaseWebPage


class WebChatPage(BaseWebPage):
    """Page Object modeling the VeriCoach frontend chat application."""

    # Selectors matching frontend data-testid and fallback DOM attributes
    CHAT_WINDOW = "[data-testid='chat-window']"
    APP_HEADER = "[data-testid='app-header']"
    APP_TITLE = "[data-testid='app-title']"
    APP_FOOTER = "[data-testid='app-footer']"
    LANGUAGE_SELECTOR = "[data-testid='language-select'], select"
    CHAT_INPUT = "[data-testid='chat-input'], textarea, input[type='text']"
    SEND_BUTTON = "[data-testid='send-button'], button[type='submit']"
    USER_MESSAGES = "[data-testid='message-user']"
    ASSISTANT_MESSAGES = "[data-testid='message-assistant']"
    MESSAGE_ITEMS = (
        "[data-testid='message-user'], [data-testid='message-assistant'], .message"
    )
    MESSAGE_TEXT = "[data-testid='message-text']"
    CITATIONS_TOGGLE = "[data-testid='citations-toggle']"
    CITATIONS_PANEL = "[data-testid='citations-panel'], .citations"
    CITATION_ITEMS = "[data-testid='citation-item']"
    CITATION_TITLE = "[data-testid='citation-title']"
    CITATION_SCORE = "[data-testid='citation-score']"
    FEEDBACK_CONTAINER = "[data-testid='feedback-container']"
    FEEDBACK_THUMBS_UP = "[data-testid='feedback-thumbs-up']"
    FEEDBACK_THUMBS_DOWN = "[data-testid='feedback-thumbs-down']"
    FEEDBACK_STATUS = "[data-testid='feedback-status']"
    LOADING_INDICATOR = "[data-testid='loading-indicator']"
    ERROR_BANNER = "[data-testid='error-banner']"
    ERROR_RETRY = "[data-testid='error-banner-retry']"
    ERROR_DISMISS = "[data-testid='error-banner-dismiss']"

    def open(self) -> None:
        """Open chat home page."""
        self.navigate("/")
        self.wait_for_selector(self.CHAT_WINDOW, timeout_ms=10000)

    def select_language(self, lang_code: str) -> None:
        """Change application language via header selector ('en', 'hi', 'te')."""
        self.select_option(self.LANGUAGE_SELECTOR, lang_code)

    def get_selected_language(self) -> str:
        """Get currently selected language code."""
        return self.page.locator(self.LANGUAGE_SELECTOR).input_value()

    def get_input_placeholder(self) -> str:
        """Retrieve current placeholder text in the chat input."""
        return self.page.locator(self.CHAT_INPUT).get_attribute("placeholder") or ""

    def send_chat_message(self, message: str) -> None:
        """Input query into chat box and submit via send button."""
        self.fill(self.CHAT_INPUT, message)
        self.click(self.SEND_BUTTON)

    def send_message_via_keyboard(self, message: str) -> None:
        """Input query and submit using keyboard Enter key."""
        self.fill(self.CHAT_INPUT, message)
        self.press_key(self.CHAT_INPUT, "Enter")

    def is_input_ready(self) -> bool:
        """Check if chat input is visible and interactive."""
        return (
            self.is_visible(self.CHAT_INPUT)
            and self.page.locator(self.CHAT_INPUT).is_enabled()
        )

    def get_messages(self) -> list[str]:
        """Extract all message texts visible on screen."""
        loc = self.locator(self.MESSAGE_ITEMS)
        count = loc.count()
        return [loc.nth(i).inner_text().strip() for i in range(count)]

    def get_assistant_messages(self) -> list[str]:
        """Extract all assistant response texts."""
        loc = self.locator(f"{self.ASSISTANT_MESSAGES} {self.MESSAGE_TEXT}")
        count = loc.count()
        if count == 0:
            loc = self.locator(self.ASSISTANT_MESSAGES)
            count = loc.count()
        return [loc.nth(i).inner_text().strip() for i in range(count)]

    def wait_for_assistant_response(self, timeout_ms: int = 15000) -> str:
        """Wait explicitly until at least one assistant message arrives."""
        loc = self.page.locator(self.ASSISTANT_MESSAGES).last
        loc.wait_for(state="visible", timeout=timeout_ms)
        text_loc = loc.locator(self.MESSAGE_TEXT)
        if text_loc.count() > 0:
            return text_loc.inner_text().strip()
        return loc.inner_text().strip()

    def is_loading_visible(self) -> bool:
        """Check if typing/loading indicator is currently displayed."""
        return self.is_visible(self.LOADING_INDICATOR, timeout_ms=1000)

    def wait_for_loading_to_disappear(self, timeout_ms: int = 15000) -> None:
        """Wait until loading indicator is detached or hidden."""
        try:
            self.page.locator(self.LOADING_INDICATOR).wait_for(
                state="hidden", timeout=timeout_ms
            )
        except Exception:
            pass

    def open_citations(self) -> None:
        """Toggle citations disclosure button if present."""
        if self.is_visible(self.CITATIONS_TOGGLE, timeout_ms=3000):
            self.click(self.CITATIONS_TOGGLE)
            self.wait_for_selector(self.CITATIONS_PANEL, timeout_ms=5000)

    def is_citations_panel_visible(self) -> bool:
        """Check if citations panel is expanded and visible."""
        return self.is_visible(self.CITATIONS_PANEL, timeout_ms=2000)

    def get_citation_titles(self) -> list[str]:
        """Extract titles of all visible citations."""
        loc = self.locator(self.CITATION_TITLE)
        count = loc.count()
        return [loc.nth(i).inner_text().strip() for i in range(count)]

    def submit_feedback(self, positive: bool = True) -> None:
        """Click thumbs-up or thumbs-down feedback button."""
        selector = self.FEEDBACK_THUMBS_UP if positive else self.FEEDBACK_THUMBS_DOWN
        self.click(selector)
        self.wait_for_selector(self.FEEDBACK_STATUS, timeout_ms=5000)

    def is_feedback_submitted(self) -> bool:
        """Verify feedback submitted status icon/text is visible."""
        return self.is_visible(self.FEEDBACK_STATUS, timeout_ms=3000)

    def get_feedback_status_text(self) -> str:
        """Read text from feedback status confirmation."""
        return self.get_text(self.FEEDBACK_STATUS)

    def is_error_banner_visible(self) -> bool:
        """Check if error banner is displayed."""
        return self.is_visible(self.ERROR_BANNER, timeout_ms=3000)

    def get_error_banner_text(self) -> str:
        """Retrieve message inside error banner."""
        return self.get_text(self.ERROR_BANNER)

    def click_retry_button(self) -> None:
        """Click retry button on error banner."""
        self.click(self.ERROR_RETRY)

    def click_dismiss_button(self) -> None:
        """Click dismiss button on error banner."""
        self.click(self.ERROR_DISMISS)
