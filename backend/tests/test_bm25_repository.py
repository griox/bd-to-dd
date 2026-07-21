"""Phase 5 tests: BM25 Local Sparse Index.

Review gate: BM25 implementation should be replaceable later by SPLADE
without changing application use cases.
"""

import json
import os
import tempfile
import unittest
from typing import Any, Dict, List

from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.retrieval import RetrievalCandidate
from app.infrastructure.search.bm25_repository import (
    BM25Repository,
    _tokenize,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk(
    chunk_id: str,
    content: str,
    module_type: str = "screen",
    approval_status: str = "reviewed",
    **extra_meta: Any,
) -> KnowledgeChunk:
    meta: Dict[str, Any] = {
        "doc_type": "reviewed_dd",
        "module_type": module_type,
        "approval_status": approval_status,
        "quality_score": 1.0,
        "reused_count": 0,
    }
    meta.update(extra_meta)
    return KnowledgeChunk(
        id=chunk_id,
        content=content,
        metadata=meta,
        doc_id=chunk_id.split(":")[0],
        is_leaf=True,
    )


def _tmp_repo() -> BM25Repository:
    """Return a BM25Repository backed by a temp file (auto-cleaned by OS)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    os.unlink(tmp.name)  # Remove so repo starts fresh
    return BM25Repository(index_path=tmp.name)


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class TokenizerTest(unittest.TestCase):
    def test_lowercases_ascii(self):
        self.assertEqual(_tokenize("Hello World"), ["hello", "world"])

    def test_splits_on_punctuation(self):
        tokens = _tokenize("screen_id, API.name, class-Name")
        self.assertIn("screen_id", tokens)
        self.assertIn("api", tokens)
        self.assertIn("name", tokens)

    def test_handles_empty_string(self):
        self.assertEqual(_tokenize(""), [])

    def test_handles_whitespace_only(self):
        self.assertEqual(_tokenize("   "), [])


# ---------------------------------------------------------------------------
# Technical term ranking
# ---------------------------------------------------------------------------

class TechnicalTermRankingTest(unittest.TestCase):
    """Exact technical term such as N9P90M4X4004W009 ranks matching chunk first."""

    def setUp(self):
        self.repo = _tmp_repo()
        self.repo.upsert_chunks([
            _chunk("chunk-A", "Screen N9P90M4X4004W009 API integration details"),
            _chunk("chunk-B", "Generic screen with form components and buttons"),
            _chunk("chunk-C", "Batch job for order sync with external partner"),
        ])

    def test_exact_technical_id_ranks_matching_chunk_first(self):
        results = self.repo.query_sparse("N9P90M4X4004W009", limit=3, filters={})
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].chunk_id, "chunk-A")
        self.assertEqual(results[0].source, "sparse")

    def test_results_are_sorted_descending_by_score(self):
        results = self.repo.query_sparse("screen", limit=5, filters={})
        scores = [r.score for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))


# ---------------------------------------------------------------------------
# Metadata filter
# ---------------------------------------------------------------------------

class MetadataFilterTest(unittest.TestCase):
    """Metadata filter excludes wrong module_type."""

    def setUp(self):
        self.repo = _tmp_repo()
        self.repo.upsert_chunks([
            _chunk("screen-1", "User registration screen with form", module_type="screen"),
            _chunk("api-1", "POST /api/register endpoint specification", module_type="api"),
            _chunk("screen-2", "Registration confirmation screen UI", module_type="screen"),
        ])

    def test_filter_excludes_wrong_module_type(self):
        results = self.repo.query_sparse(
            "registration", limit=10, filters={"module_type": "api"}
        )
        for r in results:
            self.assertEqual(r.metadata["module_type"], "api")

    def test_filter_returns_only_matching_module(self):
        results = self.repo.query_sparse(
            "screen registration", limit=10, filters={"module_type": "screen"}
        )
        self.assertGreater(len(results), 0)
        chunk_ids = {r.chunk_id for r in results}
        self.assertNotIn("api-1", chunk_ids)

    def test_empty_filter_returns_all_matching(self):
        results = self.repo.query_sparse("registration", limit=10, filters={})
        self.assertGreaterEqual(len(results), 2)


# ---------------------------------------------------------------------------
# Persist and reload
# ---------------------------------------------------------------------------

class PersistReloadTest(unittest.TestCase):
    """Persist and reload produce same query result."""

    def test_reload_produces_same_results(self):
        # Use a named temp file that persists between repo instances
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            # First repo: index and save
            repo1 = BM25Repository(index_path=path)
            repo1.upsert_chunks([
                _chunk("chunk-A", "Screen N9P90M4X4004W009 API details"),
                _chunk("chunk-B", "Generic form component design"),
            ])
            results_before = [r.chunk_id for r in repo1.query_sparse("N9P90M4X4004W009", limit=5, filters={})]

            # Second repo: reload from same path
            repo2 = BM25Repository(index_path=path)
            results_after = [r.chunk_id for r in repo2.query_sparse("N9P90M4X4004W009", limit=5, filters={})]

            self.assertEqual(results_before, results_after)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_index_file_is_created_after_upsert(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        os.unlink(path)  # Start fresh

        try:
            repo = BM25Repository(index_path=path)
            self.assertFalse(os.path.exists(path))
            repo.upsert_chunks([_chunk("c1", "some content")])
            self.assertTrue(os.path.exists(path))
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_upsert_is_idempotent(self):
        """Same chunk upserted twice should not duplicate."""
        repo = _tmp_repo()
        chunk = _chunk("chunk-X", "Registration screen UI form")
        repo.upsert_chunks([chunk])
        repo.upsert_chunks([chunk])  # second upsert — same ID

        self.assertEqual(repo.status()["chunkCount"], 1)

    def test_upsert_updates_content_in_place(self):
        """Updated content for same chunk_id replaces old content."""
        repo = _tmp_repo()
        repo.upsert_chunks([_chunk("chunk-X", "old content about forms")])
        repo.upsert_chunks([_chunk("chunk-X", "new content about N9P90M4X4004W009")])

        results = repo.query_sparse("N9P90M4X4004W009", limit=5, filters={})
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].chunk_id, "chunk-X")

    def test_clear_removes_memory_and_persisted_documents(self):
        repo = _tmp_repo()
        repo.upsert_chunks([_chunk("chunk-X", "reviewed DD")])

        repo.clear()

        self.assertEqual(repo.status()["chunkCount"], 0)
        reloaded = BM25Repository(index_path=str(repo._index_path))
        self.assertEqual(reloaded.status()["chunkCount"], 0)


# ---------------------------------------------------------------------------
# Empty query
# ---------------------------------------------------------------------------

class EmptyQueryTest(unittest.TestCase):
    """Empty query returns empty results."""

    def setUp(self):
        self.repo = _tmp_repo()
        self.repo.upsert_chunks([_chunk("c1", "some content")])

    def test_empty_string_returns_empty(self):
        self.assertEqual(self.repo.query_sparse("", limit=5, filters={}), [])

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(self.repo.query_sparse("   ", limit=5, filters={}), [])

    def test_empty_index_returns_empty(self):
        empty_repo = _tmp_repo()
        self.assertEqual(empty_repo.query_sparse("anything", limit=5, filters={}), [])


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class StatusTest(unittest.TestCase):
    def test_status_reports_provider_bm25(self):
        repo = _tmp_repo()
        s = repo.status()
        self.assertEqual(s["provider"], "bm25")

    def test_status_reports_chunk_count(self):
        repo = _tmp_repo()
        repo.upsert_chunks([
            _chunk("c1", "content one"),
            _chunk("c2", "content two"),
        ])
        self.assertEqual(repo.status()["chunkCount"], 2)

    def test_empty_repo_chunk_count_is_zero(self):
        repo = _tmp_repo()
        self.assertEqual(repo.status()["chunkCount"], 0)


# ---------------------------------------------------------------------------
# Protocol isolation — SparseKeywordIndex port
# ---------------------------------------------------------------------------

class ProtocolIsolationTest(unittest.TestCase):
    """BM25Repository satisfies SparseKeywordIndex protocol structurally."""

    def test_has_upsert_chunks_method(self):
        repo = _tmp_repo()
        self.assertTrue(callable(getattr(repo, "upsert_chunks", None)))

    def test_has_query_sparse_method(self):
        repo = _tmp_repo()
        self.assertTrue(callable(getattr(repo, "query_sparse", None)))

    def test_has_status_method(self):
        repo = _tmp_repo()
        self.assertTrue(callable(getattr(repo, "status", None)))

    def test_bm25_module_not_imported_by_domain(self):
        import sys
        domain_modules = [m for m in sys.modules if m.startswith("app.domain")]
        for mod in domain_modules:
            src = getattr(sys.modules[mod], "__file__", "") or ""
            self.assertNotIn("bm25", src, f"Domain module {mod} references bm25")


if __name__ == "__main__":
    unittest.main()
