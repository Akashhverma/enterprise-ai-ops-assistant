from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, Literal, Protocol

from mcp_servers.common.errors import DatasetLoadError, RecordNotFoundError, ToolInputError
from mcp_servers.common.repository import EnterpriseDatasetRepository

from .config import get_agent_runtime_config
from .models import ToolCallRecord


ServerName = Literal["ticket", "document", "log"]


class MCPToolClient(Protocol):
    def call_tool(
        self,
        server: ServerName,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, ToolCallRecord]:
        """Call one MCP tool and return the structured result plus call metadata."""


class LocalMCPToolClient:
    """Local adapter over the same tool contracts exposed by the FastMCP servers.

    The LangGraph workflow uses this by default for deterministic local runs. A remote
    adapter can be swapped in later without changing the agent nodes.
    """

    def __init__(
        self,
        repository: EnterpriseDatasetRepository | None = None,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._repository = repository or EnterpriseDatasetRepository()
        self._logger = logger or logging.getLogger(__name__)
        self._max_attempts = get_agent_runtime_config().max_tool_attempts

    def call_tool(
        self,
        server: ServerName,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, ToolCallRecord]:
        attempts = 0
        last_error: str | None = None

        for attempts in range(1, self._max_attempts + 1):
            try:
                result = self._dispatch(server, tool_name, arguments)
                call_record = ToolCallRecord(
                    server=server,
                    tool_name=tool_name,
                    arguments=arguments,
                    status="success",
                    attempts=attempts,
                    result_count=_result_count(result),
                )
                self._logger.info(
                    "mcp_tool_call server=%s tool=%s status=success attempts=%s result_count=%s",
                    server,
                    tool_name,
                    attempts,
                    call_record.result_count,
                )
                return result, call_record
            except (ToolInputError, RecordNotFoundError) as exc:
                last_error = str(exc)
                break
            except DatasetLoadError as exc:
                last_error = str(exc)
                break
            except Exception as exc:
                last_error = str(exc)
                self._logger.warning(
                    "mcp_tool_call server=%s tool=%s status=retryable_error attempts=%s error=%s",
                    server,
                    tool_name,
                    attempts,
                    exc,
                )
                if attempts < self._max_attempts:
                    time.sleep(min(0.25 * attempts, 1.0))

        call_record = ToolCallRecord(
            server=server,
            tool_name=tool_name,
            arguments=arguments,
            status="failed",
            attempts=attempts,
            error=last_error or "Unknown tool error.",
        )
        self._logger.error(
            "mcp_tool_call server=%s tool=%s status=failed attempts=%s error=%s",
            server,
            tool_name,
            attempts,
            call_record.error,
        )
        return None, call_record

    def _dispatch(self, server: ServerName, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        dispatch: dict[tuple[str, str], Callable[..., dict[str, Any]]] = {
            ("ticket", "search_tickets"): self._repository.search_tickets,
            ("ticket", "list_open_tickets"): self._repository.list_open_tickets,
            ("ticket", "list_blockers"): self._repository.list_blockers,
            ("document", "search_documents"): self._repository.search_documents,
            ("log", "search_logs"): self._repository.search_logs,
            ("log", "get_recent_failures"): self._repository.get_recent_failures,
        }

        if server == "ticket" and tool_name == "get_ticket_by_id":
            return {"ticket": self._repository.get_ticket_by_id(str(arguments.get("ticket_id", "")))}

        if server == "document" and tool_name == "get_document":
            return {"document": self._repository.get_document(str(arguments.get("document_id", "")))}

        operation = dispatch.get((server, tool_name))
        if operation is None:
            raise ToolInputError(f"Unknown MCP tool: {server}.{tool_name}")

        return operation(**arguments)


def _result_count(result: dict[str, Any]) -> int | None:
    count = result.get("count")
    if isinstance(count, int):
        return count

    for key in ("ticket", "document"):
        if key in result:
            return 1

    results = result.get("results")
    if isinstance(results, list):
        return len(results)

    return None

