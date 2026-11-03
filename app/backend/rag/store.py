"""Chroma vector store integration for VeriCoach."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.corpus.documents import DOCUMENTS_CORPUS, FinancialDocument
from backend.providers.base import BaseLLMProvider
from backend.rag.chunker import DocumentChunk, TextChunker
from backend.rag.embeddings import MultilingualEmbedder

logger = logging.getLogger("vericoach.rag")


@dataclass
class RetrievedSource:
    doc_id: str
    title: str
    snippet: str
    score: float


class ChromaRAGStore:
    """Manages document vectorization and top-k retrieval with Chroma."""

    COLLECTION_NAME = "vericoach_corpus"

    def __init__(
        self,
        provider: BaseLLMProvider,
        persist_dir: str = "",
        top_k: int = 4,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.provider = provider
        self.top_k = top_k
        self.embedder = MultilingualEmbedder(provider)
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Initialize Chroma (Ephemeral for tests / in-memory, Persistent if dir provided)
        chroma_settings = ChromaSettings(anonymized_telemetry=False)
        if persist_dir:
            self._client = chromadb.PersistentClient(
                path=persist_dir, settings=chroma_settings
            )
        else:
            self._client = chromadb.EphemeralClient(settings=chroma_settings)

        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Cache of indexed documents for GET /v1/documents
        self._documents_by_id: dict[str, FinancialDocument] = {}

    def bootstrap_default_corpus(self) -> int:
        """Load and index the 30 original documents corpus."""
        return self.index_documents(DOCUMENTS_CORPUS)

    def index_documents(self, documents: list[FinancialDocument]) -> int:
        """Chunk, embed, and store financial documents."""
        all_chunks: list[DocumentChunk] = []
        for doc in documents:
            self._documents_by_id[doc.doc_id] = doc
            chunks = self.chunker.chunk_document(
                doc_id=doc.doc_id,
                title=doc.title,
                category=doc.category,
                text=doc.content,
                extra_keywords=doc.keywords,
            )
            all_chunks.extend(chunks)

        if not all_chunks:
            return 0

        # In MOCK mode: enrich chunks with keywords for cross-lingual lexical matching
        ids = [c.chunk_id for c in all_chunks]
        texts = [c.text for c in all_chunks]
        metadatas: list[dict[str, Any]] = [
            {
                "doc_id": c.doc_id,
                "title": c.title,
                "category": c.category,
                "keywords": " ".join(c.metadata.get("keywords", [])),  # type: ignore[arg-type]
            }
            for c in all_chunks
        ]

        # Generate embeddings
        embeddings = [
            self.embedder.embed_document(f"{c.title} {c.text}") for c in all_chunks
        ]

        # Upsert into Chroma
        self._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        logger.info(
            "Indexed documents into Chroma",
            extra={"documents_count": len(documents), "chunks_count": len(all_chunks)},
        )
        return len(all_chunks)

    def retrieve(
        self, query: str, top_k: int | None = None, language: str = "auto"
    ) -> list[RetrievedSource]:
        """Perform multilingual semantic search and return top-k sources."""
        k = top_k or self.top_k
        count = self._collection.count()
        if count == 0:
            return []

        actual_k = min(k, count)
        query_vector = self.embedder.embed_query(query, language=language)

        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"],
        )

        sources: list[RetrievedSource] = []
        doc_lists = results.get("documents", [[]])
        meta_lists = results.get("metadatas", [[]])
        dist_lists = results.get("distances", [[]])

        if doc_lists and meta_lists and dist_lists:
            docs = doc_lists[0]
            metas = meta_lists[0]
            dists = dist_lists[0]

            for doc_text, meta, dist in zip(docs, metas, dists, strict=False):
                # Cosine distance to similarity score
                similarity = max(
                    0.0, min(1.0, 1.0 - (dist if dist is not None else 0.5))
                )
                sources.append(
                    RetrievedSource(
                        doc_id=str(meta.get("doc_id", "unknown")),
                        title=str(meta.get("title", "Financial Knowledge")),
                        snippet=doc_text[:250] + ("..." if len(doc_text) > 250 else ""),
                        score=round(float(similarity), 4),
                    )
                )

        # Sort by score descending
        sources.sort(key=lambda s: s.score, reverse=True)
        return sources

    def get_document(self, doc_id: str) -> FinancialDocument | None:
        """Fetch original document by ID."""
        return self._documents_by_id.get(doc_id)

    def list_documents(self) -> list[FinancialDocument]:
        """List all indexed documents."""
        return list(self._documents_by_id.values())

    def clear(self) -> None:
        """Clear all indexed data from Chroma."""
        try:
            self._client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._documents_by_id.clear()
