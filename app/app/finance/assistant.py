"""FinanceAssistant — main RAG-powered assistant class."""

from __future__ import annotations

from app.config import Settings, get_settings
from app.i18n.translator import Locale, t
from app.providers.base import BaseLLMProvider, LLMResponse
from app.rag.chunker import TextChunker
from app.rag.embedder import Embedder
from app.rag.retriever import InMemoryRetriever

_PROMPT_TEMPLATE = """\
You are a helpful personal finance assistant that answers in {locale_name}.

Context from the user's documents:
{context}

User question: {question}

Answer concisely and accurately based only on the provided context.
If the context does not contain enough information, say so clearly.
"""


def _build_provider(settings: Settings) -> BaseLLMProvider:
    """Instantiate the correct provider based on *settings.llm_provider*."""
    from app.config import LLMProvider

    if settings.llm_provider == LLMProvider.mock:
        from app.providers.mock import MockLLMProvider

        return MockLLMProvider()
    elif settings.llm_provider == LLMProvider.gemini:
        from app.providers.gemini import GeminiLLMProvider

        return GeminiLLMProvider(
            model=settings.gemini_model,
            embedding_model=settings.gemini_embedding_model,
        )
    elif settings.llm_provider == LLMProvider.ollama:
        from app.providers.ollama import OllamaLLMProvider

        return OllamaLLMProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    raise ValueError(f"Unknown provider: {settings.llm_provider}")


class FinanceAssistant:
    """
    RAG-powered multilingual finance assistant.

    Usage::

        assistant = FinanceAssistant(locale="hi")
        assistant.index_document("Your finance document text here …")
        response = assistant.ask("मेरी बचत कितनी है?")
        print(response.text)
    """

    def __init__(
        self,
        locale: Locale = "en",
        provider: BaseLLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.locale = locale
        self._settings = settings or get_settings()
        self._provider = provider or _build_provider(self._settings)

        self._chunker = TextChunker(
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )
        self._embedder = Embedder(self._provider)
        self._retriever = InMemoryRetriever(
            self._provider,
            top_k=self._settings.top_k,
        )

    # ── Document indexing ────────────────────────────────────────────────

    def index_document(
        self, text: str, source: str = "", metadata: dict[str, object] | None = None
    ) -> int:
        """Chunk and embed *text*, store in retriever. Returns chunk count."""
        chunks = self._chunker.split(text, source=source, metadata=metadata)
        pairs = self._embedder.embed_chunks(chunks)
        self._retriever.add_many(pairs)
        return len(chunks)

    def clear_index(self) -> None:
        """Remove all indexed documents."""
        self._retriever.clear()

    # ── Query ────────────────────────────────────────────────────────────

    def ask(
        self,
        question: str,
        locale: Locale | None = None,
        top_k: int | None = None,
    ) -> LLMResponse:
        """
        Answer *question* using RAG over indexed documents.

        If no documents are indexed, returns a polite no-context message.
        """
        target_locale = locale or self.locale
        if len(self._retriever) == 0:
            return LLMResponse(
                text=t("no_context", target_locale),
                provider=self._provider.provider_name,
                model="n/a",
            )

        results = self._retriever.retrieve(question, top_k=top_k)
        context = "\n\n".join(chunk.text for chunk, _ in results)

        from app.i18n.translator import LOCALE_NAMES

        locale_name = LOCALE_NAMES.get(target_locale, "English")

        prompt = _PROMPT_TEMPLATE.format(
            locale_name=locale_name,
            context=context,
            question=question,
        )
        return self._provider.complete(prompt)

    def greet(self) -> str:
        """Return a locale-appropriate greeting."""
        return t("greeting", self.locale)
