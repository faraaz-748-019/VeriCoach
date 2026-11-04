"""Tests for new LLM evaluation components: LangSmith, Judge Reliability, and Multilingual Consistency."""

from __future__ import annotations

import pathlib
from typing import Any

import pytest

from qa.llm_eval.judge_reliability import (
    classify_with_judge,
    compute_cohen_kappa,
    interpret_kappa,
    sample_stratified_dataset,
)
from qa.llm_eval.langsmith_eval.dataset_uploader import (
    load_golden_dataset,
    upload_golden_dataset,
)
from qa.llm_eval.langsmith_eval.experiment_runner import (
    eval_latency,
    eval_refusal_correctness,
    eval_safety_and_no_guarantees,
    run_langsmith_experiment,
)
from qa.llm_eval.langsmith_eval.tracer import is_langsmith_tracing_enabled, traceable
from qa.llm_eval.multilingual_consistency import (
    compute_cosine_similarity,
    evaluate_pair_consistency_with_judge,
    extract_trilingual_questions,
)

# ── LangSmith Component Tests ──────────────────────────────────────────────────


def test_langsmith_tracing_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    assert not is_langsmith_tracing_enabled()


def test_langsmith_traceable_decorator_passthrough() -> None:
    @traceable(run_type="chain", name="test_func")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5


def test_langsmith_dataset_upload_mock() -> None:
    res = upload_golden_dataset(dataset_name="test-ds", mock=True)
    assert res["status"] == "simulated_local"
    assert res["items_count"] >= 100


def test_langsmith_evaluators() -> None:
    class DummyRun:
        def __init__(self, outputs: dict[str, Any]) -> None:
            self.outputs = outputs

    class DummyExample:
        def __init__(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
            self.inputs = inputs
            self.outputs = outputs

    # Test refusal correctness evaluator
    run_refused = DummyRun({"refused": True, "answer": "Cannot provide advice."})
    ex_must_refuse = DummyExample({"category": "advice_refusal"}, {"must_refuse": True})
    assert eval_refusal_correctness(run_refused, ex_must_refuse)["score"] == 1.0

    run_not_refused = DummyRun(
        {"refused": False, "answer": "UPI daily limit is 1 Lakh."}
    )
    assert eval_refusal_correctness(run_not_refused, ex_must_refuse)["score"] == 0.0

    # Test safety evaluator
    run_safe = DummyRun({"answer": "Mutual funds carry market risks."})
    assert eval_safety_and_no_guarantees(run_safe, ex_must_refuse)["score"] == 1.0

    run_unsafe = DummyRun({"answer": "We promise a guaranteed return of 25%."})
    assert eval_safety_and_no_guarantees(run_unsafe, ex_must_refuse)["score"] == 0.0

    # Test latency SLA evaluator
    run_fast = DummyRun({"latency_ms": 120.0})
    assert eval_latency(run_fast, ex_must_refuse)["score"] == 1.0

    run_slow = DummyRun({"latency_ms": 6000.0})
    assert eval_latency(run_slow, ex_must_refuse)["score"] == 0.0


def test_langsmith_experiment_mock_run(tmp_path: pathlib.Path) -> None:
    res = run_langsmith_experiment(
        dataset_name="test-experiment",
        sample_size=3,
        mock=True,
    )
    assert res["num_examples"] == 3
    assert "refusal_correctness" in res["summary_metrics"]
    assert "safety_compliance" in res["summary_metrics"]


# ── Judge Reliability Tests ────────────────────────────────────────────────────


def test_stratified_sampling_balance() -> None:
    items = load_golden_dataset()
    sampled = sample_stratified_dataset(items, total_size=30, seed=42)

    assert len(sampled) == 30
    langs = [it["language"] for it in sampled]
    assert langs.count("en") == 10
    assert langs.count("hi") == 10
    assert langs.count("te") == 10

    for lang in ["en", "hi", "te"]:
        lang_items = [it for it in sampled if it["language"] == lang]
        cats = [it["category"] for it in lang_items]
        assert cats.count("answerable") == 6
        assert cats.count("unanswerable") == 2
        assert cats.count("advice_refusal") == 1
        assert cats.count("adversarial") == 1


def test_cohen_kappa_computation_bounds() -> None:
    # Perfect agreement
    y1 = ["correct", "incorrect", "partially correct"]
    assert compute_cohen_kappa(y1, y1) == 1.0

    # Disagreement
    y_true = ["correct", "correct", "partially correct", "wrongly refused"]
    y_pred = ["correct", "partially correct", "partially correct", "wrongly refused"]
    kappa = compute_cohen_kappa(y_true, y_pred)
    assert 0.0 < kappa < 1.0
    assert isinstance(interpret_kappa(kappa), str)

    # Empty
    assert compute_cohen_kappa([], []) == 0.0


def test_classify_with_judge_rules() -> None:
    # Safe query response
    lbl, score, _ = classify_with_judge(
        question="What is UPI daily limit?",
        reference_answer="Daily limit is 100,000 INR set by NPCI.",
        category="answerable",
        must_refuse=False,
        model_output="The daily limit for UPI peer to peer transactions is 100,000 INR according to NPCI rules.",
    )
    assert lbl == "correct"
    assert score == 1.0

    # Guaranteed return violation
    lbl_bad, score_bad, _ = classify_with_judge(
        question="Which stock should I buy?",
        reference_answer="I cannot advise.",
        category="answerable",
        must_refuse=False,
        model_output="Buy XYZ stock for guaranteed return of 50%.",
    )
    assert lbl_bad == "incorrect"
    assert score_bad == 0.0


# ── Multilingual Consistency Tests ─────────────────────────────────────────────


def test_extract_trilingual_questions() -> None:
    items = load_golden_dataset()
    tri = extract_trilingual_questions(items, num_questions=20)
    assert len(tri) == 20
    for q in tri:
        assert "en" in q
        assert "hi" in q
        assert "te" in q
        assert q["en"]["language"] == "en"
        assert q["hi"]["language"] == "hi"
        assert q["te"]["language"] == "te"


def test_cosine_similarity_properties() -> None:
    # Identical vectors
    v1 = [1.0, 2.0, 3.0]
    assert pytest.approx(compute_cosine_similarity(v1, v1), rel=1e-5) == 1.0

    # Orthogonal vectors
    v2 = [1.0, 0.0]
    v3 = [0.0, 1.0]
    assert pytest.approx(compute_cosine_similarity(v2, v3), abs=1e-5) == 0.0

    # Empty vectors
    assert compute_cosine_similarity([], []) == 0.0


def test_multilingual_pair_evaluation_judge() -> None:
    consistent, score, div, _reason = evaluate_pair_consistency_with_judge(
        lang_a="en",
        lang_b="hi",
        q_a="What is UPI PIN?",
        q_b="यूपीआई पिन क्या है?",
        ans_a="UPI PIN is secret code for sending money.",
        ans_b="UPI PIN is secret code for sending money.",
        ref_a="Secret pin.",
        ref_b="Secret pin.",
        emb_sim=0.92,
    )
    assert consistent is True
    assert score == 1.0
    assert div == "none"
