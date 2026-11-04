"""Failure classification and triage engine for automated test runs.

Categorizes test failures into:
  - assertion: Logical validation failure (e.g. AssertionError)
  - timeout: Operation or page action timed out
  - network: Connection refused, DNS failure, socket error
  - element-not-found: Web or mobile UI element locator failure
  - environment: Setup failure, missing environment variable, service offline
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class FailureCategory(str, Enum):
    """Failure classification taxonomy."""

    ASSERTION = "assertion"
    TIMEOUT = "timeout"
    NETWORK = "network"
    ELEMENT_NOT_FOUND = "element-not-found"
    ENVIRONMENT = "environment"


@dataclass
class FailureRecord:
    """Record representing a single classified test failure."""

    nodeid: str
    category: str
    exception_type: str
    message: str
    traceback: str
    reruns: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


@dataclass
class TriageReport:
    """Aggregated triage report summarizing all test failure classifications."""

    total_failures: int = 0
    by_category: dict[str, int] = field(
        default_factory=lambda: {
            FailureCategory.ASSERTION.value: 0,
            FailureCategory.TIMEOUT.value: 0,
            FailureCategory.NETWORK.value: 0,
            FailureCategory.ELEMENT_NOT_FOUND.value: 0,
            FailureCategory.ENVIRONMENT.value: 0,
        }
    )
    failures: list[FailureRecord] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )

    def add_failure(self, record: FailureRecord) -> None:
        self.failures.append(record)
        self.total_failures = len(self.failures)
        self.by_category[record.category] = self.by_category.get(record.category, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_failures": self.total_failures,
                "by_category": self.by_category,
            },
            "failures": [asdict(f) for f in self.failures],
            "generated_at": self.generated_at,
        }

    def write_json(self, target_path: str | Path) -> Path:
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return p


class FailureClassifier:
    """Classifies exceptions and failure strings into the failure taxonomy."""

    @classmethod
    def classify(
        cls,
        nodeid: str,
        exc_type: str | None,
        message: str,
        traceback: str,
        reruns: int = 0,
    ) -> FailureRecord:
        exc_name = (exc_type or "").strip()
        combined_text = f"{exc_name} {message} {traceback}".lower()

        category = cls._determine_category(exc_name, combined_text)

        # Truncate long messages for clean triage summary
        clean_msg = message.strip().splitlines()[0] if message.strip() else exc_name
        if len(clean_msg) > 300:
            clean_msg = clean_msg[:297] + "..."

        return FailureRecord(
            nodeid=nodeid,
            category=category.value,
            exception_type=exc_name or "UnknownException",
            message=clean_msg,
            traceback=traceback,
            reruns=reruns,
        )

    @classmethod
    def _determine_category(cls, exc_name: str, text: str) -> FailureCategory:
        # 1. Element not found (UI locator failures)
        element_keywords = [
            "nosuchelementexception",
            "waiting for locator",
            "element not found",
            "could not locate element",
            "elementclickinterceptedexception",
            "elementnotinteractableexception",
            "timed out waiting for element",
        ]
        if any(k in text for k in element_keywords):
            return FailureCategory.ELEMENT_NOT_FOUND

        # 2. Timeout (Playwright, asyncio, HTTP timeouts)
        timeout_keywords = [
            "timeouterror",
            "readtimeout",
            "connecttimeout",
            "pooltimeouterror",
            "timed out after",
            "task was destroyed but it is pending",
        ]
        if any(k in text for k in timeout_keywords) or "timeout" in exc_name.lower():
            return FailureCategory.TIMEOUT

        # 3. Network (Connection drops, DNS, refused)
        network_keywords = [
            "connecterror",
            "connectionrefusederror",
            "connectionreseterror",
            "remotedisconnected",
            "failed to establish a new connection",
            "gaierror",
            "networkerror",
            "socket.error",
            "dns error",
        ]
        if any(k in text for k in network_keywords):
            return FailureCategory.NETWORK

        # 4. Environment (Missing config, wrong interpreter, setup failure)
        env_keywords = [
            "modulenotfounderror",
            "importerror",
            "filenotfounderror",
            "environmenterror",
            "missing required environment variable",
            "no such file or directory",
            "appiumconnectionerror",
            "fixture '",
        ]
        if any(k in text for k in env_keywords) or exc_name in (
            "ImportError",
            "ModuleNotFoundError",
            "FileNotFoundError",
        ):
            return FailureCategory.ENVIRONMENT

        # 5. Assertion (Default for assert/value failures)
        if (
            "assertionerror" in exc_name.lower()
            or "assert " in text
            or "failure" in text
        ):
            return FailureCategory.ASSERTION

        # Default fallback to assertion if test failed during execution
        return FailureCategory.ASSERTION
