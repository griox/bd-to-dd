import unittest

from app.application.services.hybrid_search_service import HybridSearchService
from app.application.services.rerank_service import RerankService
from tests.fixtures import make_candidate


class HybridSearchServiceTest(unittest.TestCase):
    def test_rrf_deduplicates_and_combines_dense_sparse_rank(self):
        dense = [
            make_candidate("A", "dense A", 0.90, "dense"),
            make_candidate("B", "dense B", 0.80, "dense"),
        ]
        sparse = [
            make_candidate("B", "sparse B", 12.0, "sparse"),
            make_candidate("C", "sparse C", 10.0, "sparse"),
        ]

        fused = HybridSearchService().fuse(dense, sparse, limit=3, rrf_k=60)

        self.assertEqual([c.chunk_id for c in fused], ["B", "A", "C"])
        self.assertEqual(fused[0].source, "rrf")
        self.assertIn("sources", fused[0].metadata)
        self.assertEqual(set(fused[0].metadata["sources"]), {"dense", "sparse"})

    def test_rrf_respects_limit(self):
        dense = [make_candidate(str(i), f"dense {i}", 1.0, "dense") for i in range(5)]

        fused = HybridSearchService().fuse(dense, [], limit=2)

        self.assertEqual(len(fused), 2)


class RerankServiceTest(unittest.TestCase):
    def test_rerank_prefers_keyword_overlap_when_scores_are_close(self):
        candidates = [
            make_candidate("A", "payment batch retry logic", 0.030, "rrf"),
            make_candidate(
                "B",
                "user registration email password validation",
                0.029,
                "rrf",
            ),
        ]

        reranked = RerankService().rerank(
            "registration email validation",
            candidates,
            limit=1,
        )

        self.assertEqual(reranked[0].chunk_id, "B")
        self.assertEqual(reranked[0].source, "rerank")

    def test_rerank_uses_quality_and_reuse_signals(self):
        candidates = [
            make_candidate("A", "registration form", 0.030, "rrf", {"quality_score": 0.3}),
            make_candidate(
                "B",
                "registration form",
                0.029,
                "rrf",
                {"quality_score": 1.0, "reused_count": 4},
            ),
        ]

        reranked = RerankService().rerank("registration", candidates, limit=2)

        self.assertEqual(reranked[0].chunk_id, "B")
        self.assertEqual(reranked[0].metadata["rerank"]["algorithm"], "token_overlap_quality_reuse")

    def test_adaptive_top_k_stops_on_score_gap(self):
        candidates = [
            make_candidate("A", "A", 0.90, "rerank"),
            make_candidate("B", "B", 0.86, "rerank"),
            make_candidate("C", "C", 0.40, "rerank"),
            make_candidate("D", "D", 0.39, "rerank"),
        ]

        selected = RerankService().select_adaptive_top_k(
            candidates,
            min_limit=2,
            max_limit=4,
            score_gap=0.15,
        )

        self.assertEqual([candidate.chunk_id for candidate in selected], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
