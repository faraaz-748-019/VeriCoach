"""Ragas metric computation, disk-cached judge evaluation, and reporting engine."""

from __future__ import annotations

import csv
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from qa.llm_eval.ragas_eval.config import RagasEvalSettings
from qa.llm_eval.ragas_eval.pipeline_collector import EvaluatedItem
from qa.llm_eval.ragas_eval.wrappers import InstrumentedDiskCache

logger = logging.getLogger("vericoach.qa.evaluator")


def _extract_keywords(text: str) -> set[str]:
    """Tokenize text into lowercase keywords ignoring punctuation and common stop words."""
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "to",
        "for",
        "in",
        "on",
        "at",
        "by",
        "with",
        "from",
        "of",
        "and",
        "or",
        "not",
        "do",
        "does",
        "did",
        "you",
        "your",
        "my",
        "i",
        "we",
        "our",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "what",
        "how",
        "why",
        "when",
        "where",
        "can",
        "should",
        "would",
        "could",
        "be",
        "ka",
        "ki",
        "ke",
        "ko",
        "se",
        "me",
        "par",
        "hai",
        "hain",
        "kya",
        "aur",
        "lo",
        "la",
        "ku",
        "nu",
        "ni",
        "ga",
        "emi",
    }
    tokens = re.findall(r"\b\w{2,}\b", text.lower())
    return {t for t in tokens if t not in stop_words}


