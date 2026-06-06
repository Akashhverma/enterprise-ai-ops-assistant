from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Any

from app.agents.graph import build_ops_assistant_graph
from app.agents.models import FinalReport
from app.agents.state import empty_state
from app.core.logging import configure_api_logging


logger = configure_api_logging()


@dataclass(frozen=True)
class WorkflowResult:
    request_id: str
    duration_ms: int
    report: FinalReport
    debug: dict[str, Any]


class LangGraphWorkflowService:
    def __init__(self) -> None:
        self._graph = build_ops_assistant_graph()

    async def run_question(self, question: str) -> WorkflowResult:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()
        logger.info("workflow_start request_id=%s", request_id)

        final_state = await asyncio.to_thread(self._graph.invoke, empty_state(question))
        duration_ms = int((time.perf_counter() - start) * 1000)

        final_report = final_state.get("final_report")
        if not final_report:
            raise RuntimeError("LangGraph workflow completed without a final_report.")

        report = FinalReport.model_validate(final_report)
        logger.info(
            "workflow_complete request_id=%s duration_ms=%s confidence=%s citations=%s",
            request_id,
            duration_ms,
            report.confidence,
            len(report.citations),
        )

        return WorkflowResult(
            request_id=request_id,
            duration_ms=duration_ms,
            report=report,
            debug={
                "plan": final_state.get("plan"),
                "ticket_agent": final_state.get("ticket_agent"),
                "document_agent": final_state.get("document_agent"),
                "log_agent": final_state.get("log_agent"),
                "tool_calls": final_state.get("tool_calls", []),
                "errors": final_state.get("errors", []),
                "started_at": final_state.get("started_at"),
                "completed_at": final_state.get("completed_at"),
            },
        )


workflow_service = LangGraphWorkflowService()

