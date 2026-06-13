from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from mcp_servers.common.mongodb_documents import MongoDocumentStore  # noqa: E402
from mcp_servers.common.repository import EnterpriseDatasetRepository  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest project documents and OpenAI embeddings into MongoDB."
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Store documents and chunks without calling OpenAI.",
    )
    parser.add_argument(
        "--require-embeddings",
        action="store_true",
        help="Fail when OPENAI_API_KEY is unavailable.",
    )
    args = parser.parse_args()

    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
    if args.require_embeddings and not has_openai_key:
        raise SystemExit("OPENAI_API_KEY is required but is not configured.")

    generate_embeddings = not args.skip_embeddings and has_openai_key
    if not generate_embeddings:
        print(
            "OPENAI_API_KEY is not configured; ingesting MongoDB documents "
            "without embeddings."
        )

    documents = EnterpriseDatasetRepository().documents()
    result = MongoDocumentStore().ingest_documents(
        documents,
        generate_embeddings=generate_embeddings,
    )
    for key, value in result.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
