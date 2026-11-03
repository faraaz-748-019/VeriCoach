"""Tests for PII Compliance and Leakage Prevention."""

from __future__ import annotations

import pytest

from app.data.synthetic import generate_user, generate_users
from qa.evaluators.pii_guard import PIIScanner


def test_synthetic_profiles_have_zero_violations(pii_scanner: PIIScanner) -> None:
    users = generate_users(n=10, locale="en")
    for u in users:
        violations = pii_scanner.validate_synthetic_profile(
            name=u.name,
            email=u.email,
            phone=u.phone,
            pan=u.pan,
            aadhaar=u.aadhaar,
            upi_id=u.upi_id,
        )
        assert violations == [], f"Violations found in user {u.name}: {violations}"


@pytest.mark.parametrize("locale", ["en", "hi", "te"])
def test_multilingual_user_profiles_pass_pii_scan(
    pii_scanner: PIIScanner, locale: str
) -> None:
    user = generate_user(locale=locale, seed=101)
    violations = pii_scanner.validate_synthetic_profile(
        name=user.name,
        email=user.email,
        phone=user.phone,
        pan=user.pan,
        aadhaar=user.aadhaar,
        upi_id=user.upi_id,
    )
    assert violations == []


def test_pii_scanner_catches_invalid_aadhaar_prefix(pii_scanner: PIIScanner) -> None:
    # Aadhaar starting with 0 is invalid
    bad_aadhaar = "012345678901"
    violations = pii_scanner.scan_for_real_aadhaar_violations(
        f"User Aadhaar: {bad_aadhaar}"
    )
    assert len(violations) == 1
    assert violations[0].category == "invalid_aadhaar_prefix"


def test_pii_scanner_detects_credit_card_leak(pii_scanner: PIIScanner) -> None:
    leaked_text = "The user card number is 4111111111111111 with expiry 12/28"
    violations = pii_scanner.scan_for_credit_card_leak(leaked_text)
    assert len(violations) >= 1
    assert violations[0].category == "credit_card_detected"
    assert "******" in violations[0].matched_value
