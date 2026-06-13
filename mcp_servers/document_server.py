from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from pymongo.errors import PyMongoError
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_servers.common.config import get_port
from mcp_servers.common.errors import MCPServerError
from mcp_servers.common.logging_config import configure_logging
from mcp_servers.common.mongodb_documents import MongoDocumentStore
from mcp_servers.common.repository import EnterpriseDatasetRepository
from mcp_servers.common.server import run_server
from mcp_servers.common.tooling import execute_tool


logger = configure_logging(__name__)
repository = EnterpriseDatasetRepository()
mongo_documents = MongoDocumentStore()

mcp = FastMCP(
    name="AI Dashboard Document MCP Server",
    mask_error_details=True,
    on_duplicate="error",
)


@mcp.tool
def search_documents(
    query: str,
    document_type: str | None = None,
    service: str | None = None,
    environment: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search project documents semantically with MongoDB vector retrieval."""

    return execute_tool(
        logger,
        "search_documents",
        lambda: _search_documents(
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
        lambda: {"document": _get_document(document_id)},
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    try:
        mongo_documents.ping()
        mongo_status = "connected"
    except Exception:
        mongo_status = "unavailable"
    return JSONResponse(
        {
            "status": "ok",
            "server": mcp.name,
            "mongodb": mongo_status,
        }
    )


def _search_documents(
    *,
    query: str,
    document_type: str | None,
    service: str | None,
    environment: str | None,
    limit: int,
) -> dict[str, Any]:
    try:
        if mongo_documents.has_documents():
            return mongo_documents.search_documents(
                query=query,
                document_type=document_type,
                service=service,
                environment=environment,
                limit=limit,
            )
        logger.warning("mongodb_document_collection_empty fallback=json")
    except (PyMongoError, MCPServerError) as exc:
        logger.warning("mongodb_document_search_failed fallback=json error=%s", exc)

    result = repository.search_documents(
        query=query,
        document_type=document_type,
        service=service,
        environment=environment,
        limit=limit,
    )
    result["search_mode"] = "json-keyword-fallback"
    return result


def _get_document(document_id: str) -> dict[str, Any]:
    try:
        if mongo_documents.has_documents():
            return dict(mongo_documents.get_document(document_id))
    except (PyMongoError, MCPServerError) as exc:
        logger.warning("mongodb_document_get_failed fallback=json error=%s", exc)
    return dict(repository.get_document(document_id))


if __name__ == "__main__":
    run_server(mcp, default_port=get_port("DOCUMENT_MCP_PORT", 8102))
