from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from mcp_servers.common.repository import EnterpriseDatasetRepository  # noqa: E402


def main() -> None:
    repository = EnterpriseDatasetRepository()

    ticket = repository.get_ticket_by_id("AIDASH-1001")
    ticket_search = repository.search_tickets(query="timeout dashboard", limit=5)
    open_tickets = repository.list_open_tickets(limit=5)
    blockers = repository.list_blockers(limit=5)

    document = repository.get_document("DOC-AIDASH-001")
    document_search = repository.search_documents(query="architecture auth", limit=5)

    log_search = repository.search_logs(query="timeout", limit=5)
    failures = repository.get_recent_failures(limit=5)

    checks = {
        "ticket": ticket["ticket_id"],
        "ticket_search_count": ticket_search["count"],
        "open_ticket_count": open_tickets["count"],
        "blocker_count": blockers["count"],
        "document": document["document_id"],
        "document_search_count": document_search["count"],
        "log_search_count": log_search["count"],
        "recent_failure_count": failures["count"],
    }

    for name, value in checks.items():
        print(f"{name}={value}")


if __name__ == "__main__":
    main()

