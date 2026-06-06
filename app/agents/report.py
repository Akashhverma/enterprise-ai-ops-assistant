from __future__ import annotations

from collections import Counter
from typing import Any

from .config import get_agent_runtime_config, openai_is_configured
from .models import AgentOutput, Citation, EvidenceItem, FinalReport, PlannerOutput


class ReportAgent:
    def run(
        self,
        *,
        question: str,
        plan: PlannerOutput,
        ticket_output: AgentOutput,
        document_output: AgentOutput,
        log_output: AgentOutput,
        graph_errors: list[str],
    ) -> FinalReport:
        evidence = ticket_output.evidence + document_output.evidence + log_output.evidence
        errors = graph_errors + ticket_output.errors + document_output.errors + log_output.errors

        if openai_is_configured():
            llm_report = self._report_with_llm(
                question=question,
                plan=plan,
                ticket_output=ticket_output,
                document_output=document_output,
                log_output=log_output,
                errors=errors,
            )
            if llm_report is not None:
                return llm_report

        return self._deterministic_report(
            question=question,
            plan=plan,
            ticket_output=ticket_output,
            document_output=document_output,
            log_output=log_output,
            evidence=evidence,
            errors=errors,
        )

    def _report_with_llm(
        self,
        *,
        question: str,
        plan: PlannerOutput,
        ticket_output: AgentOutput,
        document_output: AgentOutput,
        log_output: AgentOutput,
        errors: list[str],
    ) -> FinalReport | None:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return None

        config = get_agent_runtime_config()
        model = ChatOpenAI(model=config.model_name, temperature=config.temperature)
        structured_model = model.with_structured_output(FinalReport, method="json_schema")
        prompt = (
            "You are the report agent for an enterprise AI operations assistant. "
            "Use only the provided evidence. Do not invent source IDs or facts. "
            "Return a concise structured final report.\n\n"
            f"Question: {question}\n"
            f"Plan: {plan.model_dump()}\n"
            f"Ticket Evidence: {ticket_output.model_dump()}\n"
            f"Document Evidence: {document_output.model_dump()}\n"
            f"Log Evidence: {log_output.model_dump()}\n"
            f"Errors: {errors}"
        )

        try:
            result = structured_model.invoke(prompt)
        except Exception:
            return None

        if isinstance(result, FinalReport):
            return result

        if isinstance(result, dict):
            return FinalReport.model_validate(result)

        return None

    def _deterministic_report(
        self,
        *,
        question: str,
        plan: PlannerOutput,
        ticket_output: AgentOutput,
        document_output: AgentOutput,
        log_output: AgentOutput,
        evidence: list[EvidenceItem],
        errors: list[str],
    ) -> FinalReport:
        top_evidence = sorted(evidence, key=lambda item: item.relevance_score, reverse=True)[:10]
        source_counts = Counter(item.source_type for item in evidence)
        citations = [
            Citation(source_type=item.source_type, source_id=item.source_id, title=item.title)
            for item in top_evidence[:8]
        ]
        confidence = _confidence(evidence_count=len(evidence), error_count=len(errors))
        answer = _build_answer(
            plan=plan,
            tickets=ticket_output.evidence,
            documents=document_output.evidence,
            logs=log_output.evidence,
        )

        return FinalReport(
            question=question,
            intent=plan.intent,
            answer=answer,
            confidence=confidence,
            citations=citations,
            source_summary={
                "tickets": f"{source_counts.get('ticket', 0)} relevant ticket records. {ticket_output.summary}",
                "documents": f"{source_counts.get('document', 0)} relevant project documents. {document_output.summary}",
                "logs": f"{source_counts.get('log', 0)} relevant deployment log records. {log_output.summary}",
            },
            next_actions=_next_actions(plan, ticket_output.evidence, document_output.evidence, log_output.evidence),
            errors=errors,
        )


def _confidence(*, evidence_count: int, error_count: int) -> str:
    if evidence_count >= 6 and error_count == 0:
        return "high"
    if evidence_count >= 3:
        return "medium"
    return "low"


def _build_answer(
    *,
    plan: PlannerOutput,
    tickets: list[EvidenceItem],
    documents: list[EvidenceItem],
    logs: list[EvidenceItem],
) -> str:
    if not any([tickets, documents, logs]):
        return (
            "I could not find matching ticket, document, or deployment log evidence for this question. "
            "Try adding a ticket ID, service name, environment, deployment ID, or failure type."
        )

    parts: list[str] = []

    if tickets:
        high_value = tickets[:3]
        statuses = ", ".join(
            f"{item.source_id} is {item.metadata.get('status')} / {item.metadata.get('priority')}"
            for item in high_value
        )
        parts.append(f"Ticket evidence shows {statuses}.")

    if logs:
        causes = [
            str(item.metadata.get("probable_cause"))
            for item in logs[:3]
            if item.metadata.get("probable_cause")
        ]
        if causes:
            parts.append("Log evidence points to: " + "; ".join(dict.fromkeys(causes)) + ".")
        else:
            parts.append(f"Log evidence includes {len(logs)} matching deployment/runtime events.")

    if documents:
        doc_summaries = [
            f"{item.source_id} ({item.metadata.get('document_type')})"
            for item in documents[:3]
        ]
        parts.append("Document evidence to consult: " + ", ".join(doc_summaries) + ".")

    if plan.intent == "root_cause_analysis":
        parts.append("Likely root-cause confidence depends on correlating timestamps, affected service, and linked tickets.")
    elif plan.intent == "blocker_analysis":
        parts.append("The main operational risk is unresolved dependency or blocked-ticket flow.")

    return " ".join(parts)


def _next_actions(
    plan: PlannerOutput,
    tickets: list[EvidenceItem],
    documents: list[EvidenceItem],
    logs: list[EvidenceItem],
) -> list[str]:
    actions: list[str] = []

    if logs:
        remediation_hints = [
            str(item.metadata.get("remediation_hint"))
            for item in logs
            if item.metadata.get("remediation_hint")
        ]
        actions.extend(list(dict.fromkeys(remediation_hints))[:2])

    blocked_tickets = [
        item
        for item in tickets
        if item.metadata.get("status") == "Blocked"
        or str(item.metadata.get("dependency", "")).casefold() != "none"
    ]
    if blocked_tickets:
        actions.append("Review blocked tickets and confirm dependency owners before closing the incident.")

    if documents:
        actions.append("Check the cited runbook, release plan, or incident report before applying remediation.")

    if not actions:
        actions.append("Run a more specific query with service, environment, ticket ID, or deployment ID.")

    if plan.intent == "root_cause_analysis":
        actions.append("Validate the proposed cause against trace timestamps and deployment windows.")

    return actions[:5]

