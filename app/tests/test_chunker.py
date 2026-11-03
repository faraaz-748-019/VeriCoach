"""Tests for the TextChunker."""

from __future__ import annotations

import pytest

from app.rag.chunker import Chunk, TextChunker


class TestTextChunker:
    def test_empty_text_returns_empty(self) -> None:
        chunker = TextChunker()
        assert chunker.split("") == []

    def test_single_chunk_short_text(self) -> None:
        chunker = TextChunker(chunk_size=512, chunk_overlap=64)
        text = "Short text that fits in one chunk."
        chunks = chunker.split(text)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_multiple_chunks_long_text(self) -> None:
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        text = "x" * 250
        chunks = chunker.split(text)
        assert len(chunks) > 1

    def test_chunk_index_starts_at_zero(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=5)
        chunks = chunker.split("a" * 200)
        assert chunks[0].index == 0
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_source_propagated(self) -> None:
        chunker = TextChunker()
        chunks = chunker.split("some text", source="my_doc")
        assert all(c.source == "my_doc" for c in chunks)

    def test_metadata_propagated(self) -> None:
        chunker = TextChunker()
        meta = {"author": "test", "year": 2024}
        chunks = chunker.split("some text", metadata=meta)
        assert all(c.metadata == meta for c in chunks)

    def test_overlap_too_large_raises(self) -> None:
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, chunk_overlap=100)

    def test_chunks_are_chunk_instances(self) -> None:
        chunker = TextChunker()
        chunks = chunker.split("hello world")
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_no_empty_chunks(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "   " * 200  # mostly whitespace
        chunks = chunker.split(text)
        for c in chunks:
            assert c.text  # no blank chunks
