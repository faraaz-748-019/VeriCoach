"""Deterministic MOCK LLM provider — zero network, safe for CI."""

from __future__ import annotations

import hashlib
import math

from app.providers.base import BaseLLMProvider, LLMResponse

_EMBEDDING_DIM = 384  # match common sentence-transformer dim


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic provider that never makes network calls.

    * complete() echoes the prompt prefix and appends a fixed tag.
    * embed()     returns a stable, normalised pseudo-random vector derived
                  from the text's SHA-256 hash, so identical inputs always
                  produce identical embeddings.
    """

    MODEL = "mock-deterministic-v1"

    def complete(self, prompt: str, **kwargs: object) -> LLMResponse:
        # Deterministic reply: first 80 chars of the prompt + a label
        snippet = prompt[:80].replace("\n", " ")
        text = f"[MOCK] Echo: {snippet} … (deterministic stub)"
        words = len(prompt.split())
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self.MODEL,
            prompt_tokens=words,
            completion_tokens=len(text.split()),
        )

    def embed(self, text: str) -> list[float]:
        """Stable unit-norm embedding derived from SHA-256 of *text*."""
        digest = hashlib.sha256(text.encode()).digest()
        # Seed a sequence of values from the 32 digest bytes, tiled to fill dim
        raw: list[float] = []
        for i in range(_EMBEDDING_DIM):
            byte_val = digest[i % 32]
            # Map 0-255 → [-1, 1]
            raw.append((byte_val / 127.5) - 1.0)
        # Normalise to unit length
        norm = math.sqrt(sum(v * v for v in raw))
        return [v / norm for v in raw]

    @property
    def provider_name(self) -> str:
        return "mock"
