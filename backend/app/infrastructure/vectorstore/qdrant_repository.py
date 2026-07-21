"""Infrastructure adapter: Qdrant dense vector store.

Implements the DenseVectorStore port defined in
``app.domain.repositories.vector_store_repository``.

Rules:
- All qdrant_client code lives here; Application layer depends only on the
  DenseVectorStore Protocol, never on this class directly.
- Collection is created on first upsert if missing.
- Points use deterministic chunk IDs converted to UUID5 values so upserts
  stay reproducible.
- Payload structure mirrors the spec in planning.md Phase 4.
"""

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import (
    GEMINI_EMBEDDING_DIMENSIONS,
    QDRANT_COLLECTION,
    QDRANT_URL,
)
from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.retrieval import RetrievalCandidate


@dataclass
class _FallbackPointStruct:
    id: str
    vector: List[float]
    payload: Dict[str, Any]


@dataclass
class _FallbackVectorParams:
    size: int
    distance: str


class _FallbackDistance:
    COSINE = "cosine"


def _point_struct_cls():
    try:
        from qdrant_client.models import PointStruct  # noqa: PLC0415
    except ImportError:
        return _FallbackPointStruct
    return PointStruct


def _vector_params_cls():
    try:
        from qdrant_client.models import VectorParams  # noqa: PLC0415
    except ImportError:
        return _FallbackVectorParams
    return VectorParams


def _distance_cls():
    try:
        from qdrant_client.models import Distance  # noqa: PLC0415
    except ImportError:
        return _FallbackDistance
    return Distance


def _chunk_id_to_uuid(chunk_id: str) -> str:
    """Convert a deterministic string chunk ID to a UUID5 for Qdrant.

    UUID5 is deterministic — same input always produces the same UUID.
    This ensures idempotent upserts across repeated indexing runs.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


def _build_payload(chunk: KnowledgeChunk) -> Dict[str, Any]:
    """Flatten a KnowledgeChunk into the Qdrant point payload."""
    meta = dict(chunk.metadata)
    return {
        "chunk_id": chunk.id,
        "content": chunk.content,
        "doc_id": chunk.doc_id,
        "parent_chunk_id": chunk.parent_chunk_id,
        "root_chunk_id": chunk.root_chunk_id,
        "section_path": " > ".join(chunk.section_path) if chunk.section_path else "",
        "section_level": chunk.section_level,
        "sibling_order": chunk.sibling_order,
        "is_leaf": chunk.is_leaf,
        # Metadata fields (also at top-level for Qdrant payload filtering)
        "doc_type": meta.get("doc_type", "reviewed_dd"),
        "module_type": meta.get("module_type", ""),
        "project_context": meta.get("project_context", ""),
        "approval_status": meta.get("approval_status", "reviewed"),
        "component_id": meta.get("component_id", ""),
        "quality_score": float(meta.get("quality_score", 1.0)),
        "reused_count": int(meta.get("reused_count", 0)),
        "tags": meta.get("tags", []),
    }


def _build_filter(filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert a simple key=value filter dict into a Qdrant filter object.

    Only handles equality conditions. Returns None for empty filters.
    """
    if not filters:
        return None

    must_conditions = []
    for key, value in filters.items():
        must_conditions.append({
            "key": key,
            "match": {"value": value},
        })
    return {"must": must_conditions}


