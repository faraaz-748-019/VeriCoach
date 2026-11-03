"""Synthetic PII data generator using Faker.

All generated values are FAKE and must never be used in production.
No real personal data is stored or returned.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field

from faker import Faker

_faker_en = Faker("en_IN")
_faker_hi = Faker("hi_IN")

Faker.seed(42)  # reproducible in tests


@dataclass
class SyntheticUser:
    """A fully synthetic user profile. All fields are fake."""

    name: str
    email: str
    phone: str
    pan: str  # fake PAN (India tax ID format: AAAAA1234A)
    aadhaar: str  # fake 12-digit Aadhaar-style number
    upi_id: str  # fake UPI ID
    locale: str = "en"
    monthly_income: float = 0.0
    accounts: list[dict[str, object]] = field(default_factory=list)


def _fake_pan() -> str:
    """Generate a fake PAN-style string (AAAAA1234A). NOT a real PAN."""
    letters = string.ascii_uppercase
    return (
        "".join(random.choices(letters, k=5))
        + "".join(random.choices(string.digits, k=4))
        + random.choice(letters)
    )


def _fake_aadhaar() -> str:
    """Generate a fake 12-digit Aadhaar-style number. NOT a real Aadhaar."""
    # First digit must not be 0 or 1
    first = str(random.randint(2, 9))
    rest = "".join(random.choices(string.digits, k=11))
    return first + rest


def generate_user(locale: str = "en", seed: int | None = None) -> SyntheticUser:
    """Return a single synthetic user for the given locale."""
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)

    faker = _faker_hi if locale == "hi" else _faker_en
    name: str = faker.name()
    email: str = faker.email()
    phone: str = faker.phone_number()
    upi_id = f"{faker.user_name()}@okicici"

    income = round(random.uniform(20_000, 200_000), 2)

    accounts = [
        {
            "bank": faker.company(),
            "account_number": faker.bban(),
            "balance": round(random.uniform(1_000, 500_000), 2),
            "type": random.choice(["savings", "current"]),
        }
    ]

    return SyntheticUser(
        name=name,
        email=email,
        phone=phone,
        pan=_fake_pan(),
        aadhaar=_fake_aadhaar(),
        upi_id=upi_id,
        locale=locale,
        monthly_income=income,
        accounts=accounts,
    )


def generate_users(n: int = 5, locale: str = "en") -> list[SyntheticUser]:
    """Return *n* synthetic users."""
    return [generate_user(locale=locale) for _ in range(n)]


def generate_finance_document(user: SyntheticUser) -> str:
    """Generate a short synthetic finance narrative for RAG indexing."""
    return (
        f"Customer: {user.name}\n"
        f"Monthly income: ₹{user.monthly_income:,.2f}\n"
        f"Bank: {user.accounts[0]['bank']}\n"
        f"Balance: ₹{user.accounts[0]['balance']:,.2f}\n"
        f"Account type: {user.accounts[0]['type']}\n"
        f"UPI: {user.upi_id}\n"
        "Advice: Maintain an emergency fund of 3-6 months' expenses. "
        "Invest in diversified mutual funds via SIP. "
        "Review insurance coverage annually."
    )
