"""Text chunking for financial educational documents."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    text: str
    metadata: dict[str, object] = field(default_factory=dict)


class TextChunker:
    """Splits documents into sensible chunks for retrieval."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        doc_id: str,
        title: str,
        category: str,
        text: str,
        extra_keywords: list[str] | None = None,
    ) -> list[DocumentChunk]:
        """Split a document into overlapping chunks, preserving sentence boundaries where possible."""
        cleaned = text.strip()
        if not cleaned:
            return []

        if len(cleaned) <= self.chunk_size:
            return [
                DocumentChunk(
                    chunk_id=f"{doc_id}_0",
                    doc_id=doc_id,
                    title=title,
                    category=category,
                    text=cleaned,
                    metadata={"keywords": extra_keywords or []},
                )
            ]

        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.chunk_overlap
        idx = 0
        start = 0

        while start < len(cleaned):
            end = start + self.chunk_size
            chunk_slice = cleaned[start:end].strip()
            if chunk_slice:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{doc_id}_{idx}",
                        doc_id=doc_id,
                        title=title,
                        category=category,
                        text=chunk_slice,
                        metadata={"keywords": extra_keywords or []},
                    )
                )
                idx += 1
            start += step

        return chunks
