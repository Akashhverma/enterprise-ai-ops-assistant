from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from .config import DatasetPaths, get_dataset_paths
from .errors import DatasetLoadError, RecordNotFoundError, ToolInputError
from .search import (
    contains_optional,
    ensure_query_or_filter,
    exact_optional,
    matched_fields,
    normalize_text,
    text_score,
    timestamp_in_range,
    validate_limit,
)
from .types import DeploymentLogRecord, JsonDict, ProjectDocumentRecord, TicketRecord


OPEN_TICKET_STATUSES = {"Backlog", "In Progress", "Blocked", "In Review"}


@lru_cache(maxsize=16)
def _load_json(path_value: str) -> JsonDict:
    path = Path(path_value)
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except FileNotFoundError as exc:
        raise DatasetLoadError(f"Dataset file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DatasetLoadError(f"Dataset file is not valid JSON: {path}") from exc
    except OSError as exc:
        raise DatasetLoadError(f"Could not read dataset file: {path}") from exc

    if not isinstance(payload, dict):
        raise DatasetLoadError(f"Dataset file must contain a JSON object: {path}")

    return cast(JsonDict, payload)


def _safe_records(payload: JsonDict, key: str, path: Path) -> list[dict[str, Any]]:
    records = payload.get(key)
    if not isinstance(records, list):
        raise DatasetLoadError(f"{path} must contain a list at key {key!r}.")

    return copy.deepcopy(cast(list[dict[str, Any]], records))


class EnterpriseDatasetRepository:
    def __init__(self, paths: DatasetPaths | None = None) -> None:
        self._paths = paths or get_dataset_paths()

    def tickets(self) -> list[TicketRecord]:
        payload = _load_json(str(self._paths.tickets_path))
        return cast(list[TicketRecord], _safe_records(payload, "tickets", self._paths.tickets_path))

    def documents(self) -> list[ProjectDocumentRecord]:
        payload = _load_json(str(self._paths.documents_path))
        return cast(
            list[ProjectDocumentRecord],
            _safe_records(payload, "documents", self._paths.documents_path),
        )

    def logs(self) -> list[DeploymentLogRecord]:
        payload = _load_json(str(self._paths.logs_path))
        return cast(list[DeploymentLogRecord], _safe_records(payload, "logs", self._paths.logs_path))

    def get_ticket_by_id(self, ticket_id: str) -> TicketRecord:
        normalized_id = ticket_id.strip().casefold()
        if not normalized_id:
            raise ToolInputError("ticket_id is required.")

        for ticket in self.tickets():
            if ticket["ticket_id"].casefold() == normalized_id:
                return ticket

        raise RecordNotFoundError(f"Ticket not found: {ticket_id}")

    def search_tickets(
        self,
        *,
        query: str,
        priority: str | None = None,
        status: str | None = None,
        owner: str | None = None,
        limit: int = 10,
    ) -> JsonDict:
        limit = validate_limit(limit)
        ensure_query_or_filter(query, [priority, status, owner])

        results: list[JsonDict] = []
        searchable_fields = [
            "ticket_id",
            "title",
            "description",
            "priority",
            "status",
            "owner",
            "dependency",
            "created_date",
        ]

        for ticket in self.tickets():
            if not exact_optional(ticket["priority"], priority):
                continue
            if not exact_optional(ticket["status"], status):
                continue
            if not contains_optional(ticket["owner"], owner):
                continue

            searchable_text = " ".join(normalize_text(ticket[field]) for field in searchable_fields)
            score = text_score(query, searchable_text)
            if score == 0:
                continue

            results.append(
                {
                    **ticket,
                    "relevance_score": score,
                    "matched_fields": matched_fields(query, dict(ticket), searchable_fields),
                }
            )

        results.sort(key=lambda item: (item["relevance_score"], item["created_date"]), reverse=True)

        return {
            "query": query,
            "filters": {
                "priority": priority,
                "status": status,
                "owner": owner,
            },
            "count": min(len(results), limit),
            "total_matches": len(results),
            "results": results[:limit],
        }

    def list_open_tickets(
        self,
        *,
        priority: str | None = None,
        owner: str | None = None,
        limit: int = 25,
    ) -> JsonDict:
        limit = validate_limit(limit)

        tickets = [
            ticket
            for ticket in self.tickets()
            if ticket["status"] in OPEN_TICKET_STATUSES
            and exact_optional(ticket["priority"], priority)
            and contains_optional(ticket["owner"], owner)
        ]
        tickets.sort(key=lambda item: item["created_date"], reverse=True)

        return {
            "filters": {
                "priority": priority,
                "owner": owner,
                "open_statuses": sorted(OPEN_TICKET_STATUSES),
            },
            "count": min(len(tickets), limit),
            "total_matches": len(tickets),
            "results": tickets[:limit],
        }

    def list_blockers(
        self,
        *,
        owner: str | None = None,
        dependency: str | None = None,
        limit: int = 25,
    ) -> JsonDict:
        limit = validate_limit(limit)

        blockers: list[JsonDict] = []
        for ticket in self.tickets():
            has_blocked_status = ticket["status"] == "Blocked"
            has_dependency = ticket["dependency"].strip().casefold() != "none"
            if not (has_blocked_status or has_dependency):
                continue
            if not contains_optional(ticket["owner"], owner):
                continue
            if not contains_optional(ticket["dependency"], dependency):
                continue

            reason = "blocked status" if has_blocked_status else "active dependency"
            blockers.append({**ticket, "blocker_reason": reason})

        blockers.sort(key=lambda item: (item["priority"], item["created_date"]))

        return {
            "filters": {
                "owner": owner,
                "dependency": dependency,
            },
            "count": min(len(blockers), limit),
            "total_matches": len(blockers),
            "results": blockers[:limit],
        }

    def get_document(self, document_id: str) -> ProjectDocumentRecord:
        normalized_id = document_id.strip().casefold()
        if not normalized_id:
            raise ToolInputError("document_id is required.")

        for document in self.documents():
            if document["document_id"].casefold() == normalized_id:
                return document

        raise RecordNotFoundError(f"Document not found: {document_id}")

    def search_documents(
        self,
        *,
        query: str,
        document_type: str | None = None,
        service: str | None = None,
        environment: str | None = None,
        limit: int = 10,
    ) -> JsonDict:
        limit = validate_limit(limit)
        ensure_query_or_filter(query, [document_type, service, environment])

        results: list[JsonDict] = []
        searchable_fields = [
            "document_id",
            "title",
            "document_type",
            "project",
            "owner_team",
            "owner",
            "service",
            "environment",
            "version",
            "created_date",
            "related_ticket_ids",
            "tags",
            "sections",
        ]

        for document in self.documents():
            if not exact_optional(document["document_type"], document_type):
                continue
            if not exact_optional(document["service"], service):
                continue
            if not exact_optional(document["environment"], environment):
                continue

            searchable_text = " ".join(normalize_text(document[field]) for field in searchable_fields)
            score = text_score(query, searchable_text)
            if score == 0:
                continue

            results.append(
                {
                    **document,
                    "relevance_score": score,
                    "matched_fields": matched_fields(query, dict(document), searchable_fields),
                }
            )

        results.sort(key=lambda item: (item["relevance_score"], item["created_date"]), reverse=True)

        return {
            "query": query,
            "filters": {
                "document_type": document_type,
                "service": service,
                "environment": environment,
            },
            "count": min(len(results), limit),
            "total_matches": len(results),
            "results": results[:limit],
        }

    def search_logs(
        self,
        *,
        query: str,
        log_type: str | None = None,
        severity: str | None = None,
        service: str | None = None,
        environment: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 10,
    ) -> JsonDict:
        limit = validate_limit(limit)
        ensure_query_or_filter(query, [log_type, severity, service, environment, since, until])

        results: list[JsonDict] = []
        searchable_fields = [
            "log_id",
            "log_type",
            "deployment_id",
            "project",
            "service",
            "environment",
            "severity",
            "status",
            "timestamp",
            "error_code",
            "message",
            "trace_id",
            "related_ticket_id",
            "probable_cause",
            "remediation_hint",
        ]

        for log in self.logs():
            if not exact_optional(log["log_type"], log_type):
                continue
            if not exact_optional(log["severity"], severity):
                continue
            if not exact_optional(log["service"], service):
                continue
            if not exact_optional(log["environment"], environment):
                continue
            if not timestamp_in_range(log["timestamp"], since=since, until=until):
                continue

            searchable_text = " ".join(normalize_text(log[field]) for field in searchable_fields)
            score = text_score(query, searchable_text)
            if score == 0:
                continue

            results.append(
                {
                    **log,
                    "relevance_score": score,
                    "matched_fields": matched_fields(query, dict(log), searchable_fields),
                }
            )

        results.sort(key=lambda item: (item["relevance_score"], item["timestamp"]), reverse=True)

        return {
            "query": query,
            "filters": {
                "log_type": log_type,
                "severity": severity,
                "service": service,
                "environment": environment,
                "since": since,
                "until": until,
            },
            "count": min(len(results), limit),
            "total_matches": len(results),
            "results": results[:limit],
        }

    def get_recent_failures(
        self,
        *,
        service: str | None = None,
        environment: str | None = None,
        limit: int = 10,
    ) -> JsonDict:
        limit = validate_limit(limit)

        failures = [
            log
            for log in self.logs()
            if log["status"] == "failed"
            and exact_optional(log["service"], service)
            and exact_optional(log["environment"], environment)
        ]
        failures.sort(key=lambda item: item["timestamp"], reverse=True)

        return {
            "filters": {
                "service": service,
                "environment": environment,
                "status": "failed",
            },
            "count": min(len(failures), limit),
            "total_matches": len(failures),
            "results": failures[:limit],
        }

