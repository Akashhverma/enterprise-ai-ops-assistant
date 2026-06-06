from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.frontend.client import FrontendClient  # noqa: E402


def main() -> None:
    client = FrontendClient()

    health = client.health("Auto")
    print(f"health={health['status']}")

    summary = client.dataset_summary()
    print(f"tickets={summary['tickets']} documents={summary['documents']} logs={summary['logs']}")

    response = client.query(
        "Why did the production dashboard deployment fail?",
        include_debug=True,
        mode="Auto",
    )
    print(f"confidence={response['report']['confidence']}")
    print(f"citations={len(response['report']['citations'])}")
    print(f"tool_calls={len(response['debug']['tool_calls'])}")

    tickets = client.tickets(
        mode="Auto",
        query="dashboard",
        priority=None,
        status=None,
        owner=None,
        blockers_only=False,
        limit=3,
    )
    print(f"ticket_rows={tickets['count']}")

    logs = client.logs(
        mode="Auto",
        query="deployment failure",
        log_type=None,
        severity=None,
        service=None,
        environment=None,
        recent_failures=False,
        limit=3,
    )
    print(f"log_rows={logs['count']}")


if __name__ == "__main__":
    main()

