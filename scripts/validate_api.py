from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200, health.text
    print(f"health={health.json()['status']}")

    tickets = client.get("/tickets", params={"query": "dashboard", "limit": 3})
    assert tickets.status_code == 200, tickets.text
    print(f"tickets={tickets.json()['count']}")

    logs = client.get("/logs", params={"query": "deployment failure", "limit": 3})
    assert logs.status_code == 200, logs.text
    print(f"logs={logs.json()['count']}")

    recent_logs = client.get("/logs", params={"limit": 3})
    assert recent_logs.status_code == 200, recent_logs.text
    print(f"recent_logs={recent_logs.json()['count']}")

    query = client.post(
        "/query",
        json={"question": "Why did the production dashboard deployment fail?", "include_debug": True},
    )
    assert query.status_code == 200, query.text
    payload = query.json()
    print(f"query_confidence={payload['report']['confidence']}")
    print(f"query_citations={len(payload['report']['citations'])}")

    chat = client.post(
        "/chat",
        json={
            "session_id": "validation-session",
            "messages": [{"role": "user", "content": "Show recent deployment failures"}],
        },
    )
    assert chat.status_code == 200, chat.text
    print(f"chat_role={chat.json()['message']['role']}")


if __name__ == "__main__":
    main()
