from dataclasses import replace
from typing import Dict, List

from app.domain.entities.retrieval import RetrievalCandidate


class HybridSearchService:
    def fuse(
        self,
        dense_results: List[RetrievalCandidate],
        sparse_results: List[RetrievalCandidate],
        limit: int = 20,
        rrf_k: int = 60,
    ) -> List[RetrievalCandidate]:
        scores: Dict[str, float] = {}
        candidates: Dict[str, RetrievalCandidate] = {}
        sources: Dict[str, List[str]] = {}

        for result_list in [dense_results, sparse_results]:
            for rank, candidate in enumerate(result_list, start=1):
                chunk_id = candidate.chunk_id
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
                if chunk_id not in candidates:
                    candidates[chunk_id] = candidate
                sources.setdefault(chunk_id, [])
                if candidate.source not in sources[chunk_id]:
                    sources[chunk_id].append(candidate.source)

        ranked_ids = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)
        fused: List[RetrievalCandidate] = []
        for chunk_id in ranked_ids[:limit]:
            candidate = candidates[chunk_id]
            fused.append(
                replace(
                    candidate,
                    score=scores[chunk_id],
                    source="rrf",
                    metadata={**candidate.metadata, "sources": sources[chunk_id]},
                )
            )
        return fused

    def merge(self, semantic_results: List[str], keyword_results: List[str]) -> List[str]:
        merged: List[str] = []
        for item in semantic_results + keyword_results:
            if item not in merged:
                merged.append(item)
        return merged
