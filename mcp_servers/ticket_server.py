from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_servers.common.config import get_port
from mcp_servers.common.logging_config import configure_logging
from mcp_servers.common.repository import EnterpriseDatasetRepository
from mcp_servers.common.server import run_server
from mcp_servers.common.tooling import execute_tool


logger = configure_logging(__name__)
repository = EnterpriseDatasetRepository()

mcp = FastMCP(
    name="AI Dashboard Ticket MCP Server",
    mask_error_details=True,
    on_duplicate="error",
)


@mcp.tool
def search_tickets(
    query: str,
    priority: str | None = None,
    status: str | None = None,
    owner: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search Jira-style tickets by keyword and optional structured filters."""

    return execute_tool(
        logger,
        "search_tickets",
        lambda: repository.search_tickets(
            query=query,
            priority=priority,
            status=status,
            owner=owner,
            limit=limit,
        ),
    )


@mcp.tool
def get_ticket_by_id(ticket_id: str) -> dict[str, Any]:
    """Fetch a single Jira-style ticket by its ticket ID, such as AIDASH-1001."""

    return execute_tool(
        logger,
        "get_ticket_by_id",
        lambda: {"ticket": repository.get_ticket_by_id(ticket_id)},
    )


@mcp.tool
def list_open_tickets(
    priority: str | None = None,
    owner: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """List active tickets that are not resolved or closed."""

    return execute_tool(
        logger,
        "list_open_tickets",
        lambda: repository.list_open_tickets(priority=priority, owner=owner, limit=limit),
    )


@mcp.tool
def list_blockers(
    owner: str | None = None,
    dependency: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """List blocked tickets and active tickets that depend on another ticket or external team."""

    return execute_tool(
        logger,
        "list_blockers",
        lambda: repository.list_blockers(owner=owner, dependency=dependency, limit=limit),
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": mcp.name})


if __name__ == "__main__":
    run_server(mcp, default_port=get_port("TICKET_MCP_PORT", 8101))
