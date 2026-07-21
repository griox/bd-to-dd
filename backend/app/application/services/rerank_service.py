import re
from dataclasses import replace
from typing import List

from app.domain.entities.retrieval import RetrievalCandidate


def _tokens(text: str) -> set:
    return {token for token in re.split(r"[^\w]+", text.lower()) if token}


class RerankService:
    def rerank(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
        limit: int = 8,
    ) -> List[RetrievalCandidate]:
        query_tokens = _tokens(query)

        def score(candidate: RetrievalCandidate) -> float:
            candidate_tokens = _tokens(candidate.content)
            overlap = len(query_tokens & candidate_tokens)
            quality_score = float(candidate.metadata.get("quality_score", 1.0) or 1.0)
            reused_count = int(candidate.metadata.get("reused_count", 0) or 0)
            reuse_boost = min(reused_count, 10) * 0.005
            quality_boost = max(0.0, min(quality_score, 1.0)) * 0.05
            return candidate.score + (overlap * 0.01) + quality_boost + reuse_boost

        ranked = sorted(candidates, key=score, reverse=True)
        return [
            replace(
                candidate,
                score=score(candidate),
                source="rerank",
                metadata={
                    **candidate.metadata,
                    "rerank": {
                        "algorithm": "token_overlap_quality_reuse",
                        "quality_score": candidate.metadata.get("quality_score", 1.0),
                        "reused_count": candidate.metadata.get("reused_count", 0),
                    },
                },
            )
            for candidate in ranked[:limit]
        ]

    def select_adaptive_top_k(
        self,
        candidates: List[RetrievalCandidate],
        min_limit: int,
        max_limit: int,
        score_gap: float,
    ) -> List[RetrievalCandidate]:
        if not candidates:
            return []

        selected = candidates[:max(1, min_limit)]
        previous_score = selected[-1].score
        for candidate in candidates[len(selected):max_limit]:
            gap = previous_score - candidate.score
            if gap > score_gap:
                break
            selected.append(candidate)
            previous_score = candidate.score
        return selected

    def top(self, candidates: List[str], limit: int = 2) -> List[str]:
        return candidates[:limit]
