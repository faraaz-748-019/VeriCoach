"""Pydantic schemas for the REST API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded"] = "healthy"
    version: str = "0.1.0"
    provider: str
    default_locale: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User query or question")
    locale: Literal["en", "hi", "te"] = Field(
        default="en", description="Conversation locale"
    )
    top_k: int | None = Field(
        default=None, ge=1, le=20, description="Number of context chunks to retrieve"
    )


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    locale: Literal["en", "hi", "te"]


class DocumentIndexRequest(BaseModel):
    content: str = Field(
        ..., min_length=1, description="Document text content to index"
    )
    source: str = Field(default="", description="Identifier or source name of document")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata tags for document"
    )


class DocumentIndexResponse(BaseModel):
    status: str = "indexed"
    chunks_indexed: int
    source: str


class ClearDocumentsResponse(BaseModel):
    status: str = "cleared"
    message: str


class AccountInfo(BaseModel):
    bank: str
    account_number: str
    balance: float
    type: str


class SyntheticUserResponse(BaseModel):
    name: str
    email: str
    phone: str
    pan: str
    aadhaar: str
    upi_id: str
    locale: str
    monthly_income: float
    accounts: list[AccountInfo]


class BootstrapSyntheticRequest(BaseModel):
    locale: Literal["en", "hi", "te"] = "en"
    count: int = Field(default=1, ge=1, le=10)


class BootstrapSyntheticResponse(BaseModel):
    status: str = "bootstrapped"
    users_created: int
    documents_indexed: int
    chunks_indexed: int
