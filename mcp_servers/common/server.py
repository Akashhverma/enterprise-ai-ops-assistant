from __future__ import annotations

import argparse

from fastmcp import FastMCP

from .config import get_default_host, get_default_transport


def run_server(mcp: FastMCP, *, default_port: int) -> None:
    parser = argparse.ArgumentParser(description=f"Run {mcp.name}")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse", "streamable-http"],
        default=get_default_transport(),
        help="MCP transport to use.",
    )
    parser.add_argument("--host", default=get_default_host(), help="Host for HTTP transports.")
    parser.add_argument("--port", type=int, default=default_port, help="Port for HTTP transports.")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
        return

    mcp.run(transport=args.transport, host=args.host, port=args.port)

