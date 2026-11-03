"""Tests for app.config."""

from __future__ import annotations

import pytest

from app.config import LLMProvider, Settings, get_settings


def test_default_provider_is_mock() -> None:
    """With LLM_PROVIDER=mock in env, provider should be mock."""
    s = Settings()
    assert s.llm_provider == LLMProvider.mock


def test_settings_singleton_is_settings_instance() -> None:
    s = get_settings()
    assert isinstance(s, Settings)


def test_invalid_provider_raises() -> None:
    """An unknown provider value should raise a validation error."""
    with pytest.raises(Exception):  # noqa: B017
        Settings(llm_provider="unknown_provider")  # type: ignore[arg-type]


def test_default_locale() -> None:
    s = Settings()
    # conftest sets LLM_PROVIDER=mock but default_locale defaults to "en"
    assert s.default_locale in ("en", "hi", "te")


def test_chunk_size_positive() -> None:
    s = Settings()
    assert s.chunk_size > 0
    assert s.chunk_overlap >= 0
    assert s.chunk_overlap < s.chunk_size
