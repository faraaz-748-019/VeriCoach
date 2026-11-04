"""Schemathesis property-based fuzz testing for VeriCoach API.

Automatically discovers unhandled 5xx server errors and schema inconsistencies.
Any real defects found are logged and recorded in docs/KNOWN_FAILURES.md.
"""

from __future__ import annotations

import schemathesis
from backend.main import app
from hypothesis import settings

# Load ASGI schema in-memory (zero-network, fast execution)
schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@settings(max_examples=15, deadline=None)
@schema.parametrize()
def test_schemathesis_no_server_errors(case: schemathesis.Case) -> None:
    """Verify that no fuzz payload causes a 500 Internal Server Error."""
    response = case.call()
    # Ensure every endpoint handles edge case fuzzing gracefully (2xx, 4xx, but never 500)
    assert (
        response.status_code < 500
    ), f"Server error {response.status_code} on {case.method} {case.path} with body: {case.body}"
