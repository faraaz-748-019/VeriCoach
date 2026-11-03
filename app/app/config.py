"""Application configuration via pydantic-settings + .env."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    gemini = "gemini"
    mock = "mock"
    ollama = "ollama"


class EmbeddingProvider(str, Enum):
    mock = "mock"
    gemini = "gemini"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    llm_provider: LLMProvider = LLMProvider.mock
    google_api_key: str = Field(default="", repr=False)
    gemini_model: str = "gemini-1.5-flash"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    default_locale: Literal["en", "hi", "te"] = "en"

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k: int = 5

    # Embeddings
    embedding_provider: EmbeddingProvider = EmbeddingProvider.mock
    gemini_embedding_model: str = "text-embedding-004"

    @field_validator("google_api_key")
    @classmethod
    def _warn_missing_api_key(cls, v: str) -> str:
        if not v:
            logger.debug(
                "GOOGLE_API_KEY is not set; Gemini provider will raise at runtime."
            )
        return v


def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return _settings


_settings: Settings = Settings()
