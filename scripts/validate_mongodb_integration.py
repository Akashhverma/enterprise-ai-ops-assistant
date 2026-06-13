from __future__ import annotations

from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from mcp_servers.common.mongodb_documents import MongoDocumentStore  # noqa: E402


def main() -> None:
    store = MongoDocumentStore()
    store.ping()
    print("mongodb=connected")
    print(f"documents_available={store.has_documents()}")

    if store.has_documents():
        result = store.search_documents(
            query="production deployment rollback procedure",
            environment="production",
            limit=3,
        )
        print(f"search_mode={result['search_mode']}")
        print(f"results={result['count']}")
        for document in result["results"]:
            print(
                f"{document['document_id']} "
                f"score={document.get('relevance_score', 0)}"
            )


if __name__ == "__main__":
    main()
