"""Shared test fixtures for the VeriCoach QA platform."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Ensure mock provider is used for zero-network testing
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"

from app.api.main import app, reset_assistant_instance
from app.finance.assistant import FinanceAssistant
from app.providers.mock import MockLLMProvider
from qa.evaluators.metrics import (
    AnswerRelevancyEvaluator,
    ContextPrecisionEvaluator,
    ContextRecallEvaluator,
    FaithfulnessEvaluator,
)
from qa.evaluators.pii_guard import PIIScanner
from qa.evaluators.safety import AdversarialSafetyEvaluator


@pytest.fixture
def mock_provider():
    return MockLLMProvider()


@pytest.fixture
def assistant(mock_provider):
    return FinanceAssistant(locale="en", provider=mock_provider)


@pytest.fixture
def client(mock_provider):
    reset_assistant_instance()
    from app.api.main import get_assistant

    test_assistant = FinanceAssistant(locale="en", provider=mock_provider)
    app.dependency_overrides[get_assistant] = lambda: test_assistant
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    reset_assistant_instance()


@pytest.fixture
def faithfulness_evaluator(mock_provider):
    return FaithfulnessEvaluator(provider=mock_provider)


@pytest.fixture
def relevancy_evaluator(mock_provider):
    return AnswerRelevancyEvaluator(provider=mock_provider)


@pytest.fixture
def precision_evaluator():
    return ContextPrecisionEvaluator()


@pytest.fixture
def recall_evaluator():
    return ContextRecallEvaluator()


@pytest.fixture
def pii_scanner():
    return PIIScanner()


@pytest.fixture
def safety_evaluator():
    return AdversarialSafetyEvaluator()
