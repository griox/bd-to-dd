"""Phase 6 tests: Ingestion Use Case for Qdrant + BM25.

Review gate:
- Ingestion use case returns unavailable when Qdrant is unavailable.
- Single Gemini embedding call must cover all chunks (no per-chunk calls).
"""

import json
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock

from fastapi import BackgroundTasks

from app.application.services.chunking_service import ChunkingService
from app.application.use_cases.ingest_reviewed_dd import KnowledgeBaseService
from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.sample_design import ReviewedDetailDesignSample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample(
    sample_id: str = "sample-reg",
    module_type: str = "screen",
    headings: Dict[str, Dict[str, str]] = None,
) -> ReviewedDetailDesignSample:
    if headings is None:
        headings = {"screen": {"01_UI_Design": "Form", "02_Components": "Button"}}
    content = json.dumps({"detailDesign": headings})
    return ReviewedDetailDesignSample(
        id=sample_id,
        content=content,
        metadata={"module_type": module_type, "review_status": "reviewed"},
    )


def _mock_loader(samples: List[ReviewedDetailDesignSample]) -> MagicMock:
    loader = MagicMock()
    loader.load.return_value = samples
    loader.source.return_value = "mock://seed"
    return loader


def _mock_qdrant(available: bool = True) -> MagicMock:
    store = MagicMock()
    store.is_available.return_value = available
    store.status.return_value = {
        "provider": "qdrant",
        "available": available,
        "pointCount": 10 if available else 0,
    }
    return store


def _mock_gemini(n_vectors: int = 5) -> MagicMock:
    embedder = MagicMock()
    embedder.embed_documents.return_value = [[0.1] * 3 for _ in range(n_vectors)]
    embedder.describe.return_value = {"provider": "gemini", "model": "gemini-embedding-001"}
    return embedder


def _mock_bm25() -> MagicMock:
    bm25 = MagicMock()
    bm25.status.return_value = {"provider": "bm25", "chunkCount": 0}
    return bm25


# ---------------------------------------------------------------------------
# Dual-index ingestion
# ---------------------------------------------------------------------------

class DualIndexIngestionTest(unittest.TestCase):
    """Seeding indexes both Qdrant and BM25 in single pipeline."""

    def _make_service(self, samples, qdrant, embedder, bm25):
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader(samples),
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )
        svc.reindex()
        return svc

    def test_both_qdrant_and_bm25_upsert_called(self):
        samples = [_make_sample()]
        # Figure out how many chunks get produced
        chunks = ChunkingService().chunk_samples(samples)
        n = len(chunks)

        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()

        svc = self._make_service(samples, qdrant, embedder, bm25)

        qdrant.upsert_chunks.assert_called_once()
        bm25.upsert_chunks.assert_called_once()

    def test_gemini_called_once_for_all_chunks(self):
        """Single Gemini embed_documents call, not one per chunk."""
        samples = [_make_sample("s1"), _make_sample("s2")]
        chunks = ChunkingService().chunk_samples(samples)
        n = len(chunks)

        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()

        svc = self._make_service(samples, qdrant, embedder, bm25)

        # embed_documents called exactly once
        self.assertEqual(embedder.embed_documents.call_count, 1)
        # with all chunk texts in one call
        called_texts = embedder.embed_documents.call_args[0][0]
        self.assertEqual(len(called_texts), n)

    def test_bm25_chunks_do_not_contain_embedding_key(self):
        """Embedding vector must be stripped before BM25 indexing."""
        samples = [_make_sample()]
        chunks = ChunkingService().chunk_samples(samples)
        n = len(chunks)

        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()

        svc = self._make_service(samples, qdrant, embedder, bm25)

        bm25_call_chunks: List[KnowledgeChunk] = bm25.upsert_chunks.call_args[0][0]
        for chunk in bm25_call_chunks:
            self.assertNotIn(
                "embedding", chunk.metadata,
                f"Chunk {chunk.id} has 'embedding' in BM25 metadata — should be stripped"
            )

    def test_qdrant_chunks_contain_embedding_key(self):
        """Qdrant chunks must include the embedding vector."""
        samples = [_make_sample()]
        chunks = ChunkingService().chunk_samples(samples)
        n = len(chunks)

        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()

        svc = self._make_service(samples, qdrant, embedder, bm25)

        qdrant_call_chunks: List[KnowledgeChunk] = qdrant.upsert_chunks.call_args[0][0]
        for chunk in qdrant_call_chunks:
            self.assertIn("embedding", chunk.metadata)

    def test_seed_result_contains_sparse_index_key(self):
        """Return dict must include sparseIndex when BM25 is configured."""
        samples = [_make_sample()]
        chunks = ChunkingService().chunk_samples(samples)
        n = len(chunks)

        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()

        # Re-invoke by calling seed_default_samples directly
        svc = KnowledgeBaseService.__new__(KnowledgeBaseService)
        svc.sample_loader = _mock_loader(samples)
        svc.dense_vector_store = qdrant
        svc.dense_embedding_service = embedder
        svc.chunking_service = ChunkingService()
        svc.sparse_keyword_index = bm25
        result = svc._seed_dense_samples()

        self.assertIn("sparseIndex", result)
        self.assertIn("sparse", result)
        self.assertIn("dense", result)
        self.assertEqual(result["chunkCount"], len(chunks))
        self.assertEqual(result["status"], "seeded")
        self.assertEqual(result["seeded"], 1)


