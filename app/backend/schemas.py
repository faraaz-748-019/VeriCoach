"""Pydantic request and response schemas with rich OpenAPI examples."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LanguageType = Literal["en", "hi", "te", "auto"]


class SourceCitation(BaseModel):
    doc_id: str = Field(
        description="Unique ID of the retrieved document", examples=["upi_pin_rules"]
    )
    title: str = Field(
        description="Document title",
        examples=["UPI PIN Usage Rules and Receiving Money"],
    )
    snippet: str = Field(
        description="Text snippet from the matched chunk",
        examples=[
            "A UPI PIN is required ONLY when sending money... You NEVER need to enter PIN to receive money."
        ],
    )
    score: float = Field(
        description="Relevance similarity score (0.0 to 1.0)", examples=[0.92]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doc_id": "upi_pin_rules",
                "title": "UPI PIN Usage Rules and Receiving Money",
                "snippet": "A UPI PIN is required ONLY when sending money... You NEVER need to enter PIN to receive money.",
                "score": 0.92,
            }
        }
    )


class ChatRequestV1(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User financial query in English, Hindi, or Telugu (1-1000 characters)",
        examples=["Do I need to enter my UPI PIN to receive money?"],
    )
    language: LanguageType = Field(
        default="auto",
        description="Target language code: 'en' (English), 'hi' (Hindi), 'te' (Telugu), or 'auto'",
        examples=["en"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session tracking ID for multi-turn dialogue",
        examples=["sess_abc123"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Do I need to enter my UPI PIN to receive money?",
                "language": "en",
                "session_id": "sess_user_456",
            }
        }
    )


class ChatResponseV1(BaseModel):
    answer: str = Field(
        description="Educational answer grounded in retrieved verified financial documents",
        examples=[
            "No, you never need to enter your UPI PIN to receive money. UPI PIN is only needed for sending payments."
        ],
    )
    language: str = Field(
        description="Detected or target language code", examples=["en"]
    )
    sources: list[SourceCitation] = Field(
        default_factory=list,
        description="Ranked list of top retrieved document citations (up to top-k=4)",
    )
    refused: bool = Field(
        description="Whether the query was refused due to safety or guardrail rules",
        examples=[False],
    )
    refusal_reason: str | None = Field(
        default=None,
        description="Specific reason code if query was refused (e.g. guaranteed_returns_prohibited)",
        examples=[None],
    )
    trace_id: str = Field(
        description="Unique request tracing ID for logging, auditing, and feedback",
        examples=["b74d6fb2-3784-4861-b4cf-e94025a17684"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "No, you never need to enter your UPI PIN to receive money. A UPI PIN is only required when authorizing a debit from your account.",
                "language": "en",
                "sources": [
                    {
                        "doc_id": "upi_pin_rules",
                        "title": "UPI PIN Usage Rules and Receiving Money",
                        "snippet": "A UPI PIN is required ONLY when sending money or checking your balance. You NEVER need PIN to receive money.",
                        "score": 0.94,
                    }
                ],
                "refused": False,
                "refusal_reason": None,
                "trace_id": "b74d6fb2-3784-4861-b4cf-e94025a17684",
            }
        }
    )


class HealthResponseV1(BaseModel):
    status: str = Field(description="Service status", examples=["healthy"])
    version: str = Field(description="API version", examples=["1.0.0"])
    provider: str = Field(
        description="Active LLM provider (mock, gemini, ollama)", examples=["mock"]
    )
    documents_indexed: int = Field(
        description="Total financial documents currently indexed in Chroma",
        examples=[30],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "provider": "mock",
                "documents_indexed": 30,
            }
        }
    )


class DocumentItemV1(BaseModel):
    id: str = Field(description="Document identifier", examples=["upi_pin_rules"])
    title: str = Field(
        description="Document title",
        examples=["UPI PIN Usage Rules and Receiving Money"],
    )
    category: str = Field(description="Financial category", examples=["UPI Safety"])
    content: str = Field(
        description="Document full text content",
        examples=["A UPI PIN is required ONLY when sending money..."],
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Associated cross-lingual search keywords",
        examples=[["upi", "pin", "qr code", "यूपीआई", "పిన్"]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "upi_pin_rules",
                "title": "UPI PIN Usage Rules and Receiving Money",
                "category": "UPI Safety",
                "content": "A UPI PIN is required ONLY when sending money or checking your account balance...",
                "keywords": ["upi", "pin", "qr code", "यूपीआई", "పిన్"],
            }
        }
    )


class DocumentListResponseV1(BaseModel):
    total: int = Field(description="Total number of documents", examples=[30])
    documents: list[DocumentItemV1] = Field(description="List of indexed documents")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 30,
                "documents": [
                    {
                        "id": "upi_pin_rules",
                        "title": "UPI PIN Usage Rules and Receiving Money",
                        "category": "UPI Safety",
                        "content": "A UPI PIN is required ONLY when sending money...",
                        "keywords": ["upi", "pin"],
                    }
                ],
            }
        }
    )


class FeedbackRequestV1(BaseModel):
    trace_id: str = Field(
        description="Trace ID of the chat turn",
        examples=["b74d6fb2-3784-4861-b4cf-e94025a17684"],
    )
    rating: int = Field(
        ge=1,
        le=5,
        description="Satisfaction rating from 1 (poor) to 5 (excellent)",
        examples=[5],
    )
    comment: str | None = Field(
        default=None,
        description="Optional user commentary",
        examples=["Very clear answer on UPI safety!"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trace_id": "b74d6fb2-3784-4861-b4cf-e94025a17684",
                "rating": 5,
                "comment": "Very clear answer on UPI safety!",
            }
        }
    )


class FeedbackResponseV1(BaseModel):
    status: str = Field(examples=["feedback_recorded"])
    trace_id: str = Field(examples=["b74d6fb2-3784-4861-b4cf-e94025a17684"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "feedback_recorded",
                "trace_id": "b74d6fb2-3784-4861-b4cf-e94025a17684",
            }
        }
    )


class MetricsResponseV1(BaseModel):
    total_chat_requests: int = Field(
        description="Total processed chat requests", examples=[124]
    )
    total_refusals: int = Field(
        description="Total safety guardrail refusals", examples=[6]
    )
    refusal_rate: float = Field(
        description="Ratio of refused requests to total", examples=[0.0484]
    )
    avg_latency_ms: float = Field(
        description="Average processing latency in milliseconds", examples=[42.5]
    )
    feedback_count: int = Field(
        description="Total feedback items received", examples=[18]
    )
    average_feedback_rating: float = Field(
        description="Average satisfaction rating (1-5)", examples=[4.7]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_chat_requests": 124,
                "total_refusals": 6,
                "refusal_rate": 0.0484,
                "avg_latency_ms": 42.5,
                "feedback_count": 18,
                "average_feedback_rating": 4.7,
            }
        }
    )
