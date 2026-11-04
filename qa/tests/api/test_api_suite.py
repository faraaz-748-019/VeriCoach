"""Comprehensive API test suite for VeriCoach v1 REST endpoints.

Covers:
1. Authentication (missing, invalid, valid API keys)
2. Validation boundaries (empty "", 1000 chars, 1001 chars)
3. Unsupported language handling
4. Negative cases (404s, out-of-range ratings, malformed bodies)
5. Feedback idempotency and metrics integrity
6. Response schema validation using jsonschema against committed OpenAPI spec
7. Performance latency benchmark with p95 assertion over 50 requests
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import jsonschema
import numpy as np
import pytest
from backend.config import BackendSettings, get_backend_settings
from backend.main import app, get_rag_store, reset_rag_store
from backend.providers.mock import MockLLMProvider
from backend.rag.store import ChromaRAGStore
from backend.rate_limit import _default_limiter
from faker import Faker
from fastapi.testclient import TestClient

fake = Faker("en_IN")
SNAPSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "api" / "openapi.json"

VALID_API_KEY = "vc-test-key-67890"
INVALID_API_KEY = "vc-invalid-forbidden-999"


@pytest.fixture(autouse=True)
def setup_api_backend():
    """Ensure clean in-memory Chroma store, fresh settings, and reset limiter for each test."""
    test_settings = BackendSettings(
        llm_provider="mock",
        require_api_key=False,
        api_keys=["vc-dev-key-12345", VALID_API_KEY],
        rate_limit_per_minute=200,
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
def client() -> TestClient:
    """Synchronous FastAPI TestClient with default JSON headers."""
    return TestClient(
        app,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )


@pytest.fixture(scope="session")
def openapi_schemas() -> dict[str, Any]:
    """Load JSON Schema definitions and components from the OpenAPI spec."""
    assert SNAPSHOT_PATH.exists(), f"OpenAPI spec snapshot missing at {SNAPSHOT_PATH}"
    with open(SNAPSHOT_PATH, encoding="utf-8") as f:
        spec = json.load(f)
    return spec


def validate_schema(instance: Any, schema_name: str, spec: dict[str, Any]) -> None:
    """Validate a JSON response payload against OpenAPI component schemas."""
    schemas = spec.get("components", {}).get("schemas", {})
    assert schema_name in schemas, f"Schema '{schema_name}' not found in OpenAPI spec"

    target_schema = dict(schemas[schema_name])
    # Embed full component definitions for resolving nested $ref pointers
    target_schema["components"] = {"schemas": schemas}
    jsonschema.validate(instance=instance, schema=target_schema)


# ── 1. Authentication Tests ───────────────────────────────────────────────────


@pytest.mark.api
def test_auth_missing_key(client: TestClient) -> None:
    """Verify that requests missing X-API-Key are rejected with 401 when auth is enforced."""
    app.dependency_overrides[get_backend_settings] = lambda: BackendSettings(
        llm_provider="mock",
        require_api_key=True,
        api_keys=[VALID_API_KEY],
    )
    resp = client.post(
        "/v1/chat",
        json={"question": "What is an emergency fund?", "language": "en"},
    )
    assert resp.status_code == 401
    assert "Missing required X-API-Key" in resp.json().get("detail", "")


@pytest.mark.api
def test_auth_wrong_key(client: TestClient) -> None:
    """Verify that requests with an invalid X-API-Key are rejected with 401."""
    app.dependency_overrides[get_backend_settings] = lambda: BackendSettings(
        llm_provider="mock",
        require_api_key=True,
        api_keys=[VALID_API_KEY],
    )
    resp = client.post(
        "/v1/chat",
        headers={"X-API-Key": INVALID_API_KEY},
        json={"question": "What is an emergency fund?", "language": "en"},
    )
    assert resp.status_code == 401
    assert "Invalid X-API-Key" in resp.json().get("detail", "")


@pytest.mark.api
def test_auth_valid_key(client: TestClient) -> None:
    """Verify that requests with a valid X-API-Key succeed with 200 OK."""
    app.dependency_overrides[get_backend_settings] = lambda: BackendSettings(
        llm_provider="mock",
        require_api_key=True,
        api_keys=[VALID_API_KEY],
    )
    resp = client.post(
        "/v1/chat",
        headers={"X-API-Key": VALID_API_KEY},
        json={"question": "What is an emergency fund?", "language": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["refused"] is False
    assert len(data["answer"]) > 0


# ── 2. Validation Boundaries ──────────────────────────────────────────────────


@pytest.mark.api
def test_validation_empty_question(client: TestClient) -> None:
    """Verify empty question boundary (min_length=1) triggers 422 Unprocessable Entity."""
    resp = client.post(
        "/v1/chat",
        json={"question": "", "language": "en"},
    )
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any("question" in str(err.get("loc", [])) for err in errors)


@pytest.mark.api
def test_validation_boundary_1000_characters(client: TestClient) -> None:
    """Verify upper boundary of exactly 1000 characters is accepted with 200 OK."""
    base_query = f"Financial query for user {fake.name()}: What are UPI rules? "
    padding_needed = 1000 - len(base_query)
    boundary_question = base_query + ("x" * padding_needed)
    assert len(boundary_question) == 1000

    resp = client.post(
        "/v1/chat",
        json={"question": boundary_question, "language": "en"},
    )
    assert resp.status_code == 200
    assert resp.json()["refused"] is False


@pytest.mark.api
def test_validation_boundary_1001_characters(client: TestClient) -> None:
    """Verify boundary exceeding maximum length (1001 characters) is rejected with 422."""
    base_query = f"Financial query for user {fake.name()}: What are UPI rules? "
    padding_needed = 1001 - len(base_query)
    over_limit_question = base_query + ("y" * padding_needed)
    assert len(over_limit_question) == 1001

    resp = client.post(
        "/v1/chat",
        json={"question": over_limit_question, "language": "en"},
    )
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any("question" in str(err.get("loc", [])) for err in errors)


# ── 3. Unsupported Language ───────────────────────────────────────────────────


@pytest.mark.api
@pytest.mark.parametrize("bad_lang", ["fr", "es", "de", "klingon", "unknown"])
def test_unsupported_language_rejected(client: TestClient, bad_lang: str) -> None:
    """Verify that unsupported languages outside ('en', 'hi', 'te', 'auto') trigger 422."""
    resp = client.post(
        "/v1/chat",
        json={"question": "How do I plan my retirement savings?", "language": bad_lang},
    )
    assert resp.status_code == 422
    errors = resp.json().get("detail", [])
    assert any("language" in str(err.get("loc", [])) for err in errors)


# ── 4. Negative Cases ─────────────────────────────────────────────────────────


@pytest.mark.api
def test_negative_document_not_found(client: TestClient) -> None:
    """Verify fetching a non-existent document ID returns 404 Not Found."""
    random_doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    resp = client.get(f"/v1/documents/{random_doc_id}")
    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


@pytest.mark.api
@pytest.mark.parametrize("invalid_rating", [0, 6, -1, 10])
def test_negative_feedback_rating_out_of_bounds(
    client: TestClient, invalid_rating: int
) -> None:
    """Verify feedback rating outside 1..5 range is rejected with 422."""
    synthetic_trace = str(uuid.uuid4())
    resp = client.post(
        "/v1/feedback",
        json={"trace_id": synthetic_trace, "rating": invalid_rating},
    )
    assert resp.status_code == 422


@pytest.mark.api
def test_negative_malformed_json_payloads(client: TestClient) -> None:
    """Verify missing required body fields trigger 422 Unprocessable Entity."""
    # Chat missing 'question'
    resp = client.post("/v1/chat", json={"language": "en"})
    assert resp.status_code == 422

    # Feedback missing 'trace_id'
    resp = client.post("/v1/feedback", json={"rating": 5})
    assert resp.status_code == 422


# ── 5. Feedback Idempotency ───────────────────────────────────────────────────


@pytest.mark.api
def test_feedback_idempotency_preserves_metrics(client: TestClient) -> None:
    """Verify that submitting multiple feedback entries for the same trace_id updates rather than duplicates."""
    trace_id = str(uuid.uuid4())

    # Get initial metrics
    m0 = client.get("/v1/metrics")
    initial_count = m0.json()["feedback_count"]

    # 1. First submission
    resp1 = client.post(
        "/v1/feedback",
        json={"trace_id": trace_id, "rating": 5, "comment": "Excellent answer!"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "feedback_recorded"

    m1 = client.get("/v1/metrics")
    assert m1.json()["feedback_count"] == initial_count + 1

    # 2. Duplicate submission for identical trace_id with revised rating
    resp2 = client.post(
        "/v1/feedback",
        json={
            "trace_id": trace_id,
            "rating": 4,
            "comment": "Revised feedback for same turn.",
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "feedback_recorded"

    m2 = client.get("/v1/metrics")
    # Count must remain unchanged because the operation is idempotent
    assert m2.json()["feedback_count"] == initial_count + 1


# ── 6. Response Schema Validation with jsonschema ──────────────────────────────


@pytest.mark.api
def test_response_schema_validation_all_endpoints(
    client: TestClient, openapi_schemas: dict[str, Any]
) -> None:
    """Validate all response payloads against the committed OpenAPI JSON schemas."""
    # 1. GET /v1/health -> HealthResponseV1
    r_health = client.get("/v1/health")
    assert r_health.status_code == 200
    validate_schema(r_health.json(), "HealthResponseV1", openapi_schemas)

    # 2. POST /v1/chat -> ChatResponseV1
    r_chat = client.post(
        "/v1/chat",
        json={
            "question": "What is the 50/30/20 budget rule?",
            "language": "en",
        },
    )
    assert r_chat.status_code == 200
    chat_data = r_chat.json()
    validate_schema(chat_data, "ChatResponseV1", openapi_schemas)
    trace_id = chat_data["trace_id"]

    # 3. GET /v1/documents -> DocumentListResponseV1
    r_docs = client.get("/v1/documents")
    assert r_docs.status_code == 200
    validate_schema(r_docs.json(), "DocumentListResponseV1", openapi_schemas)

    # 4. GET /v1/documents/{id} -> DocumentItemV1
    r_doc = client.get("/v1/documents/upi_pin_rules")
    assert r_doc.status_code == 200
    validate_schema(r_doc.json(), "DocumentItemV1", openapi_schemas)

    # 5. POST /v1/feedback -> FeedbackResponseV1
    r_fb = client.post(
        "/v1/feedback",
        json={"trace_id": trace_id, "rating": 5, "comment": "Helpful overview"},
    )
    assert r_fb.status_code == 200
    validate_schema(r_fb.json(), "FeedbackResponseV1", openapi_schemas)

    # 6. GET /v1/metrics -> MetricsResponseV1
    r_metrics = client.get("/v1/metrics")
    assert r_metrics.status_code == 200
    validate_schema(r_metrics.json(), "MetricsResponseV1", openapi_schemas)


# ── 7. p95 Latency Assertion on 50 Requests ───────────────────────────────────


@pytest.mark.api
def test_p95_latency_50_requests_under_threshold(client: TestClient) -> None:
    """Execute 50 synthetic queries and assert p95 response time is strictly under 250ms."""
    sample_queries = [
        "Do I need to enter my UPI PIN to receive money?",
        "What is the difference between term insurance and life insurance?",
        "How is CIBIL score calculated?",
        "What documents are acceptable for KYC?",
        "How does a mutual fund SIP work?",
        "What is an emergency fund?",
        "How can I report a financial cyber fraud to 1930?",
        "What is compound interest in simple terms?",
        "How does a home loan EMI get calculated?",
        "What is the 50/30/20 budgeting method?",
    ]

    latencies_ms: list[float] = []

    for i in range(50):
        # Generate synthetic query variants using Faker
        query_text = f"{sample_queries[i % len(sample_queries)]} (query id: {fake.unique.random_number(digits=6)})"
        start_time = time.perf_counter()
        resp = client.post(
            "/v1/chat",
            json={"question": query_text, "language": "en"},
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        assert resp.status_code == 200
        latencies_ms.append(elapsed_ms)

    assert len(latencies_ms) == 50

    p50 = float(np.percentile(latencies_ms, 50))
    p90 = float(np.percentile(latencies_ms, 90))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))
    max_lat = max(latencies_ms)

    print(
        f"\n[Latency Benchmark - 50 Requests] "
        f"p50: {p50:.2f}ms | p90: {p90:.2f}ms | p95: {p95:.2f}ms | p99: {p99:.2f}ms | max: {max_lat:.2f}ms"
    )

    # Acceptance requirement: p95 latency assertion on 50 requests
    assert p95 < 250.0, f"Expected p95 latency < 250ms, got {p95:.2f}ms"