# ---------------------------------------------------------------------------
# Qdrant unavailable
# ---------------------------------------------------------------------------

class QdrantUnavailableTest(unittest.TestCase):
    """Ingestion returns unavailable when Qdrant is unreachable."""

    def test_seed_returns_unavailable_when_qdrant_down(self):
        svc = KnowledgeBaseService.__new__(KnowledgeBaseService)
        svc.sample_loader = _mock_loader([_make_sample()])
        svc.dense_vector_store = _mock_qdrant(available=False)
        svc.dense_embedding_service = _mock_gemini()
        svc.chunking_service = ChunkingService()
        svc.sparse_keyword_index = None

        result = svc._seed_dense_samples()

        self.assertEqual(result["status"], "unavailable")

    def test_no_embed_call_when_qdrant_unavailable(self):
        embedder = _mock_gemini()
        svc = KnowledgeBaseService.__new__(KnowledgeBaseService)
        svc.sample_loader = _mock_loader([_make_sample()])
        svc.dense_vector_store = _mock_qdrant(available=False)
        svc.dense_embedding_service = embedder
        svc.chunking_service = ChunkingService()
        svc.sparse_keyword_index = None

        svc._seed_dense_samples()

        embedder.embed_documents.assert_not_called()


# ---------------------------------------------------------------------------
# Explicit reindex and startup safety
# ---------------------------------------------------------------------------

class ExplicitReindexTest(unittest.TestCase):
    """Dense ingestion should be triggered explicitly, not as startup side effect."""

    def test_auto_seed_false_does_not_call_external_services(self):
        samples = [_make_sample()]
        qdrant = _mock_qdrant()
        embedder = _mock_gemini()
        bm25 = _mock_bm25()

        KnowledgeBaseService(
            sample_loader=_mock_loader(samples),
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )

        embedder.embed_documents.assert_not_called()
        qdrant.upsert_chunks.assert_not_called()
        bm25.upsert_chunks.assert_not_called()

    def test_reindex_raises_when_qdrant_is_unavailable(self):
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader([_make_sample()]),
            dense_vector_store=_mock_qdrant(available=False),
            dense_embedding_service=_mock_gemini(),
            sparse_keyword_index=_mock_bm25(),
            auto_seed=False,
        )

        with self.assertRaisesRegex(RuntimeError, "Qdrant is unavailable"):
            svc.reindex()

    def test_reindex_raises_when_no_reviewed_dd_samples_exist(self):
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader([]),
            dense_vector_store=_mock_qdrant(),
            dense_embedding_service=_mock_gemini(),
            sparse_keyword_index=_mock_bm25(),
            auto_seed=False,
        )

        with self.assertRaisesRegex(RuntimeError, "No reviewed DD samples"):
            svc.reindex()

    def test_reindex_triggers_dense_and_sparse_ingestion(self):
        samples = [_make_sample()]
        n = len(ChunkingService().chunk_samples(samples))
        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader(samples),
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )

        result = svc.reindex()

        self.assertEqual(result["status"], "seeded")
        qdrant.clear.assert_called_once_with()
        bm25.clear.assert_called_once_with()
        embedder.embed_documents.assert_called_once()
        qdrant.upsert_chunks.assert_called_once()
        bm25.upsert_chunks.assert_called_once()

    def test_embedding_count_mismatch_raises_and_skips_upsert(self):
        samples = [_make_sample()]
        n = len(ChunkingService().chunk_samples(samples))
        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n - 1)
        bm25 = _mock_bm25()
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader(samples),
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )

        with self.assertRaises(RuntimeError):
            svc.reindex()

        qdrant.upsert_chunks.assert_not_called()
        bm25.upsert_chunks.assert_not_called()

    def test_reindex_result_exposes_dense_and_sparse_aliases(self):
        samples = [_make_sample()]
        n = len(ChunkingService().chunk_samples(samples))
        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader(samples),
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )

        result = svc.reindex()

        self.assertEqual(result["dense"]["provider"], "qdrant")
        self.assertEqual(result["sparse"]["provider"], "bm25")
        self.assertEqual(result["sampleCount"], 1)
        self.assertEqual(result["chunkCount"], n)

    def test_reindex_updates_progress_with_chunk_embedding_and_metadata_steps(self):
        samples = [_make_sample()]
        n = len(ChunkingService().chunk_samples(samples))
        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()
        svc = KnowledgeBaseService(
            sample_loader=_mock_loader(samples),
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )

        svc.reindex()
        progress = svc.get_progress()

        self.assertEqual(progress["status"], "completed")
        self.assertEqual(progress["operation"], "reindex_reviewed_dd")
        step_keys = [step["key"] for step in progress["steps"]]
        self.assertIn("chunking", step_keys)
        self.assertIn("embedding", step_keys)
        self.assertIn("metadata", step_keys)

        chunking_step = next(step for step in progress["steps"] if step["key"] == "chunking")
        embedding_step = next(step for step in progress["steps"] if step["key"] == "embedding")
        metadata_step = next(step for step in progress["steps"] if step["key"] == "metadata")

        self.assertEqual(chunking_step["output"]["chunkCount"], n)
        self.assertEqual(embedding_step["output"]["embeddingCount"], n)
        self.assertTrue(metadata_step["output"]["preview"][0]["hasEmbedding"])

    def test_reindex_accepts_reviewed_dd_loader_samples(self):
        sample = _make_sample("dd-screen-N9P90M4X4004W009")
        samples = [sample]
        n = len(ChunkingService().chunk_samples(samples))
        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)
        bm25 = _mock_bm25()
        loader = _mock_loader(samples)
        loader.source.return_value = "INPUT"
        svc = KnowledgeBaseService(
            sample_loader=loader,
            dense_vector_store=qdrant,
            dense_embedding_service=embedder,
            sparse_keyword_index=bm25,
            auto_seed=False,
        )

        result = svc.reindex()

        self.assertEqual(result["reviewedDetailDesigns"], ["dd-screen-N9P90M4X4004W009"])
        self.assertEqual(result["chunkCount"], n)
        qdrant.upsert_chunks.assert_called_once()
        bm25.upsert_chunks.assert_called_once()


