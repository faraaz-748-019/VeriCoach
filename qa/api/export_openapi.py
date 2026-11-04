"""Export OpenAPI specification for VeriCoach backend to qa/api/openapi.json."""

from __future__ import annotations

import json
from pathlib import Path

from backend.main import app


def export_openapi(output_path: Path | None = None) -> dict:
    """Generate and serialize the OpenAPI schema to disk."""
    if output_path is None:
        output_path = Path(__file__).resolve().parent / "openapi.json"

    openapi_schema = app.openapi()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return openapi_schema


if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "openapi.json"
    schema = export_openapi(target)
    print(
        f"Exported OpenAPI {schema.get('openapi')} spec with {len(schema.get('paths', {}))} paths to {target}"
    )
