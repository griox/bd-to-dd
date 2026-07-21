import unittest

from app.application.services.retrieval_query_service import build_retrieval_request
from app.application.use_cases.ingest_reviewed_dd import KnowledgeBaseService
from tests.fixtures import FakeDenseStore, FakeEmbedder, FakeSparseIndex, make_candidate


class KnowledgeBaseRetrievalTest(unittest.TestCase):
    def test_retrieve_context_uses_rrf_and_returns_top_k(self):
        dense = [
            make_candidate("A", "dense A", 0.9, "dense"),
            make_candidate("B", "dense B", 0.8, "dense"),
        ]
        sparse = [
            make_candidate("B", "sparse B", 12.0, "sparse"),
            make_candidate("C", "sparse C", 10.0, "sparse"),
        ]
        service = KnowledgeBaseService(
            sample_loader=None,
            dense_vector_store=FakeDenseStore(results=dense),
            dense_embedding_service=FakeEmbedder(),
            sparse_keyword_index=FakeSparseIndex(results=sparse),
            auto_seed=False,
        )

        context = service.retrieve_context("registration screen")

        self.assertEqual(context[0], "dense B")
        self.assertEqual(len(context), 3)

    def test_retrieve_context_passes_filters_to_dense_and_sparse(self):
        dense_store = FakeDenseStore(results=[make_candidate("A", "dense A", 0.9, "dense")])
        sparse_index = FakeSparseIndex(results=[make_candidate("A", "dense A", 10.0, "sparse")])
        service = KnowledgeBaseService(
            sample_loader=None,
            dense_vector_store=dense_store,
            dense_embedding_service=FakeEmbedder(),
            sparse_keyword_index=sparse_index,
            auto_seed=False,
        )

        service.retrieve_context(
            "registration screen",
            filters={"approval_status": "reviewed", "module_type": "screen"},
        )

        self.assertEqual(
            dense_store.last_filters,
            {"approval_status": "reviewed", "module_type": "screen"},
        )
        self.assertEqual(
            sparse_index.last_filters,
            {"approval_status": "reviewed", "module_type": "screen"},
        )


class RetrievalRequestBuilderTest(unittest.TestCase):
    def test_build_retrieval_request_adds_confident_filters(self):
        request = build_retrieval_request(
            "Implement screen N9P90M4X4004W002 registration flow",
            {
                "summary": "Screen-level detail design for registration",
                "modules": ["screen"],
                "screens": ["N9P90M4X4004W002 Registration"],
                "entities": ["User"],
                "businessFlows": ["Open screen", "Submit form"],
            },
        )

        self.assertEqual(request["filters"]["approval_status"], "reviewed")
        self.assertEqual(request["filters"]["module_type"], "screen")
        self.assertEqual(request["filters"]["component_id"], "N9P90M4X4004W002")

    def test_build_retrieval_request_skips_ambiguous_filters(self):
        request = build_retrieval_request(
            "Support screen and api generation",
            {
                "summary": "Cross-module change",
                "modules": ["screen", "api"],
                "screens": ["Registration"],
                "entities": ["User"],
                "businessFlows": ["Generate screen", "Call API"],
            },
        )

        self.assertEqual(request["filters"], {"approval_status": "reviewed"})

    def test_build_retrieval_request_separates_dense_and_sparse_queries(self):
        request = build_retrieval_request(
            "Login screen N9P90M4X4004W002",
            {
                "summary": "Login module",
                "modules": ["screen"],
                "screens": ["N9P90M4X4004W002 Login"],
                "entities": ["User"],
                "businessFlows": ["Submit login"],
                "apiCandidates": ["POST /api/v1/auth/login"],
            },
        )

        self.assertIn("denseQuery", request)
        self.assertIn("sparseQuery", request)
        self.assertIn("segments", request)
        self.assertIn("POST /api/v1/auth/login", request["sparseQuery"])
        self.assertGreater(len(request["segments"]), 1)


if __name__ == "__main__":
    unittest.main()
