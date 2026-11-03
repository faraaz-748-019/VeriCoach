"""Structured JSON logging with automatic PII redaction."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from backend.guardrails import mask_pii


class JSONFormatter(logging.Formatter):
    """Custom logging formatter that produces clean, structured JSON lines with PII masked."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt)
            or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_pii(record.getMessage()),
        }

        # Include custom extra fields attached to log records
        for key, val in record.__dict__.items():
            if key not in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "id",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ):
                if isinstance(val, str):
                    log_entry[key] = mask_pii(val)
                else:
                    log_entry[key] = val

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_backend_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure root / backend logger with JSON formatting."""
    logger = logging.getLogger("vericoach")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger
