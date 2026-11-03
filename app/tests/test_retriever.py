"""Tests for the InMemoryRetriever."""

from __future__ import annotations

import pytest

from app.providers.mock import MockLLMProvider
from app.rag.chunker import Chunk
from app.rag.retriever import InMemoryRetriever, _cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors(self) -> None:
        v = [1.0, 0.0, 0.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        assert abs(_cosine_similarity(v1, v2)) < 1e-6

    def test_zero_vector_returns_zero(self) -> None:
        v1 = [0.0, 0.0]
        v2 = [1.0, 1.0]
        assert _cosine_similarity(v1, v2) == 0.0

    def test_opposite_vectors(self) -> None:
        v1 = [1.0, 0.0]
        v2 = [-1.0, 0.0]
        assert abs(_cosine_similarity(v1, v2) - (-1.0)) < 1e-6


class TestInMemoryRetriever:
    @pytest.fixture
    def provider(self) -> MockLLMProvider:
        return MockLLMProvider()

    @pytest.fixture
    def retriever(self, provider: MockLLMProvider) -> InMemoryRetriever:
        return InMemoryRetriever(provider, top_k=3)

    def test_empty_retriever_returns_empty(self, retriever: InMemoryRetriever) -> None:
        results = retriever.retrieve("any query")
        assert results == []

    def test_add_and_retrieve(
        self, retriever: InMemoryRetriever, provider: MockLLMProvider
    ) -> None:
        chunk = Chunk(text="emergency fund advice", index=0)
        retriever.add(chunk)
        results = retriever.retrieve("emergency fund")
        assert len(results) == 1
        assert results[0][0].text == "emergency fund advice"

    def test_top_k_limits_results(
        self, retriever: InMemoryRetriever, provider: MockLLMProvider
    ) -> None:
        for i in range(10):
            retriever.add(Chunk(text=f"document chunk {i}", index=i))
        results = retriever.retrieve("document", top_k=3)
        assert len(results) == 3

    def test_scores_between_neg1_and_1(self, retriever: InMemoryRetriever) -> None:
        for i in range(5):
            retriever.add(Chunk(text=f"text {i}", index=i))
        results = retriever.retrieve("text")
        for _, score in results:
            assert -1.0 <= score <= 1.0 + 1e-6

    def test_results_sorted_by_score_descending(
        self, retriever: InMemoryRetriever
    ) -> None:
        for i in range(5):
            retriever.add(Chunk(text=f"text {i}", index=i))
        results = retriever.retrieve("text")
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_len_reflects_added_chunks(self, retriever: InMemoryRetriever) -> None:
        assert len(retriever) == 0
        for i in range(4):
            retriever.add(Chunk(text=f"c{i}", index=i))
        assert len(retriever) == 4

    def test_clear_empties_store(self, retriever: InMemoryRetriever) -> None:
        retriever.add(Chunk(text="something", index=0))
        retriever.clear()
        assert len(retriever) == 0

    def test_add_many(
        self, retriever: InMemoryRetriever, provider: MockLLMProvider
    ) -> None:
        from app.rag.embedder import Embedder

        embedder = Embedder(provider)
        chunks = [Chunk(text=f"chunk {i}", index=i) for i in range(5)]
        pairs = embedder.embed_chunks(chunks)
        retriever.add_many(pairs)
        assert len(retriever) == 5
