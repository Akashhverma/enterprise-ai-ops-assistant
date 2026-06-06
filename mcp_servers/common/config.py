from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_DIR = PROJECT_ROOT / "data" / "seed"


@dataclass(frozen=True)
class DatasetPaths:
    seed_dir: Path

    @property
    def tickets_path(self) -> Path:
        return self.seed_dir / "tickets.json"

    @property
    def documents_path(self) -> Path:
        return self.seed_dir / "project_documents.json"

    @property
    def logs_path(self) -> Path:
        return self.seed_dir / "deployment_logs.json"


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default

    configured = Path(value)
    if configured.is_absolute():
        return configured

    return PROJECT_ROOT / configured


def get_dataset_paths() -> DatasetPaths:
    return DatasetPaths(
        seed_dir=_resolve_path(os.getenv("AI_DASHBOARD_SEED_DIR"), DEFAULT_SEED_DIR)
    )


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_default_transport() -> str:
    return os.getenv("MCP_TRANSPORT", "stdio").lower()


def get_default_host() -> str:
    return os.getenv("MCP_HOST", "127.0.0.1")


def get_port(env_name: str, default: int) -> int:
    value = os.getenv(env_name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{env_name} must be an integer, got {value!r}") from exc

