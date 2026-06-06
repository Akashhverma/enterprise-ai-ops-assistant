from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRuntimeConfig:
    model_name: str
    temperature: float
    retrieval_limit: int
    max_tool_attempts: int


def get_agent_runtime_config() -> AgentRuntimeConfig:
    return AgentRuntimeConfig(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")),
        retrieval_limit=int(os.getenv("AGENT_RETRIEVAL_LIMIT", "8")),
        max_tool_attempts=int(os.getenv("AGENT_TOOL_MAX_ATTEMPTS", "3")),
    )


def openai_is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))

