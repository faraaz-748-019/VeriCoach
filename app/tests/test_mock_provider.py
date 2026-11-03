"""Tests for the deterministic MOCK provider."""

from __future__ import annotations

import math

import pytest

from app.providers.mock import _EMBEDDING_DIM, MockLLMProvider


@pytest.fixture
def provider() -> MockLLMProvider:
    return MockLLMProvider()


class TestMockComplete:
    def test_returns_llm_response(self, provider: MockLLMProvider) -> None:
        from app.providers.base import LLMResponse

        resp = provider.complete("Hello, world!")
        assert isinstance(resp, LLMResponse)

    def test_provider_name(self, provider: MockLLMProvider) -> None:
        assert provider.provider_name == "mock"

    def test_deterministic(self, provider: MockLLMProvider) -> None:
        r1 = provider.complete("test prompt")
        r2 = provider.complete("test prompt")
        assert r1.text == r2.text

    def test_different_prompts_different_output(
        self, provider: MockLLMProvider
    ) -> None:
        r1 = provider.complete("prompt one")
        r2 = provider.complete("prompt two")
        assert r1.text != r2.text

    def test_echo_contains_mock_tag(self, provider: MockLLMProvider) -> None:
        resp = provider.complete("What is SIP?")
        assert "[MOCK]" in resp.text

    def test_token_counts_are_nonnegative(self, provider: MockLLMProvider) -> None:
        resp = provider.complete("token test")
        assert resp.prompt_tokens >= 0
        assert resp.completion_tokens >= 0
        assert resp.total_tokens >= 0


class TestMockEmbed:
    def test_returns_correct_dimension(self, provider: MockLLMProvider) -> None:
        vec = provider.embed("hello")
        assert len(vec) == _EMBEDDING_DIM

    def test_unit_norm(self, provider: MockLLMProvider) -> None:
        vec = provider.embed("unit norm test")
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-6

    def test_deterministic_embedding(self, provider: MockLLMProvider) -> None:
        v1 = provider.embed("consistent text")
        v2 = provider.embed("consistent text")
        assert v1 == v2

    def test_different_texts_different_embeddings(
        self, provider: MockLLMProvider
    ) -> None:
        v1 = provider.embed("apple")
        v2 = provider.embed("banana")
        assert v1 != v2
