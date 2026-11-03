"""Abstract base class for all LLM providers in VeriCoach backend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Typed response from an LLM provider."""

    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class BaseLLMProvider(ABC):
    """Common interface for all LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, **kwargs: object) -> LLMResponse:
        """Synchronous text completion."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for text."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
