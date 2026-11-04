"""Pipeline runner and golden dataset collector for Ragas evaluation."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backend.config import BackendSettings, LLMProviderType
from backend.main import chat_v1
from backend.providers import create_llm_provider
from backend.rag.store import ChromaRAGStore
from backend.schemas import ChatRequestV1
from starlette.requests import Request

from qa.llm_eval.ragas_eval.config import RagasEvalSettings

logger = logging.getLogger("vericoach.qa.pipeline_collector")


@dataclass
class EvaluatedItem:
    """Individual item collected from running golden question through pipeline."""

    id: str
    language: str
    category: str
    question: str
    response: str
    reference: str
    retrieved_contexts: list[str]
    must_refuse: bool
    refused: bool
    sources: list[dict[str, Any]]

    # Metric scores (filled during evaluation)
    context_precision: float = 0.0
    context_recall: float = 0.0
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    composite_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_golden_items(
    golden_path: Path | str,
    limit: int | None = None,
    languages: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load and optionally balance golden dataset items."""
    path = Path(golden_path)
    if not path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {path}")

    items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    if languages:
        items = [item for item in items if item.get("language") in languages]

    if limit is not None and limit < len(items):
        # Balanced sampling across languages (en, hi, te)
        by_lang: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            by_lang.setdefault(item.get("language", "en"), []).append(item)

        selected: list[dict[str, Any]] = []
        per_lang = limit // len(by_lang) if by_lang else limit
        for lang_items in by_lang.values():
            selected.extend(lang_items[:per_lang])

        # Fill remaining if any
        remaining = limit - len(selected)
        if remaining > 0:
            for item in items:
                if item not in selected:
                    selected.append(item)
                    if len(selected) >= limit:
                        break
        return selected[:limit]

    return items


class RAGPipelineCollector:
    """Executes golden items through the active VeriCoach RAG pipeline."""

    def __init__(self, eval_settings: RagasEvalSettings) -> None:
        self.eval_settings = eval_settings

        # Determine backend settings matching provider
        provider_name = eval_settings.provider
        if provider_name not in ("gemini", "mock", "ollama"):
            provider_name = "mock"

        backend_provider_type = LLMProviderType(provider_name)

        self.backend_settings = BackendSettings(
            llm_provider=backend_provider_type,
            google_api_key=eval_settings.google_api_key,
            gemini_model=eval_settings.judge_model,
            gemini_embedding_model=eval_settings.embedding_model,
            ollama_base_url=eval_settings.ollama_base_url,
            ollama_model=eval_settings.ollama_judge_model,
            require_api_key=False,
            rate_limit_per_minute=1000,
        )

        llm_provider = create_llm_provider(self.backend_settings)
        self.store = ChromaRAGStore(
            provider=llm_provider,
            persist_dir="",  # In-memory ephemeral for isolated clean state
            top_k=4,
        )
        self.store.bootstrap_default_corpus()
        logger.info(
            "Initialized RAGPipelineCollector with provider=%s",
            backend_provider_type.value,
        )

    def process_item(self, item: dict[str, Any]) -> EvaluatedItem:
        """Run single golden item through the real RAG pipeline."""
        req_data = ChatRequestV1(
            question=item["question"],
            language=item.get("language", "en"),
        )
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/v1/chat",
            "headers": [],
        }
        request = Request(scope)

        chat_response = chat_v1(
            request_data=req_data,
            request=request,
            settings=self.backend_settings,
            store=self.store,
        )

        retrieved_contexts = [source.snippet for source in chat_response.sources]
        sources_data = [
            {
                "doc_id": s.doc_id,
                "title": s.title,
                "score": round(s.score, 4),
                "snippet": s.snippet,
            }
            for s in chat_response.sources
        ]

        return EvaluatedItem(
            id=item["id"],
            language=item.get("language", "en"),
            category=item.get("category", "answerable"),
            question=item["question"],
            response=chat_response.answer,
            reference=item.get("reference_answer", ""),
            retrieved_contexts=retrieved_contexts,
            must_refuse=item.get("must_refuse", False),
            refused=chat_response.refused,
            sources=sources_data,
        )

    # Convenience alias for process_item
    collect_item = process_item

    def collect_dataset(
        self,
        golden_path: Path | str,
        limit: int | None = None,
    ) -> list[EvaluatedItem]:
        """Run golden dataset items through pipeline and collect evaluation rows."""
        items = load_golden_items(golden_path, limit=limit)
        results: list[EvaluatedItem] = []
        logger.info("Processing %d golden items through RAG pipeline...", len(items))

        for idx, item in enumerate(items, 1):
            eval_item = self.process_item(item)
            results.append(eval_item)
            if idx % 10 == 0 or idx == len(items):
                logger.info(
                    "Processed %d/%d items (last: %s - %s)",
                    idx,
                    len(items),
                    eval_item.id,
                    eval_item.language,
                )

        return results

    def collect_all(self, items: list[dict[str, Any]]) -> list[EvaluatedItem]:
        """Process an explicit list of golden items."""
        return [self.process_item(item) for item in items]
