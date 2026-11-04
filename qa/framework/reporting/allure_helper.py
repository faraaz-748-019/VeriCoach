"""Allure attachment utilities for API calls, screenshots, and Playwright traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import allure
    from allure_commons.types import AttachmentType

    HAS_ALLURE = True
except ImportError:
    HAS_ALLURE = False


def attach_api_request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: Any = None,
    name: str = "API Request",
) -> None:
    """Format and attach HTTP request details to the current Allure test."""
    if not HAS_ALLURE:
        return

    payload: dict[str, Any] = {
        "method": method,
        "url": url,
        "headers": headers or {},
    }
    if body is not None:
        payload["body"] = body

    allure.attach(
        json.dumps(payload, indent=2, default=str),
        name=f"[{method}] {url} - Request",
        attachment_type=AttachmentType.JSON,
    )


def attach_api_response(
    status_code: int,
    headers: dict[str, str] | None = None,
    body: Any = None,
    duration_ms: float = 0.0,
    name: str = "API Response",
) -> None:
    """Format and attach HTTP response details to the current Allure test."""
    if not HAS_ALLURE:
        return

    payload: dict[str, Any] = {
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "headers": headers or {},
    }
    if body is not None:
        payload["body"] = body

    allure.attach(
        json.dumps(payload, indent=2, default=str),
        name=f"Response ({status_code}) - {round(duration_ms, 1)}ms",
        attachment_type=AttachmentType.JSON,
    )


def attach_screenshot(image_bytes: bytes, name: str = "screenshot") -> None:
    """Attach PNG screenshot to the current Allure test."""
    if not HAS_ALLURE:
        return

    allure.attach(
        image_bytes,
        name=name,
        attachment_type=AttachmentType.PNG,
    )


def attach_playwright_trace(
    trace_path: str | Path, name: str = "playwright-trace"
) -> None:
    """Attach Playwright trace ZIP file to the current Allure test."""
    if not HAS_ALLURE:
        return

    p = Path(trace_path)
    if p.exists() and p.is_file():
        allure.attach.file(
            source=str(p),
            name=name,
            attachment_type=AttachmentType.ZIP,
            extension="zip",
        )


def attach_json(data: Any, name: str = "data") -> None:
    """Attach arbitrary JSON serializable payload to Allure."""
    if not HAS_ALLURE:
        return

    allure.attach(
        json.dumps(data, indent=2, default=str),
        name=name,
        attachment_type=AttachmentType.JSON,
    )


def attach_text(text: str, name: str = "log") -> None:
    """Attach raw text to Allure."""
    if not HAS_ALLURE:
        return

    allure.attach(
        text,
        name=name,
        attachment_type=AttachmentType.TEXT,
    )
