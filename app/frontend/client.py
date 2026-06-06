from __future__ import annotations

from typing import Any, Literal

import httpx

from .config import FrontendSettings, get_frontend_settings
from .local_backend import LocalFrontendBackend


BackendMode = Literal["Auto", "FastAPI", "Local"]


class FrontendClient:
    def __init__(self, settings: FrontendSettings | None = None) -> None:
        self._settings = settings or get_frontend_settings()
        self._local = LocalFrontendBackend()

    @property
    def api_base_url(self) -> str:
        return self._settings.api_base_url

    def health(self, mode: BackendMode) -> dict[str, Any]:
        if mode == "Local":
            return self._local.health()

        try:
            return self._api_get("/health")
        except Exception as exc:
            if mode == "Auto":
                health = self._local.health()
                health["fallback_reason"] = str(exc)
                return health
            raise

    def dataset_summary(self) -> dict[str, int]:
        return self._local.dataset_summary()

    def query(self, question: str, *, include_debug: bool, mode: BackendMode) -> dict[str, Any]:
        if mode == "Local":
            return self._local.run_query(question, include_debug=include_debug)

        try:
            return self._api_post(
                "/query",
                {"question": question, "include_debug": include_debug},
            )
        except Exception:
            if mode == "Auto":
                return self._local.run_query(question, include_debug=include_debug)
            raise

    def tickets(
        self,
        *,
        mode: BackendMode,
        query: str | None,
        priority: str | None,
        status: str | None,
        owner: str | None,
        blockers_only: bool,
        limit: int,
    ) -> dict[str, Any]:
        if mode == "Local":
            return self._local.list_tickets(
                query=query,
                priority=priority,
                status=status,
                owner=owner,
                blockers_only=blockers_only,
                limit=limit,
            )

        params = _clean_params(
            {
                "query": query,
                "priority": priority,
                "status": status,
                "owner": owner,
                "blockers_only": blockers_only,
                "limit": limit,
            }
        )
        try:
            return self._api_get("/tickets", params=params)
        except Exception:
            if mode == "Auto":
                return self._local.list_tickets(
                    query=query,
                    priority=priority,
                    status=status,
                    owner=owner,
                    blockers_only=blockers_only,
                    limit=limit,
                )
            raise

    def logs(
        self,
        *,
        mode: BackendMode,
        query: str | None,
        log_type: str | None,
        severity: str | None,
        service: str | None,
        environment: str | None,
        recent_failures: bool,
        limit: int,
    ) -> dict[str, Any]:
        if mode == "Local":
            return self._local.list_logs(
                query=query,
                log_type=log_type,
                severity=severity,
                service=service,
                environment=environment,
                recent_failures=recent_failures,
                limit=limit,
            )

        params = _clean_params(
            {
                "query": query,
                "log_type": log_type,
                "severity": severity,
                "service": service,
                "environment": environment,
                "recent_failures": recent_failures,
                "limit": limit,
            }
        )
        try:
            return self._api_get("/logs", params=params)
        except Exception:
            if mode == "Auto":
                return self._local.list_logs(
                    query=query,
                    log_type=log_type,
                    severity=severity,
                    service=service,
                    environment=environment,
                    recent_failures=recent_failures,
                    limit=limit,
                )
            raise

    def documents(self) -> list[dict[str, Any]]:
        return self._local.documents()

    def _api_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        with httpx.Client(timeout=self._settings.request_timeout_seconds) as client:
            response = client.get(f"{self._settings.api_base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    def _api_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self._settings.request_timeout_seconds) as client:
            response = client.post(f"{self._settings.api_base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value not in (None, "")}

