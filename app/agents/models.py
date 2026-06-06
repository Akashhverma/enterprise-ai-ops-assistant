from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AgentName = Literal["planner", "ticket_agent", "document_agent", "log_agent", "report_agent"]
AgentStatus = Literal["success", "partial", "failed", "skipped"]


class QueryEntities(BaseModel):
    ticket_ids: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    deployment_ids: list[str] = Field(default_factory=list)
    trace_ids: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    environments: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)


class SourcePlan(BaseModel):
    enabled: bool
    reason: str
    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    preferred_tools: list[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    intent: str
    normalized_question: str
    entities: QueryEntities = Field(default_factory=QueryEntities)
    ticket_plan: SourcePlan
    document_plan: SourcePlan
    log_plan: SourcePlan
    answer_requirements: list[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    server: Literal["ticket", "document", "log"]
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: Literal["success", "failed"]
    attempts: int
    result_count: int | None = None
    error: str | None = None


class EvidenceItem(BaseModel):
    source_type: Literal["ticket", "document", "log"]
    source_id: str
    title: str
    snippet: str
    relevance_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent_name: AgentName
    status: AgentStatus
    summary: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    source_type: Literal["ticket", "document", "log"]
    source_id: str
    title: str


class FinalReport(BaseModel):
    question: str
    intent: str
    answer: str
    confidence: Literal["high", "medium", "low"]
    citations: list[Citation] = Field(default_factory=list)
    source_summary: dict[str, str] = Field(default_factory=dict)
    next_actions: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