class QdrantVectorStore:
    """Qdrant implementation of DenseVectorStore.

    Application layer must depend on the DenseVectorStore Protocol,
    not this class directly (except in dependency wiring / deps.py).
    """

    def __init__(
        self,
        url: str = QDRANT_URL,
        collection: str = QDRANT_COLLECTION,
        vector_size: int = GEMINI_EMBEDDING_DIMENSIONS,
    ) -> None:
        self._url = url
        self._collection = collection
        self._vector_size = vector_size
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        """Attempt to connect to Qdrant. Fails silently if unavailable."""
        try:
            from qdrant_client import QdrantClient  # noqa: PLC0415
            self._client = QdrantClient(url=self._url, timeout=5)
            # Verify connectivity with a lightweight call
            self._client.get_collections()
            self._available = True
        except Exception:
            self._client = None
            self._available = False

    def _ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not exist."""
        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            distance = _distance_cls()
            vector_params = _vector_params_cls()
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=vector_params(
                    size=self._vector_size,
                    distance=distance.COSINE,
                ),
            )

    # ------------------------------------------------------------------
    # DenseVectorStore protocol
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._available

    def clear(self) -> None:
        """Replace the configured collection with an empty collection."""
        if not self._available:
            raise RuntimeError("Qdrant is unavailable; knowledge base cannot be cleared.")

        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection in existing:
            self._client.delete_collection(collection_name=self._collection)
        distance = _distance_cls()
        vector_params = _vector_params_cls()
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=vector_params(
                size=self._vector_size,
                distance=distance.COSINE,
            ),
        )

    def upsert_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Upsert KnowledgeChunks into Qdrant.

        Each chunk must already have its embedding vector stored in
        ``chunk.metadata["embedding"]`` (set by the ingestion use case
        before calling this method).

        Raises:
            ValueError: If a chunk is missing its embedding vector.
        """
        if not self._available or not chunks:
            return

        self._ensure_collection()
        point_struct = _point_struct_cls()

        points = []
        for chunk in chunks:
            embedding = chunk.metadata.get("embedding")
            if embedding is None:
                raise ValueError(
                    f"Chunk '{chunk.id}' is missing 'embedding' in metadata. "
                    "Embed documents before calling upsert_chunks()."
                )
            points.append(
                point_struct(
                    id=_chunk_id_to_uuid(chunk.id),
                    vector=list(embedding),
                    payload=_build_payload(chunk),
                )
            )

        self._client.upsert(collection_name=self._collection, points=points)

    def query_dense(
        self,
        query_vector: List[float],
        limit: int,
        filters: Dict[str, Any],
    ) -> List[RetrievalCandidate]:
        """Query Qdrant by cosine similarity, returning RetrievalCandidates."""
        if not self._available:
            return []

        qdrant_filter = _build_filter(filters)
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        results = getattr(response, "points", response)

        candidates = []
        for hit in results:
            payload = hit.payload or {}
            candidates.append(
                RetrievalCandidate(
                    chunk_id=payload.get("chunk_id", str(hit.id)),
                    content=payload.get("content", ""),
                    metadata={k: v for k, v in payload.items() if k != "content"},
                    score=float(hit.score),
                    source="dense",
                )
            )
        return candidates

    def status(self) -> Dict[str, Any]:
        """Return provider metadata for the KB status endpoint."""
        base = {
            "provider": "qdrant",
            "url": self._url,
            "collection": self._collection,
            "vectorSize": self._vector_size,
            "available": self._available,
        }
        if self._available:
            try:
                info = self._client.get_collection(self._collection)
                base["pointCount"] = info.points_count
            except Exception:
                pass
        return base

    def get_by_chunk_ids(self, chunk_ids: List[str]) -> List[RetrievalCandidate]:
        if not self._available or not chunk_ids:
            return []

        records = self._client.retrieve(
            collection_name=self._collection,
            ids=[_chunk_id_to_uuid(chunk_id) for chunk_id in chunk_ids],
            with_payload=True,
        )

        ordered_records = {}
        for record in records:
            payload = record.payload or {}
            candidate = RetrievalCandidate(
                chunk_id=payload.get("chunk_id", str(record.id)),
                content=payload.get("content", ""),
                metadata={k: v for k, v in payload.items() if k != "content"},
                score=1.0,
                source="rrf",
            )
            ordered_records[candidate.chunk_id] = candidate

        return [ordered_records[chunk_id] for chunk_id in chunk_ids if chunk_id in ordered_records]
