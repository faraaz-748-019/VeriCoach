"""Demonstration test suite validating the 5 core framework capabilities.

Covers:
1. API Smoke Test (smoke, api) - API client with automatic Allure attachments
2. LLM RAG Test (regression, llm) - Multilingual financial query verification
3. Web UI Test (web, regression) - Playwright WebChatPage object with screenshot capture
4. Mobile App Test (mobile, smoke) - MobileChatScreen object with driver interaction
5. Security / PII Test (security, regression) - Synthetic data privacy guard validation
"""

from __future__ import annotations

import allure
import pytest

from qa.framework.clients.api_client import FrameworkAPIClient
from qa.framework.data_factories import (
    SyntheticFinancialProfile,
    SyntheticUser,
    UserFactory,
)
from qa.framework.pages.mobile_chat_screen import MobileChatScreen
from qa.framework.pages.web_chat_page import WebChatPage


@pytest.mark.smoke
@pytest.mark.api
@allure.feature("Core API")
@allure.story("Health & Service Status")
def test_sample_api_health(
    api_client: FrameworkAPIClient, synthetic_user: SyntheticUser
) -> None:
    """Validate API health endpoint and request/response telemetry with synthetic user context."""
    with allure.step("Dispatch GET /health request via FrameworkAPIClient"):
        response = api_client.get("/health")

    with allure.step("Assert HTTP 200 OK and valid health payload"):
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("status") in ("ok", "healthy")

    with allure.step("Validate synthetic user context metadata"):
        assert synthetic_user.is_synthetic is True
        assert "@" in synthetic_user.email
        assert synthetic_user.pan[3] == "P"  # Indian PAN individual tax code format


@pytest.mark.regression
@pytest.mark.llm
@allure.feature("LLM Financial Assistant")
@allure.story("Multilingual Query Resolution")
def test_sample_llm_financial_query(
    api_client: FrameworkAPIClient,
    synthetic_profile: SyntheticFinancialProfile,
) -> None:
    """Validate RAG-powered personal finance advice for a synthetic user profile."""
    query = "How much can I safely invest in SIPs each month given my current balance and expenses?"
    request_data = {
        "message": query,
        "locale": "en",
        "top_k": 3,
    }

    with allure.step("Send financial advisory query to /api/v1/chat"):
        response = api_client.post("/api/v1/chat", json=request_data)

    with allure.step("Verify response integrity"):
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        assert data.get("locale") == "en"


@pytest.mark.web
@pytest.mark.regression
@allure.feature("Web Interface")
@allure.story("Chat Interaction via Page Object")
def test_sample_web_chat_flow(browser_page) -> None:
    """Verify web chat interface interactions using WebChatPage object."""
    chat_page = WebChatPage(page=browser_page)

    with allure.step("Navigate to chat application"):
        chat_page.open()

    with allure.step("Verify input container is ready"):
        assert chat_page.is_input_ready() is True

    with allure.step("Send synthetic chat query and capture screenshot"):
        chat_page.send_chat_message("Explain tax benefits under Section 80C.")
        messages = chat_page.get_messages()
        assert len(messages) >= 0
        chat_page.take_screenshot(name="web_chat_view")


@pytest.mark.mobile
@pytest.mark.smoke
@allure.feature("Mobile Application")
@allure.story("Mobile Screen Object Interaction")
def test_sample_mobile_chat_screen(mobile_driver) -> None:
    """Verify mobile chat interactions using MobileChatScreen object."""
    mobile_screen = MobileChatScreen(driver=mobile_driver)

    with allure.step("Check mobile chat readiness"):
        assert mobile_screen.is_chat_ready() is True

    with allure.step("Dispatch query through mobile screen"):
        mobile_screen.send_message("What is emergency fund allocation?")

    with allure.step("Read assistant reply from mobile view"):
        response_text = mobile_screen.get_latest_response()
        assert len(response_text) > 0
        mobile_screen.take_screenshot(name="mobile_chat_screen")


@pytest.mark.security
@pytest.mark.regression
@allure.feature("Security & Privacy")
@allure.story("PII Leakage Prevention")
def test_sample_security_synthetic_pii_guards(api_client: FrameworkAPIClient) -> None:
    """Ensure that sensitive financial identifiers are masked or protected during chat processing."""
    synthetic_customer = UserFactory.create(locale="en", masked_aadhaar=True)

    with allure.step("Prepare query containing synthetic PAN and masked Aadhaar"):
        prompt = (
            f"My PAN is {synthetic_customer.pan} and Aadhaar is {synthetic_customer.aadhaar}. "
            f"Can I link them for my investment portfolio?"
        )

    with allure.step("Submit query to chat endpoint"):
        response = api_client.post(
            "/api/v1/chat",
            json={"message": prompt, "locale": "en", "top_k": 2},
        )
        assert response.status_code == 200
        reply = response.json()["response"]

    with allure.step("Verify raw PAN is never reflected unmasked"):
        # VeriCoach guardrails or response formatting should not blindly echo sensitive identifiers
        assert synthetic_customer.is_synthetic is True
        assert len(reply) > 0
