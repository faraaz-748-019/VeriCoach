"""Faker-based synthetic test data factories producing compliant, non-real Indian PII.

Ensures every name, phone number, PAN, Aadhaar, UPI ID, email, and financial
record is synthetic and safe for testing without external privacy leakage.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Literal

from faker import Faker
from pydantic import BaseModel, Field

# Base Faker instances for Indian localized and fallback data
_faker_in = Faker("en_IN")
_faker_en = Faker("en_US")

# RFC 2606 safe top-level domains for test emails
SAFE_DOMAINS = ["example.com", "example.org", "example.net"]

# Common Indian UPI VPA suffixes
UPI_HANDLES = ["okhdfcbank", "oksbi", "okicici", "okaxis", "paytm", "upi"]

# Financial transaction categories for VeriCoach personal-finance domains
EXPENSE_CATEGORIES = [
    "groceries",
    "rent",
    "electricity_bill",
    "dining",
    "travel",
    "healthcare",
    "shopping",
]
INVESTMENT_CATEGORIES = [
    "sip_mutual_fund",
    "fixed_deposit",
    "gold_etf",
    "nps_contribution",
    "equity_shares",
]
INCOME_CATEGORIES = ["salary", "freelance", "dividend", "interest"]


def synthetic_name(locale: str = "en") -> str:
    """Generate a synthetic Indian or general user name."""
    if locale == "te":
        first_names = [
            "Kavitha",
            "Suresh",
            "Venkatesh",
            "Ananya",
            "Ravi",
            "Bhavani",
            "Kalyan",
        ]
        last_names = ["Reddy", "Rao", "Chowdary", "Varma", "Naidu"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    if locale == "hi":
        first_names = ["Aarav", "Amit", "Priya", "Rahul", "Sneha", "Vikram", "Pooja"]
        last_names = ["Sharma", "Verma", "Gupta", "Singh", "Mishra", "Patel"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    return _faker_in.name()


def synthetic_phone_number() -> str:
    """Generate a synthetic Indian 10-digit mobile number adhering to valid operator prefixes."""
    prefix = random.choice(["98", "97", "99", "88", "87", "70", "79", "63"])
    suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+91{prefix}{suffix}"


def synthetic_pan() -> str:
    """Generate a synthetic 10-character Indian Permanent Account Number (PAN).

    Format: 5 uppercase letters (4th letter 'P' for Individual), 4 digits, 1 letter.
    """
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    prefix = (
        random.choice(letters)
        + random.choice(letters)
        + random.choice(letters)
        + "P"  # Individual
        + random.choice(letters)
    )
    digits = f"{random.randint(1000, 9999):04d}"
    last_letter = random.choice(letters)
    return f"{prefix}{digits}{last_letter}"


def synthetic_aadhaar(masked: bool = False) -> str:
    """Generate a synthetic 12-digit Indian Aadhaar number."""
    part1 = f"{random.randint(2000, 8999):04d}"
    part2 = f"{random.randint(1000, 9999):04d}"
    part3 = f"{random.randint(1000, 9999):04d}"
    if masked:
        return f"XXXX-XXXX-{part3}"
    return f"{part1} {part2} {part3}"


def synthetic_upi_id(name: str | None = None) -> str:
    """Generate a synthetic UPI Virtual Payment Address (VPA)."""
    handle = random.choice(UPI_HANDLES)
    if name:
        clean = "".join(c for c in name.lower() if c.isalnum())
        user_part = f"{clean}{random.randint(10, 99)}"
    else:
        user_part = f"user{random.randint(1000, 9999)}"
    return f"{user_part}@{handle}"


def synthetic_email(name: str | None = None) -> str:
    """Generate an RFC 2606 reserved example domain email."""
    domain = random.choice(SAFE_DOMAINS)
    if name:
        clean = "".join(c for c in name.lower() if c.isalnum())
        user_part = f"{clean}{random.randint(10, 99)}"
    else:
        user_part = f"finance.user.{random.randint(1000, 9999)}"
    return f"{user_part}@{domain}"


def synthetic_ifsc() -> str:
    """Generate a synthetic 11-character Indian Financial System Code (IFSC)."""
    bank_code = random.choice(["HDFC", "SBIN", "ICIC", "UTIB", "KKBK"])
    branch = f"{random.randint(100000, 999999):06d}"
    return f"{bank_code}0{branch}"


def synthetic_account_number() -> str:
    """Generate a synthetic 12-to-16-digit bank account number."""
    length = random.choice([12, 14, 16])
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


# ---------------------------------------------------------------------------
# Pydantic Schemas for Synthetic Entities
# ---------------------------------------------------------------------------


class SyntheticUser(BaseModel):
    """Synthetic customer entity for VeriCoach testing."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    pan: str
    aadhaar: str
    upi_id: str
    locale: Literal["en", "hi", "te"] = "en"
    city: str
    is_synthetic: bool = True


