"""Text chunker for RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A text chunk with metadata."""

    text: str
    index: int
    source: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


class TextChunker:
    """
    Simple sliding-window character chunker.

    Parameters
    ----------
    chunk_size:
        Maximum characters per chunk.
    chunk_overlap:
        Characters of overlap between successive chunks.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(
        self, text: str, source: str = "", metadata: dict[str, object] | None = None
    ) -> list[Chunk]:
        """Split *text* into overlapping chunks."""
        if not text:
            return []
        meta = metadata or {}
        chunks: list[Chunk] = []
        step = self.chunk_size - self.chunk_overlap
        idx = 0
        position = 0
        while position < len(text):
            end = min(position + self.chunk_size, len(text))
            chunk_text = text[position:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text, index=idx, source=source, metadata=meta.copy()
                    )
                )
                idx += 1
            position += step
        return chunks
