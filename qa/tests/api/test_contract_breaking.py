"""OpenAPI Breaking Changes Contract Tests.

Compares current live application OpenAPI specification against the committed
snapshot in qa/api/openapi.json to prevent breaking API changes from shipping.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from backend.main import app

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "api" / "openapi.json"


def find_breaking_changes(
    baseline: dict[str, Any], current: dict[str, Any]
) -> list[str]:
    """Identify backwards-incompatible API contract modifications."""
    breaking: list[str] = []

    baseline_paths = baseline.get("paths", {})
    current_paths = current.get("paths", {})

    # 1. Removed Endpoints
    for path in baseline_paths:
        if path not in current_paths:
            breaking.append(f"Removed endpoint path: '{path}'")
            continue

        baseline_methods = baseline_paths[path]
        current_methods = current_paths[path]

        # 2. Removed HTTP Methods
        for method, baseline_op in baseline_methods.items():
            if method.lower() in ("parameters", "summary", "description"):
                continue
            if method not in current_methods:
                breaking.append(
                    f"Removed HTTP method '{method.upper()}' on path '{path}'"
                )
                continue

            current_op = current_methods[method]

            # 3. Removed Documented Status Codes
            baseline_responses = baseline_op.get("responses", {})
            current_responses = current_op.get("responses", {})
            for code in baseline_responses:
                if code.startswith("2") and code not in current_responses:
                    breaking.append(
                        f"Removed success status code '{code}' on {method.upper()} {path}"
                    )

            # 4. Added New Required Query / Path / Header Parameters
            baseline_params = {
                p.get("name"): p for p in baseline_op.get("parameters", [])
            }
            current_params = {
                p.get("name"): p for p in current_op.get("parameters", [])
            }
            for p_name, p_data in current_params.items():
                if p_data.get("required", False):
                    if p_name not in baseline_params or not baseline_params[p_name].get(
                        "required", False
                    ):
                        breaking.append(
                            f"Added new required parameter '{p_name}' to {method.upper()} {path}"
                        )

    # 5. Schema Level Breaking Changes: Added new required properties in Request Bodies
    baseline_schemas = baseline.get("components", {}).get("schemas", {})
    current_schemas = current.get("components", {}).get("schemas", {})

    for schema_name, base_schema in baseline_schemas.items():
        if schema_name not in current_schemas:
            # Component schema removed
            if "Request" in schema_name or "Response" in schema_name:
                breaking.append(f"Removed component schema '{schema_name}'")
            continue

        curr_schema = current_schemas[schema_name]

        # Check for newly added required request fields
        if "Request" in schema_name:
            base_required = set(base_schema.get("required", []))
            curr_required = set(curr_schema.get("required", []))
            new_required = curr_required - base_required
            if new_required:
                breaking.append(
                    f"Added new required property {new_required} to request schema '{schema_name}'"
                )

        # Check for removed required response fields
        if "Response" in schema_name:
            base_required = set(base_schema.get("required", []))
            curr_required = set(curr_schema.get("required", []))
            removed_required = base_required - curr_required
            if removed_required:
                breaking.append(
                    f"Removed required property {removed_required} from response schema '{schema_name}'"
                )

    return breaking


@pytest.mark.api
def test_openapi_contract_has_no_breaking_changes() -> None:
    """Ensure current live app does not break the committed OpenAPI snapshot contract."""
    assert (
        SNAPSHOT_PATH.exists()
    ), f"Committed OpenAPI snapshot missing at {SNAPSHOT_PATH}"

    with open(SNAPSHOT_PATH, encoding="utf-8") as f:
        snapshot = json.load(f)

    live_spec = app.openapi()
    breaking_changes = find_breaking_changes(baseline=snapshot, current=live_spec)

    assert not breaking_changes, (
        f"Detected {len(breaking_changes)} breaking changes against snapshot:\n"
        + "\n".join(f"- {c}" for c in breaking_changes)
    )


@pytest.mark.api
def test_contract_diff_detector_sensitivity() -> None:
    """Verify that breaking diff detector correctly catches removed endpoints and added required fields."""
    with open(SNAPSHOT_PATH, encoding="utf-8") as f:
        snapshot = json.load(f)

    # Simulate breaking change 1: removing an endpoint
    tampered_1 = copy.deepcopy(snapshot)
    tampered_1["paths"].pop("/v1/chat", None)
    diffs_1 = find_breaking_changes(baseline=snapshot, current=tampered_1)
    assert any("Removed endpoint path: '/v1/chat'" in d for d in diffs_1)

    # Simulate breaking change 2: adding a required field to ChatRequestV1
    tampered_2 = copy.deepcopy(snapshot)
    tampered_2["components"]["schemas"]["ChatRequestV1"]["required"].append(
        "new_mandatory_field"
    )
    diffs_2 = find_breaking_changes(baseline=snapshot, current=tampered_2)
    assert any("Added new required property" in d for d in diffs_2)
