from __future__ import annotations

import re
from typing import Any

from .config import get_agent_runtime_config, openai_is_configured
from .models import PlannerOutput, QueryEntities, SourcePlan


TICKET_ID_PATTERN = re.compile(r"\bAIDASH-\d{4}\b", re.IGNORECASE)
DOCUMENT_ID_PATTERN = re.compile(r"\bDOC-AIDASH-\d{3}\b", re.IGNORECASE)
DEPLOYMENT_ID_PATTERN = re.compile(r"\bDEP-AIDASH-\d{6}-\d{3}\b", re.IGNORECASE)
TRACE_ID_PATTERN = re.compile(r"\btrace-[a-f0-9]{12}\b", re.IGNORECASE)

SERVICES = [
    "dashboard-api",
    "auth-service",
    "telemetry-ingestion",
    "analytics-worker",
    "reporting-service",
    "model-insights-service",
    "notification-service",
    "admin-console",
    "feature-store-sync",
    "vector-search-gateway",
]

ENVIRONMENTS = ["dev", "staging", "production"]
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
STATUSES = ["Backlog", "In Progress", "Blocked", "In Review", "Resolved", "Closed"]


class PlannerAgent:
    def plan(self, question: str) -> PlannerOutput:
        if openai_is_configured():
            llm_plan = self._plan_with_llm(question)
            if llm_plan is not None:
                return llm_plan

        return self._plan_with_rules(question)

    def _plan_with_llm(self, question: str) -> PlannerOutput | None:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return None

        config = get_agent_runtime_config()
        model = ChatOpenAI(model=config.model_name, temperature=config.temperature)
        structured_model = model.with_structured_output(PlannerOutput, method="json_schema")
        prompt = (
            "You are the planner for an enterprise AI operations assistant. "
            "Create a concise retrieval plan over ticket, document, and deployment-log sources. "
            "Enable a source only when it can help answer the question. "
            "Return structured output only.\n\n"
            f"Question: {question}"
        )
        try:
            result = structured_model.invoke(prompt)
        except Exception:
            return None

        if isinstance(result, PlannerOutput):
            return result

        if isinstance(result, dict):
            return PlannerOutput.model_validate(result)

        return None

    def _plan_with_rules(self, question: str) -> PlannerOutput:
        normalized = " ".join(question.strip().split())
        lowered = normalized.lower()
        entities = _extract_entities(normalized)
        search_query = _search_query_from_question(normalized)
        intent = _classify_intent(lowered)

        ticket_needed = _contains_any(
            lowered,
            ["ticket", "jira", "incident", "blocker", "blocked", "dependency", "owner", "priority", "status"],
        ) or bool(entities.ticket_ids)
        document_needed = _contains_any(
            lowered,
            [
                "document",
                "runbook",
                "architecture",
                "meeting",
                "release",
                "release plan",
                "deployment",
                "procedure",
                "incident",
                "postmortem",
            ],
        ) or bool(entities.document_ids)
        log_needed = _contains_any(
            lowered,
            ["log", "deployment", "failure", "timeout", "auth", "migration", "trace", "error", "root cause"],
        ) or bool(entities.deployment_ids or entities.trace_ids)

        if not any([ticket_needed, document_needed, log_needed]):
            ticket_needed = document_needed = log_needed = True

        return PlannerOutput(
            intent=intent,
            normalized_question=normalized,
            entities=entities,
            ticket_plan=SourcePlan(
                enabled=ticket_needed,
                reason="Tickets can show ownership, priority, status, dependencies, and incident context.",
                query=search_query,
                filters=_ticket_filters(entities),
                preferred_tools=_ticket_tools(lowered, entities),
            ),
            document_plan=SourcePlan(
                enabled=document_needed,
                reason="Documents can provide architecture, procedure, release, meeting, and incident context.",
                query=search_query,
                filters=_document_filters(lowered, entities),
                preferred_tools=_document_tools(entities),
            ),
            log_plan=SourcePlan(
                enabled=log_needed,
                reason="Deployment logs can reveal failures, timeouts, migrations, and authentication errors.",
                query=search_query,
                filters=_log_filters(lowered, entities),
                preferred_tools=_log_tools(lowered),
            ),
            answer_requirements=[
                "Summarize evidence from each relevant source.",
                "Call out blockers, likely causes, and remediation steps when evidence supports them.",
                "Include citations to source records.",
                "State uncertainty when evidence is weak or unavailable.",
            ],
        )


