"""Mobile automation test suite for the VeriCoach Android application.

Tests:
1. Launch and ask a question in English
2. Switch to Hindi and Telugu and assert localized script text renders
3. Scroll to citations and verify sources panel
4. Background and foreground the app and verify conversation state is kept
5. Rotate device to landscape and back to portrait
6. Turn on airplane mode and verify the offline banner
"""

from __future__ import annotations

import re

import allure
import pytest

from qa.framework.data_factories import UserFactory
from qa.framework.pages.mobile_chat_screen import MobileChatScreen


@pytest.mark.mobile
@pytest.mark.smoke
@allure.feature("Mobile Application")
@allure.story("English Advisory Query Flow")
def test_mobile_launch_and_ask_question_english(
    mobile_chat_screen: MobileChatScreen,
) -> None:
    """Validate app launch, synthetic personal-finance query submission, and English response."""
    synthetic_user = UserFactory.create(locale="en")
    query = f"Hello, I am {synthetic_user.name}. What are the tax deduction limits under Section 80C?"

    with allure.step("Verify mobile chat screen is initialized and input is ready"):
        assert mobile_chat_screen.is_chat_ready() is True

    with allure.step(f"Submit English query for synthetic user: {synthetic_user.name}"):
        mobile_chat_screen.send_message(query)

    with allure.step(
        "Wait for assistant response and assert non-empty advisory content"
    ):
        response_text = mobile_chat_screen.wait_for_response(timeout_s=15.0)
        assert len(response_text) > 0, "Expected non-empty response from assistant"
        assert any(
            keyword in response_text.lower()
            for keyword in ("section 80c", "80c", "deduction", "tax", "invest", "₹1.5")
        ), f"Response did not contain expected financial keywords: {response_text}"

    with allure.step("Capture screenshot of completed chat"):
        mobile_chat_screen.take_screenshot(name="mobile_chat_english_completed")


@pytest.mark.mobile
@pytest.mark.regression
@allure.feature("Mobile Application")
@allure.story("Multilingual Switching - Hindi & Telugu")
def test_mobile_switch_to_hindi_and_telugu(
    mobile_chat_screen: MobileChatScreen,
) -> None:
    """Verify switching languages renders localized scripts (Devanagari for Hindi, Telugu script for Telugu)."""
    # 1. Hindi Switch & Verification
    with allure.step("Switch language to Hindi ('hi')"):
        mobile_chat_screen.select_language("hi")

    with allure.step("Verify Hindi text renders with Devanagari script"):
        hindi_response = mobile_chat_screen.get_latest_response()
        assert len(hindi_response) > 0, "Expected Hindi response text"
        # Devanagari unicode range: \u0900 - \u097F
        devanagari_match = re.search(r"[\u0900-\u097F]", hindi_response)
        assert (
            devanagari_match is not None
        ), f"Expected Devanagari characters in Hindi response, got: {hindi_response}"
        mobile_chat_screen.take_screenshot(name="mobile_chat_hindi_response")

    # 2. Telugu Switch & Verification
    with allure.step("Switch language to Telugu ('te')"):
        mobile_chat_screen.select_language("te")

    with allure.step("Verify Telugu text renders with Telugu script"):
        telugu_response = mobile_chat_screen.get_latest_response()
        assert len(telugu_response) > 0, "Expected Telugu response text"
        # Telugu unicode range: \u0C00 - \u0C7F
        telugu_match = re.search(r"[\u0C00-\u0C7F]", telugu_response)
        assert (
            telugu_match is not None
        ), f"Expected Telugu characters in Telugu response, got: {telugu_response}"
        mobile_chat_screen.take_screenshot(name="mobile_chat_telugu_response")


