from __future__ import annotations


class MCPServerError(Exception):
    """Base exception for controlled MCP server failures."""


class DatasetLoadError(MCPServerError):
    """Raised when a seed dataset cannot be loaded or parsed."""


class ToolInputError(MCPServerError):
    """Raised when a tool receives invalid input."""


class RecordNotFoundError(MCPServerError):
    """Raised when a requested enterprise record does not exist."""

