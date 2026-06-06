from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict


class OpsAssistantState(TypedDict, total=False):
    user_question: str
    started_at: str
    completed_at: str
    plan: dict[str, Any]
    ticket_agent: dict[str, Any]
    document_agent: dict[str, Any]
    log_agent: dict[str, Any]
    final_report: dict[str, Any]
    tool_calls: Annotated[list[dict[str, Any]], add]
    errors: Annotated[list[str], add]


def empty_state(question: str) -> OpsAssistantState:
    return {
        "user_question": question,
        "tool_calls": [],
        "errors": [],
    }

