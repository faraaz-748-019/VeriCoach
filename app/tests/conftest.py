"""Shared pytest fixtures for app/ tests."""

from __future__ import annotations

import os

import pytest

# Force MOCK provider for all tests — no network
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_PROVIDER", "mock")


@pytest.fixture(scope="session")
def mock_provider():
    from app.providers.mock import MockLLMProvider

    return MockLLMProvider()


@pytest.fixture(scope="session")
def default_settings():
    from app.config import get_settings

    return get_settings()