# ---------------------------------------------------------------------------
# No sparse index configured (BM25 optional)
# ---------------------------------------------------------------------------

class NoBM25ConfiguredTest(unittest.TestCase):
    """When sparse_keyword_index is None, ingestion still works (Qdrant-only)."""

    def test_qdrant_still_upserted_without_bm25(self):
        samples = [_make_sample()]
        chunks = ChunkingService().chunk_samples(samples)
        n = len(chunks)

        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=n)

        svc = KnowledgeBaseService.__new__(KnowledgeBaseService)
        svc.sample_loader = _mock_loader(samples)
        svc.dense_vector_store = qdrant
        svc.dense_embedding_service = embedder
        svc.chunking_service = ChunkingService()
        svc.sparse_keyword_index = None

        result = svc._seed_dense_samples()

        qdrant.upsert_chunks.assert_called_once()
        self.assertNotIn("sparseIndex", result)
        self.assertEqual(result["status"], "seeded")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class StatusTest(unittest.TestCase):
    """get_status() includes sparseIndex block when BM25 is configured."""

    def test_get_status_includes_sparse_index(self):
        qdrant = _mock_qdrant()
        embedder = _mock_gemini(n_vectors=0)

        bm25 = MagicMock()
        bm25.status.return_value = {"provider": "bm25", "chunkCount": 42}

        svc = KnowledgeBaseService.__new__(KnowledgeBaseService)
        svc.sample_loader = _mock_loader([])
        svc.dense_vector_store = qdrant
        svc.dense_embedding_service = embedder
        svc.chunking_service = ChunkingService()
        svc.sparse_keyword_index = bm25

        status = svc.get_status()

        self.assertIn("sparseIndex", status)
        self.assertIn("sparse", status)
        self.assertIn("dense", status)
        self.assertIn("progress", status)
        self.assertEqual(status["sparseIndex"]["provider"], "bm25")
        self.assertEqual(status["sparseIndex"]["chunkCount"], 42)


# ---------------------------------------------------------------------------
# Presentation endpoint
# ---------------------------------------------------------------------------

class ReindexEndpointTest(unittest.TestCase):
    """Admin API exposes explicit reindex instead of relying on constructor seed."""

    def test_reindex_endpoint_calls_knowledge_base_reindex(self):
        from app.presentation.api.v1 import router as api_router

        original_kb = api_router.knowledge_base
        fake_kb = MagicMock()
        fake_kb.queue_reindex.return_value = {"status": "queued", "operation": "reindex_reviewed_dd"}
        background_tasks = BackgroundTasks()
        api_router.knowledge_base = fake_kb
        try:
            response = api_router.reindex_knowledge_base(background_tasks)
        finally:
            api_router.knowledge_base = original_kb

        fake_kb.queue_reindex.assert_called_once()
        self.assertEqual(len(background_tasks.tasks), 1)
        self.assertEqual(response["data"]["status"], "queued")


if __name__ == "__main__":
    unittest.main()
