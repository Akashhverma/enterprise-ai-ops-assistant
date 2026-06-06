from __future__ import annotations

from collections.abc import Generator

from app.core.config import Settings, get_settings
from app.services.langgraph_service import LangGraphWorkflowService, workflow_service
from mcp_servers.common.repository import EnterpriseDatasetRepository


def settings_dependency() -> Settings:
    return get_settings()


def workflow_dependency() -> LangGraphWorkflowService:
    return workflow_service


def repository_dependency() -> Generator[EnterpriseDatasetRepository, None, None]:
    yield EnterpriseDatasetRepository()

