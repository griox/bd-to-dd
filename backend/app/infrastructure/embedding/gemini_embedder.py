"""Infrastructure adapter: Gemini Embeddings API.

Implements the DenseEmbeddingService port for ingestion and retrieval. All
Gemini-specific SDK calls stay in this infrastructure module.
"""

import math
import re
import time
from typing import Any, Dict, List, Optional

from app.core.config import (
    GEMINI_EMBEDDING_API_KEY,
    GEMINI_EMBEDDING_BATCH_SIZE,
    GEMINI_EMBEDDING_DIMENSIONS,
    GEMINI_EMBEDDING_MODEL,
)


class InfrastructureError(Exception):
    """Raised when an external embedding service call fails."""


def _rate_limit_retry_delay(exc: Exception) -> Optional[int]:
    message = str(exc)
    if "429" not in message or "RESOURCE_EXHAUSTED" not in message:
        return None
    match = re.search(r"retry in\s+([0-9.]+)s", message, flags=re.IGNORECASE)
    return max(1, math.ceil(float(match.group(1)))) if match else 60


class GeminiEmbeddingService:
    """Dense embedding adapter backed by Gemini embedding models."""

    def __init__(
        self,
        api_key: str = GEMINI_EMBEDDING_API_KEY,
        model: str = GEMINI_EMBEDDING_MODEL,
        dimensions: int = GEMINI_EMBEDDING_DIMENSIONS,
        batch_size: int = GEMINI_EMBEDDING_BATCH_SIZE,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._batch_size = max(1, batch_size)

    def _embed_batch(self, client, texts: List[str]) -> List[List[float]]:  # type: ignore[no-untyped-def]
        response = client.models.embed_content(
            model=self._model,
            contents=texts,
            config={"output_dimensionality": self._dimensions},
        )
        return [list(item.values) for item in response.embeddings]

    def _get_client(self):  # type: ignore[return]
        if not self._api_key:
            raise InfrastructureError(
                "GEMINI_EMBEDDING_API_KEY is not configured. "
                "Set GEMINI_EMBEDDING_API_KEY or GEMINI_API_KEY before embedding."
            )

        try:
            from google import genai  # noqa: PLC0415
        except ImportError as exc:
            raise InfrastructureError(
                "google-genai package is not installed. Add 'google-genai' to requirements.txt."
            ) from exc

        return genai.Client(api_key=self._api_key)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            client = self._get_client()
            embeddings: List[List[float]] = []
            for start_index in range(0, len(texts), self._batch_size):
                batch = texts[start_index : start_index + self._batch_size]
                for attempt in range(4):
                    try:
                        embeddings.extend(self._embed_batch(client, batch))
                        break
                    except Exception as exc:
                        retry_delay = _rate_limit_retry_delay(exc)
                        if retry_delay is None or attempt == 3:
                            raise
                        time.sleep(retry_delay)
            return embeddings
        except InfrastructureError:
            raise
        except Exception as exc:
            batch_count = (len(texts) + self._batch_size - 1) // self._batch_size
            raise InfrastructureError(
                "Gemini embed_documents failed "
                f"(texts={len(texts)}, batch_size={self._batch_size}, batches={batch_count}): {exc}"
            ) from exc

    def embed_query(self, text: str) -> List[float]:
        results = self.embed_documents([text])
        return results[0]

    def describe(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self._model,
            "dimensions": self._dimensions,
            "batchSize": self._batch_size,
            "configured": bool(self._api_key),
        }

    def is_available(self) -> bool:
        return bool(self._api_key)
