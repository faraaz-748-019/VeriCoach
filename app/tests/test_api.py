"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.api.main import app, reset_assistant_instance
from app.finance.assistant import FinanceAssistant
from app.providers.mock import MockLLMProvider

PAN_PATTERN = re.compile(r"^[A-Z]{5}\d{4}[A-Z]$")
AADHAAR_PATTERN = re.compile(r"^[2-9]\d{11}$")


@pytest.fixture(autouse=True)
def clean_assistant():
    """Ensure a fresh FinanceAssistant using MockLLMProvider for each test."""
    reset_assistant_instance()
    from app.api.main import get_assistant

    mock_assistant = FinanceAssistant(locale="en", provider=MockLLMProvider())
    app.dependency_overrides[get_assistant] = lambda: mock_assistant
    yield mock_assistant
    app.dependency_overrides.clear()
    reset_assistant_instance()


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["provider"] == "mock"
    assert data["default_locale"] == "en"


def test_chat_without_documents_returns_no_context(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "What is my mutual fund return?", "locale": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "context" in data["response"].lower()
    assert data["provider"] == "mock"
    assert data["locale"] == "en"


@pytest.mark.parametrize("locale", ["en", "hi", "te"])
def test_chat_multilingual_locales(client: TestClient, locale: str) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Test question", "locale": locale},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["locale"] == locale
    assert data["response"] != ""


def test_index_document_and_chat(client: TestClient) -> None:
    doc_text = (
        "Customer: Aarav Sharma\n"
        "Account balance: INR 85,000\n"
        "Recommendation: Invest in large cap mutual funds."
    )
    index_resp = client.post(
        "/api/v1/documents",
        json={"content": doc_text, "source": "test_statement"},
    )
    assert index_resp.status_code == 201
    assert index_resp.json()["chunks_indexed"] >= 1

    chat_resp = client.post(
        "/api/v1/chat",
        json={"message": "What is Aarav's balance?", "locale": "en"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "[MOCK]" in data["response"]


def test_clear_documents(client: TestClient) -> None:
    # First index
    client.post(
        "/api/v1/documents",
        json={"content": "Some financial advice text here.", "source": "temp"},
    )

    # Clear
    clear_resp = client.delete("/api/v1/documents")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["status"] == "cleared"

    # Now chat should yield no_context
    chat_resp = client.post(
        "/api/v1/chat",
        json={"message": "What is the advice?", "locale": "en"},
    )
    assert chat_resp.status_code == 200
    from app.i18n.translator import t

    assert chat_resp.json()["response"] == t("no_context", "en")


def test_get_synthetic_user(client: TestClient) -> None:
    response = client.get("/api/v1/synthetic-user?locale=en&seed=123")
    assert response.status_code == 200
    data = response.json()
    assert data["name"]
    assert "@" in data["email"]
    assert PAN_PATTERN.match(data["pan"])
    assert AADHAAR_PATTERN.match(data["aadhaar"])
    assert "@" in data["upi_id"]
    assert data["monthly_income"] > 0
    assert len(data["accounts"]) >= 1


def test_bootstrap_synthetic(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bootstrap-synthetic",
        json={"locale": "en", "count": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["users_created"] == 2
    assert data["documents_indexed"] == 2
    assert data["chunks_indexed"] >= 2

    # Now chat should be grounded in the bootstrapped knowledge base
    chat_resp = client.post(
        "/api/v1/chat",
        json={"message": "What accounts exist?", "locale": "en"},
    )
    assert chat_resp.status_code == 200
    assert "[MOCK]" in chat_resp.json()["response"]


def test_chat_invalid_empty_message(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "", "locale": "en"},
    )
    assert response.status_code == 422
