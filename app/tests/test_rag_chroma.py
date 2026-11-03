"""Unit tests for Chroma RAG Store, multilingual retrieval, and 30-document corpus."""

from __future__ import annotations

import pytest

from backend.corpus.documents import DOCUMENTS_CORPUS
from backend.providers.mock import MockLLMProvider
from backend.rag.store import ChromaRAGStore


@pytest.fixture
def chroma_store():
    provider = MockLLMProvider()
    store = ChromaRAGStore(provider=provider, persist_dir="", top_k=4)
    store.bootstrap_default_corpus()
    return store


def test_corpus_size_is_exactly_30(chroma_store: ChromaRAGStore):
    docs = chroma_store.list_documents()
    assert len(docs) == 30
    assert len(DOCUMENTS_CORPUS) == 30


def test_corpus_covers_all_eight_topics(chroma_store: ChromaRAGStore):
    docs = chroma_store.list_documents()
    categories = {d.category for d in docs}
    expected_categories = {
        "UPI Safety",
        "KYC Basics",
        "Credit Score Basics",
        "SIP & Mutual Funds",
        "Fraud Awareness",
        "Budgeting & Emergency Funds",
        "Loan Terminology",
        "Insurance Basics",
    }
    assert expected_categories.issubset(categories)


def test_retrieval_returns_at_most_top_k(chroma_store: ChromaRAGStore):
    sources = chroma_store.retrieve("What is an emergency fund?", top_k=4)
    assert len(sources) <= 4
    assert len(sources) > 0
    for s in sources:
        assert 0.0 <= s.score <= 1.0
        assert s.doc_id
        assert s.title
        assert s.snippet


def test_english_query_upi_pin_retrieval(chroma_store: ChromaRAGStore):
    sources = chroma_store.retrieve("Do I need to enter my UPI PIN to receive money?")
    assert len(sources) > 0
    top_doc_ids = [s.doc_id for s in sources]
    assert "upi_pin_rules" in top_doc_ids


def test_multilingual_hindi_query_retrieval(chroma_store: ChromaRAGStore):
    # Hindi query asking if UPI PIN is required to receive money
    sources = chroma_store.retrieve(
        "क्या पैसे प्राप्त करने के लिए यूपीआई पिन जरूरी है?",
        language="hi",
    )
    assert len(sources) > 0
    top_doc_ids = [s.doc_id for s in sources]
    assert "upi_pin_rules" in top_doc_ids or "upi_qr_code_scams" in top_doc_ids


def test_multilingual_telugu_query_retrieval(chroma_store: ChromaRAGStore):
    # Telugu query asking about UPI PIN and receiving money
    sources = chroma_store.retrieve(
        "ఖాతాలో డబ్బులు తీసుకోవడానికి యూపీఐ పిన్ కావాలా?",
        language="te",
    )
    assert len(sources) > 0
    top_doc_ids = [s.doc_id for s in sources]
    assert "upi_pin_rules" in top_doc_ids or "upi_qr_code_scams" in top_doc_ids


def test_get_document_by_id(chroma_store: ChromaRAGStore):
    doc = chroma_store.get_document("fifty_thirty_twenty_budget_rule")
    assert doc is not None
    assert doc.doc_id == "fifty_thirty_twenty_budget_rule"
    assert "50/30/20" in doc.title
    assert "50%" in doc.content


def test_get_document_nonexistent_returns_none(chroma_store: ChromaRAGStore):
    doc = chroma_store.get_document("nonexistent_id_12345")
    assert doc is None


def test_store_clear(chroma_store: ChromaRAGStore):
    chroma_store.clear()
    assert len(chroma_store.list_documents()) == 0
    sources = chroma_store.retrieve("any query")
    assert sources == []
