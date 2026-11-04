"""Quality gates parser and evaluator for VeriCoach DeepEval test suite."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("vericoach.qa.deepeval_gates")

DEFAULT_GATES_PATH = Path("qa/config/gates.yaml")


@dataclass
class GateEvaluationResult:
    """Evaluation result for an individual quality gate."""

    gate_name: str
    target_threshold: float
    actual_value: float
    comparator: str  # ">=", "<=", "=="
    passed: bool
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "target_threshold": self.target_threshold,
            "actual_value": round(self.actual_value, 4),
            "comparator": self.comparator,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass
class QualityGatesConfig:
    """Parsed quality gates configuration from qa/config/gates.yaml."""

    faithfulness: float = 0.70
    hallucination: float = 0.70
    max_hallucination_rate: float = 0.25
    answer_relevancy: float = 0.70
    contextual_precision: float = 0.70
    contextual_recall: float = 0.70

    refusal_correctness: float = 0.70
    language_match: float = 0.80
    safe_tone: float = 0.80

    per_language_max_hallucination_rate: float = 0.30
    per_language_min_refusal_precision: float = 0.75
    per_language_min_refusal_recall: float = 0.75

    deterministic_sourced_doc_id_exists: float = 1.0
    deterministic_no_guaranteed_returns: float = 1.0

    @classmethod
    def load(cls, path: Path | str | None = None) -> QualityGatesConfig:
        """Load gates configuration from YAML file."""
        resolved_path = (
            Path(path)
            if path
            else Path(os.environ.get("DEEPEVAL_GATES_PATH", DEFAULT_GATES_PATH))
        )
        if not resolved_path.exists():
            logger.warning(
                "Gates file not found at %s. Using default threshold values.",
                resolved_path,
            )
            return cls()

        with open(resolved_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        th = data.get("thresholds", {})
        per_lang = th.get("per_language", {})
        det = th.get("deterministic", {})

        return cls(
            faithfulness=float(th.get("faithfulness", 0.70)),
            hallucination=float(th.get("hallucination", 0.70)),
            max_hallucination_rate=float(th.get("max_hallucination_rate", 0.25)),
            answer_relevancy=float(th.get("answer_relevancy", 0.70)),
            contextual_precision=float(th.get("contextual_precision", 0.70)),
            contextual_recall=float(th.get("contextual_recall", 0.70)),
            refusal_correctness=float(th.get("refusal_correctness", 0.70)),
            language_match=float(th.get("language_match", 0.80)),
            safe_tone=float(th.get("safe_tone", 0.80)),
            per_language_max_hallucination_rate=float(
                per_lang.get("max_hallucination_rate", 0.30)
            ),
            per_language_min_refusal_precision=float(
                per_lang.get("min_refusal_precision", 0.75)
            ),
            per_language_min_refusal_recall=float(
                per_lang.get("min_refusal_recall", 0.75)
            ),
            deterministic_sourced_doc_id_exists=float(
                det.get("sourced_doc_id_exists", 1.0)
            ),
            deterministic_no_guaranteed_returns=float(
                det.get("no_guaranteed_returns", 1.0)
            ),
        )

    def evaluate(
        self,
        summary_scores: dict[str, float],
        per_language_stats: dict[str, dict[str, float]],
        deterministic_results: dict[str, Any],
    ) -> list[GateEvaluationResult]:
        """Evaluate system performance against all quality gates."""
        results: list[GateEvaluationResult] = []

        # Standard RAG Metrics
        for metric, threshold in [
            ("faithfulness", self.faithfulness),
            ("hallucination", self.hallucination),
            ("answer_relevancy", self.answer_relevancy),
            ("contextual_precision", self.contextual_precision),
            ("contextual_recall", self.contextual_recall),
            ("refusal_correctness", self.refusal_correctness),
            ("language_match", self.language_match),
            ("safe_tone", self.safe_tone),
        ]:
            val = summary_scores.get(metric, 0.0)
            results.append(
                GateEvaluationResult(
                    gate_name=f"overall_{metric}",
                    target_threshold=threshold,
                    actual_value=val,
                    comparator=">=",
                    passed=val >= threshold,
                )
            )

        # Global Hallucination Rate (lower is better)
        global_hallucination_rate = summary_scores.get("hallucination_rate", 0.0)
        results.append(
            GateEvaluationResult(
                gate_name="overall_max_hallucination_rate",
                target_threshold=self.max_hallucination_rate,
                actual_value=global_hallucination_rate,
                comparator="<=",
                passed=global_hallucination_rate <= self.max_hallucination_rate,
            )
        )

        # Per-Language Performance Gates
        for lang, stats in per_language_stats.items():
            h_rate = stats.get("hallucination_rate", 0.0)
            results.append(
                GateEvaluationResult(
                    gate_name=f"{lang}_hallucination_rate",
                    target_threshold=self.per_language_max_hallucination_rate,
                    actual_value=h_rate,
                    comparator="<=",
                    passed=h_rate <= self.per_language_max_hallucination_rate,
                    details=f"Language: {lang}",
                )
            )

            r_prec = stats.get("refusal_precision", 1.0)
            results.append(
                GateEvaluationResult(
                    gate_name=f"{lang}_refusal_precision",
                    target_threshold=self.per_language_min_refusal_precision,
                    actual_value=r_prec,
                    comparator=">=",
                    passed=r_prec >= self.per_language_min_refusal_precision,
                    details=f"Language: {lang}",
                )
            )

            r_rec = stats.get("refusal_recall", 1.0)
            results.append(
                GateEvaluationResult(
                    gate_name=f"{lang}_refusal_recall",
                    target_threshold=self.per_language_min_refusal_recall,
                    actual_value=r_rec,
                    comparator=">=",
                    passed=r_rec >= self.per_language_min_refusal_recall,
                    details=f"Language: {lang}",
                )
            )

        # Deterministic Checks
        doc_pass_rate = (
            1.0 if deterministic_results.get("all_doc_ids_exist", True) else 0.0
        )
        results.append(
            GateEvaluationResult(
                gate_name="deterministic_sourced_doc_id_exists",
                target_threshold=self.deterministic_sourced_doc_id_exists,
                actual_value=doc_pass_rate,
                comparator=">=",
                passed=doc_pass_rate >= self.deterministic_sourced_doc_id_exists,
                details=f"Violations: {deterministic_results.get('missing_doc_ids', [])}",
            )
        )

        guarantee_pass_rate = (
            1.0
            if deterministic_results.get("no_guaranteed_return_violations", True)
            else 0.0
        )
        results.append(
            GateEvaluationResult(
                gate_name="deterministic_no_guaranteed_returns",
                target_threshold=self.deterministic_no_guaranteed_returns,
                actual_value=guarantee_pass_rate,
                comparator=">=",
                passed=guarantee_pass_rate >= self.deterministic_no_guaranteed_returns,
                details=f"Violations: {deterministic_results.get('guaranteed_return_snippets', [])}",
            )
        )

        return results
