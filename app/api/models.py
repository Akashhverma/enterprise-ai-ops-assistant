from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agents.models import FinalReport


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    include_debug: bool = Field(
        default=False,
        description="Include agent/tool debug state in the response.",
    )


class QueryResponse(BaseModel):
    request_id: str
    duration_ms: int
    report: FinalReport
    debug: dict[str, Any] | None = None


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    session_id: str | None = Field(default=None, max_length=120)
    include_debug: bool = False


class ChatResponse(BaseModel):
    request_id: str
    session_id: str | None = None
    message: ChatMessage
    report: FinalReport
    duration_ms: int
    debug: dict[str, Any] | None = None


class TicketRecord(BaseModel):
    ticket_id: str
    title: str
    description: str
    priority: str
    status: str
    owner: str
    dependency: str
    created_date: str
    relevance_score: float | None = None
    matched_fields: list[str] | None = None
    blocker_reason: str | None = None


class TicketListResponse(BaseModel):
    count: int
    total_matches: int
    results: list[TicketRecord]
    filters: dict[str, Any] = Field(default_factory=dict)


class LogRecord(BaseModel):
    log_id: str
    log_type: str
    deployment_id: str
    project: str
    service: str
    environment: str
    severity: str
    status: str
    timestamp: str
    error_code: str
    message: str
    trace_id: str
    related_ticket_id: str
    probable_cause: str
    remediation_hint: str
    relevance_score: float | None = None
    matched_fields: list[str] | None = None


class LogListResponse(BaseModel):
    count: int
    total_matches: int
    results: list[LogRecord]
    filters: dict[str, Any] = Field(default_factory=dict)

