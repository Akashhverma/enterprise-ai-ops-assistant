from __future__ import annotations

import json
import urllib.request


URLS = [
    "http://127.0.0.1:8000/health",
    "http://127.0.0.1:8000/tickets?query=dashboard&limit=1",
    "http://127.0.0.1:8000/logs?recent_failures=true&limit=1",
    "http://127.0.0.1:8001/api/v2/heartbeat",
    "http://127.0.0.1:8101/health",
    "http://127.0.0.1:8102/health",
    "http://127.0.0.1:8103/health",
    "http://127.0.0.1:8501/_stcore/health",
]


def get(url: str) -> None:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8", errors="replace")
        print(json.dumps({"url": url, "status": response.status, "body": body[:160]}))


def main() -> None:
    for url in URLS:
        get(url)


if __name__ == "__main__":
    main()
