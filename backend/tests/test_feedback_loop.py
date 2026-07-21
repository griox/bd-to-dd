import unittest

from app.application.use_cases.ingest_reviewed_dd import KnowledgeBaseService
from tests.fixtures import FakeDenseStore, FakeEmbedder, FakeSparseIndex


class FeedbackLoopTest(unittest.TestCase):
    def test_approved_detail_design_can_be_ingested_as_reviewed_sample(self):
        service = KnowledgeBaseService(
            dense_vector_store=FakeDenseStore(),
            dense_embedding_service=FakeEmbedder(),
            sparse_keyword_index=FakeSparseIndex(),
            auto_seed=False,
        )
        result = {
            "detailDesign": {
                "screen": {
                    "01_UI_Design": "Registration form",
                    "02_Components": "EmailInput, PasswordInput",
                }
            },
            "review": {"status": "PASS"},
        }

        status = service.ingest_generated_reviewed_dd("project-1", "job-1", result)

        self.assertEqual(status["status"], "seeded")
        self.assertGreater(status["chunkCount"], 0)


if __name__ == "__main__":
    unittest.main()
