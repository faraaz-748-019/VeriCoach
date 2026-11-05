"""Configuration for VeriCoach Backend."""

from __future__ import annotations

import json
from enum import Enum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderType(str, Enum):
    gemini = "gemini"
    mock = "mock"
    ollama = "ollama"


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider
    llm_provider: LLMProviderType = LLMProviderType.mock
    google_api_key: str = Field(default="", repr=False)
    gemini_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # Ollama Provider
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # API Security & Authentication
    api_keys: list[str] | str = Field(
        default_factory=lambda: ["vc-dev-key-12345", "vc-test-key-67890"]
    )
    require_api_key: bool = False  # Allows open access in dev/CI when False

    @field_validator("api_keys", mode="after")
    @classmethod
    def normalize_api_keys(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(k).strip() for k in parsed]
                except Exception:
                    pass
            return [k.strip() for k in v.split(",") if k.strip()]
        return v

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # RAG & Chroma
    chroma_persist_directory: str = ""  # Empty means ephemeral/in-memory
    rag_top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 50
    enable_poisoned_corpus: bool = False  # Test-only mode: injects adversarial document

    # Logging
    log_level: str = "INFO"
    environment: str = "development"


_settings: BackendSettings | None = None


def get_backend_settings() -> BackendSettings:
    """Return cached settings instance."""
    global _settings
    if _settings is None:
        _settings = BackendSettings()
    return _settings