@pytest.mark.mobile
@pytest.mark.regression
@allure.feature("Mobile Application")
@allure.story("Citations Scrolling and Inspection")
def test_mobile_scroll_to_citations(
    mobile_chat_screen: MobileChatScreen,
) -> None:
    """Verify scrolling down to citations, expanding sources toggle, and reading citation items."""
    with allure.step("Send query that produces citations"):
        mobile_chat_screen.send_message("What are mutual fund capital gains rules?")
        mobile_chat_screen.wait_for_response()

    with allure.step("Scroll down to citations toggle button"):
        mobile_chat_screen.scroll_to_citations()
        assert mobile_chat_screen.is_citations_toggle_displayed() is True

    with allure.step("Expand citations panel and assert sources are visible"):
        mobile_chat_screen.expand_citations()
        assert mobile_chat_screen.is_citations_panel_displayed() is True
        mobile_chat_screen.take_screenshot(name="mobile_citations_expanded")


@pytest.mark.mobile
@pytest.mark.regression
@allure.feature("Mobile Application")
@allure.story("App Lifecycle - Background & Foreground State Retention")
def test_mobile_background_and_foreground_keeps_conversation(
    mobile_chat_screen: MobileChatScreen,
) -> None:
    """Validate that backgrounding the app for 2 seconds and resuming preserves conversation history."""
    query = "How much should I allocate to liquid funds for an emergency corpus?"

    with allure.step("Send message before backgrounding"):
        mobile_chat_screen.send_message(query)
        initial_response = mobile_chat_screen.wait_for_response()
        assert len(initial_response) > 0

    with allure.step("Background the application for 2 seconds"):
        mobile_chat_screen.background_and_resume(seconds=2)

    with allure.step("Verify conversation history and UI state are fully preserved"):
        assert mobile_chat_screen.is_chat_ready() is True
        messages = mobile_chat_screen.get_conversation_messages()
        assert (
            len(messages) >= 2
        ), f"Expected conversation history to be retained, got: {messages}"
        # Ensure our prior query is preserved
        assert any(
            "liquid" in m.lower() or "emergency" in m.lower() for m in messages
        ), f"Previous query not found in conversation history: {messages}"
        mobile_chat_screen.take_screenshot(name="mobile_resumed_state")


@pytest.mark.mobile
@pytest.mark.regression
@allure.feature("Mobile Application")
@allure.story("Device Rotation")
def test_mobile_rotate_device(
    mobile_chat_screen: MobileChatScreen,
) -> None:
    """Validate device rotation to LANDSCAPE and back to PORTRAIT maintains UI integrity."""
    with allure.step("Send message in PORTRAIT mode"):
        mobile_chat_screen.send_message("Explain PPF interest rate computation.")
        mobile_chat_screen.wait_for_response()

    with allure.step("Rotate device to LANDSCAPE"):
        mobile_chat_screen.rotate_device("LANDSCAPE")
        assert mobile_chat_screen.get_orientation() == "LANDSCAPE"
        assert mobile_chat_screen.is_chat_ready() is True
        mobile_chat_screen.take_screenshot(name="mobile_landscape_mode")

    with allure.step("Rotate device back to PORTRAIT"):
        mobile_chat_screen.rotate_device("PORTRAIT")
        assert mobile_chat_screen.get_orientation() == "PORTRAIT"
        assert mobile_chat_screen.is_chat_ready() is True
        mobile_chat_screen.take_screenshot(name="mobile_portrait_restored")


@pytest.mark.mobile
@pytest.mark.regression
@allure.feature("Mobile Application")
@allure.story("Network Fault Injection - Airplane Mode & Offline Banner")
def test_mobile_airplane_mode_offline_banner(
    mobile_chat_screen: MobileChatScreen,
) -> None:
    """Validate enabling airplane mode immediately surfaces the offline banner."""
    with allure.step("Enable airplane mode on device"):
        mobile_chat_screen.set_airplane_mode(True)

    with allure.step("Verify offline banner is displayed"):
        assert (
            mobile_chat_screen.is_offline_banner_displayed() is True
        ), "Offline warning banner was not displayed when airplane mode was enabled."
        mobile_chat_screen.take_screenshot(name="mobile_offline_banner_active")

    with allure.step("Disable airplane mode and restore network"):
        mobile_chat_screen.set_airplane_mode(False)
        mobile_chat_screen.take_screenshot(name="mobile_network_restored")
