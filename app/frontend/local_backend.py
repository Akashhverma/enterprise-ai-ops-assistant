from __future__ import annotations

import time
import uuid
from typing import Any

from app.agents.graph import build_ops_assistant_graph
from app.agents.models import FinalReport
from app.agents.state import empty_state
from mcp_servers.common.repository import EnterpriseDatasetRepository


class LocalFrontendBackend:
    def __init__(self) -> None:
        self._graph = build_ops_assistant_graph()
        self._repository = EnterpriseDatasetRepository()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "Enterprise AI Operations Assistant",
            "version": "0.1.0",
            "environment": "local",
        }

    def dataset_summary(self) -> dict[str, int]:
        return {
            "tickets": len(self._repository.tickets()),
            "documents": len(self._repository.documents()),
            "logs": len(self._repository.logs()),
        }

    def run_query(self, question: str, *, include_debug: bool = True) -> dict[str, Any]:
        request_id = f"local-{uuid.uuid4()}"
        started = time.perf_counter()
        final_state = self._graph.invoke(empty_state(question))
        duration_ms = int((time.perf_counter() - started) * 1000)
        report = FinalReport.model_validate(final_state["final_report"])

        debug = {
            "plan": final_state.get("plan"),
            "ticket_agent": final_state.get("ticket_agent"),
            "document_agent": final_state.get("document_agent"),
            "log_agent": final_state.get("log_agent"),
            "tool_calls": final_state.get("tool_calls", []),
            "errors": final_state.get("errors", []),
            "started_at": final_state.get("started_at"),
            "completed_at": final_state.get("completed_at"),
        }

        return {
            "request_id": request_id,
            "duration_ms": duration_ms,
            "report": report.model_dump(),
            "debug": debug if include_debug else None,
        }

    def list_tickets(
        self,
        *,
        query: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        owner: str | None = None,
        blockers_only: bool = False,
        limit: int = 25,
    ) -> dict[str, Any]:
        if blockers_only:
            return self._repository.list_blockers(owner=owner, limit=limit)

        if query or priority or status or owner:
            return self._repository.search_tickets(
                query=query or "",
                priority=priority,
                status=status,
                owner=owner,
                limit=limit,
            )

        return self._repository.list_open_tickets(limit=limit)

    def list_logs(
        self,
        *,
        query: str | None = None,
        log_type: str | None = None,
        severity: str | None = None,
        service: str | None = None,
        environment: str | None = None,
        recent_failures: bool = False,
        limit: int = 25,
    ) -> dict[str, Any]:
        if recent_failures or not any([query, log_type, severity, service, environment]):
            return self._repository.get_recent_failures(
                service=service,
                environment=environment,
                limit=limit,
            )

        return self._repository.search_logs(
            query=query or "",
            log_type=log_type,
            severity=severity,
            service=service,
            environment=environment,
            limit=limit,
        )

    def documents(self) -> list[dict[str, Any]]:
        return self._repository.documents()

