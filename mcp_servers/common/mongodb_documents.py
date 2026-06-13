from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable, cast

from pymongo import ASCENDING, MongoClient, ReplaceOne
from pymongo.collection import Collection
from pymongo.errors import OperationFailure, PyMongoError
from pymongo.operations import SearchIndexModel

from .embeddings import OpenAIEmbeddingService
from .errors import DatasetLoadError, RecordNotFoundError, ToolInputError
from .mongodb_config import MongoDBConfig, get_mongodb_config
from .search import ensure_query_or_filter, validate_limit
from .types import JsonDict, ProjectDocumentRecord


class MongoDocumentStore:
    def __init__(
        self,
        config: MongoDBConfig | None = None,
        embeddings: OpenAIEmbeddingService | None = None,
    ) -> None:
        self._config = config or get_mongodb_config()
        self._embeddings = embeddings or OpenAIEmbeddingService()
        self._client: MongoClient[dict[str, Any]] | None = None

    def ping(self) -> bool:
        self._get_client().admin.command("ping")
        return True

    def has_documents(self) -> bool:
        return self._documents().estimated_document_count() > 0

    def ingest_documents(
        self,
        documents: list[ProjectDocumentRecord],
        *,
        generate_embeddings: bool = True,
    ) -> JsonDict:
        document_collection = self._documents()
        chunk_collection = self._chunks()
        now = datetime.now(timezone.utc)
        document_operations: list[ReplaceOne] = []
        chunks: list[dict[str, Any]] = []

        for document in documents:
            stored_document = dict(document)
            stored_document["_id"] = document["document_id"]
            stored_document["indexed_at"] = now
            document_operations.append(
                ReplaceOne({"_id": stored_document["_id"]}, stored_document, upsert=True)
            )
            chunks.extend(_chunk_document(document, indexed_at=now))

        if generate_embeddings:
            texts = [chunk["content"] for chunk in chunks]
            try:
                vectors = self._embeddings.embed_texts(texts)
                if len(vectors) != len(chunks):
                    raise DatasetLoadError("Embedding response count did not match document chunks.")
                for chunk, vector in zip(chunks, vectors):
                    chunk["embedding"] = vector
                    chunk["embedding_model"] = self._embeddings.model
            except Exception as e:
                # If embeddings fail (e.g., invalid API key), gracefully skip embeddings
                if "401" in str(e) or "invalid_api_key" in str(e).lower():
                    print(f"⚠️  Embedding failed due to authentication: {str(e)[:100]}. Proceeding without embeddings.")
                    generate_embeddings = False
                else:
                    raise

        if document_operations:
            document_collection.bulk_write(document_operations, ordered=False)

        chunk_operations = [
            ReplaceOne({"_id": chunk["_id"]}, chunk, upsert=True) for chunk in chunks
        ]
        if chunk_operations:
            chunk_collection.bulk_write(chunk_operations, ordered=False)

        self._ensure_standard_indexes()
        vector_index_status = self.ensure_vector_index() if generate_embeddings else "skipped"

        return {
            "documents_upserted": len(document_operations),
            "chunks_upserted": len(chunk_operations),
            "embeddings_generated": len(chunks) if generate_embeddings else 0,
            "embedding_model": self._embeddings.model if generate_embeddings else None,
            "vector_index": vector_index_status,
        }

    def ensure_vector_index(self) -> str:
        if not self._config.create_vector_index:
            return "disabled"

        collection = self._chunks()
        definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": self._embeddings.dimensions,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "document_type"},
                {"type": "filter", "path": "service"},
                {"type": "filter", "path": "environment"},
            ]
        }

        try:
            existing = {
                index.get("name") for index in collection.list_search_indexes()
            }
            if self._config.vector_index in existing:
                return "exists"

            model = SearchIndexModel(
                definition=definition,
                name=self._config.vector_index,
                type="vectorSearch",
            )
            collection.create_search_index(model=model)
            return "created"
        except (OperationFailure, PyMongoError):
            if self._config.vector_search_mode == "atlas":
                raise
            return "unsupported-local"

    def get_document(self, document_id: str) -> ProjectDocumentRecord:
        normalized = document_id.strip()
        if not normalized:
            raise ToolInputError("document_id is required.")

        document = self._documents().find_one({"_id": normalized})
        if not document:
            raise RecordNotFoundError(f"Document not found: {document_id}")

        return _clean_document(document)

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
        filters = _metadata_filters(
            document_type=document_type,
            service=service,
            environment=environment,
        )

        if query.strip():
            try:
                query_vector = self._embeddings.embed_query(query)
                chunks = self._vector_search(
                    query_vector=query_vector,
                    filters=filters,
                    limit=limit,
                )
                search_mode = "semantic"
            except Exception as exc:
                if not self._config.allow_keyword_fallback:
                    raise DatasetLoadError(f"MongoDB semantic search failed: {exc}") from exc
                chunks = self._keyword_search(query=query, filters=filters, limit=limit)
                search_mode = "keyword-fallback"
        else:
            chunks = self._metadata_search(filters=filters, limit=limit)
            search_mode = "metadata"

        results = self._hydrate_results(chunks, limit=limit)
        return {
            "query": query,
            "search_mode": search_mode,
            "filters": {
                "document_type": document_type,
                "service": service,
                "environment": environment,
            },
            "count": len(results),
            "total_matches": len(results),
            "results": results,
        }

    def _vector_search(
        self,
        *,
        query_vector: list[float],
        filters: dict[str, str],
        limit: int,
    ) -> list[dict[str, Any]]:
        mode = self._config.vector_search_mode
        if mode not in {"auto", "atlas", "local"}:
            raise ToolInputError(
                "MONGODB_VECTOR_SEARCH_MODE must be auto, atlas, or local."
            )

        if mode in {"auto", "atlas"}:
            try:
                return self._atlas_vector_search(
                    query_vector=query_vector,
                    filters=filters,
                    limit=limit,
                )
            except (OperationFailure, PyMongoError):
                if mode == "atlas":
                    raise

        return self._local_vector_search(
            query_vector=query_vector,
            filters=filters,
            limit=limit,
        )

    def _atlas_vector_search(
        self,
        *,
        query_vector: list[float],
        filters: dict[str, str],
        limit: int,
    ) -> list[dict[str, Any]]:
        vector_stage: dict[str, Any] = {
            "index": self._config.vector_index,
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": max(limit * 20, 100),
            "limit": max(limit * 4, 20),
        }
        if filters:
            vector_stage["filter"] = filters

        pipeline = [
            {"$vectorSearch": vector_stage},
            {
                "$project": {
                    "_id": 1,
                    "document_id": 1,
                    "chunk_id": 1,
                    "heading": 1,
                    "content": 1,
                    "document_type": 1,
                    "service": 1,
                    "environment": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        return list(self._chunks().aggregate(pipeline))

    def _local_vector_search(
        self,
        *,
        query_vector: list[float],
        filters: dict[str, str],
        limit: int,
    ) -> list[dict[str, Any]]:
        mongo_filter: dict[str, Any] = {**filters, "embedding.0": {"$exists": True}}
        candidates = self._chunks().find(
            mongo_filter,
            {
                "document_id": 1,
                "chunk_id": 1,
                "heading": 1,
                "content": 1,
                "document_type": 1,
                "service": 1,
                "environment": 1,
                "embedding": 1,
            },
        )

        scored: list[dict[str, Any]] = []
        for candidate in candidates:
            embedding = candidate.get("embedding")
            if not isinstance(embedding, list):
                continue
            candidate["score"] = _cosine_similarity(query_vector, embedding)
            candidate.pop("embedding", None)
            scored.append(candidate)

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[: max(limit * 4, 20)]

    def _keyword_search(
        self,
        *,
        query: str,
        filters: dict[str, str],
        limit: int,
    ) -> list[dict[str, Any]]:
        words = [word for word in re.findall(r"[a-z0-9_-]+", query.lower()) if len(word) > 2]
        mongo_filter: dict[str, Any] = dict(filters)
        if words:
            mongo_filter["$or"] = [
                {"content": {"$regex": re.escape(word), "$options": "i"}}
                for word in words
            ]

        results = list(self._chunks().find(mongo_filter).limit(max(limit * 4, 20)))
        for result in results:
            content = str(result.get("content", "")).lower()
            hits = sum(1 for word in words if word in content)
            result["score"] = hits / max(len(words), 1)
        results.sort(key=lambda item: item["score"], reverse=True)
        return results

    def _metadata_search(
        self,
        *,
        filters: dict[str, str],
        limit: int,
    ) -> list[dict[str, Any]]:
        results = list(self._chunks().find(filters).limit(max(limit * 4, 20)))
        for result in results:
            result["score"] = 1.0
        return results

    def _hydrate_results(
        self,
        chunks: list[dict[str, Any]],
        *,
        limit: int,
    ) -> list[JsonDict]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for chunk in chunks:
            grouped[str(chunk["document_id"])].append(chunk)

        results: list[JsonDict] = []
        for document_id, document_chunks in grouped.items():
            document = self._documents().find_one({"_id": document_id})
            if not document:
                continue
            ordered_chunks = sorted(
                document_chunks,
                key=lambda item: float(item.get("score", 0.0)),
                reverse=True,
            )
            result: JsonDict = dict(_clean_document(document))
            result["relevance_score"] = round(
                float(ordered_chunks[0].get("score", 0.0)), 6
            )
            result["semantic_snippets"] = [
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "heading": chunk.get("heading"),
                    "content": chunk.get("content"),
                    "score": round(float(chunk.get("score", 0.0)), 6),
                }
                for chunk in ordered_chunks[:3]
            ]
            result["matched_fields"] = ["semantic_content"]
            results.append(result)

        results.sort(
            key=lambda item: float(item.get("relevance_score", 0.0)),
            reverse=True,
        )
        return results[:limit]

    def _ensure_standard_indexes(self) -> None:
        self._documents().create_index([("document_id", ASCENDING)], unique=True)
        self._chunks().create_index([("document_id", ASCENDING)])
        self._chunks().create_index(
            [
                ("document_type", ASCENDING),
                ("service", ASCENDING),
                ("environment", ASCENDING),
            ]
        )

    def _get_client(self) -> MongoClient[dict[str, Any]]:
        if self._client is None:
            self._client = MongoClient(
                self._config.uri,
                serverSelectionTimeoutMS=self._config.server_selection_timeout_ms,
                connectTimeoutMS=self._config.server_selection_timeout_ms,
                socketTimeoutMS=30000,
                appname="enterprise-ai-ops-assistant",
            )
        return self._client

    def _documents(self) -> Collection[dict[str, Any]]:
        return self._get_client()[self._config.database][
            self._config.documents_collection
        ]

    def _chunks(self) -> Collection[dict[str, Any]]:
        return self._get_client()[self._config.database][self._config.chunks_collection]


def _chunk_document(
    document: ProjectDocumentRecord,
    *,
    indexed_at: datetime,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    sections = document.get("sections", [])
    for index, section in enumerate(sections, start=1):
        heading = section.get("heading", f"Section {index}")
        body = section.get("body", "").strip()
        if not body:
            continue
        content = f"{document['title']}\n{heading}\n{body}"
        chunk_id = f"{document['document_id']}-{index:03d}"
        chunks.append(
            {
                "_id": chunk_id,
                "chunk_id": chunk_id,
                "document_id": document["document_id"],
                "title": document["title"],
                "heading": heading,
                "content": content,
                "document_type": document["document_type"],
                "project": document["project"],
                "service": document["service"],
                "environment": document["environment"],
                "owner_team": document["owner_team"],
                "version": document["version"],
                "related_ticket_ids": document.get("related_ticket_ids", []),
                "tags": document.get("tags", []),
                "indexed_at": indexed_at,
            }
        )
    return chunks


def _metadata_filters(
    *,
    document_type: str | None,
    service: str | None,
    environment: str | None,
) -> dict[str, str]:
    filters: dict[str, str] = {}
    if document_type:
        filters["document_type"] = document_type
    if service:
        filters["service"] = service
    if environment:
        filters["environment"] = environment
    return filters


def _clean_document(document: dict[str, Any]) -> ProjectDocumentRecord:
    cleaned = {
        key: value
        for key, value in document.items()
        if key not in {"_id", "indexed_at"}
    }
    return cast(ProjectDocumentRecord, cleaned)


def _cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    if len(left_values) != len(right_values):
        return 0.0

    dot = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
