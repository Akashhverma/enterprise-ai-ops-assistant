from __future__ import annotations

from typing import Any

from .config import get_agent_runtime_config
from .mcp_tool_client import MCPToolClient, ServerName
from .models import AgentOutput, EvidenceItem, PlannerOutput, SourcePlan, ToolCallRecord


class TicketAgent:
    def __init__(self, tool_client: MCPToolClient) -> None:
        self._tool_client = tool_client
        self._limit = get_agent_runtime_config().retrieval_limit

    def run(self, plan: PlannerOutput) -> AgentOutput:
        if not plan.ticket_plan.enabled:
            return _skipped("ticket_agent", plan.ticket_plan.reason)

        evidence: list[EvidenceItem] = []
        calls: list[ToolCallRecord] = []
        errors: list[str] = []

        for ticket_id in plan.entities.ticket_ids:
            result, call = self._call("get_ticket_by_id", {"ticket_id": ticket_id})
            calls.append(call)
            if result and "ticket" in result:
                evidence.append(_ticket_to_evidence(result["ticket"], relevance_score=1.5))
            elif call.error:
                errors.append(call.error)

        search_args = {"query": plan.ticket_plan.query, "limit": self._limit}
        search_args.update(_known_filters(plan.ticket_plan, ["priority", "status", "owner"]))
        result, call = self._call("search_tickets", search_args)
        calls.append(call)
        _append_ticket_results(result, evidence)
        _append_call_error(call, errors)

        if "list_open_tickets" in plan.ticket_plan.preferred_tools:
            args = {"limit": self._limit}
            args.update(_known_filters(plan.ticket_plan, ["priority", "owner"]))
            result, call = self._call("list_open_tickets", args)
            calls.append(call)
            _append_ticket_results(result, evidence)
            _append_call_error(call, errors)

        if "list_blockers" in plan.ticket_plan.preferred_tools:
            result, call = self._call("list_blockers", {"limit": self._limit})
            calls.append(call)
            _append_ticket_results(result, evidence)
            _append_call_error(call, errors)

        evidence = _dedupe_evidence(evidence)
        return _agent_output(
            agent_name="ticket_agent",
            evidence=evidence,
            tool_calls=calls,
            errors=errors,
            success_summary=f"Found {len(evidence)} ticket evidence records.",
            empty_summary="No matching ticket evidence found.",
        )

    def _call(self, tool_name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any] | None, ToolCallRecord]:
        return self._tool_client.call_tool("ticket", tool_name, arguments)


class DocumentAgent:
    def __init__(self, tool_client: MCPToolClient) -> None:
        self._tool_client = tool_client
        self._limit = get_agent_runtime_config().retrieval_limit

    def run(self, plan: PlannerOutput) -> AgentOutput:
        if not plan.document_plan.enabled:
            return _skipped("document_agent", plan.document_plan.reason)

        evidence: list[EvidenceItem] = []
        calls: list[ToolCallRecord] = []
        errors: list[str] = []

        for document_id in plan.entities.document_ids:
            result, call = self._call("get_document", {"document_id": document_id})
            calls.append(call)
            if result and "document" in result:
                evidence.append(_document_to_evidence(result["document"], relevance_score=1.5))
            elif call.error:
                errors.append(call.error)

        search_args = {"query": plan.document_plan.query, "limit": self._limit}
        search_args.update(_known_filters(plan.document_plan, ["document_type", "service", "environment"]))
        result, call = self._call("search_documents", search_args)
        calls.append(call)
        _append_document_results(result, evidence)
        _append_call_error(call, errors)

        evidence = _dedupe_evidence(evidence)
        return _agent_output(
            agent_name="document_agent",
            evidence=evidence,
            tool_calls=calls,
            errors=errors,
            success_summary=f"Found {len(evidence)} document evidence records.",
            empty_summary="No matching project document evidence found.",
        )

    def _call(self, tool_name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any] | None, ToolCallRecord]:
        return self._tool_client.call_tool("document", tool_name, arguments)


class LogAgent:
    def __init__(self, tool_client: MCPToolClient) -> None:
        self._tool_client = tool_client
        self._limit = get_agent_runtime_config().retrieval_limit

    def run(self, plan: PlannerOutput) -> AgentOutput:
        if not plan.log_plan.enabled:
            return _skipped("log_agent", plan.log_plan.reason)

        evidence: list[EvidenceItem] = []
        calls: list[ToolCallRecord] = []
        errors: list[str] = []

        search_args = {"query": plan.log_plan.query, "limit": self._limit}
        search_args.update(
            _known_filters(
                plan.log_plan,
                ["log_type", "severity", "service", "environment", "since", "until"],
            )
        )
        result, call = self._call("search_logs", search_args)
        calls.append(call)
        _append_log_results(result, evidence)
        _append_call_error(call, errors)

        if "get_recent_failures" in plan.log_plan.preferred_tools:
            failure_args = {"limit": self._limit}
            failure_args.update(_known_filters(plan.log_plan, ["service", "environment"]))
            result, call = self._call("get_recent_failures", failure_args)
            calls.append(call)
            _append_log_results(result, evidence)
            _append_call_error(call, errors)

        evidence = _dedupe_evidence(evidence)
        return _agent_output(
            agent_name="log_agent",
            evidence=evidence,
            tool_calls=calls,
            errors=errors,
            success_summary=f"Found {len(evidence)} deployment log evidence records.",
            empty_summary="No matching deployment log evidence found.",
        )

    def _call(self, tool_name: str, arguments: dict[str, Any]) -> tuple[dict[str, Any] | None, ToolCallRecord]:
        return self._tool_client.call_tool("log", tool_name, arguments)


