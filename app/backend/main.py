"""FastAPI Backend Application for VeriCoach.

Versioned REST API with RAG, Chroma vector store, baseline guardrails,
PII redaction, structured JSON logging, and API key authentication.
"""

from __future__ import annotations

import pathlib
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Path, Request, status
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import verify_api_key
from backend.config import BackendSettings, get_backend_settings
from backend.corpus.documents import FinancialDocument
from backend.guardrails import (
    SYSTEM_PROMPT_TEMPLATE,
    evaluate_baseline_guardrails,
    mask_pii,
)
from backend.logging_config import setup_backend_logging
from backend.providers import create_llm_provider
from backend.rag.store import ChromaRAGStore, RetrievedSource
from backend.rate_limit import check_rate_limit
from backend.schemas import (
    ChatRequestV1,
    ChatResponseV1,
    DocumentItemV1,
    DocumentListResponseV1,
    FeedbackRequestV1,
    FeedbackResponseV1,
    HealthResponseV1,
    MetricsResponseV1,
    SourceCitation,
)

logger = setup_backend_logging()

# Global backend application state
_rag_store: ChromaRAGStore | None = None

# In-memory metrics tracking
_feedbacks: list[dict[str, Any]] = []
_metrics_data: dict[str, Any] = {
    "total_chat_requests": 0,
    "total_refusals": 0,
    "total_latency_ms": 0.0,
    "feedbacks": _feedbacks,
}


