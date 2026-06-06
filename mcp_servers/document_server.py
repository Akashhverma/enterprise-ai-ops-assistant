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
    name="AI Dashboard Document MCP Server",
    mask_error_details=True,
    on_duplicate_tools="error",
)


@mcp.tool
def search_documents(
    query: str,
    document_type: str | None = None,
    service: str | None = None,
    environment: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search project documents by keyword and optional document metadata filters."""

    return execute_tool(
        logger,
        "search_documents",
        lambda: repository.search_documents(
            query=query,
            document_type=document_type,
            service=service,
            environment=environment,
            limit=limit,
        ),
    )


@mcp.tool
def get_document(document_id: str) -> dict[str, Any]:
    """Fetch one project document by document ID, such as DOC-AIDASH-001."""

    return execute_tool(
        logger,
        "get_document",
        lambda: {"document": repository.get_document(document_id)},
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": mcp.name})


if __name__ == "__main__":
    run_server(mcp, default_port=get_port("DOCUMENT_MCP_PORT", 8102))

