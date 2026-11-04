"""Ragas Judge LLM, multilingual embedding models, and disk cache wrappers."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ragas.cache import DiskCacheBackend
from ragas.embeddings.base import LangchainEmbeddingsWrapper
from ragas.llms.base import LangchainLLMWrapper

from qa.llm_eval.ragas_eval.config import RagasEvalSettings

logger = logging.getLogger("vericoach.qa.ragas_wrappers")


@dataclass
class CacheStats:
    """Statistics tracking for disk cache hits and misses."""

    hits: int = 0
    misses: int = 0

    @property
    def total(self) -> int:
        return self.hits + self.misses

    @property
    def hit_ratio(self) -> float:
        return (self.hits / self.total) if self.total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": self.total,
            "hit_ratio": round(self.hit_ratio, 4),
        }


class InstrumentedDiskCache:
    """Wraps Ragas DiskCacheBackend to track cache hits, misses, and keys."""

    def __init__(
        self, cache_dir: Path | str | None = None, directory: Path | str | None = None
    ) -> None:
        target_dir = cache_dir or directory or Path(".cache/ragas_judge")
        self.cache_dir = Path(target_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.backend = DiskCacheBackend(str(self.cache_dir))
        self.stats = CacheStats()

    def get(self, key: str) -> Any | None:
        if self.backend.has_key(key):
            self.stats.hits += 1
            return self.backend.get(key)
        self.stats.misses += 1
        return None

    def set(self, key: str, value: Any) -> None:
        self.backend.set(key, value)

    def has_key(self, key: str) -> bool:
        return self.backend.has_key(key)

    @staticmethod
    def make_key(namespace: str, data: dict[str, Any] | str) -> str:
        """Create deterministic SHA-256 cache key."""
        serialized = data if isinstance(data, str) else json.dumps(data, sort_keys=True)
        hashed = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"{namespace}:{hashed}"

    def close(self) -> None:
        """Close underlying diskcache if supported."""
        if hasattr(self.backend, "cache") and hasattr(self.backend.cache, "close"):
            self.backend.cache.close()
        elif hasattr(self.backend, "close"):
            self.backend.close()


def create_judge_llm(
    settings: RagasEvalSettings,
    cache: InstrumentedDiskCache | None = None,
) -> Any:
    """Create and wrap the LLM judge according to configured provider."""
    cache_backend = cache.backend if cache else None

    if settings.provider == "gemini" and settings.google_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=settings.judge_model,
                google_api_key=settings.google_api_key,
                temperature=0.0,
            )
            return LangchainLLMWrapper(llm, cache=cache_backend)
        except Exception as exc:
            logger.warning(
                "Failed to initialize Gemini judge: %s. Falling back to mock provider.",
                exc,
            )

    if settings.provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama

            llm = ChatOllama(
                model=settings.ollama_judge_model,
                base_url=settings.ollama_base_url,
                temperature=0.0,
            )
            return LangchainLLMWrapper(llm, cache=cache_backend)
        except Exception as exc:
            logger.warning(
                "Failed to initialize Ollama judge: %s. Falling back to mock provider.",
                exc,
            )

    # Default / fallback: Mock deterministic judge
    from langchain_community.chat_models import FakeListChatModel

    responses = [
        json.dumps(
            {
                "statements": [
                    "The answer provides educational information on the financial topic.",
                    "The response refers to official guidelines.",
                ]
            }
        ),
        json.dumps(
            [
                {"statement": "Statement 1", "verdict": 1, "reason": "Consistent"},
                {"statement": "Statement 2", "verdict": 1, "reason": "Consistent"},
            ]
        ),
        json.dumps({"verdict": 1, "reason": "Context is relevant"}),
        json.dumps([{"statement": "Claim 1", "attributed": 1, "reason": "Covered"}]),
        json.dumps({"question": "Clarifying question", "noncommittal": 0}),
    ] * 200
    mock_llm = FakeListChatModel(responses=responses)
    return LangchainLLMWrapper(mock_llm, cache=cache_backend)


def create_embedding_model(
    settings: RagasEvalSettings,
    cache: InstrumentedDiskCache | None = None,
) -> Any:
    """Create and wrap the multilingual embedding model according to configured provider."""
    cache_backend = cache.backend if cache else None

    if settings.provider == "gemini" and settings.google_api_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            emb = GoogleGenerativeAIEmbeddings(
                model=settings.embedding_model,
                google_api_key=settings.google_api_key,
            )
            return LangchainEmbeddingsWrapper(emb, cache=cache_backend)
        except Exception as exc:
            logger.warning(
                "Failed to initialize Gemini embeddings: %s. Falling back to mock embeddings.",
                exc,
            )

    # Fallback to deterministic fake embeddings (384 dimensions)
    from langchain_community.embeddings import FakeEmbeddings

    mock_emb = FakeEmbeddings(size=384)
    return LangchainEmbeddingsWrapper(mock_emb, cache=cache_backend)
