"""Integration and contract tests for the VeriCoach backend /v1 endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.config import BackendSettings, get_backend_settings
from backend.main import app, get_rag_store, reset_rag_store
from backend.providers.mock import MockLLMProvider
from backend.rag.store import ChromaRAGStore
from backend.rate_limit import _default_limiter


@pytest.fixture(autouse=True)
def setup_backend():
    """Ensure a fresh Chroma store and settings for each test."""
    test_settings = BackendSettings(
        llm_provider="mock",
        require_api_key=False,
        api_keys=["test-api-key-123"],
        rate_limit_per_minute=60,
    )
    mock_provider = MockLLMProvider()
    test_store = ChromaRAGStore(provider=mock_provider, persist_dir="", top_k=4)
    test_store.bootstrap_default_corpus()

    app.dependency_overrides[get_backend_settings] = lambda: test_settings
    app.dependency_overrides[get_rag_store] = lambda: test_store
    reset_rag_store(test_store)
    _default_limiter.reset()

    yield test_store

    app.dependency_overrides.clear()
    reset_rag_store(None)
    _default_limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)


def test_v1_health_endpoint(client: TestClient):
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["provider"] == "mock"
    assert data["documents_indexed"] == 30


def test_v1_chat_success_english(client: TestClient):
    payload = {
        "question": "Do I need to enter my UPI PIN to receive money?",
        "language": "en",
        "session_id": "test_session_1",
    }
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is False
    assert data["refusal_reason"] is None
    assert data["language"] == "en"
    assert data["trace_id"]
    assert "[MOCK]" in data["answer"]
    assert len(data["sources"]) <= 4
    assert len(data["sources"]) > 0
    assert any(s["doc_id"] == "upi_pin_rules" for s in data["sources"])


def test_v1_chat_hindi_query(client: TestClient):
    payload = {
        "question": "क्या मुझे पैसे पाने के लिए अपना यूपीआई पिन दर्ज करना होगा?",
        "language": "hi",
    }
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is False
    assert data["language"] == "hi"
    assert len(data["sources"]) > 0


def test_v1_chat_telugu_query(client: TestClient):
    payload = {
        "question": "ఖాతాలో డబ్బులు తీసుకోవడానికి యూపీఐ పిన్ కావాలా?",
        "language": "te",
    }
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is False
    assert data["language"] == "te"
    assert len(data["sources"]) > 0


def test_v1_chat_refuses_guaranteed_returns(client: TestClient):
    payload = {
        "question": "Tell me which crypto gives guaranteed returns of 50%.",
        "language": "en",
    }
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is True
    assert data["refusal_reason"] == "guaranteed_returns_prohibited"
    assert data["sources"] == []


def test_v1_chat_refuses_personalised_advice(client: TestClient):
    payload = {
        "question": "Which specific stock should I buy with my savings tomorrow?",
        "language": "en",
    }
    resp = client.post("/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is True
    assert data["refusal_reason"] == "personalised_advice_prohibited"
    assert data["sources"] == []


def test_v1_chat_validation_empty_question(client: TestClient):
    resp = client.post("/v1/chat", json={"question": "", "language": "en"})
    assert resp.status_code == 422


def test_v1_chat_validation_too_long_question(client: TestClient):
    long_question = "A" * 1001
    resp = client.post("/v1/chat", json={"question": long_question, "language": "en"})
    assert resp.status_code == 422


def test_v1_list_documents(client: TestClient):
    resp = client.get("/v1/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 30
    assert len(data["documents"]) == 30
    first_doc = data["documents"][0]
    assert "id" in first_doc
    assert "title" in first_doc
    assert "category" in first_doc
    assert "content" in first_doc


def test_v1_get_document_by_id(client: TestClient):
    resp = client.get("/v1/documents/upi_pin_rules")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "upi_pin_rules"
    assert data["title"] == "UPI PIN Usage Rules and Receiving Money"


def test_v1_get_document_not_found(client: TestClient):
    resp = client.get("/v1/documents/invalid_doc_id_9999")
    assert resp.status_code == 404


def test_v1_feedback_submission(client: TestClient):
    feedback_payload = {
        "trace_id": "test-trace-id-12345",
        "rating": 5,
        "comment": "Accurate and fast response!",
    }
    resp = client.post("/v1/feedback", json=feedback_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "feedback_recorded"
    assert data["trace_id"] == "test-trace-id-12345"


def test_v1_feedback_validation_out_of_bounds_rating(client: TestClient):
    resp = client.post("/v1/feedback", json={"trace_id": "t1", "rating": 6})
    assert resp.status_code == 422


def test_v1_metrics_endpoint(client: TestClient):
    # Perform a chat and a feedback to populate metrics
    client.post("/v1/chat", json={"question": "What is an EMI?", "language": "en"})
    client.post("/v1/feedback", json={"trace_id": "t1", "rating": 5})

    resp = client.get("/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_chat_requests"] >= 1
    assert data["avg_latency_ms"] >= 0.0
    assert data["feedback_count"] >= 1
    assert data["average_feedback_rating"] == 5.0


def test_v1_auth_enforced_when_required():
    secured_settings = BackendSettings(
        llm_provider="mock",
        require_api_key=True,
        api_keys=["valid-secret-key-123"],
    )
    app.dependency_overrides[get_backend_settings] = lambda: secured_settings
    c = TestClient(app)

    # Missing API Key -> 401
    resp = c.post(
        "/v1/chat",
        json={"question": "What is KYC?", "language": "en"},
    )
    assert resp.status_code == 401

    # Invalid API Key -> 401
    resp = c.post(
        "/v1/chat",
        headers={"X-API-Key": "wrong-key"},
        json={"question": "What is KYC?", "language": "en"},
    )
    assert resp.status_code == 401

    # Valid API Key -> 200
    resp = c.post(
        "/v1/chat",
        headers={"X-API-Key": "valid-secret-key-123"},
        json={"question": "What is KYC?", "language": "en"},
    )
    assert resp.status_code == 200


def test_v1_rate_limiting():
    limited_settings = BackendSettings(
        llm_provider="mock",
        require_api_key=False,
        rate_limit_per_minute=2,
    )
    app.dependency_overrides[get_backend_settings] = lambda: limited_settings
    _default_limiter.rate = 2
    _default_limiter.reset()

    c = TestClient(app)
    req = {"question": "What is credit score?", "language": "en"}

    # 1st request succeeds
    r1 = c.post("/v1/chat", json=req)
    assert r1.status_code == 200

    # 2nd request succeeds
    r2 = c.post("/v1/chat", json=req)
    assert r2.status_code == 200

    # 3rd request within window exceeds rate limit -> 429
    r3 = c.post("/v1/chat", json=req)
    assert r3.status_code == 429
