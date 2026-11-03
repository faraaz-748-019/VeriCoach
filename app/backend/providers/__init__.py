"""Provider abstraction module for VeriCoach backend."""

from __future__ import annotations

from backend.config import BackendSettings, LLMProviderType
from backend.providers.base import BaseLLMProvider, LLMResponse
from backend.providers.gemini import GeminiLLMProvider
from backend.providers.mock import MockLLMProvider
from backend.providers.ollama import OllamaLLMProvider


def create_llm_provider(settings: BackendSettings) -> BaseLLMProvider:
    """Factory creating the configured LLM provider."""
    if settings.llm_provider == LLMProviderType.mock:
        return MockLLMProvider()
    elif settings.llm_provider == LLMProviderType.gemini:
        return GeminiLLMProvider(
            model=settings.gemini_model,
            embedding_model=settings.gemini_embedding_model,
            api_key=settings.google_api_key,
        )
    elif settings.llm_provider == LLMProviderType.ollama:
        return OllamaLLMProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    raise ValueError(f"Unsupported provider: {settings.llm_provider}")


__all__ = [
    "BaseLLMProvider",
    "GeminiLLMProvider",
    "LLMResponse",
    "MockLLMProvider",
    "OllamaLLMProvider",
    "create_llm_provider",
]
