"""In-memory cosine-similarity retriever for RAG."""

from __future__ import annotations

import math

from app.providers.base import BaseLLMProvider
from app.rag.chunker import Chunk


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryRetriever:
    """
    Stores (chunk, embedding) pairs and retrieves the top-k
    most similar chunks for a query, using cosine similarity.
    """

    def __init__(self, provider: BaseLLMProvider, top_k: int = 5) -> None:
        self._provider = provider
        self.top_k = top_k
        self._store: list[tuple[Chunk, list[float]]] = []

    def add(self, chunk: Chunk, embedding: list[float] | None = None) -> None:
        """Index a chunk (optionally pre-computed embedding)."""
        vec = embedding if embedding is not None else self._provider.embed(chunk.text)
        self._store.append((chunk, vec))

    def add_many(self, pairs: list[tuple[Chunk, list[float]]]) -> None:
        self._store.extend(pairs)

    def retrieve(
        self, query: str, top_k: int | None = None
    ) -> list[tuple[Chunk, float]]:
        """Return top-k (chunk, score) pairs for *query*."""
        k = top_k if top_k is not None else self.top_k
        if not self._store:
            return []
        q_vec = self._provider.embed(query)
        scored = [(chunk, _cosine_similarity(q_vec, vec)) for chunk, vec in self._store]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
