"""Phase 1 tests: Domain contracts for hybrid retrieval.

Review gate: Domain layer must not import qdrant_client, openai, rank_bm25,
FastAPI, SQLAlchemy, or LangChain.
"""

import importlib
import sys
import unittest
from typing import Any, Dict, List


class KnowledgeChunkTest(unittest.TestCase):
    """KnowledgeChunk stores hierarchy fields and keeps metadata immutable."""

    def setUp(self):
        from app.domain.entities.chunk import KnowledgeChunk
        self.KnowledgeChunk = KnowledgeChunk

    def test_stores_hierarchy_fields(self):
        chunk = self.KnowledgeChunk(
            id="screen-ABC:Screen設計",
            content="Screen design section",
            doc_id="screen-ABC",
            parent_chunk_id="screen-ABC:root",
            root_chunk_id="screen-ABC:root",
            section_path=("Screen設計",),
            section_level=1,
            sibling_order=0,
            is_leaf=False,
        )

        self.assertEqual(chunk.id, "screen-ABC:Screen設計")
        self.assertEqual(chunk.doc_id, "screen-ABC")
        self.assertEqual(chunk.parent_chunk_id, "screen-ABC:root")
        self.assertEqual(chunk.root_chunk_id, "screen-ABC:root")
        self.assertEqual(chunk.section_path, ("Screen設計",))
        self.assertEqual(chunk.section_level, 1)
        self.assertEqual(chunk.sibling_order, 0)
        self.assertFalse(chunk.is_leaf)

    def test_metadata_is_immutable_by_frozen_dataclass(self):
        chunk = self.KnowledgeChunk(
            id="chunk-1",
            content="content",
            metadata={"quality_score": 1.0},
        )
        # Frozen dataclass raises FrozenInstanceError on direct field assignment
        with self.assertRaises(Exception):
            chunk.id = "new-id"  # type: ignore[misc]

    def test_metadata_mapping_cannot_be_mutated(self):
        chunk = self.KnowledgeChunk(
            id="chunk-1",
            content="content",
            metadata={"quality_score": 1.0},
        )

        with self.assertRaises(TypeError):
            chunk.metadata["quality_score"] = 0.5

    def test_default_values_are_sensible(self):
        chunk = self.KnowledgeChunk(id="chunk-min", content="minimal")
        self.assertIsNone(chunk.doc_id)
        self.assertIsNone(chunk.parent_chunk_id)
        self.assertEqual(chunk.section_path, ())
        self.assertEqual(chunk.section_level, 0)
        self.assertEqual(chunk.sibling_order, 0)
        self.assertTrue(chunk.is_leaf)

    def test_leaf_chunk_carries_parent_reference(self):
        leaf = self.KnowledgeChunk(
            id="screen-ABC:04_API",
            content="API integration details",
            doc_id="screen-ABC",
            parent_chunk_id="screen-ABC:Screen設計",
            root_chunk_id="screen-ABC:root",
            section_path=("Screen設計", "04_API_Integration"),
            section_level=2,
            sibling_order=3,
            is_leaf=True,
        )
        self.assertTrue(leaf.is_leaf)
        self.assertEqual(leaf.parent_chunk_id, "screen-ABC:Screen設計")
        self.assertEqual(leaf.sibling_order, 3)


class RetrievalCandidateTest(unittest.TestCase):
    """RetrievalCandidate carries score and source."""

    def setUp(self):
        from app.domain.entities.retrieval import RetrievalCandidate
        self.RetrievalCandidate = RetrievalCandidate

    def test_carries_score_and_source(self):
        candidate = self.RetrievalCandidate(
            chunk_id="screen-ABC:04_API",
            content="API integration details",
            metadata={"quality_score": 0.9, "module_type": "screen"},
            score=0.87,
            source="dense",
        )
        self.assertEqual(candidate.chunk_id, "screen-ABC:04_API")
        self.assertAlmostEqual(candidate.score, 0.87)
        self.assertEqual(candidate.source, "dense")

    def test_supports_all_source_literals(self):
        from app.domain.entities.retrieval import RetrievalCandidate

        for source in ("dense", "sparse", "rrf", "rerank"):
            c = RetrievalCandidate(
                chunk_id="c1",
                content="x",
                metadata={},
                score=0.5,
                source=source,  # type: ignore[arg-type]
            )
            self.assertEqual(c.source, source)

    def test_assembled_context_serializes_to_dict(self):
        from app.domain.entities.retrieval import AssembledContext, RetrievalCandidate

        c = RetrievalCandidate(
            chunk_id="screen-ABC:04_API",
            content="API section",
            metadata={
                "parent_chunk_id": "screen-ABC:Screen設計",
                "section_path": "Screen設計 > 04_API_Integration",
            },
            score=0.031,
            source="rrf",
        )
        ctx = AssembledContext(references=[c], reference_count=1)
        d = ctx.to_dict()

        self.assertEqual(d["referenceCount"], 1)
        ref = d["references"][0]
        self.assertEqual(ref["chunkId"], "screen-ABC:04_API")
        self.assertEqual(ref["parentChunkId"], "screen-ABC:Screen設計")
        self.assertIn("rrf", ref["sources"])


class DomainLayerIsolationTest(unittest.TestCase):
    """Protocol import does not import infrastructure packages."""

    FORBIDDEN = [
        "qdrant_client",
        "openai",
        "rank_bm25",
        "fastapi",
        "sqlalchemy",
        "langchain",
    ]

    def _imported_modules(self, module_name: str) -> List[str]:
        """Return list of top-level module names loaded when importing module_name."""
        # Remove cached versions to force a clean import graph inspection
        before = set(sys.modules.keys())
        importlib.import_module(module_name)
        after = set(sys.modules.keys())
        return list(after - before)

    def test_chunk_entity_does_not_import_infrastructure(self):
        # chunk.py must already be importable without infra packages
        loaded = self._imported_modules("app.domain.entities.chunk")
        for forbidden in self.FORBIDDEN:
            self.assertFalse(
                any(m.startswith(forbidden) for m in loaded),
                f"chunk.py pulled in forbidden package: {forbidden}",
            )

    def test_retrieval_entity_does_not_import_infrastructure(self):
        loaded = self._imported_modules("app.domain.entities.retrieval")
        for forbidden in self.FORBIDDEN:
            self.assertFalse(
                any(m.startswith(forbidden) for m in loaded),
                f"retrieval.py pulled in forbidden package: {forbidden}",
            )

    def test_vector_store_repository_does_not_import_infrastructure(self):
        loaded = self._imported_modules(
            "app.domain.repositories.vector_store_repository"
        )
        for forbidden in self.FORBIDDEN:
            self.assertFalse(
                any(m.startswith(forbidden) for m in loaded),
                f"vector_store_repository.py pulled in forbidden package: {forbidden}",
            )


if __name__ == "__main__":
    unittest.main()
