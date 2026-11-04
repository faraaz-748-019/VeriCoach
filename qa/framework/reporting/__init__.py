"""Reporting and failure triage package for VeriCoach QA Framework."""

from qa.framework.reporting.allure_helper import (
    attach_api_request,
    attach_api_response,
    attach_json,
    attach_playwright_trace,
    attach_screenshot,
    attach_text,
)
from qa.framework.reporting.triager import (
    FailureCategory,
    FailureClassifier,
    TriageReport,
)

__all__ = [
    "FailureCategory",
    "FailureClassifier",
    "TriageReport",
    "attach_api_request",
    "attach_api_response",
    "attach_json",
    "attach_playwright_trace",
    "attach_screenshot",
    "attach_text",
]
