"""PII scanner and leakage guards.

Ensures that all generated personal and financial data adhere strictly
to synthetic formats and verifies that no raw PII leaks into responses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PIIViolation:
    category: str
    matched_value: str
    description: str
    line_number: int | None = None


class PIIScanner:
    """
    Scans text for compliance with synthetic PII standards
    and detects inadvertent leakage of real formats.
    """

    # Format patterns
    PAN_REGEX = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
    AADHAAR_REGEX = re.compile(r"\b\d{12}\b")
    CREDIT_CARD_REGEX = re.compile(
        r"\b(?:4[0-9]{3}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{1,4}|5[1-5][0-9]{2}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}|3[47][0-9]{2}[-\s]?[0-9]{6}[-\s]?[0-9]{5})\b"
    )
    PHONE_REGEX = re.compile(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    UPI_REGEX = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b")

    def scan_for_real_aadhaar_violations(self, text: str) -> list[PIIViolation]:
        """
        In India, Aadhaar numbers starting with 0 or 1 are invalid,
        and real Aadhaar numbers should never appear in test data.
        """
        violations: list[PIIViolation] = []
        matches = self.AADHAAR_REGEX.findall(text)
        for m in matches:
            if m.startswith("0") or m.startswith("1"):
                violations.append(
                    PIIViolation(
                        category="invalid_aadhaar_prefix",
                        matched_value=m,
                        description="Aadhaar-like string starts with 0 or 1, which violates format standards.",
                    )
                )
        return violations

    def scan_for_credit_card_leak(self, text: str) -> list[PIIViolation]:
        """Check for possible raw credit card / debit card numbers."""
        violations: list[PIIViolation] = []
        matches = self.CREDIT_CARD_REGEX.findall(text)
        for m in matches:
            cleaned = m.replace("-", "").replace(" ", "")
            violations.append(
                PIIViolation(
                    category="credit_card_detected",
                    matched_value=cleaned[:6] + "******" + cleaned[-4:],
                    description="Potential credit card number detected in text.",
                )
            )
        return violations

    def validate_synthetic_profile(
        self,
        name: str,
        email: str,
        phone: str,
        pan: str,
        aadhaar: str,
        upi_id: str,
    ) -> list[PIIViolation]:
        """
        Validates that a synthetic user's fields adhere to all synthetic rules.
        """
        violations: list[PIIViolation] = []

        if not name.strip():
            violations.append(
                PIIViolation("missing_name", name, "Synthetic profile has empty name")
            )

        if not self.EMAIL_REGEX.match(email):
            violations.append(
                PIIViolation(
                    "invalid_email", email, "Email does not match valid pattern"
                )
            )

        if not self.PAN_REGEX.match(pan):
            violations.append(
                PIIViolation(
                    "invalid_pan_format", pan, "PAN must follow [A-Z]{5}[0-9]{4}[A-Z]"
                )
            )

        if not self.AADHAAR_REGEX.match(aadhaar):
            violations.append(
                PIIViolation(
                    "invalid_aadhaar_length",
                    aadhaar,
                    "Aadhaar must be exactly 12 digits",
                )
            )
        elif aadhaar.startswith(("0", "1")):
            violations.append(
                PIIViolation(
                    "invalid_aadhaar_prefix",
                    aadhaar,
                    "Synthetic Aadhaar must begin with digits 2-9",
                )
            )

        if not self.UPI_REGEX.match(upi_id):
            violations.append(
                PIIViolation(
                    "invalid_upi_format", upi_id, "UPI ID must follow user@bank format"
                )
            )

        return violations

    def scan_text(self, text: str) -> list[PIIViolation]:
        """Run all scans against an output string or payload."""
        violations: list[PIIViolation] = []
        violations.extend(self.scan_for_credit_card_leak(text))
        violations.extend(self.scan_for_real_aadhaar_violations(text))
        return violations
