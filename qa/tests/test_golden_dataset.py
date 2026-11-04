"""Automated test suite validating the Golden Evaluation Dataset."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa.data.validate_golden import validate_golden_dataset


@pytest.mark.llm
def test_golden_v1_dataset_integrity() -> None:
    """Assert that qa/data/golden/golden_v1.jsonl conforms to all evaluation criteria:

    - Schema validity (Pydantic model)
    - Total 120 records
    - Exact language balance (40 en, 40 hi, 40 te)
    - Target category distribution (60% answerable, 15% unanswerable, 15% refusal, 10% adversarial)
    - Reference document IDs exist in canonical documents corpus
    - No duplicate questions or IDs
    """
    dataset_path = (
        Path(__file__).resolve().parent.parent / "data" / "golden" / "golden_v1.jsonl"
    )
    assert dataset_path.exists(), f"Golden dataset missing at {dataset_path}"

    stats = validate_golden_dataset(dataset_path)

    assert stats["total_items"] == 120
    assert stats["language_counts"] == {"en": 40, "hi": 40, "te": 40}
    assert stats["category_counts"] == {
        "answerable": 72,
        "unanswerable": 18,
        "advice_refusal": 18,
        "adversarial": 12,
    }

    # Verify per-language consistency
    for lang in ("en", "hi", "te"):
        matrix = stats["matrix"][lang]
        assert matrix["answerable"] == 24
        assert matrix["unanswerable"] == 6
        assert matrix["advice_refusal"] == 6
        assert matrix["adversarial"] == 4
