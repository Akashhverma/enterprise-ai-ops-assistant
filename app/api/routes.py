from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import repository_dependency, settings_dependency, workflow_dependency
from app.api.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    LogListResponse,
    QueryRequest,
    QueryResponse,
    TicketListResponse,
)
from app.core.config import Settings
from app.core.errors import APIError
from app.core.logging import configure_api_logging
from app.services.langgraph_service import LangGraphWorkflowService
from mcp_servers.common.errors import MCPServerError
from mcp_servers.common.repository import EnterpriseDatasetRepository


router = APIRouter()
logger = configure_api_logging()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
)
async def health(settings: Annotated[Settings, Depends(settings_dependency)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    tags=["assistant"],
    summary="Run an enterprise operations query",
)
async def query(
    payload: QueryRequest,
    workflow: Annotated[LangGraphWorkflowService, Depends(workflow_dependency)],
) -> QueryResponse:
    try:
        result = await workflow.run_question(payload.question)
    except Exception as exc:
        logger.exception("query_failed")
        raise APIError(
            "Failed to run LangGraph workflow.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    return QueryResponse(
        request_id=result.request_id,
        duration_ms=result.duration_ms,
        report=result.report,
        debug=result.debug if payload.include_debug else None,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    tags=["assistant"],
    summary="Chat with the enterprise operations assistant",
)
async def chat(
    payload: ChatRequest,
    workflow: Annotated[LangGraphWorkflowService, Depends(workflow_dependency)],
) -> ChatResponse:
    user_question = _latest_user_message(payload.messages)
    if not user_question:
        raise APIError("Chat request must include at least one user message.")

    try:
        result = await workflow.run_question(user_question)
    except Exception as exc:
        logger.exception("chat_failed")
        raise APIError(
            "Failed to run LangGraph workflow.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    return ChatResponse(
        request_id=result.request_id,
        session_id=payload.session_id,
        message=ChatMessage(role="assistant", content=result.report.answer),
        report=result.report,
        duration_ms=result.duration_ms,
        debug=result.debug if payload.include_debug else None,
    )


@router.get(
    "/tickets",
    response_model=TicketListResponse,
    tags=["data"],
    summary="Search or list tickets",
)
async def tickets(
    repository: Annotated[EnterpriseDatasetRepository, Depends(repository_dependency)],
    query_text: Annotated[
        str | None,
        Query(alias="query", description="Keyword search over ticket fields."),
    ] = None,
    priority: str | None = None,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description="Ticket status filter."),
    ] = None,
    owner: str | None = None,
    blockers_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 25,
) -> TicketListResponse:
    try:
        if blockers_only:
            result = await _to_thread(
                repository.list_blockers,
                owner=owner,
                limit=limit,
            )
        elif query_text or priority or status_filter or owner:
            result = await _to_thread(
                repository.search_tickets,
                query=query_text or "",
                priority=priority,
                status=status_filter,
                owner=owner,
                limit=limit,
            )
        else:
            result = await _to_thread(repository.list_open_tickets, limit=limit)
    except MCPServerError as exc:
        raise APIError(str(exc)) from exc

    return TicketListResponse.model_validate(result)


@router.get(
    "/logs",
    response_model=LogListResponse,
    tags=["data"],
    summary="Search deployment logs or list recent failures",
)
async def logs(
    repository: Annotated[EnterpriseDatasetRepository, Depends(repository_dependency)],
    query_text: Annotated[
        str | None,
        Query(alias="query", description="Keyword search over deployment log fields."),
    ] = None,
    log_type: str | None = None,
    severity: str | None = None,
    service: str | None = None,
    environment: str | None = None,
    since: str | None = None,
    until: str | None = None,
    recent_failures: bool = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 25,
) -> LogListResponse:
    try:
        has_search_or_filters = any(
            value
            for value in [query_text, log_type, severity, service, environment, since, until]
        )
        if recent_failures or not has_search_or_filters:
            result = await _to_thread(
                repository.get_recent_failures,
                service=service,
                environment=environment,
                limit=limit,
            )
        else:
            result = await _to_thread(
                repository.search_logs,
                query=query_text or "",
                log_type=log_type,
                severity=severity,
                service=service,
                environment=environment,
                since=since,
                until=until,
                limit=limit,
            )
    except MCPServerError as exc:
        raise APIError(str(exc)) from exc

    return LogListResponse.model_validate(result)


def _latest_user_message(messages: list[ChatMessage]) -> str | None:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return None


async def _to_thread(func: Any, /, *args: Any, **kwargs: Any) -> Any:
    import asyncio

    return await asyncio.to_thread(func, *args, **kwargs)
