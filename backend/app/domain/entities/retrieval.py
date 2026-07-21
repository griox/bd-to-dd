"""Domain value objects for hybrid retrieval results.

These types are the shared contract between application services
(hybrid_search_service, context_assembly_service) and the infrastructure
adapters (qdrant_repository, bm25_repository).

No infrastructure package (qdrant_client, openai, rank_bm25) may be
imported into this module.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal


@dataclass(frozen=True)
class RetrievalCandidate:
    """A single candidate returned by dense or sparse retrieval.

    Attributes:
        chunk_id:  Matches ``KnowledgeChunk.id`` and the Qdrant payload
                   ``chunk_id`` field — used for deduplication in RRF.
        content:   Chunk text copied into context assembly without further
                   DB lookups.
        metadata:  Payload fields (doc_id, section_path, quality_score,
                   parent_chunk_id, etc.) forwarded from the store.
        score:     Raw score from the retrieval backend (cosine similarity
                   for dense, BM25 score for sparse, RRF fused score after
                   merging).
        source:    Which stage produced this candidate:
                   - ``"dense"``   — Qdrant HNSW query
                   - ``"sparse"``  — BM25 local index
                   - ``"rrf"``     — after Reciprocal Rank Fusion
                   - ``"rerank"``  — after optional cross-encoder rerank
    """

    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: Literal["dense", "sparse", "rrf", "rerank"]


@dataclass(frozen=True)
class AssembledContext:
    """Final context package handed to the LLM generation stage.

    Attributes:
        references:       Ordered list of candidates selected for the prompt.
        reference_count:  Convenience field — equals ``len(references)``.
    """

    references: List[RetrievalCandidate] = field(default_factory=list)
    reference_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the JSON shape consumed by the frontend and prompts."""
        return {
            "references": [
                {
                    "chunkId": c.chunk_id,
                    "parentChunkId": c.metadata.get("parent_chunk_id"),
                    "sectionPath": c.metadata.get("section_path", ""),
                    "content": c.content,
                    "score": c.score,
                    "sources": c.metadata.get("sources", [c.source]),
                }
                for c in self.references
            ],
            "referenceCount": self.reference_count,
        }
