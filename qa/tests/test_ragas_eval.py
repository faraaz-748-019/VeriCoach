"""Integration and unit tests for Ragas evaluation framework."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from qa.llm_eval.ragas_eval.config import RagasEvalSettings
from qa.llm_eval.ragas_eval.evaluator import RagasEvaluator
from qa.llm_eval.ragas_eval.pipeline_collector import (
    EvaluatedItem,
    RAGPipelineCollector,
    load_golden_items,
)
from qa.llm_eval.ragas_eval.wrappers import InstrumentedDiskCache


@pytest.mark.llm
def test_load_golden_items_balanced_multilingual() -> None:
    """Verify load_golden_items samples evenly across English, Hindi, and Telugu."""
    golden_path = Path("qa/data/golden/golden_v1.jsonl")
    items_30 = load_golden_items(golden_path=golden_path, limit=30)
    assert len(items_30) == 30

    lang_counts: dict[str, int] = {}
    for it in items_30:
        lang = it["language"]
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

    assert lang_counts == {"en": 10, "hi": 10, "te": 10}

    # Verify attributes
    for item in items_30:
        assert item["id"]
        assert item["question"]
        assert item["language"] in ("en", "hi", "te")
        assert item["category"] in (
            "answerable",
            "unanswerable",
            "advice_refusal",
            "adversarial",
        )


@pytest.mark.llm
def test_pipeline_collector_executes_real_rag() -> None:
    """Verify RAGPipelineCollector executes chat_v1 and collects contexts and answers."""
    golden_path = Path("qa/data/golden/golden_v1.jsonl")
    settings = RagasEvalSettings(
        golden_path=golden_path,
        provider="mock",
    )
    collector = RAGPipelineCollector(settings)
    items = load_golden_items(golden_path=golden_path, limit=3)

    evaluated_item = collector.collect_item(items[0])

    assert isinstance(evaluated_item, EvaluatedItem)
    assert evaluated_item.id == items[0]["id"]
    assert evaluated_item.question == items[0]["question"]
    assert evaluated_item.language == items[0]["language"]
    assert isinstance(evaluated_item.response, str)
    assert len(evaluated_item.response) > 0
    assert isinstance(evaluated_item.retrieved_contexts, list)


@pytest.mark.llm
def test_disk_cache_recording(tmp_path: Path) -> None:
    """Verify InstrumentedDiskCache tracks cache hits and misses correctly."""
    cache = InstrumentedDiskCache(directory=tmp_path / "cache_test")

    # Initial miss
    val = cache.get("key1")
    assert val is None
    assert cache.stats.misses == 1
    assert cache.stats.hits == 0

    # Set value
    cache.set("key1", {"score": 0.85})

    # Subsequent hit
    cached_val = cache.get("key1")
    assert cached_val == {"score": 0.85}
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1
    assert cache.stats.hit_ratio == 0.5
    cache.close()


@pytest.mark.llm
def test_ragas_evaluation_and_cache_replay(tmp_path: Path) -> None:
    """Verify RagasEvaluator computes metrics and replays 100% from disk cache on rerun."""
    cache_dir = tmp_path / "ragas_cache"
    output_dir = tmp_path / "results"
    golden_path = Path("qa/data/golden/golden_v1.jsonl")

    settings = RagasEvalSettings(
        golden_path=golden_path,
        provider="mock",
        cache_dir=cache_dir,
        output_dir=output_dir,
    )

    items = load_golden_items(golden_path=golden_path, limit=3)
    collector = RAGPipelineCollector(settings)
    collected_items = collector.collect_all(items)

    # First run (Cache Misses)
    evaluator_run1 = RagasEvaluator(settings=settings)
    result_run1 = evaluator_run1.evaluate_dataset(collected_items)

    assert result_run1["total_items"] == 3
    assert "context_precision" in result_run1["overall_scores"]
    assert "context_recall" in result_run1["overall_scores"]
    assert "faithfulness" in result_run1["overall_scores"]
    assert "answer_relevancy" in result_run1["overall_scores"]

    for metric_name, val in result_run1["overall_scores"].items():
        assert 0.0 <= val <= 1.0, f"Metric {metric_name} score out of range: {val}"

    assert len(result_run1["worst_10_items"]) <= 3
    assert evaluator_run1.cache.stats.misses == 3
    evaluator_run1.cache.close()

    # Second run on fresh items through identical evaluator / cache dir (Cache Hits)
    fresh_items = collector.collect_all(items)
    evaluator_run2 = RagasEvaluator(settings=settings)
    result_run2 = evaluator_run2.evaluate_dataset(fresh_items)

    assert result_run2["total_items"] == 3
    assert evaluator_run2.cache.stats.hits == 3
    assert evaluator_run2.cache.stats.misses == 0
    assert evaluator_run2.cache.stats.hit_ratio == 1.0

    # Ensure identical scores between cached and uncached run
    assert (
        result_run1["overall_scores"]["faithfulness"]
        == result_run2["overall_scores"]["faithfulness"]
    )
    evaluator_run2.cache.close()


@pytest.mark.llm
def test_ragas_json_and_csv_export(tmp_path: Path) -> None:
    """Verify evaluation generates schema-compliant JSON and CSV export files."""
    cache_dir = tmp_path / "ragas_cache"
    output_dir = tmp_path / "results"
    golden_path = Path("qa/data/golden/golden_v1.jsonl")

    settings = RagasEvalSettings(
        golden_path=golden_path,
        provider="mock",
        cache_dir=cache_dir,
        output_dir=output_dir,
    )

    items = load_golden_items(golden_path=golden_path, limit=6)
    collector = RAGPipelineCollector(settings)
    collected_items = collector.collect_all(items)

    evaluator = RagasEvaluator(settings=settings)
    result = evaluator.evaluate_dataset(collected_items)

    date_str = result["run_date"]
    json_path = output_dir / f"ragas_{date_str}.json"
    csv_path = output_dir / f"ragas_{date_str}.csv"

    assert json_path.exists()
    assert csv_path.exists()

    # Validate JSON content
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "overall_scores" in data
    assert "scores_by_language" in data
    assert "scores_by_category" in data
    assert "worst_10_items" in data
    assert "items" in data
    assert len(data["items"]) == 6

    # Check language breakdown contains en, hi, te
    for lang in ("en", "hi", "te"):
        assert lang in data["scores_by_language"]

    # Validate CSV content
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 6
    expected_cols = {
        "id",
        "language",
        "category",
        "question",
        "response",
        "reference",
        "retrieved_contexts",
        "context_precision",
        "context_recall",
        "faithfulness",
        "answer_relevancy",
        "composite_score",
    }
    assert expected_cols.issubset(set(rows[0].keys()))
    evaluator.cache.close()
