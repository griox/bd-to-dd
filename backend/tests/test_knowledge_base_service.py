import unittest
import json
from typing import Any, Dict, List

from app.application.use_cases.ingest_reviewed_dd import (
    KnowledgeBaseService,
    load_seed_samples,
)
from app.application.services.retrieval_query_service import build_retrieval_query
from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.sample_design import ReviewedDetailDesignSample


class FakeSampleLoader:
    def __init__(self, samples: List[ReviewedDetailDesignSample]) -> None:
        self._samples = samples

    def load(self) -> List[ReviewedDetailDesignSample]:
        return self._samples

    def source(self) -> str:
        return "fake"


class FakeDenseEmbeddingService:
    def __init__(self) -> None:
        self.embedded_texts: List[str] = []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self.embedded_texts = texts
        return [[float(i), float(i + 1)] for i, _ in enumerate(texts)]

    def embed_query(self, text: str) -> List[float]:
        return [1.0, 2.0]

    def describe(self) -> Dict[str, Any]:
        return {"provider": "gemini", "model": "gemini-embedding-001"}


class FakeDenseVectorStore:
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.upserted_chunks: List[KnowledgeChunk] = []

    def upsert_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        self.upserted_chunks = chunks

    def query_dense(self, query_vector, limit, filters):
        return []

    def is_available(self) -> bool:
        return self.available

    def status(self) -> Dict[str, Any]:
        return {
            "provider": "qdrant",
            "collection": "bd_to_dd_chunks",
            "available": self.available,
            "pointCount": len(self.upserted_chunks),
        }


class KnowledgeBaseServiceTest(unittest.TestCase):
    def test_add_sample_indexes_content_in_dense_store(self):
        embedder = FakeDenseEmbeddingService()
        store = FakeDenseVectorStore()
        service = KnowledgeBaseService(
            sample_loader=FakeSampleLoader([]),
            dense_vector_store=store,
            dense_embedding_service=embedder,
            auto_seed=False,
        )

        result = service.add_sample(
            '{"detailDesign":{"screen":{"01_UI_Design":"Image-extracted layout"}}}'
        )

        self.assertEqual(result["status"], "indexed")
        self.assertGreater(len(store.upserted_chunks), 0)
        self.assertTrue(
            all("embedding" in chunk.metadata for chunk in store.upserted_chunks)
        )

    def test_load_seed_samples_returns_reviewed_samples(self):
        samples = load_seed_samples()

        self.assertGreaterEqual(len(samples), 3)
        self.assertTrue(all(sample["id"] for sample in samples))
        self.assertTrue(all(sample["content"] for sample in samples))
        self.assertTrue(all("id" in sample for sample in samples))

    def test_seed_samples_use_schema_aligned_detail_design_json(self):
        samples = load_seed_samples()

        for sample in samples:
            payload = json.loads(sample["content"]) if isinstance(sample["content"], str) and sample["content"].startswith("{") else sample
            self.assertIn("detailDesign", payload)
            self.assertTrue(any(k in payload["detailDesign"] for k in ("screen", "api", "batch")))

    def test_status_exposes_reviewed_design_embedding_and_vector_db_blocks(self):
        status = KnowledgeBaseService().get_status()

        self.assertIn("reviewedDetailDesigns", status)
        self.assertIn("embedding", status)
        self.assertIn("vectorDb", status)
        self.assertEqual(status["embedding"]["provider"], "gemini")
        self.assertEqual(status["vectorDb"]["provider"], "qdrant")
        self.assertIn("sparseIndex", status)
        self.assertEqual(status["sparseIndex"]["provider"], "bm25")

    def test_qdrant_ingestion_chunks_embeds_and_upserts_reviewed_samples(self):
        sample = ReviewedDetailDesignSample(
            id="screen-N9P90M4X4004W009",
            content=json.dumps({
                "detailDesign": {
                    "screen": {
                        "01_UI": "Registration screen layout",
                        "02_API": "POST /users/register",
                    }
                }
            }),
            metadata={
                "module_type": "screen",
                "approval_status": "reviewed",
                "quality_score": 1.0,
                "reused_count": 0,
            },
        )
        embedder = FakeDenseEmbeddingService()
        store = FakeDenseVectorStore()

        service = KnowledgeBaseService(
            sample_loader=FakeSampleLoader([sample]),
            dense_vector_store=store,
            dense_embedding_service=embedder,
        )

        self.assertGreater(len(store.upserted_chunks), 0)
        self.assertEqual(embedder.embedded_texts, [c.content for c in store.upserted_chunks])
        self.assertTrue(
            all("embedding" in chunk.metadata for chunk in store.upserted_chunks)
        )
        self.assertEqual(store.upserted_chunks[0].metadata["embedding"], [0.0, 1.0])
        self.assertEqual(service.get_status()["vectorDb"]["provider"], "qdrant")

    def test_qdrant_ingestion_returns_unavailable_without_upserting(self):
        store = FakeDenseVectorStore(available=False)
        service = KnowledgeBaseService(
            sample_loader=FakeSampleLoader([]),
            dense_vector_store=store,
            dense_embedding_service=FakeDenseEmbeddingService(),
        )

        status = service.seed_default_samples()

        self.assertEqual(status["status"], "unavailable")
        self.assertEqual(store.upserted_chunks, [])

    def test_build_retrieval_query_combines_bd_and_analytics(self):
        query = build_retrieval_query(
            basic_design="User Registration flow with email verification",
            basic_design_analytics={
                "summary": "Registration module for user onboarding",
                "entities": ["User", "VerificationToken"],
                "businessFlows": ["Submit registration", "Verify email"],
            },
        )

        self.assertIn("User Registration flow with email verification", query)
        self.assertIn("Registration module for user onboarding", query)
        self.assertIn("User VerificationToken", query)
        self.assertIn("Submit registration", query)

    def test_build_retrieval_query_handles_structured_analytics_values(self):
        query = build_retrieval_query(
            basic_design="User Registration flow with email verification",
            basic_design_analytics={
                "summary": "Registration module for user onboarding",
                "entities": [{"name": "User"}, {"name": "VerificationToken"}],
                "businessFlows": [{"step": "Submit registration"}],
            },
        )

        self.assertIn('"name": "User"', query)
        self.assertIn('"step": "Submit registration"', query)


if __name__ == "__main__":
    unittest.main()
