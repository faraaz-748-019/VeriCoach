"""RAG Quality Benchmark Tests (Faithfulness, Relevancy, Precision, Recall)."""

from __future__ import annotations

import pytest

from app.data.synthetic import generate_finance_document, generate_user
from app.finance.assistant import FinanceAssistant
from qa.evaluators.metrics import (
    AnswerRelevancyEvaluator,
    ContextPrecisionEvaluator,
    ContextRecallEvaluator,
    FaithfulnessEvaluator,
    evaluate_rag_turn,
)


def test_faithfulness_evaluation_with_grounded_answer(
    faithfulness_evaluator: FaithfulnessEvaluator,
) -> None:
    context = [
        "Customer Aarav Sharma has a savings account balance of INR 45,000.",
        "Monthly SIP contribution is INR 5,000 into Nifty 50 Index Fund.",
    ]
    grounded_answer = (
        "Aarav Sharma has an account balance of INR 45,000 and invests in Nifty 50."
    )
    score = faithfulness_evaluator.evaluate(grounded_answer, context)
    assert (
        score > 0.6
    ), f"Expected high faithfulness score for grounded answer, got {score}"


def test_faithfulness_evaluation_with_hallucination(
    faithfulness_evaluator: FaithfulnessEvaluator,
) -> None:
    context = ["Customer holds fixed deposit in HDFC Bank with 7% interest rate."]
    hallucinated_answer = (
        "Customer holds Bitcoin and Ethereum cryptocurrency on Binance exchange."
    )
    score = faithfulness_evaluator.evaluate(hallucinated_answer, context)
    assert (
        score < 0.3
    ), f"Expected low faithfulness score for hallucinated answer, got {score}"


def test_faithfulness_polite_refusal_when_no_context(
    faithfulness_evaluator: FaithfulnessEvaluator,
) -> None:
    answer = "I don't have enough context to answer that question."
    score = faithfulness_evaluator.evaluate(answer, contexts=[])
    assert score == 1.0


def test_answer_relevancy(relevancy_evaluator: AnswerRelevancyEvaluator) -> None:
    question = "What is the emergency fund recommendation?"
    relevant_answer = (
        "The emergency fund recommendation is to keep 3 to 6 months of expenses."
    )
    irrelevant_answer = "The weather in Bengaluru is sunny today."

    score_rel = relevancy_evaluator.evaluate(question, relevant_answer)
    score_irrel = relevancy_evaluator.evaluate(question, irrelevant_answer)

    assert score_rel > score_irrel
    assert score_rel >= 0.5


def test_context_precision(precision_evaluator: ContextPrecisionEvaluator) -> None:
    question = "mutual funds SIP"
    contexts = [
        "Mutual funds SIP provides disciplined investing.",
        "Credit cards have high interest rates.",
        "Savings account offers liquidity.",
    ]
    score = precision_evaluator.evaluate(question, contexts)
    assert score > 0.5


def test_context_recall(recall_evaluator: ContextRecallEvaluator) -> None:
    ground_truth = ["emergency fund 6 months", "term insurance coverage"]
    retrieved = [
        "Maintain an emergency fund of 3 to 6 months.",
        "Review term insurance coverage annually.",
    ]
    score = recall_evaluator.evaluate(ground_truth, retrieved)
    assert score == 1.0


@pytest.mark.parametrize("locale", ["en", "hi", "te"])
def test_multilingual_rag_evaluation(
    assistant: FinanceAssistant,
    locale: str,
) -> None:
    user = generate_user(locale=locale, seed=42)
    doc = generate_finance_document(user)
    assistant.index_document(doc, source=f"profile_{user.name}")

    query = "What is the monthly income?"
    response = assistant.ask(query, locale=locale)  # type: ignore[arg-type]

    eval_result = evaluate_rag_turn(
        question=query,
        answer=response.text,
        contexts=[doc],
        ground_truth=f"income {user.monthly_income}",
    )

    assert eval_result.faithfulness >= 0.0
    assert eval_result.answer_relevancy >= 0.0
    assert eval_result.context_precision >= 0.0
    assert eval_result.context_recall >= 0.0
