"""DeepEval evaluation test suite for VeriCoach."""

from qa.llm_eval.deepeval_tests.judge import (
    DeepEvalGeminiJudge,
    DeepEvalMockJudge,
    DeepEvalOllamaJudge,
    create_deepeval_judge,
)
from qa.llm_eval.deepeval_tests.metrics import (
    create_language_match_metric,
    create_refusal_correctness_metric,
    create_safe_tone_metric,
    verify_no_guaranteed_return_phrases,
    verify_sourced_doc_ids_exist,
)

__all__ = [
    "DeepEvalGeminiJudge",
    "DeepEvalMockJudge",
    "DeepEvalOllamaJudge",
    "create_deepeval_judge",
    "create_language_match_metric",
    "create_refusal_correctness_metric",
    "create_safe_tone_metric",
    "verify_no_guaranteed_return_phrases",
    "verify_sourced_doc_ids_exist",
]
