from __future__ import annotations

from typing import Any, TypedDict


class TicketRecord(TypedDict):
    ticket_id: str
    title: str
    description: str
    priority: str
    status: str
    owner: str
    dependency: str
    created_date: str


class DocumentSection(TypedDict):
    heading: str
    body: str


class ProjectDocumentRecord(TypedDict):
    document_id: str
    title: str
    document_type: str
    project: str
    owner_team: str
    owner: str
    service: str
    environment: str
    version: str
    created_date: str
    related_ticket_ids: list[str]
    tags: list[str]
    sections: list[DocumentSection]


class DeploymentLogRecord(TypedDict):
    log_id: str
    log_type: str
    deployment_id: str
    project: str
    service: str
    environment: str
    severity: str
    status: str
    timestamp: str
    error_code: str
    message: str
    trace_id: str
    related_ticket_id: str
    probable_cause: str
    remediation_hint: str


JsonDict = dict[str, Any]

