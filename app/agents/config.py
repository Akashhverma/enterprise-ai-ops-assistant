from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AgentRuntimeConfig:
    model_name: str
    temperature: float
    retrieval_limit: int
    max_tool_attempts: int
    mcp_client_mode: str
    mcp_timeout_seconds: float
    mcp_allow_local_fallback: bool
    ticket_mcp_url: str
    document_mcp_url: str
    log_mcp_url: str


def get_agent_runtime_config() -> AgentRuntimeConfig:
    return AgentRuntimeConfig(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")),
        retrieval_limit=int(os.getenv("AGENT_RETRIEVAL_LIMIT", "8")),
        max_tool_attempts=int(os.getenv("AGENT_TOOL_MAX_ATTEMPTS", "3")),
        mcp_client_mode=os.getenv("MCP_CLIENT_MODE", "local").lower(),
        mcp_timeout_seconds=float(os.getenv("MCP_CLIENT_TIMEOUT_SECONDS", "15")),
        mcp_allow_local_fallback=_as_bool(os.getenv("MCP_ALLOW_LOCAL_FALLBACK", "true")),
        ticket_mcp_url=os.getenv("TICKET_MCP_URL", "http://127.0.0.1:8101/mcp"),
        document_mcp_url=os.getenv("DOCUMENT_MCP_URL", "http://127.0.0.1:8102/mcp"),
        log_mcp_url=os.getenv("LOG_MCP_URL", "http://127.0.0.1:8103/mcp"),
    )


def openai_is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