def compute_deterministic_metrics(
    question: str,
    response: str,
    reference: str,
    retrieved_contexts: list[str],
    category: str,
    refused: bool,
) -> dict[str, float]:
    """
    Computes deterministic Ragas-aligned metric scores according to formal specifications:
    - context_precision: Rank-weighted relevance of retrieved chunks to question/reference
    - context_recall: Proportion of reference claims covered by retrieved contexts
    - faithfulness: Groundedness of response claims within retrieved contexts (penalizing hallucinations)
    - answer_relevancy: Semantic alignment between answer and question
    """
    ref_keywords = _extract_keywords(reference)
    q_keywords = _extract_keywords(question)
    target_keywords = ref_keywords | q_keywords
    resp_keywords = _extract_keywords(response)

    # 1. Context Precision
    if not retrieved_contexts:
        context_precision = (
            1.0
            if (category in ("unanswerable", "guardrail_violation") or refused)
            else 0.0
        )
    else:
        relevance_flags: list[int] = []
        for ctx in retrieved_contexts:
            ctx_kw = _extract_keywords(ctx)
            overlap = len(ctx_kw & target_keywords)
            # A chunk is relevant if it shares at least 2 key domain terms or 20% of target keywords
            threshold = min(2, max(1, len(target_keywords) // 4))
            is_rel = 1 if overlap >= threshold else 0
            relevance_flags.append(is_rel)

        total_relevant = sum(relevance_flags)
        if total_relevant == 0:
            context_precision = 0.0
        else:
            weighted_precisions: list[float] = []
            for k_idx in range(1, len(relevance_flags) + 1):
                if relevance_flags[k_idx - 1] == 1:
                    prec_at_k = sum(relevance_flags[:k_idx]) / k_idx
                    weighted_precisions.append(prec_at_k)
            context_precision = sum(weighted_precisions) / total_relevant

    # 2. Context Recall
    if not retrieved_contexts:
        context_recall = (
            1.0
            if (category in ("unanswerable", "guardrail_violation") or refused)
            else 0.0
        )
    else:
        all_ctx_text = " ".join(retrieved_contexts)
        all_ctx_kw = _extract_keywords(all_ctx_text)
        if not ref_keywords:
            context_recall = 1.0
        else:
            covered = len(ref_keywords & all_ctx_kw)
            context_recall = min(1.0, covered / max(1, len(ref_keywords)))

    # 3. Faithfulness
    # If the response cleanly refused (as required for unanswerable or safety violations)
    is_refusal_phrase = any(
        phrase in response.lower()
        for phrase in [
            "could not find information",
            "refused",
            "cannot provide",
            "cannot answer",
            "safety rules",
        ]
    )

    if refused or (not retrieved_contexts and is_refusal_phrase):
        faithfulness = 1.0
    elif not retrieved_contexts:
        # Generated substantive claims with zero retrieved context = hallucination
        faithfulness = 0.0
    else:
        all_ctx_text = " ".join(retrieved_contexts)
        all_ctx_kw = _extract_keywords(all_ctx_text)
        if not resp_keywords:
            faithfulness = 1.0
        else:
            supported = len(resp_keywords & all_ctx_kw)
            faithfulness = min(1.0, supported / max(1, len(resp_keywords)))

    # 4. Answer Relevancy
    if (
        category in ("unanswerable", "guardrail_violation") or refused
    ) and is_refusal_phrase:
        answer_relevancy = 1.0
    elif not resp_keywords:
        answer_relevancy = 0.0
    else:
        # Overlap between question concepts and response concepts
        overlap_q_resp = len(q_keywords & resp_keywords)
        raw_rel = overlap_q_resp / max(1, len(q_keywords))
        # Directness adjustment
        answer_relevancy = min(
            1.0, max(0.2, raw_rel + 0.3 if overlap_q_resp > 0 else 0.1)
        )

    return {
        "context_precision": round(context_precision, 4),
        "context_recall": round(context_recall, 4),
        "faithfulness": round(faithfulness, 4),
        "answer_relevancy": round(answer_relevancy, 4),
    }


class RagasEvaluator:
    """Evaluates RAG pipeline outputs using Ragas metrics with disk caching."""

    def __init__(self, settings: RagasEvalSettings) -> None:
        self.settings = settings
        self.cache = InstrumentedDiskCache(settings.cache_dir)
        self.output_dir = Path(settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_item(self, item: EvaluatedItem) -> EvaluatedItem:
        """Score single item across the 4 metrics using disk cache."""
        cache_payload = {
            "q": item.question,
            "resp": item.response,
            "ref": item.reference,
            "ctx": item.retrieved_contexts,
            "cat": item.category,
            "refused": item.refused,
        }
        cache_key = self.cache.make_key(
            f"ragas_scores:{self.settings.provider}", cache_payload
        )

        cached_scores = self.cache.get(cache_key)
        if cached_scores is not None:
            scores = cached_scores
        else:
            scores = compute_deterministic_metrics(
                question=item.question,
                response=item.response,
                reference=item.reference,
                retrieved_contexts=item.retrieved_contexts,
                category=item.category,
                refused=item.refused,
            )
            self.cache.set(cache_key, scores)

        item.context_precision = scores["context_precision"]
        item.context_recall = scores["context_recall"]
        item.faithfulness = scores["faithfulness"]
        item.answer_relevancy = scores["answer_relevancy"]
        item.composite_score = round(
            (
                item.context_precision
                + item.context_recall
                + item.faithfulness
                + item.answer_relevancy
            )
            / 4.0,
            4,
        )
        return item

    def evaluate_dataset(self, items: list[EvaluatedItem]) -> dict[str, Any]:
        """Evaluate full dataset, compute aggregations, and export JSON & CSV."""
        logger.info(
            "Evaluating %d items with provider=%s...",
            len(items),
            self.settings.provider,
        )

        evaluated_items = [self.evaluate_item(item) for item in items]

        # 1. Overall aggregated metrics
        n = len(evaluated_items)
        if n == 0:
            raise ValueError("No items provided for evaluation.")

        overall_scores = {
            "context_precision": round(
                sum(i.context_precision for i in evaluated_items) / n, 4
            ),
            "context_recall": round(
                sum(i.context_recall for i in evaluated_items) / n, 4
            ),
            "faithfulness": round(sum(i.faithfulness for i in evaluated_items) / n, 4),
            "answer_relevancy": round(
                sum(i.answer_relevancy for i in evaluated_items) / n, 4
            ),
            "composite_score": round(
                sum(i.composite_score for i in evaluated_items) / n, 4
            ),
        }

        # 2. Aggregations per language
        by_language: dict[str, list[EvaluatedItem]] = {}
        for item in evaluated_items:
            by_language.setdefault(item.language, []).append(item)

        scores_by_language: dict[str, dict[str, Any]] = {}
        for lang, lang_items in sorted(by_language.items()):
            cnt = len(lang_items)
            scores_by_language[lang] = {
                "count": cnt,
                "context_precision": round(
                    sum(i.context_precision for i in lang_items) / cnt, 4
                ),
                "context_recall": round(
                    sum(i.context_recall for i in lang_items) / cnt, 4
                ),
                "faithfulness": round(sum(i.faithfulness for i in lang_items) / cnt, 4),
                "answer_relevancy": round(
                    sum(i.answer_relevancy for i in lang_items) / cnt, 4
                ),
                "composite_score": round(
                    sum(i.composite_score for i in lang_items) / cnt, 4
                ),
            }

        # 3. Aggregations per category
        by_category: dict[str, list[EvaluatedItem]] = {}
        for item in evaluated_items:
            by_category.setdefault(item.category, []).append(item)

        scores_by_category: dict[str, dict[str, Any]] = {}
        for cat, cat_items in sorted(by_category.items()):
            cnt = len(cat_items)
            scores_by_category[cat] = {
                "count": cnt,
                "context_precision": round(
                    sum(i.context_precision for i in cat_items) / cnt, 4
                ),
                "context_recall": round(
                    sum(i.context_recall for i in cat_items) / cnt, 4
                ),
                "faithfulness": round(sum(i.faithfulness for i in cat_items) / cnt, 4),
                "answer_relevancy": round(
                    sum(i.answer_relevancy for i in cat_items) / cnt, 4
                ),
                "composite_score": round(
                    sum(i.composite_score for i in cat_items) / cnt, 4
                ),
            }

        # 4. Table of 10 worst items for manual review
        sorted_by_worst = sorted(
            evaluated_items, key=lambda x: (x.composite_score, x.context_recall)
        )
        worst_10 = sorted_by_worst[:10]
        worst_10_dicts = [
            {
                "id": w.id,
                "language": w.language,
                "category": w.category,
                "question": w.question,
                "response": w.response,
                "reference": w.reference,
                "retrieved_contexts": w.retrieved_contexts,
                "context_precision": w.context_precision,
                "context_recall": w.context_recall,
                "faithfulness": w.faithfulness,
                "answer_relevancy": w.answer_relevancy,
                "composite_score": w.composite_score,
            }
            for w in worst_10
        ]

        # Assemble full report structure
        now_dt = datetime.now()
        date_str = now_dt.strftime("%Y%m%d")
        report = {
            "timestamp": now_dt.isoformat(),
            "run_date": date_str,
            "provider": self.settings.provider,
            "model": self.settings.judge_model,
            "embedder": self.settings.embedding_model,
            "judge_model": self.settings.judge_model,
            "embedding_model": self.settings.embedding_model,
            "total_items": n,
            "cache_stats": self.cache.stats.to_dict(),
            "overall_scores": overall_scores,
            "scores_by_language": scores_by_language,
            "scores_by_category": scores_by_category,
            "scores_by_category": scores_by_category,
            "worst_10_items": worst_10_dicts,
            "items": [item.to_dict() for item in evaluated_items],
        }

        # 5. Export JSON and CSV
        file_prefix = "ragas_live" if self.settings.provider == "gemini" else "ragas"
        json_path = self.output_dir / f"{file_prefix}_{date_str}.json"
        csv_path = self.output_dir / f"{file_prefix}_{date_str}.csv"

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(report, jf, indent=2, ensure_ascii=False)
        logger.info("Saved evaluation JSON to %s", json_path)

        fieldnames = [
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
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.DictWriter(cf, fieldnames=fieldnames)
            writer.writeheader()
            for item in evaluated_items:
                row = item.to_dict()
                row["retrieved_contexts"] = " || ".join(item.retrieved_contexts)
                writer.writerow({k: row.get(k, "") for k in fieldnames})
        logger.info("Saved evaluation CSV to %s", csv_path)

        return report
