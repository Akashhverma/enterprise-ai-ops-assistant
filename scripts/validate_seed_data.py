from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT_DIR / "data" / "seed"

EXPECTED_TICKET_FIELDS = {
    "ticket_id",
    "title",
    "description",
    "priority",
    "status",
    "owner",
    "dependency",
    "created_date",
}

EXPECTED_DOCUMENT_TYPES = {
    "architecture document",
    "meeting notes",
    "release plan",
    "deployment procedure",
    "incident report",
}

EXPECTED_LOG_TYPES = {
    "deployment failure",
    "authentication failure",
    "database migration issue",
    "api timeout error",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> None:
    tickets_payload = load_json(SEED_DIR / "tickets.json")
    documents_payload = load_json(SEED_DIR / "project_documents.json")
    logs_payload = load_json(SEED_DIR / "deployment_logs.json")

    tickets = tickets_payload["tickets"]
    documents = documents_payload["documents"]
    logs = logs_payload["logs"]

    assert len(tickets) == 150, f"expected 150 tickets, got {len(tickets)}"
    assert len(documents) == 50, f"expected 50 documents, got {len(documents)}"
    assert len(logs) == 50, f"expected 50 logs, got {len(logs)}"

    for ticket in tickets:
        assert set(ticket) == EXPECTED_TICKET_FIELDS, ticket["ticket_id"]

    document_types = {document["document_type"] for document in documents}
    log_types = {log["log_type"] for log in logs}

    assert EXPECTED_DOCUMENT_TYPES == document_types, document_types
    assert EXPECTED_LOG_TYPES == log_types, log_types

    print("validated tickets=150 documents=50 logs=50")
    print(f"document_types={sorted(document_types)}")
    print(f"log_types={sorted(log_types)}")


if __name__ == "__main__":
    validate()
