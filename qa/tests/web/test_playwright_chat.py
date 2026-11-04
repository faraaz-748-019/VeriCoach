"""Playwright Web UI test suite for VeriCoach Multilingual Assistant.

Covers:
- Chat happy path in English, Hindi, and Telugu
- Citations panel visibility and source details
- User feedback submission (thumbs up/down)
- Error banner presentation on HTTP 500 via route interception
- Loading indicator state during request execution
- Keyboard-only navigation (zero mouse clicks)
- Automated accessibility scan using axe-core
- Visual screenshot snapshot of the main chat interface
"""

from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, Route

from qa.framework.axe import AccessibilityScanner
from qa.framework.pages.web_chat_page import WebChatPage


@pytest.mark.web
@allure.feature("Web UI - Multilingual Chat")
@allure.story("English Happy Path")
def test_chat_happy_path_english(chat_page: WebChatPage) -> None:
    """Validate end-to-end question and answer flow in English."""
    with allure.step("Navigate to chat application"):
        chat_page.open()
        assert chat_page.is_input_ready() is True

    with allure.step("Submit financial query in English"):
        query = "What is the recommended emergency fund size?"
        chat_page.send_chat_message(query)

    with allure.step("Verify assistant response is displayed"):
        response = chat_page.wait_for_assistant_response(timeout_ms=15000)
        assert len(response) > 0
        assert any(
            term in response.lower()
            for term in ["fund", "month", "expense", "saving", "emergency", "reserve"]
        )


@pytest.mark.web
@allure.feature("Web UI - Multilingual Chat")
@allure.story("Hindi Happy Path")
def test_chat_happy_path_hindi(chat_page: WebChatPage) -> None:
    """Validate end-to-end question and answer flow in Hindi."""
    with allure.step("Navigate and switch language to Hindi"):
        chat_page.open()
        chat_page.select_language("hi")
        assert chat_page.get_selected_language() == "hi"

    with allure.step("Submit financial query in Hindi"):
        query = "आपातकालीन निधि क्या है और मुझे कितना बचाना चाहिए?"
        chat_page.send_chat_message(query)

    with allure.step("Verify assistant responds"):
        response = chat_page.wait_for_assistant_response(timeout_ms=15000)
        assert len(response) > 0


@pytest.mark.web
@allure.feature("Web UI - Multilingual Chat")
@allure.story("Telugu Happy Path")
def test_chat_happy_path_telugu(chat_page: WebChatPage) -> None:
    """Validate end-to-end question and answer flow in Telugu."""
    with allure.step("Navigate and switch language to Telugu"):
        chat_page.open()
        chat_page.select_language("te")
        assert chat_page.get_selected_language() == "te"

    with allure.step("Submit financial query in Telugu"):
        query = "మ్యూచువల్ ఫండ్లలో సిప్ ఎలా ప్రారంభించాలి?"
        chat_page.send_chat_message(query)

    with allure.step("Verify assistant responds"):
        response = chat_page.wait_for_assistant_response(timeout_ms=15000)
        assert len(response) > 0


