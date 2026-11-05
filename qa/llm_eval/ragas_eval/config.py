"""Configuration settings for Ragas evaluation framework."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RagasEvalSettings(BaseSettings):
    """Evaluation configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    google_api_key: str = Field(
        default="",
        validation_alias="GOOGLE_API_KEY",
        description="Google API key for Gemini judge and embeddings.",
    )
    provider: str = Field(
        default="gemini",
        validation_alias="EVAL_PROVIDER",
        description="Judge and embedding provider: gemini, mock, or ollama.",
    )
    judge_model: str = Field(
        default="gemini-3.5-flash-lite",
        validation_alias="RAGAS_JUDGE_MODEL",
        description="Gemini LLM judge model name.",
    )
    embedding_model: str = Field(
        default="models/gemini-embedding-001",
        validation_alias="RAGAS_EMBEDDING_MODEL",
        description="Multilingual embedding model name.",
    )
    cache_dir: Path = Field(
        default=Path(".cache/ragas_judge"),
        validation_alias="RAGAS_CACHE_DIR",
        description="Path to disk cache directory for judge LLM and embedding calls.",
    )
    output_dir: Path = Field(
        default=Path("results"),
        validation_alias="RAGAS_OUTPUT_DIR",
        description="Directory where evaluation JSON and CSV results are written.",
    )
    golden_path: Path = Field(
        default=Path("qa/data/golden/golden_v1.jsonl"),
        validation_alias="GOLDEN_DATASET_PATH",
        description="Path to golden evaluation dataset jsonl.",
    )
    default_sample_limit: int = Field(
        default=30,
        validation_alias="RAGAS_SAMPLE_LIMIT",
        description="Default number of items to evaluate if limit is not provided.",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
        description="Base URL for local Ollama instance.",
    )
    ollama_judge_model: str = Field(
        default="llama3",
        validation_alias="OLLAMA_JUDGE_MODEL",
        description="Ollama model name for evaluation.",
    )


def get_eval_settings() -> RagasEvalSettings:
    """Retrieve or create RagasEvalSettings singleton."""
    return RagasEvalSettings()