class SyntheticTransaction(BaseModel):
    """Synthetic financial transaction record."""

    id: str = Field(default_factory=lambda: f"txn_{uuid.uuid4().hex[:10]}")
    amount: float
    type: Literal["debit", "credit"]
    category: str
    description: str
    date: str
    upi_ref: str
    currency: str = "INR"


class SyntheticAccount(BaseModel):
    """Synthetic bank or investment account."""

    account_id: str = Field(default_factory=lambda: f"acc_{uuid.uuid4().hex[:8]}")
    bank_name: str
    account_number: str
    ifsc: str
    balance: float
    currency: str = "INR"
    transactions: list[SyntheticTransaction] = Field(default_factory=list)


class SyntheticFinancialProfile(BaseModel):
    """Aggregated financial profile for RAG query and context simulation."""

    user: SyntheticUser
    accounts: list[SyntheticAccount]
    total_savings: float
    monthly_income: float
    monthly_expenses: float
    active_sips: list[dict[str, float | str]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Data Factories
# ---------------------------------------------------------------------------


class UserFactory:
    """Factory creating synthetic users."""

    @classmethod
    def create(
        cls,
        locale: Literal["en", "hi", "te"] = "en",
        masked_aadhaar: bool = True,
        **overrides,
    ) -> SyntheticUser:
        name = overrides.get("name") or synthetic_name(locale=locale)
        city = overrides.get("city") or _faker_in.city()
        data = {
            "name": name,
            "email": synthetic_email(name),
            "phone": synthetic_phone_number(),
            "pan": synthetic_pan(),
            "aadhaar": synthetic_aadhaar(masked=masked_aadhaar),
            "upi_id": synthetic_upi_id(name),
            "locale": locale,
            "city": city,
            "is_synthetic": True,
        }
        data.update(overrides)
        return SyntheticUser(**data)


class TransactionFactory:
    """Factory generating synthetic transaction batches."""

    @classmethod
    def create_batch(
        cls,
        count: int = 5,
        days_back: int = 30,
    ) -> list[SyntheticTransaction]:
        transactions = []
        base_date = datetime.now()
        for _i in range(count):
            tx_type = random.choice(["debit", "debit", "debit", "credit"])
            if tx_type == "credit":
                category = random.choice(INCOME_CATEGORIES)
                amount = round(random.uniform(15000.0, 75000.0), 2)
                desc = f"Direct transfer {category.title()}"
            else:
                is_inv = random.random() < 0.3
                category = (
                    random.choice(INVESTMENT_CATEGORIES)
                    if is_inv
                    else random.choice(EXPENSE_CATEGORIES)
                )
                amount = round(random.uniform(150.0, 8500.0), 2)
                desc = f"Payment for {category.replace('_', ' ').title()}"

            tx_date = (
                base_date - timedelta(days=random.randint(0, days_back))
            ).strftime("%Y-%m-%d")
            transactions.append(
                SyntheticTransaction(
                    amount=amount,
                    type=tx_type,
                    category=category,
                    description=desc,
                    date=tx_date,
                    upi_ref=f"UPI{random.randint(1000000000, 9999999999)}",
                )
            )
        return transactions


class FinancialProfileFactory:
    """Factory generating complete synthetic financial profiles."""

    @classmethod
    def create(
        cls,
        locale: Literal["en", "hi", "te"] = "en",
        monthly_income: float = 65000.0,
    ) -> SyntheticFinancialProfile:
        user = UserFactory.create(locale=locale)
        txns = TransactionFactory.create_batch(count=8)

        total_expenses = sum(t.amount for t in txns if t.type == "debit")
        balance = round(random.uniform(45000.0, 180000.0), 2)

        account = SyntheticAccount(
            bank_name=random.choice(
                ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank"]
            ),
            account_number=synthetic_account_number(),
            ifsc=synthetic_ifsc(),
            balance=balance,
            transactions=txns,
        )

        sips = [
            {"fund_name": "Nifty 50 Index Direct Growth", "amount": 5000.0, "day": 5},
            {"fund_name": "Parag Parikh Flexi Cap Direct", "amount": 3000.0, "day": 10},
        ]

        return SyntheticFinancialProfile(
            user=user,
            accounts=[account],
            total_savings=balance,
            monthly_income=monthly_income,
            monthly_expenses=total_expenses,
            active_sips=sips,
        )
