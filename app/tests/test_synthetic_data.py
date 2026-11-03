"""Tests for synthetic data generation - verifies Faker-only PII."""

from __future__ import annotations

import re

from app.data.synthetic import (
    SyntheticUser,
    _fake_aadhaar,
    _fake_pan,
    generate_finance_document,
    generate_user,
    generate_users,
)

PAN_PATTERN = re.compile(r"^[A-Z]{5}\d{4}[A-Z]$")
AADHAAR_PATTERN = re.compile(r"^[2-9]\d{11}$")


class TestFakePAN:
    def test_format(self) -> None:
        for _ in range(20):
            pan = _fake_pan()
            assert PAN_PATTERN.match(pan), f"Invalid PAN format: {pan}"

    def test_uniqueness(self) -> None:
        pans = {_fake_pan() for _ in range(50)}
        # With 26^5 * 10^4 * 26 possibilities, collisions should be near-zero
        assert len(pans) > 40


class TestFakeAadhaar:
    def test_format(self) -> None:
        for _ in range(20):
            aadhaar = _fake_aadhaar()
            assert AADHAAR_PATTERN.match(aadhaar), f"Invalid Aadhaar format: {aadhaar}"
            assert len(aadhaar) == 12

    def test_first_digit_not_0_or_1(self) -> None:
        for _ in range(30):
            aadhaar = _fake_aadhaar()
            assert aadhaar[0] not in ("0", "1")


class TestGenerateUser:
    def test_returns_synthetic_user(self) -> None:
        user = generate_user()
        assert isinstance(user, SyntheticUser)

    def test_all_fields_populated(self) -> None:
        user = generate_user(seed=0)
        assert user.name
        assert "@" in user.email
        assert user.phone
        assert PAN_PATTERN.match(user.pan)
        assert AADHAAR_PATTERN.match(user.aadhaar)
        assert "@" in user.upi_id
        assert user.monthly_income > 0
        assert len(user.accounts) > 0

    def test_locale_hi(self) -> None:
        user = generate_user(locale="hi", seed=1)
        assert user.locale == "hi"

    def test_seed_reproducible(self) -> None:
        u1 = generate_user(seed=42)
        u2 = generate_user(seed=42)
        assert u1.name == u2.name
        assert u1.email == u2.email


class TestGenerateUsers:
    def test_returns_correct_count(self) -> None:
        users = generate_users(n=7)
        assert len(users) == 7

    def test_all_are_synthetic_user(self) -> None:
        for user in generate_users(n=3):
            assert isinstance(user, SyntheticUser)


class TestGenerateFinanceDocument:
    def test_contains_user_name(self) -> None:
        user = generate_user(seed=99)
        doc = generate_finance_document(user)
        assert user.name in doc

    def test_contains_financial_advice(self) -> None:
        user = generate_user(seed=10)
        doc = generate_finance_document(user)
        assert "emergency fund" in doc.lower() or "sip" in doc.lower()
