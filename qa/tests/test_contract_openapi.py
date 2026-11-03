"""OpenAPI contract conformance and endpoint fuzzing tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_openapi_schema_endpoint(client: TestClient) -> None:
    """Verify that /openapi.json is generated, valid, and exposes required endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "VeriCoach API"

    paths = schema["paths"]
    expected_endpoints = [
        "/health",
        "/api/v1/chat",
        "/api/v1/documents",
        "/api/v1/synthetic-user",
        "/api/v1/bootstrap-synthetic",
    ]

    for ep in expected_endpoints:
        assert ep in paths, f"Expected endpoint {ep} missing in OpenAPI schema"


def test_openapi_contract_chat_request_schema(client: TestClient) -> None:
    """Verify ChatRequest schema has message, locale, and top_k with correct constraints."""
    response = client.get("/openapi.json")
    schema = response.json()
    chat_schema = schema["components"]["schemas"]["ChatRequest"]

    properties = chat_schema["properties"]
    assert "message" in properties
    assert "locale" in properties
    assert "top_k" in properties
    assert "message" in chat_schema["required"]


def test_contract_fuzzing_chat_invalid_types(client: TestClient) -> None:
    """Test API contract enforcement on invalid types (fuzzing)."""
    # 1. message as integer instead of string
    resp = client.post("/api/v1/chat", json={"message": 12345, "locale": "en"})
    # FastAPI can coerce int to str or fail validation; if coerced it should succeed or 422, never 500
    assert resp.status_code in (200, 422)

    # 2. top_k out of bounds (>20)
    resp = client.post(
        "/api/v1/chat",
        json={"message": "hello", "locale": "en", "top_k": 999},
    )
    assert resp.status_code == 422

    # 3. top_k negative
    resp = client.post(
        "/api/v1/chat",
        json={"message": "hello", "locale": "en", "top_k": -1},
    )
    assert resp.status_code == 422

    # 4. unsupported locale
    resp = client.post(
        "/api/v1/chat",
        json={"message": "hello", "locale": "fr"},
    )
    assert resp.status_code == 422


def test_contract_fuzzing_documents_empty_content(client: TestClient) -> None:
    """Verify document index rejects empty content with 422."""
    resp = client.post("/api/v1/documents", json={"content": "", "source": "test"})
    assert resp.status_code == 422


def test_contract_fuzzing_bootstrap_synthetic_count(client: TestClient) -> None:
    """Verify bootstrap rejects count > 10."""
    resp = client.post(
        "/api/v1/bootstrap-synthetic", json={"count": 50, "locale": "en"}
    )
    assert resp.status_code == 422