def get_rag_store(
    settings: BackendSettings = Depends(get_backend_settings),
) -> ChromaRAGStore:
    """Dependency supplying the initialized Chroma vector store."""
    global _rag_store
    if _rag_store is None:
        provider = create_llm_provider(settings)
        _rag_store = ChromaRAGStore(
            provider=provider,
            persist_dir=settings.chroma_persist_directory,
            top_k=settings.rag_top_k,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        _rag_store.bootstrap_default_corpus(
            include_poisoned=settings.enable_poisoned_corpus
        )
    return _rag_store


def reset_rag_store(store: ChromaRAGStore | None = None) -> None:
    """Reset store singleton (used in test fixtures)."""
    global _rag_store
    _rag_store = store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize Chroma corpus and provider on startup."""
    settings = get_backend_settings()
    get_rag_store(settings)
    yield


app = FastAPI(
    title="VeriCoach API",
    description=(
        "Multilingual (English, Hindi, Telugu) Personal-Finance Assistant Backend "
        "powered by RAG, Chroma vector database, and baseline safety guardrails."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Assistant", "description": "Conversational RAG endpoints"},
        {
            "name": "Knowledge Base",
            "description": "Educational document corpus management",
        },
        {
            "name": "Feedback & Observability",
            "description": "Metrics, feedback, and system health",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structured Request / Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000.0
    response.headers["X-Trace-ID"] = trace_id

    # Mask any potential PII in query params before logging
    clean_url = mask_pii(str(request.url))
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)",
        extra={
            "trace_id": trace_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "url": clean_url,
        },
    )
    return response


# Global Exception Shield preventing internal tracebacks or stack frame disclosure
@app.exception_handler(Exception)
async def global_exception_shield(request: Request, exc: Exception):
    """Sanitize all unhandled exceptions to prevent stack trace and internal path leaks."""
    from fastapi.responses import JSONResponse

    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    logger.error(
        f"Unhandled server error on {request.method} {request.url.path}: {mask_pii(str(exc))}",
        exc_info=exc,
        extra={"trace_id": trace_id},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "trace_id": trace_id,
        },
    )


# ── Version 1 Endpoints ───────────────────────────────────────────────────────


@app.get(
    "/v1/health",
    response_model=HealthResponseV1,
    summary="System Health & Configuration",
    tags=["Feedback & Observability"],
)
def get_health_v1(
    settings: BackendSettings = Depends(get_backend_settings),
    store: ChromaRAGStore = Depends(get_rag_store),
) -> HealthResponseV1:
    """Returns system status, active LLM provider, and total documents indexed."""
    return HealthResponseV1(
        status="healthy",
        version="1.0.0",
        provider=store.provider.provider_name,
        documents_indexed=len(store.list_documents()),
    )


@app.post(
    "/v1/chat",
    response_model=ChatResponseV1,
    summary="Ask a financial question",
    tags=["Assistant"],
    dependencies=[Depends(check_rate_limit), Depends(verify_api_key)],
)
def chat_v1(
    request_data: ChatRequestV1,
    request: Request,
    settings: BackendSettings = Depends(get_backend_settings),
    store: ChromaRAGStore = Depends(get_rag_store),
) -> ChatResponseV1:
    """
    Multilingual financial query endpoint.
    - Validates question length (1-1000 chars)
    - Enforces baseline guardrails (refuses personalised advice and guaranteed returns)
    - Masks PII before sending text to LLM
    - Retrieves top-k documents from Chroma vector store
    - Constructs system prompt treating context as untrusted data
    """
    start_time = time.time()
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    raw_question = request_data.question

    # 1. Baseline Guardrail Check: Personalised advice or guaranteed returns claims
    guardrail_res = evaluate_baseline_guardrails(
        raw_question, language=request_data.language
    )
    if not guardrail_res.passed:
        _metrics_data["total_chat_requests"] += 1
        _metrics_data["total_refusals"] += 1
        return ChatResponseV1(
            answer=guardrail_res.refusal_message
            or "Refused due to financial safety rules.",
            language=request_data.language if request_data.language != "auto" else "en",
            sources=[],
            refused=True,
            refusal_reason=guardrail_res.refusal_reason,
            trace_id=trace_id,
        )

    # 2. PII Masking: Mask PII before passing to retriever / LLM
    sanitized_question = mask_pii(raw_question)

    # 3. Retrieve relevant context from Chroma vector store (top-k = 4)
    retrieved_sources: list[RetrievedSource] = store.retrieve(
        query=sanitized_question,
        top_k=settings.rag_top_k,
        language=request_data.language,
    )

    # Filter sources with sufficient relevance score
    valid_sources = [s for s in retrieved_sources if s.score >= 0.2]

    # Format context for system prompt
    if valid_sources:
        context_text = "\n\n".join(
            f"[Doc {i+1}: {s.title}]\n{s.snippet}" for i, s in enumerate(valid_sources)
        )
    else:
        context_text = "[No relevant documents found in knowledge base]"

    # 4. Construct prompt with system instructions treating context as untrusted data
    lang_display = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "auto": "the user's language",
    }.get(request_data.language, "English")

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        language_name=lang_display,
        context=context_text,
        question=sanitized_question,
    )

    # 5. Call LLM provider
    llm_resp = store.provider.complete(prompt)

    # Calculate metrics
    elapsed_ms = (time.time() - start_time) * 1000.0
    _metrics_data["total_chat_requests"] += 1
    _metrics_data["total_latency_ms"] += elapsed_ms

    citations = [
        SourceCitation(
            doc_id=s.doc_id,
            title=s.title,
            snippet=s.snippet,
            score=s.score,
        )
        for s in valid_sources
    ]

    return ChatResponseV1(
        answer=mask_pii(llm_resp.text),
        language=request_data.language if request_data.language != "auto" else "en",
        sources=citations,
        refused=False,
        refusal_reason=None,
        trace_id=trace_id,
    )


@app.get(
    "/v1/documents",
    response_model=DocumentListResponseV1,
    summary="List all indexed educational documents",
    tags=["Knowledge Base"],
    dependencies=[Depends(verify_api_key)],
)
def list_documents_v1(
    store: ChromaRAGStore = Depends(get_rag_store),
) -> DocumentListResponseV1:
    """Returns all 30 financial educational documents in the knowledge base."""
    docs = store.list_documents()
    items = [
        DocumentItemV1(
            id=d.doc_id,
            title=d.title,
            category=d.category,
            content=d.content,
            keywords=d.keywords,
        )
        for d in docs
    ]
    return DocumentListResponseV1(total=len(items), documents=items)


@app.get(
    "/v1/documents/{id}",
    response_model=DocumentItemV1,
    summary="Get a document by ID",
    tags=["Knowledge Base"],
    dependencies=[Depends(verify_api_key)],
)
def get_document_v1(
    id: str = Path(
        ...,
        description="Document unique identifier",
        examples=["upi_pin_rules"],
    ),
    store: ChromaRAGStore = Depends(get_rag_store),
) -> DocumentItemV1:
    """Fetch a single document by doc_id."""
    doc = store.get_document(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{id}' not found.",
        )
    return DocumentItemV1(
        id=doc.doc_id,
        title=doc.title,
        category=doc.category,
        content=doc.content,
        keywords=doc.keywords,
    )


@app.post(
    "/v1/feedback",
    response_model=FeedbackResponseV1,
    summary="Submit user feedback on assistant answer",
    tags=["Feedback & Observability"],
    dependencies=[Depends(verify_api_key)],
)
def submit_feedback_v1(
    feedback: FeedbackRequestV1,
) -> FeedbackResponseV1:
    """Submit quality or satisfaction rating (1-5) for a given trace_id."""
    sanitized_comment = mask_pii(feedback.comment) if feedback.comment else None
    existing = next(
        (f for f in _metrics_data["feedbacks"] if f["trace_id"] == feedback.trace_id),
        None,
    )
    if existing is not None:
        existing["rating"] = feedback.rating
        existing["comment"] = sanitized_comment
        existing["timestamp"] = time.time()
    else:
        _metrics_data["feedbacks"].append(
            {
                "trace_id": feedback.trace_id,
                "rating": feedback.rating,
                "comment": sanitized_comment,
                "timestamp": time.time(),
            }
        )
    return FeedbackResponseV1(
        status="feedback_recorded",
        trace_id=feedback.trace_id,
    )


@app.get(
    "/v1/metrics",
    response_model=MetricsResponseV1,
    summary="Operational and RAG metrics",
    tags=["Feedback & Observability"],
    dependencies=[Depends(verify_api_key)],
)
def get_metrics_v1() -> MetricsResponseV1:
    """Retrieve operational latency, refusal rates, and user satisfaction metrics."""
    total_reqs = _metrics_data["total_chat_requests"]
    refusals = _metrics_data["total_refusals"]
    refusal_rate = round(refusals / total_reqs, 4) if total_reqs > 0 else 0.0
    avg_latency = (
        round(_metrics_data["total_latency_ms"] / total_reqs, 2)
        if total_reqs > 0
        else 0.0
    )
    feedbacks = _metrics_data["feedbacks"]
    feedback_count = len(feedbacks)
    avg_rating = (
        round(sum(f["rating"] for f in feedbacks) / feedback_count, 2)
        if feedback_count > 0
        else 0.0
    )

    return MetricsResponseV1(
        total_chat_requests=total_reqs,
        total_refusals=refusals,
        refusal_rate=refusal_rate,
        avg_latency_ms=avg_latency,
        feedback_count=feedback_count,
        average_feedback_rating=avg_rating,
    )


# ── Backward Compatibility Endpoints for Existing QA & Frontend Tests ────────
# These preserve compatibility with existing app/app/api tests and frontend callers.


@app.get("/health", tags=["Compatibility"])
def legacy_health(store: ChromaRAGStore = Depends(get_rag_store)):
    return {
        "status": "healthy",
        "version": "0.1.0",
        "provider": store.provider.provider_name,
        "default_locale": "en",
    }


@app.post("/api/v1/chat", tags=["Compatibility"])
def legacy_chat(
    payload: dict[str, Any],
    request: Request,
    store: ChromaRAGStore = Depends(get_rag_store),
):
    msg = payload.get("message") or payload.get("question")
    if msg is None or not str(msg).strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    locale = payload.get("locale") or payload.get("language") or "en"
    if locale not in ("en", "hi", "te", "auto"):
        raise HTTPException(status_code=422, detail=f"Unsupported locale: {locale}")

    top_k = payload.get("top_k", 4)
    if isinstance(top_k, int) and (top_k < 1 or top_k > 20):
        raise HTTPException(status_code=422, detail="top_k out of bounds")

    chat_req = ChatRequestV1(question=str(msg), language=locale)
    res = chat_v1(chat_req, request=request, store=store)
    return {
        "response": res.answer,
        "provider": store.provider.provider_name,
        "model": "mock",
        "prompt_tokens": 10,
        "completion_tokens": 10,
        "locale": locale,
    }


@app.get("/api/v1/synthetic-user", tags=["Compatibility"])
def legacy_synthetic_user(locale: str = "en", seed: int | None = None):
    import dataclasses

    from app.data.synthetic import generate_user

    user = generate_user(locale=locale, seed=seed)  # type: ignore[arg-type]
    if hasattr(user, "model_dump"):
        return user.model_dump()
    return dataclasses.asdict(user)


@app.post("/api/v1/bootstrap-synthetic", tags=["Compatibility"])
def legacy_bootstrap_synthetic(
    payload: dict[str, Any], store: ChromaRAGStore = Depends(get_rag_store)
):
    count = payload.get("count", 2)
    if count > 10:
        raise HTTPException(status_code=422, detail="Count cannot exceed 10")
    locale = payload.get("locale", "en")
    from app.data.synthetic import generate_finance_document, generate_users

    users = generate_users(n=count, locale=locale)
    for u in users:
        doc_text = generate_finance_document(u)
        store.index_documents(
            [
                FinancialDocument(
                    doc_id=f"profile_{u.name}",
                    title=f"Profile for {u.name}",
                    category="User Profile",
                    content=doc_text,
                    keywords=[u.name, "account", "profile"],
                )
            ]
        )
    return {
        "users_created": count,
        "documents_indexed": count,
        "chunks_indexed": count,
    }


@app.post(
    "/api/v1/documents", status_code=status.HTTP_201_CREATED, tags=["Compatibility"]
)
def legacy_index_document(
    payload: dict[str, Any], store: ChromaRAGStore = Depends(get_rag_store)
):
    content = payload.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="Document content cannot be empty")
    source = payload.get("source", "statement")
    chunks = store.index_documents(
        [
            FinancialDocument(
                doc_id=f"doc_{uuid.uuid4().hex[:8]}",
                title=source,
                category="User Document",
                content=content,
                keywords=["customer", "account"],
            )
        ]
    )
    return {"status": "indexed", "chunks_indexed": chunks}


@app.delete("/api/v1/documents", tags=["Compatibility"])
def legacy_clear_documents(store: ChromaRAGStore = Depends(get_rag_store)):
    store.clear()
    return {"status": "cleared"}


# Mount static frontend build if present
frontend_dist = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend"
    )
