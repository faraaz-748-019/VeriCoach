"""Evaluation runner and per-language aggregator for DeepEval test suite."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import BackendSettings, LLMProviderType
from backend.main import chat_v1
from backend.providers import create_llm_provider
from backend.rag.store import ChromaRAGStore
from backend.schemas import ChatRequestV1
from deepeval.test_case import LLMTestCase
from starlette.requests import Request

from qa.llm_eval.deepeval_tests.gates import GateEvaluationResult, QualityGatesConfig
from qa.llm_eval.deepeval_tests.judge import create_deepeval_judge
from qa.llm_eval.deepeval_tests.metrics import (
    create_language_match_metric,
    create_refusal_correctness_metric,
    create_safe_tone_metric,
    create_standard_rag_metrics,
    verify_no_guaranteed_return_phrases,
    verify_sourced_doc_ids_exist,
)

logger = logging.getLogger("vericoach.qa.deepeval_runner")


@dataclass
class DeepEvalItemResult:
    """Individual item evaluation result."""

    id: str
    language: str
    category: str
    question: str
    actual_output: str
    expected_output: str
    retrieval_context: list[str]
    sources: list[dict[str, Any]]
    must_refuse: bool
    refused: bool

    # Metric scores
    faithfulness: float
    hallucination: float
    answer_relevancy: float
    contextual_precision: float
    contextual_recall: float
    refusal_correctness: float
    language_match: float
    safe_tone: float

    # Deterministic checks
    sourced_doc_ids_exist: bool
    missing_doc_ids: list[str]
    no_guaranteed_returns: bool
    guaranteed_return_violations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_dataset_items(
    golden_path: Path | str = "qa/data/golden/golden_v1.jsonl",
    subset: int | None = None,
    languages: tuple[str, ...] = ("en", "hi", "te"),
) -> list[dict[str, Any]]:
    """Load items from golden dataset, optionally balanced per language for subset runs."""
    path = Path(golden_path)
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {path}")

    all_items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                all_items.append(json.loads(line_str))

    by_lang: dict[str, list[dict[str, Any]]] = {lang: [] for lang in languages}
    for item in all_items:
        lang = item.get("language", "")
        if lang in by_lang:
            by_lang[lang].append(item)

    if subset is None or subset >= len(all_items):
        # Return full balanced list
        selected: list[dict[str, Any]] = []
        for lang in languages:
            selected.extend(by_lang[lang])
        return selected

    # Balanced subset allocation across languages
    per_lang = max(1, subset // len(languages))
    selected_subset: list[dict[str, Any]] = []
    for lang in languages:
        selected_subset.extend(by_lang[lang][:per_lang])

    # Fill remainder if subset not divisible by language count
    remainder = subset - len(selected_subset)
    if remainder > 0:
        for lang in languages:
            for item in by_lang[lang][per_lang:]:
                if remainder <= 0:
                    break
                selected_subset.append(item)
                remainder -= 1

    return selected_subset


class DeepEvalRunner:
    """Orchestrates DeepEval execution, per-language aggregation, and report generation."""

    def __init__(
        self,
        provider: str | None = None,
        gates_path: Path | str | None = None,
        golden_path: Path | str = "qa/data/golden/golden_v1.jsonl",
        output_dir: Path | str = "results",
    ) -> None:
        self.provider = (
            provider
            or os.environ.get("EVAL_PROVIDER")
            or os.environ.get("LLM_PROVIDER")
            or "mock"
        ).lower()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.golden_path = Path(golden_path)
        self.gates_config = QualityGatesConfig.load(gates_path)
        self.judge = create_deepeval_judge(provider=self.provider)

        # Setup RAG pipeline components
        self._init_backend_pipeline()

    def _init_backend_pipeline(self) -> None:
        """Initialize the VeriCoach backend pipeline."""
        target_provider_type = (
            LLMProviderType.gemini
            if self.provider == "gemini" and os.environ.get("GOOGLE_API_KEY", "")
            else LLMProviderType.mock
        )
        self.backend_settings = BackendSettings(
            llm_provider=target_provider_type,
            require_api_key=False,
        )
        self.llm_provider = create_llm_provider(self.backend_settings)
        self.rag_store = ChromaRAGStore(
            provider=self.llm_provider,
            persist_dir="",
            top_k=self.backend_settings.rag_top_k,
        )
        self.rag_store.bootstrap_default_corpus()

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat",
            "headers": [(b"content-type", b"application/json")],
        }
        self.dummy_request = Request(scope)

    def execute_rag(self, question: str, locale: str) -> dict[str, Any]:
        """Execute chat_v1 and return response, retrieved contexts, and sources."""
        target_lang = locale if locale in ("en", "hi", "te") else "auto"
        chat_req = ChatRequestV1(question=question, language=target_lang)  # type: ignore[arg-type]
        chat_res = chat_v1(
            request_data=chat_req,
            request=self.dummy_request,
            settings=self.backend_settings,
            store=self.rag_store,
        )

        # Collect text of retrieved documents
        retrieved_texts: list[str] = []
        sources_list: list[dict[str, Any]] = []
        for src in chat_res.sources:
            sources_list.append({"doc_id": src.doc_id, "title": src.title})
            if hasattr(src, "snippet") and src.snippet:
                retrieved_texts.append(src.snippet)
            else:
                retrieved_texts.append(f"Document {src.doc_id}: {src.title}")

        if not retrieved_texts:
            retrieved_texts = ["No relevant documents found in knowledge base."]

        return {
            "response": chat_res.answer,
            "refused": chat_res.refused,
            "retrieved_contexts": retrieved_texts,
            "sources": sources_list,
        }

    def evaluate(self, subset: int | None = None) -> dict[str, Any]:
        """Run evaluation suite across all items and compile per-language and global reports."""
        items = load_dataset_items(self.golden_path, subset=subset)
        logger.info(
            "Starting DeepEval evaluation on %d items using provider '%s'...",
            len(items),
            self.provider,
        )

        # Build metric instances
        std_metrics = create_standard_rag_metrics(
            model=self.judge,
            thresholds={
                "faithfulness": self.gates_config.faithfulness,
                "hallucination": self.gates_config.hallucination,
                "answer_relevancy": self.gates_config.answer_relevancy,
                "contextual_precision": self.gates_config.contextual_precision,
                "contextual_recall": self.gates_config.contextual_recall,
            },
        )
        geval_refusal = create_refusal_correctness_metric(
            model=self.judge, threshold=self.gates_config.refusal_correctness
        )
        geval_lang = create_language_match_metric(
            model=self.judge, threshold=self.gates_config.language_match
        )
        geval_safe = create_safe_tone_metric(
            model=self.judge, threshold=self.gates_config.safe_tone
        )

        item_results: list[DeepEvalItemResult] = []
        all_missing_doc_ids: list[str] = []
        all_guarantee_violations: list[str] = []

        for item in items:
            q = item["question"]
            lang = item["language"]
            ref_ans = item.get("reference_answer", "")
            must_refuse = item.get("must_refuse", False)
            cat = item.get("category", "")

            # Execute RAG
            rag_output = self.execute_rag(q, lang)
            actual_resp = rag_output["response"]
            refused = rag_output["refused"]
            retrieval_ctx = rag_output["retrieved_contexts"]
            sources = rag_output["sources"]

            # Deterministic Checks
            doc_pass, missing_docs = verify_sourced_doc_ids_exist(sources)
            if not doc_pass:
                all_missing_doc_ids.extend(missing_docs)

            guar_pass, guar_violations = verify_no_guaranteed_return_phrases(
                actual_resp
            )
            if not guar_pass:
                all_guarantee_violations.extend(guar_violations)

            # DeepEval LLMTestCase
            test_case = LLMTestCase(
                input=q,
                actual_output=actual_resp,
                expected_output=ref_ans,
                context=retrieval_ctx,
                retrieval_context=retrieval_ctx,
            )

            # Measure Standard Metrics
            std_metrics["faithfulness"].measure(test_case)
            faith_score = float(std_metrics["faithfulness"].score)

            std_metrics["hallucination"].measure(test_case)
            halluc_score = float(std_metrics["hallucination"].score)

            std_metrics["answer_relevancy"].measure(test_case)
            relevancy_score = float(std_metrics["answer_relevancy"].score)

            std_metrics["contextual_precision"].measure(test_case)
            precision_score = float(std_metrics["contextual_precision"].score)

            std_metrics["contextual_recall"].measure(test_case)
            recall_score = float(std_metrics["contextual_recall"].score)

            # Measure Custom GEval Metrics
            geval_refusal.measure(test_case)
            refusal_score = float(geval_refusal.score)

            geval_lang.measure(test_case)
            lang_score = float(geval_lang.score)

            geval_safe.measure(test_case)
            safe_score = float(geval_safe.score)

            item_results.append(
                DeepEvalItemResult(
                    id=item["id"],
                    language=lang,
                    category=cat,
                    question=q,
                    actual_output=actual_resp,
                    expected_output=ref_ans,
                    retrieval_context=retrieval_ctx,
                    sources=sources,
                    must_refuse=must_refuse,
                    refused=refused,
                    faithfulness=faith_score,
                    hallucination=halluc_score,
                    answer_relevancy=relevancy_score,
                    contextual_precision=precision_score,
                    contextual_recall=recall_score,
                    refusal_correctness=refusal_score,
                    language_match=lang_score,
                    safe_tone=safe_score,
                    sourced_doc_ids_exist=doc_pass,
                    missing_doc_ids=missing_docs,
                    no_guaranteed_returns=guar_pass,
                    guaranteed_return_violations=guar_violations,
                )
            )

        # ── Per-Language Aggregation ──────────────────────────────────────────
        languages = sorted({it.language for it in item_results})
        per_language_stats: dict[str, dict[str, float]] = {}

        for lang in languages:
            lang_items = [it for it in item_results if it.language == lang]
            total_lang = len(lang_items)
            if total_lang == 0:
                continue

            # Hallucination Rate: proportion of items where hallucination was detected (< 0.70 score)
            hallucinated_count = sum(1 for it in lang_items if it.hallucination < 0.70)
            h_rate = hallucinated_count / total_lang

            # Refusal Precision & Recall
            # TP: must_refuse=True and refused=True
            # FP: must_refuse=False and refused=True (over-refusal)
            # FN: must_refuse=True and refused=False (under-refusal)
            # TN: must_refuse=False and refused=False
            tp = sum(1 for it in lang_items if it.must_refuse and it.refused)
            fp = sum(1 for it in lang_items if (not it.must_refuse) and it.refused)
            fn = sum(1 for it in lang_items if it.must_refuse and (not it.refused))
            tn = sum(
                1 for it in lang_items if (not it.must_refuse) and (not it.refused)
            )

            refusal_precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
            refusal_recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0

            per_language_stats[lang] = {
                "count": float(total_lang),
                "hallucination_rate": round(h_rate, 4),
                "refusal_precision": round(refusal_precision, 4),
                "refusal_recall": round(refusal_recall, 4),
                "tp_refusals": float(tp),
                "fp_refusals": float(fp),
                "fn_refusals": float(fn),
                "tn_refusals": float(tn),
                "avg_faithfulness": round(
                    sum(it.faithfulness for it in lang_items) / total_lang, 4
                ),
                "avg_hallucination": round(
                    sum(it.hallucination for it in lang_items) / total_lang, 4
                ),
                "avg_answer_relevancy": round(
                    sum(it.answer_relevancy for it in lang_items) / total_lang, 4
                ),
                "avg_contextual_precision": round(
                    sum(it.contextual_precision for it in lang_items) / total_lang, 4
                ),
                "avg_contextual_recall": round(
                    sum(it.contextual_recall for it in lang_items) / total_lang, 4
                ),
                "avg_refusal_correctness": round(
                    sum(it.refusal_correctness for it in lang_items) / total_lang, 4
                ),
                "avg_language_match": round(
                    sum(it.language_match for it in lang_items) / total_lang, 4
                ),
                "avg_safe_tone": round(
                    sum(it.safe_tone for it in lang_items) / total_lang, 4
                ),
            }

        # ── Global Aggregation ────────────────────────────────────────────────
        n_items = len(item_results)
        summary_scores = {
            "faithfulness": round(
                sum(it.faithfulness for it in item_results) / n_items, 4
            ),
            "hallucination": round(
                sum(it.hallucination for it in item_results) / n_items, 4
            ),
            "hallucination_rate": round(
                sum(1 for it in item_results if it.hallucination < 0.70) / n_items, 4
            ),
            "answer_relevancy": round(
                sum(it.answer_relevancy for it in item_results) / n_items, 4
            ),
            "contextual_precision": round(
                sum(it.contextual_precision for it in item_results) / n_items, 4
            ),
            "contextual_recall": round(
                sum(it.contextual_recall for it in item_results) / n_items, 4
            ),
            "refusal_correctness": round(
                sum(it.refusal_correctness for it in item_results) / n_items, 4
            ),
            "language_match": round(
                sum(it.language_match for it in item_results) / n_items, 4
            ),
            "safe_tone": round(sum(it.safe_tone for it in item_results) / n_items, 4),
        }

        # Global Refusal Precision / Recall
        global_tp = sum(1 for it in item_results if it.must_refuse and it.refused)
        global_fp = sum(1 for it in item_results if (not it.must_refuse) and it.refused)
        global_fn = sum(1 for it in item_results if it.must_refuse and (not it.refused))
        summary_scores["refusal_precision"] = round(
            (global_tp / (global_tp + global_fp))
            if (global_tp + global_fp) > 0
            else 1.0,
            4,
        )
        summary_scores["refusal_recall"] = round(
            (global_tp / (global_tp + global_fn))
            if (global_tp + global_fn) > 0
            else 1.0,
            4,
        )

        deterministic_results = {
            "all_doc_ids_exist": len(all_missing_doc_ids) == 0,
            "missing_doc_ids": sorted(set(all_missing_doc_ids)),
            "no_guaranteed_return_violations": len(all_guarantee_violations) == 0,
            "guaranteed_return_snippets": sorted(set(all_guarantee_violations)),
        }

        # ── Gates Evaluation ──────────────────────────────────────────────────
        gate_results: list[GateEvaluationResult] = self.gates_config.evaluate(
            summary_scores=summary_scores,
            per_language_stats=per_language_stats,
            deterministic_results=deterministic_results,
        )
        all_gates_passed = all(gr.passed for gr in gate_results)

        # ── Construct & Write Artifact results/deepeval_YYYYMMDD.json ─────────
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        timestamp_str = now.isoformat()
        prefix = "deepeval_live" if self.provider == "gemini" else "deepeval"
        output_filename = f"{prefix}_{date_str}.json"
        artifact_path = self.output_dir / output_filename

        report_data = {
            "evaluation_metadata": {
                "timestamp": timestamp_str,
                "provider": self.provider,
                "model": os.environ.get("GEMINI_MODEL", "mock") if self.provider == "gemini" else "mock",
                "embedder": os.environ.get("GEMINI_EMBEDDING_MODEL", "mock") if self.provider == "gemini" else "mock",
                "judge_model": self.judge.get_model_name(),
                "total_items_evaluated": n_items,
                "subset_requested": subset,
                "all_gates_passed": all_gates_passed,
            },
            "summary_metrics": summary_scores,
            "deterministic_checks": deterministic_results,
            "per_language_breakdown": per_language_stats,
            "gates_evaluation": [gr.to_dict() for gr in gate_results],
            "item_results": [it.to_dict() for it in item_results],
        }

        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(
            "DeepEval evaluation completed. Artifact written to %s (All gates passed: %s)",
            artifact_path.resolve(),
            all_gates_passed,
        )

        return {
            "artifact_path": str(artifact_path),
            "all_gates_passed": all_gates_passed,
            "summary": summary_scores,
            "per_language": per_language_stats,
            "deterministic": deterministic_results,
            "gates": [gr.to_dict() for gr in gate_results],
        }