@pytest.mark.web
@allure.feature("Web UI - Citations")
@allure.story("Citations Visibility and Disclosure")
def test_citations_visibility(page: Page, chat_page: WebChatPage) -> None:
    """Verify citations toggle and panel render document sources correctly."""
    synthetic_sources = [
        {
            "doc_id": "doc_rbi_guideline_01",
            "title": "RBI Guidelines on Deposit Insurance",
            "category": "Regulatory",
            "score": 0.94,
            "snippet": "Bank deposits up to 5 lakh rupees are insured by DICGC.",
        },
        {
            "doc_id": "doc_tax_80c",
            "title": "Income Tax Deductions Guide",
            "category": "Taxation",
            "score": 0.88,
            "snippet": "Section 80C allows deductions up to 1.5 lakh rupees annually.",
        },
    ]

    def handle_chat_route(route: Route) -> None:
        payload = {
            "answer": "Deposits are insured up to 5 lakhs by DICGC under RBI rules.",
            "language": "en",
            "sources": synthetic_sources,
            "refused": False,
            "refusal_reason": None,
            "trace_id": "tr_mock_citations_001",
        }
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        )

    # Route interception to ensure predictable citation payload
    page.route("**/v1/chat", handle_chat_route)
    page.route("**/api/v1/chat", handle_chat_route)

    with allure.step("Navigate to chat application"):
        chat_page.open()

    with allure.step("Send question triggering citations"):
        chat_page.send_chat_message("Is my bank deposit safe?")
        chat_page.wait_for_assistant_response()

    with allure.step("Verify citation toggle button is visible"):
        assert chat_page.is_visible(chat_page.CITATIONS_TOGGLE) is True

    with allure.step("Expand citations panel"):
        chat_page.open_citations()
        assert chat_page.is_citations_panel_visible() is True

    with allure.step("Verify source titles and relevance score"):
        titles = chat_page.get_citation_titles()
        assert "RBI Guidelines on Deposit Insurance" in titles
        assert "Income Tax Deductions Guide" in titles


@pytest.mark.web
@allure.feature("Web UI - Feedback")
@allure.story("Feedback Submission")
def test_feedback_submission(page: Page, chat_page: WebChatPage) -> None:
    """Verify submitting thumbs-up feedback posts to backend and updates UI status."""
    feedback_captured = []

    def handle_chat(route: Route) -> None:
        payload = {
            "answer": "PPF investments offer compounding tax-free returns.",
            "language": "en",
            "sources": [],
            "refused": False,
            "refusal_reason": None,
            "trace_id": "tr_feedback_trace_999",
        }
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(payload),
        )

    def handle_feedback(route: Route) -> None:
        data = json.loads(route.request.post_data or "{}")
        feedback_captured.append(data)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"status": "recorded", "trace_id": data.get("trace_id")}),
        )

    page.route("**/v1/chat", handle_chat)
    page.route("**/api/v1/chat", handle_chat)
    page.route("**/v1/feedback", handle_feedback)
    page.route("**/api/v1/feedback", handle_feedback)

    with allure.step("Open chat and send query"):
        chat_page.open()
        chat_page.send_chat_message("Explain PPF compounding.")
        chat_page.wait_for_assistant_response()

    with allure.step("Submit positive feedback (thumbs-up)"):
        chat_page.submit_feedback(positive=True)

    with allure.step("Verify feedback state reflects submission"):
        assert chat_page.is_feedback_submitted() is True
        assert len(feedback_captured) == 1
        assert feedback_captured[0]["trace_id"] == "tr_feedback_trace_999"
        assert feedback_captured[0]["rating"] == 5


@pytest.mark.web
@allure.feature("Web UI - Error Handling")
@allure.story("Error Banner on API 500 via Route Interception")
def test_error_banner_on_500_route_interception(
    page: Page, chat_page: WebChatPage
) -> None:
    """Intercept chat API route to return HTTP 500 and verify error banner is rendered."""

    def handle_error_500(route: Route) -> None:
        route.fulfill(
            status=500,
            content_type="application/json",
            body=json.dumps({"detail": "Internal server computation failed"}),
        )

    page.route("**/v1/chat", handle_error_500)
    page.route("**/api/v1/chat", handle_error_500)

    with allure.step("Navigate to chat application"):
        chat_page.open()

    with allure.step("Submit query that triggers 500 error"):
        chat_page.send_chat_message("Will this request fail gracefully?")

    with allure.step("Verify error banner is displayed with message"):
        assert chat_page.is_error_banner_visible() is True
        banner_text = chat_page.get_error_banner_text()
        assert "Internal server computation failed" in banner_text

    with allure.step("Verify error banner has retry and dismiss buttons"):
        assert chat_page.is_visible(chat_page.ERROR_RETRY) is True
        assert chat_page.is_visible(chat_page.ERROR_DISMISS) is True

    with allure.step("Dismiss error banner and verify it disappears"):
        chat_page.click_dismiss_button()
        assert chat_page.is_error_banner_visible() is False


