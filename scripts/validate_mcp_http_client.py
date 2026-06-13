from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.agents.mcp_tool_client import HTTPMCPToolClient  # noqa: E402


def main() -> None:
    os.environ.setdefault("MCP_ALLOW_LOCAL_FALLBACK", "false")
    client = HTTPMCPToolClient()

    checks = [
        ("ticket", "search_tickets", {"query": "dashboard", "limit": 2}),
        (
            "document",
            "search_documents",
            {"query": "deployment rollback procedure", "limit": 2},
        ),
        ("log", "search_logs", {"query": "deployment failure", "limit": 2}),
    ]

    for server, tool, arguments in checks:
        result, call = client.call_tool(server, tool, arguments)  # type: ignore[arg-type]
        if call.status != "success" or result is None:
            raise SystemExit(f"{server}.{tool} failed: {call.error}")
        print(
            f"{server}.{tool} transport={call.transport} "
            f"results={call.result_count} fallback={call.fallback_used}"
        )


if __name__ == "__main__":
    main()
