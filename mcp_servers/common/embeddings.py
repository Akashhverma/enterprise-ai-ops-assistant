from __future__ import annotations

import os
from collections.abc import Sequence

from openai import OpenAI

from .errors import ToolInputError
from .mongodb_config import EmbeddingConfig, get_embedding_config


class OpenAIEmbeddingService:
    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self._config = config or get_embedding_config()
        self._client: OpenAI | None = None

    @property
    def dimensions(self) -> int:
        return self._config.dimensions

    @property
    def model(self) -> str:
        return self._config.model

    def embed_query(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise ToolInputError("A non-empty query is required for semantic search.")
        return self.embed_texts([normalized])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        normalized = [text.strip() for text in texts if text.strip()]
        if not normalized:
            return []

        client = self._get_client()
        embeddings: list[list[float]] = []
        batch_size = max(1, self._config.batch_size)

        for offset in range(0, len(normalized), batch_size):
            batch = normalized[offset : offset + batch_size]
            response = client.embeddings.create(
                model=self._config.model,
                input=batch,
                dimensions=self._config.dimensions,
                encoding_format="float",
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            embeddings.extend([item.embedding for item in ordered])

        return embeddings

    def _get_client(self) -> OpenAI:
        if self._client is not None:
            return self._client

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ToolInputError(
                "OPENAI_API_KEY is required to generate document embeddings."
            )

        self._client = OpenAI(api_key=api_key)
        return self._client
