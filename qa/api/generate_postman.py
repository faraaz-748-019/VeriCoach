"""Generate Postman collection and environments from OpenAPI specification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

API_DIR = Path(__file__).resolve().parent
OPENAPI_PATH = API_DIR / "openapi.json"
COLLECTION_PATH = API_DIR / "vericoach.postman_collection.json"
LOCAL_ENV_PATH = API_DIR / "vericoach_local.postman_environment.json"
CI_ENV_PATH = API_DIR / "vericoach_ci.postman_environment.json"


def build_collection(openapi: dict[str, Any]) -> dict[str, Any]:
    """Convert OpenAPI spec into a rich Postman collection with tests and pre-request scripts."""
    schemas = openapi.get("components", {}).get("schemas", {})

    # Extracted simplified schemas for AJV / jsonSchema validation in Postman
    health_schema = schemas.get("HealthResponseV1", {})
    chat_schema = schemas.get("ChatResponseV1", {})
    doc_list_schema = schemas.get("DocumentListResponseV1", {})
    doc_item_schema = schemas.get("DocumentItemV1", {})
    feedback_schema = schemas.get("FeedbackResponseV1", {})
    metrics_schema = schemas.get("MetricsResponseV1", {})

    def make_test_script(schema_obj: dict[str, Any], extra_js: str = "") -> list[str]:
        # Embed components schemas so AJV can resolve $ref like #/components/schemas/SourceCitation
        full_schema = dict(schema_obj)
        full_schema["components"] = {"schemas": schemas}
        schema_json = json.dumps(full_schema)
        lines = [
            "pm.test('Status code is 200 OK', function () {",
            "    pm.response.to.have.status(200);",
            "});",
            "",
            "pm.test('Response time is under 2000ms', function () {",
            "    pm.expect(pm.response.responseTime).to.be.below(2000);",
            "});",
            "",
            "pm.test('Response matches OpenAPI JSON schema', function () {",
            f"    const schema = {schema_json};",
            "    pm.response.to.have.jsonSchema(schema);",
            "});",
        ]
        if extra_js:
            lines.append("")
            lines.append(extra_js)
        return lines

    auth_prerequest = [
        "// Dynamic API Key injection from active environment",
        "const apiKey = pm.environment.get('apiKey');",
        "if (apiKey) {",
        "    pm.request.headers.upsert({ key: 'X-API-Key', value: apiKey });",
        "}",
    ]

    items = [
        {
            "name": "Health Check (v1)",
            "request": {
                "method": "GET",
                "header": [{"key": "Accept", "value": "application/json"}],
                "url": {
                    "raw": "{{baseUrl}}/v1/health",
                    "host": ["{{baseUrl}}"],
                    "path": ["v1", "health"],
                },
                "description": "System health and provider status verification.",
            },
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": make_test_script(health_schema),
                    },
                }
            ],
        },
        {
            "name": "Ask Financial Query (v1)",
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"},
                    {"key": "Accept", "value": "application/json"},
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(
                        {
                            "question": "Do I need to enter my UPI PIN to receive money?",
                            "language": "en",
                        },
                        indent=2,
                    ),
                },
                "url": {
                    "raw": "{{baseUrl}}/v1/chat",
                    "host": ["{{baseUrl}}"],
                    "path": ["v1", "chat"],
                },
                "description": "Multilingual financial RAG query with safety guardrails.",
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": auth_prerequest},
                },
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": make_test_script(
                            chat_schema,
                            "// Capture trace_id for downstream feedback test\n"
                            "const jsonResp = pm.response.json();\n"
                            "if (jsonResp.trace_id) {\n"
                            "    pm.environment.set('lastTraceId', jsonResp.trace_id);\n"
                            "}",
                        ),
                    },
                },
            ],
        },
        {
            "name": "List Documents (v1)",
            "request": {
                "method": "GET",
                "header": [{"key": "Accept", "value": "application/json"}],
                "url": {
                    "raw": "{{baseUrl}}/v1/documents",
                    "host": ["{{baseUrl}}"],
                    "path": ["v1", "documents"],
                },
                "description": "Retrieve full corpus of indexed financial educational documents.",
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": auth_prerequest},
                },
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": make_test_script(doc_list_schema),
                    },
                },
            ],
        },
        {
            "name": "Get Document By ID (v1)",
            "request": {
                "method": "GET",
                "header": [{"key": "Accept", "value": "application/json"}],
                "url": {
                    "raw": "{{baseUrl}}/v1/documents/upi_pin_rules",
                    "host": ["{{baseUrl}}"],
                    "path": ["v1", "documents", "upi_pin_rules"],
                },
                "description": "Fetch individual verified document by identifier.",
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": auth_prerequest},
                },
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": make_test_script(doc_item_schema),
                    },
                },
            ],
        },
        {
            "name": "Submit Feedback (v1)",
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"},
                    {"key": "Accept", "value": "application/json"},
                ],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps(
                        {
                            "trace_id": "{{lastTraceId}}",
                            "rating": 5,
                            "comment": "Accurate advice on UPI security.",
                        },
                        indent=2,
                    ),
                },
                "url": {
                    "raw": "{{baseUrl}}/v1/feedback",
                    "host": ["{{baseUrl}}"],
                    "path": ["v1", "feedback"],
                },
                "description": "Submit user satisfaction feedback linked to a query trace ID.",
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": auth_prerequest},
                },
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": make_test_script(feedback_schema),
                    },
                },
            ],
        },
        {
            "name": "Get Operational Metrics (v1)",
            "request": {
                "method": "GET",
                "header": [{"key": "Accept", "value": "application/json"}],
                "url": {
                    "raw": "{{baseUrl}}/v1/metrics",
                    "host": ["{{baseUrl}}"],
                    "path": ["v1", "metrics"],
                },
                "description": "Fetch system metrics including requests, refusals, latency, and feedback.",
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {"type": "text/javascript", "exec": auth_prerequest},
                },
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": make_test_script(metrics_schema),
                    },
                },
            ],
        },
    ]

    return {
        "info": {
            "_postman_id": "c138942b-5f11-4fa3-9f88-vericoach-v1",
            "name": "VeriCoach API Collection",
            "description": "Automated regression suite for VeriCoach Multilingual Financial Assistant API.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
    }


def build_environment(name: str, base_url: str, api_key: str) -> dict[str, Any]:
    """Construct Postman environment JSON."""
    return {
        "id": f"env-{name.lower().replace(' ', '-')}",
        "name": name,
        "values": [
            {"key": "baseUrl", "value": base_url, "type": "default", "enabled": True},
            {"key": "apiKey", "value": api_key, "type": "secret", "enabled": True},
            {
                "key": "lastTraceId",
                "value": "b74d6fb2-3784-4861-b4cf-e94025a17684",
                "type": "default",
                "enabled": True,
            },
        ],
        "_postman_variable_scope": "environment",
    }


def main() -> None:
    with open(OPENAPI_PATH, encoding="utf-8") as f:
        openapi = json.load(f)

    collection = build_collection(openapi)
    with open(COLLECTION_PATH, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2)
        f.write("\n")

    local_env = build_environment(
        "VeriCoach Local", "http://127.0.0.1:8000", "vc-dev-key-12345"
    )
    with open(LOCAL_ENV_PATH, "w", encoding="utf-8") as f:
        json.dump(local_env, f, indent=2)
        f.write("\n")

    ci_env = build_environment(
        "VeriCoach CI", "http://127.0.0.1:8000", "vc-test-key-67890"
    )
    with open(CI_ENV_PATH, "w", encoding="utf-8") as f:
        json.dump(ci_env, f, indent=2)
        f.write("\n")

    print(f"Generated Postman collection: {COLLECTION_PATH}")
    print(f"Generated Postman Local env: {LOCAL_ENV_PATH}")
    print(f"Generated Postman CI env: {CI_ENV_PATH}")


if __name__ == "__main__":
    main()
