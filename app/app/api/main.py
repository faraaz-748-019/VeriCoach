"""FastAPI application for VeriCoach."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.schemas import (
    AccountInfo,
    BootstrapSyntheticRequest,
    BootstrapSyntheticResponse,
    ChatRequest,
    ChatResponse,
    ClearDocumentsResponse,
    DocumentIndexRequest,
    DocumentIndexResponse,
    HealthResponse,
    SyntheticUserResponse,
)
from app.config import Settings, get_settings
from app.data.synthetic import (
    generate_finance_document,
    generate_user,
    generate_users,
)
from app.finance.assistant import FinanceAssistant

_assistant_instance: FinanceAssistant | None = None


def get_assistant(
    settings: Settings = Depends(get_settings),
) -> FinanceAssistant:
    """Dependency that provides the shared FinanceAssistant instance."""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = FinanceAssistant(
            locale=settings.default_locale, settings=settings
        )
    return _assistant_instance


def reset_assistant_instance() -> None:
    """Helper for testing to reset the assistant singleton."""
    global _assistant_instance
    _assistant_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan setup and teardown."""
    # Ensure assistant is initialized
    settings = get_settings()
    get_assistant(settings)
    yield


app = FastAPI(
    title="VeriCoach API",
    description="Multilingual Personal-Finance Assistant API with RAG",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
def health_check(
    settings: Settings = Depends(get_settings),
    assistant: FinanceAssistant = Depends(get_assistant),
) -> HealthResponse:
    """Return system status and provider configuration."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        provider=assistant._provider.provider_name,
        default_locale=settings.default_locale,
    )


@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    summary="Ask a finance question",
    tags=["Assistant"],
)
def chat(
    request: ChatRequest,
    assistant: FinanceAssistant = Depends(get_assistant),
) -> ChatResponse:
    """Send a query to the assistant in English, Hindi, or Telugu."""
    try:
        response = assistant.ask(
            question=request.message,
            locale=request.locale,
            top_k=request.top_k,
        )
        return ChatResponse(
            response=response.text,
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            locale=request.locale,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {exc}",
        ) from exc


@app.post(
    "/api/v1/documents",
    response_model=DocumentIndexResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Index a document into RAG context",
    tags=["Knowledge Base"],
)
def index_document(
    request: DocumentIndexRequest,
    assistant: FinanceAssistant = Depends(get_assistant),
) -> DocumentIndexResponse:
    """Index a financial document (e.g. policy, bank statement summary)."""
    chunks = assistant.index_document(
        text=request.content,
        source=request.source,
        metadata=request.metadata,
    )
    return DocumentIndexResponse(
        status="indexed",
        chunks_indexed=chunks,
        source=request.source,
    )


@app.delete(
    "/api/v1/documents",
    response_model=ClearDocumentsResponse,
    summary="Clear all indexed documents",
    tags=["Knowledge Base"],
)
def clear_documents(
    assistant: FinanceAssistant = Depends(get_assistant),
) -> ClearDocumentsResponse:
    """Remove all indexed documents from memory."""
    assistant.clear_index()
    return ClearDocumentsResponse(
        status="cleared",
        message="Knowledge base index cleared successfully.",
    )


@app.get(
    "/api/v1/synthetic-user",
    response_model=SyntheticUserResponse,
    summary="Generate a synthetic user profile",
    tags=["Synthetic Data"],
)
def get_synthetic_user(
    locale: Literal["en", "hi", "te"] = "en",
    seed: int | None = None,
) -> SyntheticUserResponse:
    """Generate a realistic but 100% synthetic user with fake PII."""
    user = generate_user(locale=locale, seed=seed)
    return SyntheticUserResponse(
        name=user.name,
        email=user.email,
        phone=user.phone,
        pan=user.pan,
        aadhaar=user.aadhaar,
        upi_id=user.upi_id,
        locale=user.locale,
        monthly_income=user.monthly_income,
        accounts=[
            AccountInfo(
                bank=str(acc.get("bank", "")),
                account_number=str(acc.get("account_number", "")),
                balance=float(acc.get("balance", 0.0)),
                type=str(acc.get("type", "savings")),
            )
            for acc in user.accounts
        ],
    )


@app.post(
    "/api/v1/bootstrap-synthetic",
    response_model=BootstrapSyntheticResponse,
    summary="Bootstrap assistant with synthetic financial profiles",
    tags=["Synthetic Data"],
)
def bootstrap_synthetic(
    request: BootstrapSyntheticRequest,
    assistant: FinanceAssistant = Depends(get_assistant),
) -> BootstrapSyntheticResponse:
    """Generate synthetic user profiles and index their finance summaries."""
    users = generate_users(n=request.count, locale=request.locale)
    total_chunks = 0
    for u in users:
        doc = generate_finance_document(u)
        chunks = assistant.index_document(
            text=doc,
            source=f"synthetic_user_{u.name}",
            metadata={"locale": request.locale, "is_synthetic": True},
        )
        total_chunks += chunks

    return BootstrapSyntheticResponse(
        status="bootstrapped",
        users_created=len(users),
        documents_indexed=len(users),
        chunks_indexed=total_chunks,
    )