def _known_filters(source_plan: SourcePlan, accepted: list[str]) -> dict[str, Any]:
    return {
        key: value
        for key, value in source_plan.filters.items()
        if key in accepted and value not in (None, "")
    }


def _append_call_error(call: ToolCallRecord, errors: list[str]) -> None:
    if call.status == "failed" and call.error:
        errors.append(f"{call.server}.{call.tool_name}: {call.error}")


def _append_ticket_results(result: dict[str, Any] | None, evidence: list[EvidenceItem]) -> None:
    if not result:
        return

    for ticket in result.get("results", []):
        evidence.append(_ticket_to_evidence(ticket, relevance_score=float(ticket.get("relevance_score", 0.0))))


def _append_document_results(result: dict[str, Any] | None, evidence: list[EvidenceItem]) -> None:
    if not result:
        return

    for document in result.get("results", []):
        evidence.append(
            _document_to_evidence(document, relevance_score=float(document.get("relevance_score", 0.0)))
        )


def _append_log_results(result: dict[str, Any] | None, evidence: list[EvidenceItem]) -> None:
    if not result:
        return

    for log in result.get("results", []):
        evidence.append(_log_to_evidence(log, relevance_score=float(log.get("relevance_score", 0.0))))


def _ticket_to_evidence(ticket: dict[str, Any], *, relevance_score: float) -> EvidenceItem:
    return EvidenceItem(
        source_type="ticket",
        source_id=str(ticket["ticket_id"]),
        title=str(ticket["title"]),
        snippet=str(ticket["description"]),
        relevance_score=relevance_score,
        metadata={
            "priority": ticket.get("priority"),
            "status": ticket.get("status"),
            "owner": ticket.get("owner"),
            "dependency": ticket.get("dependency"),
            "created_date": ticket.get("created_date"),
        },
    )


def _document_to_evidence(document: dict[str, Any], *, relevance_score: float) -> EvidenceItem:
    sections = document.get("sections", [])
    section_text = " ".join(
        f"{section.get('heading', '')}: {section.get('body', '')}"
        for section in sections
        if isinstance(section, dict)
    )
    return EvidenceItem(
        source_type="document",
        source_id=str(document["document_id"]),
        title=str(document["title"]),
        snippet=section_text,
        relevance_score=relevance_score,
        metadata={
            "document_type": document.get("document_type"),
            "service": document.get("service"),
            "environment": document.get("environment"),
            "owner_team": document.get("owner_team"),
            "version": document.get("version"),
            "related_ticket_ids": document.get("related_ticket_ids", []),
        },
    )


def _log_to_evidence(log: dict[str, Any], *, relevance_score: float) -> EvidenceItem:
    return EvidenceItem(
        source_type="log",
        source_id=str(log["log_id"]),
        title=f"{log.get('log_type', 'log')} for {log.get('service', 'unknown-service')}",
        snippet=str(log["message"]),
        relevance_score=relevance_score,
        metadata={
            "deployment_id": log.get("deployment_id"),
            "service": log.get("service"),
            "environment": log.get("environment"),
            "severity": log.get("severity"),
            "status": log.get("status"),
            "timestamp": log.get("timestamp"),
            "error_code": log.get("error_code"),
            "related_ticket_id": log.get("related_ticket_id"),
            "probable_cause": log.get("probable_cause"),
            "remediation_hint": log.get("remediation_hint"),
        },
    )


def _dedupe_evidence(evidence: list[EvidenceItem]) -> list[EvidenceItem]:
    seen: set[tuple[str, str]] = set()
    deduped: list[EvidenceItem] = []

    for item in sorted(evidence, key=lambda evidence_item: evidence_item.relevance_score, reverse=True):
        key = (item.source_type, item.source_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def _skipped(agent_name: str, reason: str) -> AgentOutput:
    return AgentOutput(
        agent_name=agent_name,  # type: ignore[arg-type]
        status="skipped",
        summary=f"Skipped: {reason}",
    )


def _agent_output(
    *,
    agent_name: str,
    evidence: list[EvidenceItem],
    tool_calls: list[ToolCallRecord],
    errors: list[str],
    success_summary: str,
    empty_summary: str,
) -> AgentOutput:
    if evidence and errors:
        status = "partial"
        summary = f"{success_summary} Some tool calls failed."
    elif evidence:
        status = "success"
        summary = success_summary
    elif errors:
        status = "failed"
        summary = "Retrieval failed before useful evidence was found."
    else:
        status = "success"
        summary = empty_summary

    return AgentOutput(
        agent_name=agent_name,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        summary=summary,
        evidence=evidence,
        tool_calls=tool_calls,
        errors=errors,
    )

