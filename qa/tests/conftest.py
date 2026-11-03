"""Shared pytest fixtures for qa/ tests."""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL of the finance assistant API under test."""
    import os
    return os.getenv("APP_BASE_URL", "http://localhost:8000")

