from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from fastmcp.exceptions import ToolError

from .errors import DatasetLoadError, RecordNotFoundError, ToolInputError


T = TypeVar("T")


def _result_count(result: object) -> object:
    if isinstance(result, dict):
        return result.get("count", result.get("total_matches", "n/a"))

    return "n/a"


def execute_tool(logger: logging.Logger, tool_name: str, operation: Callable[[], T]) -> T:
    try:
        result = operation()
        logger.info("tool=%s status=success result_count=%s", tool_name, _result_count(result))
        return result
    except (ToolInputError, RecordNotFoundError) as exc:
        logger.warning("tool=%s status=user_error error=%s", tool_name, exc)
        raise ToolError(str(exc)) from exc
    except DatasetLoadError as exc:
        logger.exception("tool=%s status=dataset_error", tool_name)
        raise ToolError("Dataset is unavailable. Check server logs for details.") from exc
    except Exception as exc:
        logger.exception("tool=%s status=internal_error", tool_name)
        raise ToolError("Unexpected MCP server error. Check server logs for details.") from exc

