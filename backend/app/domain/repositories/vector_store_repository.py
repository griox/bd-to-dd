"""Domain-level port contracts for the knowledge base.

Rules
-----
- This module defines *only* Protocols and abstract types.
- No infrastructure package (qdrant_client, openai, rank_bm25,
  langchain, FastAPI, SQLAlchemy) may be imported here.
"""

from pathlib import Path
from typing import Any, Dict, List, Protocol

from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.retrieval import RetrievalCandidate
from app.domain.entities.sample_design import ReviewedDetailDesignSample


# ---------------------------------------------------------------------------
# Legacy contracts kept for older callers that expect document-level retrieval.
# ---------------------------------------------------------------------------


class EmbeddingDescriptor(Protocol):
    """Describes the embedding model/provider in use."""

    def describe(self) -> Dict[str, Any]:
        ...


class DenseEmbeddingService(EmbeddingDescriptor, Protocol):
    """Port for API-based dense embedding services."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...

    def embed_query(self, text: str) -> List[float]:
        ...


class RagSampleLoader(Protocol):
    """Loads reviewed DD samples from a backing store (JSON file, DB, etc.)."""

    def load(self) -> List[ReviewedDetailDesignSample]:
        ...

    def source(self) -> str:
        ...


class VisionDesignExtractor(Protocol):
    """Extracts structured screen sections from an image input."""

    def extract_screen_sections(self, image_path: Path) -> Dict[str, str]:
        ...


class VectorStore(Protocol):
    """Simple document-level vector store contract used by older callers."""

    def is_available(self) -> bool:
        ...

    def add_document(self, content: str, metadata: Dict[str, Any]) -> None:
        ...

    def upsert_samples(self, samples: List[ReviewedDetailDesignSample]) -> None:
        ...

    def count(self) -> int:
        ...

    def query(self, query: str, limit: int) -> List[str]:
        ...

    def status(self) -> Dict[str, Any]:
        ...


# ---------------------------------------------------------------------------
# Phase 1+ contracts (hybrid retrieval path — Qdrant + BM25)
# ---------------------------------------------------------------------------


class DenseVectorStore(Protocol):
    """Port for a dense vector database (implemented by QdrantVectorStore).

    Application services depend only on this Protocol — never on the
    concrete ``qdrant_client`` class.
    """

    def clear(self) -> None:
        """Remove every chunk from the configured knowledge-base collection."""
        ...

    def upsert_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Upsert chunks using their deterministic ``id`` as the point key."""
        ...

    def query_dense(
        self,
        query_vector: List[float],
        limit: int,
        filters: Dict[str, Any],
    ) -> List[RetrievalCandidate]:
        """Return up to ``limit`` candidates sorted by descending cosine score."""
        ...

    def is_available(self) -> bool:
        """Return False when the Qdrant service is unreachable."""
        ...

    def status(self) -> Dict[str, Any]:
        """Return provider, URL, collection name, and availability info."""
        ...

    def get_by_chunk_ids(self, chunk_ids: List[str]) -> List[RetrievalCandidate]:
        """Fetch deterministic chunk IDs for parent-context assembly."""
        ...


class SparseKeywordIndex(Protocol):
    """Port for a local sparse keyword index (implemented by BM25Repository).

    Replaceable by SPLADE or miniCOIL later without touching application code.
    """

    def clear(self) -> None:
        """Remove every chunk from the sparse knowledge-base index."""
        ...

    def upsert_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Index chunks; persist index to disk after upsert."""
        ...

    def query_sparse(
        self,
        query: str,
        limit: int,
        filters: Dict[str, Any],
    ) -> List[RetrievalCandidate]:
        """Return up to ``limit`` keyword-matched candidates."""
        ...

    def status(self) -> Dict[str, Any]:
        """Return provider name and indexed chunk count."""
        ...
