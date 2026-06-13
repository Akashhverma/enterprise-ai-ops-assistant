from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class MongoDBConfig:
    uri: str
    database: str
    documents_collection: str
    chunks_collection: str
    vector_index: str
    vector_search_mode: str
    server_selection_timeout_ms: int
    allow_keyword_fallback: bool
    create_vector_index: bool


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str
    dimensions: int
    batch_size: int


def get_mongodb_config() -> MongoDBConfig:
    return MongoDBConfig(
        uri=os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"),
        database=os.getenv("MONGODB_DATABASE", "enterprise_ai_ops"),
        documents_collection=os.getenv("MONGODB_DOCUMENTS_COLLECTION", "project_documents"),
        chunks_collection=os.getenv("MONGODB_CHUNKS_COLLECTION", "document_chunks"),
        vector_index=os.getenv("MONGODB_VECTOR_INDEX", "document_vector_index"),
        vector_search_mode=os.getenv("MONGODB_VECTOR_SEARCH_MODE", "auto").lower(),
        server_selection_timeout_ms=int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")),
        allow_keyword_fallback=_as_bool(
            os.getenv("MONGODB_ALLOW_KEYWORD_FALLBACK", "true")
        ),
        create_vector_index=_as_bool(os.getenv("MONGODB_CREATE_VECTOR_INDEX", "true")),
    )


def get_embedding_config() -> EmbeddingConfig:
    return EmbeddingConfig(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        dimensions=int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536")),
        batch_size=int(os.getenv("OPENAI_EMBEDDING_BATCH_SIZE", "64")),
    )


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
