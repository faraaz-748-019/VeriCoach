"""Smoke tests for the FinanceAssistant (MOCK provider only)."""

from __future__ import annotations

import pytest

from app.data.synthetic import generate_finance_document, generate_user
from app.finance.assistant import FinanceAssistant
from app.providers.mock import MockLLMProvider


@pytest.fixture
def assistant() -> FinanceAssistant:
    """FinanceAssistant pre-configured with the MOCK provider."""
    return FinanceAssistant(locale="en", provider=MockLLMProvider())


@pytest.fixture
def loaded_assistant() -> FinanceAssistant:
    """Assistant with one synthetic document already indexed."""
    asst = FinanceAssistant(locale="en", provider=MockLLMProvider())
    user = generate_user(seed=7)
    doc = generate_finance_document(user)
    asst.index_document(doc, source="test_doc")
    return asst


class TestGreeting:
    def test_english_greeting(self) -> None:
        asst = FinanceAssistant(locale="en", provider=MockLLMProvider())
        greeting = asst.greet()
        assert "Hello" in greeting or "hello" in greeting.lower()

    def test_hindi_greeting(self) -> None:
        asst = FinanceAssistant(locale="hi", provider=MockLLMProvider())
        greeting = asst.greet()
        assert greeting  # non-empty

    def test_telugu_greeting(self) -> None:
        asst = FinanceAssistant(locale="te", provider=MockLLMProvider())
        greeting = asst.greet()
        assert greeting  # non-empty


class TestAskNoDocuments:
    def test_returns_no_context_message(self, assistant: FinanceAssistant) -> None:
        resp = assistant.ask("What is my balance?")
        # With no documents, should return the no_context phrase
        assert resp.text  # non-empty
        assert len(resp.text) > 5

    def test_provider_name_in_response(self, assistant: FinanceAssistant) -> None:
        resp = assistant.ask("Hello?")
        assert resp.provider == "mock"


class TestIndexDocument:
    def test_returns_chunk_count(self, assistant: FinanceAssistant) -> None:
        text = "A" * 1500  # should produce multiple chunks
        count = assistant.index_document(text, source="big_doc")
        assert count > 1

    def test_empty_document_returns_zero_chunks(
        self, assistant: FinanceAssistant
    ) -> None:
        count = assistant.index_document("")
        assert count == 0

    def test_clear_index(self, assistant: FinanceAssistant) -> None:
        assistant.index_document("some text")
        assistant.clear_index()
        # After clear, asking should return no_context
        resp = assistant.ask("anything")
        from app.i18n.translator import t

        assert resp.text == t("no_context", "en")


class TestAskWithDocuments:
    def test_returns_mock_response(self, loaded_assistant: FinanceAssistant) -> None:
        resp = loaded_assistant.ask("What is the advice?")
        assert resp.text
        assert "[MOCK]" in resp.text

    def test_response_has_provider_mock(
        self, loaded_assistant: FinanceAssistant
    ) -> None:
        resp = loaded_assistant.ask("Tell me about SIP")
        assert resp.provider == "mock"

    def test_multiple_questions(self, loaded_assistant: FinanceAssistant) -> None:
        for question in ["What is SIP?", "Tell me about savings", "Insurance advice"]:
            resp = loaded_assistant.ask(question)
            assert resp.text


class TestMultilingualRAG:
    @pytest.mark.parametrize("locale", ["en", "hi", "te"])
    def test_ask_in_all_locales(self, locale: str) -> None:  # type: ignore[type-arg]
        asst = FinanceAssistant(locale=locale, provider=MockLLMProvider())  # type: ignore[arg-type]
        user = generate_user(seed=5)
        asst.index_document(generate_finance_document(user))
        resp = asst.ask("What is the balance?")
        assert resp.text