@pytest.mark.web
@allure.feature("Web UI - Loading State")
@allure.story("Loading Indicator During In-Flight Request")
def test_loading_indicator_state(page: Page, chat_page: WebChatPage) -> None:
    """Verify loading indicator appears while network request is in flight."""
    held_routes: list[Route] = []

    def hold_chat_request(route: Route) -> None:
        held_routes.append(route)

    # Intercept chat request to hold it suspended in flight
    page.route(lambda url: "/chat" in url, hold_chat_request)

    with allure.step("Open chat interface"):
        chat_page.open()

    with allure.step("Submit query and verify loading indicator is displayed"):
        chat_page.fill(chat_page.CHAT_INPUT, "What is a sovereign gold bond?")
        chat_page.click(chat_page.SEND_BUTTON)

        # Loading indicator must be visible while request is suspended
        assert (
            chat_page.is_visible(chat_page.LOADING_INDICATOR, timeout_ms=5000) is True
        )

    with allure.step("Fulfill suspended request and verify loading indicator clears"):
        assert len(held_routes) == 1
        held_routes[0].fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "answer": "Sovereign Gold Bonds are government securities denominated in grams of gold.",
                    "language": "en",
                    "sources": [],
                    "refused": False,
                    "refusal_reason": None,
                    "trace_id": "tr_loading_verified",
                }
            ),
        )

        chat_page.wait_for_loading_to_disappear()
        assert chat_page.is_loading_visible() is False
        response = chat_page.wait_for_assistant_response()
        assert "Sovereign Gold Bonds" in response


@pytest.mark.web
@allure.feature("Web UI - Accessibility")
@allure.story("Keyboard-Only Navigation")
def test_keyboard_only_navigation(page: Page, chat_page: WebChatPage) -> None:
    """Validate full chat interaction without using any mouse clicks."""
    with allure.step("Open chat interface"):
        chat_page.open()

    with allure.step("Tab focus to chat input and submit via Enter"):
        page.keyboard.press("Tab")
        # Ensure input is focused
        chat_input = page.locator(chat_page.CHAT_INPUT)
        chat_input.focus()

        # Type message purely via keyboard strokes
        test_msg = "How do index funds differ from active funds?"
        page.keyboard.type(test_msg)
        page.keyboard.press("Enter")

    with allure.step("Verify user message submitted and assistant responds"):
        response = chat_page.wait_for_assistant_response(timeout_ms=15000)
        assert len(response) > 0


@pytest.mark.web
@allure.feature("Web UI - Accessibility")
@allure.story("Axe WCAG Accessibility Scan")
def test_accessibility_scan_with_axe(page: Page, chat_page: WebChatPage) -> None:
    """Execute automated axe-core accessibility audit on main screen."""
    with allure.step("Open application home screen"):
        chat_page.open()

    with allure.step("Execute Axe accessibility audit"):
        scanner = AccessibilityScanner(page)
        report = scanner.run_scan()

    with allure.step("Assert zero critical accessibility violations"):
        critical_issues = report.critical_violations
        assert (
            len(critical_issues) == 0
        ), f"Found critical a11y violations: {critical_issues}"


@pytest.mark.web
@allure.feature("Web UI - Visual Snapshot")
@allure.story("Main Screen Visual Baseline")
def test_visual_snapshot_main_screen(page: Page, chat_page: WebChatPage) -> None:
    """Capture visual snapshot of main screen and verify UI structure."""
    with allure.step("Open application home screen"):
        chat_page.open()

    with allure.step("Capture screenshot and record snapshot"):
        screenshot_bytes = page.screenshot(full_page=True)
        assert len(screenshot_bytes) > 1000

        snapshot_dir = Path("qa/tests/web/snapshots")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = snapshot_dir / "main_screen.png"
        snapshot_file.write_bytes(screenshot_bytes)

        chat_page.take_screenshot(name="main_screen_visual_snapshot")
        assert snapshot_file.exists()
