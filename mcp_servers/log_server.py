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
    name="AI Dashboard Log MCP Server",
    mask_error_details=True,
    on_duplicate_tools="error",
)


@mcp.tool
def search_logs(
    query: str,
    log_type: str | None = None,
    severity: str | None = None,
    service: str | None = None,
    environment: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search deployment logs by keyword, log metadata, severity, service, environment, or time range."""

    return execute_tool(
        logger,
        "search_logs",
        lambda: repository.search_logs(
            query=query,
            log_type=log_type,
            severity=severity,
            service=service,
            environment=environment,
            since=since,
            until=until,
            limit=limit,
        ),
    )


@mcp.tool
def get_recent_failures(
    service: str | None = None,
    environment: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Return recent failed deployment or migration log records."""

    return execute_tool(
        logger,
        "get_recent_failures",
        lambda: repository.get_recent_failures(
            service=service,
            environment=environment,
            limit=limit,
        ),
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": mcp.name})


if __name__ == "__main__":
    run_server(mcp, default_port=get_port("LOG_MCP_PORT", 8103))

