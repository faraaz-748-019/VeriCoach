"""LangSmith Golden Dataset uploader for VeriCoach."""

from __future__ import annotations

import json
import logging
import os
import pathlib
from typing import Any

from langsmith import Client

logger = logging.getLogger("vericoach.qa.langsmith.dataset")

DEFAULT_GOLDEN_PATH = pathlib.Path("qa/data/golden/golden_v1.jsonl")
DEFAULT_DATASET_NAME = "vericoach-golden-v1"


def load_golden_dataset(path: pathlib.Path | str = DEFAULT_GOLDEN_PATH) -> list[dict[str, Any]]:
    """Load items from the golden dataset JSONL file."""
    file_path = pathlib.Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {file_path}")

    items: list[dict[str, Any]] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                items.append(json.loads(line_str))
            except json.JSONDecodeError as exc:
                logger.warning("Failed to parse golden item line %d: %s", line_num, exc)
    return items


def upload_golden_dataset(
    dataset_name: str = DEFAULT_DATASET_NAME,
    dataset_path: pathlib.Path | str = DEFAULT_GOLDEN_PATH,
    client: Client | None = None,
    mock: bool = False,
) -> dict[str, Any]:
    """
    Idempotently upload the golden dataset to LangSmith.

    If mock=True or no LANGSMITH_API_KEY is available, returns a simulated
    manifest without making remote API requests.
    """
    items = load_golden_dataset(dataset_path)
    api_key = os.getenv("LANGSMITH_API_KEY", "")

    if mock or not api_key:
        logger.info(
            "Mock or offline mode: simulating dataset upload for %s (%d items)",
            dataset_name,
            len(items),
        )
        return {
            "dataset_name": dataset_name,
            "status": "simulated_local",
            "items_count": len(items),
            "id": f"mock-ds-{dataset_name}",
        }

    langsmith_client = client or Client()

    # Check if dataset already exists
    if langsmith_client.has_dataset(dataset_name=dataset_name):
        logger.info("Dataset '%s' already exists in LangSmith.", dataset_name)
        existing = langsmith_client.read_dataset(dataset_name=dataset_name)
        return {
            "dataset_name": dataset_name,
            "status": "already_exists",
            "items_count": len(items),
            "id": str(getattr(existing, "id", "")),
        }

    dataset = langsmith_client.create_dataset(
        dataset_name=dataset_name,
        description="VeriCoach Multilingual Financial QA Golden Dataset v1 (EN, HI, TE)",
    )

    inputs = [
        {
            "question": item["question"],
            "language": item["language"],
            "category": item["category"],
        }
        for item in items
    ]
    outputs = [
        {
            "reference_answer": item["reference_answer"],
            "must_refuse": item["must_refuse"],
            "reference_doc_ids": item.get("reference_doc_ids", []),
        }
        for item in items
    ]
    metadata = [
        {
            "id": item["id"],
            "notes": item.get("notes", ""),
        }
        for item in items
    ]

    langsmith_client.create_examples(
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
        dataset_id=dataset.id,
    )

    logger.info("Successfully uploaded %d examples to LangSmith dataset '%s'", len(items), dataset_name)
    return {
        "dataset_name": dataset_name,
        "status": "created",
        "items_count": len(items),
        "id": str(dataset.id),
    }
