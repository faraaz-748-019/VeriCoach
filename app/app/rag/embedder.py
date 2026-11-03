"""Embedder — wraps LLM provider to embed text chunks."""

from __future__ import annotations

from app.providers.base import BaseLLMProvider
from app.rag.chunker import Chunk


class Embedder:
    """Embeds text using a provider's ``embed()`` method."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        self._provider = provider

    def embed_text(self, text: str) -> list[float]:
        return self._provider.embed(text)

    def embed_chunks(self, chunks: list[Chunk]) -> list[tuple[Chunk, list[float]]]:
        """Return each chunk paired with its embedding vector."""
        return [(chunk, self._provider.embed(chunk.text)) for chunk in chunks]