def _extract_entities(question: str) -> QueryEntities:
    lowered = question.lower()
    return QueryEntities(
        ticket_ids=sorted({match.upper() for match in TICKET_ID_PATTERN.findall(question)}),
        document_ids=sorted({match.upper() for match in DOCUMENT_ID_PATTERN.findall(question)}),
        deployment_ids=sorted({match.upper() for match in DEPLOYMENT_ID_PATTERN.findall(question)}),
        trace_ids=sorted({match.lower() for match in TRACE_ID_PATTERN.findall(question)}),
        services=[service for service in SERVICES if service in lowered],
        environments=[env for env in ENVIRONMENTS if re.search(rf"\b{re.escape(env)}\b", lowered)],
        priorities=[priority for priority in PRIORITIES if re.search(rf"\b{priority.lower()}\b", lowered)],
        statuses=[status for status in STATUSES if status.lower() in lowered],
    )


def _search_query_from_question(question: str) -> str:
    query = TICKET_ID_PATTERN.sub(" ", question)
    query = DOCUMENT_ID_PATTERN.sub(" ", query)
    query = DEPLOYMENT_ID_PATTERN.sub(" ", query)
    query = TRACE_ID_PATTERN.sub(" ", query)
    return " ".join(query.split()) or question


def _classify_intent(lowered_question: str) -> str:
    if _contains_any(lowered_question, ["root cause", "why", "cause"]):
        return "root_cause_analysis"
    if _contains_any(lowered_question, ["blocker", "blocked", "dependency"]):
        return "blocker_analysis"
    if _contains_any(lowered_question, ["recent", "latest", "failures"]):
        return "recent_failure_review"
    if _contains_any(lowered_question, ["summarize", "summary", "overview"]):
        return "operations_summary"
    return "enterprise_search"


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


def _ticket_filters(entities: QueryEntities) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if entities.priorities:
        filters["priority"] = entities.priorities[0]
    if entities.statuses:
        filters["status"] = entities.statuses[0]
    return filters


def _document_filters(lowered_question: str, entities: QueryEntities) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for document_type in [
        "architecture document",
        "meeting notes",
        "release plan",
        "deployment procedure",
        "incident report",
    ]:
        if document_type.replace(" document", "") in lowered_question:
            filters["document_type"] = document_type
            break
    if entities.services:
        filters["service"] = entities.services[0]
    if entities.environments:
        filters["environment"] = entities.environments[0]
    return filters


def _log_filters(lowered_question: str, entities: QueryEntities) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if "deployment" in lowered_question and "failure" in lowered_question:
        filters["log_type"] = "deployment failure"
    elif "auth" in lowered_question or "sso" in lowered_question:
        filters["log_type"] = "authentication failure"
    elif "migration" in lowered_question or "database" in lowered_question:
        filters["log_type"] = "database migration issue"
    elif "timeout" in lowered_question:
        filters["log_type"] = "api timeout error"

    if "warn" in lowered_question:
        filters["severity"] = "WARN"
    elif "error" in lowered_question or "failure" in lowered_question:
        filters["severity"] = "ERROR"

    if entities.services:
        filters["service"] = entities.services[0]
    if entities.environments:
        filters["environment"] = entities.environments[0]
    return filters


def _ticket_tools(lowered_question: str, entities: QueryEntities) -> list[str]:
    tools = ["search_tickets"]
    if entities.ticket_ids:
        tools.insert(0, "get_ticket_by_id")
    if _contains_any(lowered_question, ["open", "active", "status"]):
        tools.append("list_open_tickets")
    if _contains_any(lowered_question, ["blocker", "blocked", "dependency"]):
        tools.append("list_blockers")
    return tools


def _document_tools(entities: QueryEntities) -> list[str]:
    tools = ["search_documents"]
    if entities.document_ids:
        tools.insert(0, "get_document")
    return tools


def _log_tools(lowered_question: str) -> list[str]:
    tools = ["search_logs"]
    if _contains_any(lowered_question, ["recent", "latest", "failure", "failed", "root cause"]):
        tools.append("get_recent_failures")
    return tools
