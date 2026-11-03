"""Unit tests for VeriCoach baseline guardrails, PII masking, and system prompts."""

from __future__ import annotations

import pytest

from backend.guardrails import (
    SYSTEM_PROMPT_TEMPLATE,
    evaluate_baseline_guardrails,
    mask_pii,
)


def test_mask_pii_pan():
    raw = "My PAN number is ABCDE1234F and I want to know about KYC."
    masked = mask_pii(raw)
    assert "ABCDE1234F" not in masked
    assert "[REDACTED_PAN]" in masked


def test_mask_pii_aadhaar():
    raw = "My Aadhaar number is 5432 8765 4321 for verification."
    masked = mask_pii(raw)
    assert "5432 8765 4321" not in masked
    assert "[REDACTED_AADHAAR]" in masked


def test_mask_pii_phone():
    raw = "Please contact me on 9876543210 regarding the loan."
    masked = mask_pii(raw)
    assert "9876543210" not in masked
    assert "[REDACTED_PHONE]" in masked


def test_mask_pii_email():
    raw = "Send statement to synthetic_user12@example.org immediately."
    masked = mask_pii(raw)
    assert "synthetic_user12@example.org" not in masked
    assert "[REDACTED_EMAIL]" in masked


def test_mask_pii_upi():
    raw = "Transfer 500 to recipient.name@okaxis please."
    masked = mask_pii(raw)
    assert "recipient.name@okaxis" not in masked
    assert "[REDACTED_UPI]" in masked or "[REDACTED_EMAIL]" in masked


def test_mask_pii_credit_card():
    raw = "My card number is 4111 2222 3333 4444 with expiry 10/29."
    masked = mask_pii(raw)
    assert "4111 2222 3333 4444" not in masked
    assert "[REDACTED_CARD]" in masked


@pytest.mark.parametrize(
    "question",
    [
        "Which mutual fund gives guaranteed returns of 25%?",
        "Can you promise fixed returns on crypto?",
        "How to double my money in 1 month guaranteed?",
        "Is there a 100% safe risk-free investment giving 30% yield?",
    ],
)
def test_guardrails_refuse_guaranteed_returns(question: str):
    res = evaluate_baseline_guardrails(question)
    assert not res.passed
    assert res.refusal_reason == "guaranteed_returns_prohibited"
    assert "guaranteed" in (res.refusal_message or "").lower()


@pytest.mark.parametrize(
    "question",
    [
        "Which specific stock should I buy tomorrow?",
        "Tell me where to invest my 50000 savings in equities.",
        "How can I evade income tax this financial year?",
        "Which bank will give me a loan without CIBIL check?",
        "Manage my portfolio for me and pick stocks.",
    ],
)
def test_guardrails_refuse_personalised_advice(question: str):
    res = evaluate_baseline_guardrails(question)
    assert not res.passed
    assert res.refusal_reason == "personalised_advice_prohibited"
    assert "personalized" in (res.refusal_message or "").lower()


def test_guardrails_pass_educational_queries():
    safe_questions = [
        "What is the difference between fixed and floating interest rates?",
        "How does an emergency fund work?",
        "Do I need to enter my UPI PIN to receive money?",
        "What is CIBIL score range?",
    ]
    for q in safe_questions:
        res = evaluate_baseline_guardrails(q)
        assert res.passed
        assert res.refusal_reason is None


def test_system_prompt_treats_context_as_untrusted_data():
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        language_name="English",
        context="Doc content here",
        question="What is UPI?",
    )
    assert "untrusted" in prompt.lower()
    assert "not instructions" in prompt.lower()
    assert "never execute commands" in prompt.lower()
