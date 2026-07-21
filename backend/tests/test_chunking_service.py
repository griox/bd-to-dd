"""Phase 2 tests: Hierarchical chunking and metadata extraction.

Review gate: Chunk IDs must be deterministic across repeated indexing runs.
"""

import json
import unittest
from typing import Any, Dict

from app.application.services.chunking_service import (
    ChunkingService,
    _extract_component_id,
    _split_long_content,
)
from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.sample_design import ReviewedDetailDesignSample


def _make_sample(
    sample_id: str,
    module_type: str = "screen",
    headings: Dict[str, Dict[str, str]] = None,
    extra_meta: Dict[str, Any] = None,
) -> ReviewedDetailDesignSample:
    """Helper: build a ReviewedDetailDesignSample from simple heading/section dicts."""
    if headings is None:
        headings = {
            "screen": {"01_UI_Design": "Form component"},
            "api": {"01_Contract": "POST /api/register"},
        }
    content = json.dumps({"detailDesign": headings})
    metadata = {"module_type": module_type, "review_status": "reviewed"}
    if extra_meta:
        metadata.update(extra_meta)
    return ReviewedDetailDesignSample(id=sample_id, content=content, metadata=metadata)


class ChunkStructureTest(unittest.TestCase):
    """Markdown with two headings produces root, two section parents, and leaves."""

    def setUp(self):
        self.service = ChunkingService()

    def test_two_headings_produce_root_two_parents_and_leaves(self):
        sample = _make_sample(
            "sample-reg",
            headings={
                "screen": {"01_UI_Design": "Form", "02_Components": "Button"},
                "api": {"01_Contract": "POST /api/register"},
            },
        )
        chunks = self.service.chunk_sample(sample)

        ids = [c.id for c in chunks]
        # Root chunk
        self.assertIn("sample-reg:root", ids)

        # Two section parents
        self.assertIn("sample-reg:screen", ids)
        self.assertIn("sample-reg:api", ids)

        # Leaf chunks
        self.assertIn("sample-reg:screen:01_UI_Design", ids)
        self.assertIn("sample-reg:screen:02_Components", ids)
        self.assertIn("sample-reg:api:01_Contract", ids)

        # Structural check
        root = next(c for c in chunks if c.id == "sample-reg:root")
        self.assertFalse(root.is_leaf)
        self.assertEqual(root.section_level, 0)

        screen_parent = next(c for c in chunks if c.id == "sample-reg:screen")
        self.assertFalse(screen_parent.is_leaf)
        self.assertEqual(screen_parent.section_level, 1)
        self.assertEqual(screen_parent.parent_chunk_id, "sample-reg:root")

        leaf = next(c for c in chunks if c.id == "sample-reg:screen:01_UI_Design")
        self.assertTrue(leaf.is_leaf)
        self.assertEqual(leaf.section_level, 2)
        self.assertEqual(leaf.parent_chunk_id, "sample-reg:screen")

    def test_all_chunks_carry_section_path_and_sibling_order(self):
        sample = _make_sample(
            "sample-x",
            headings={"screen": {"01_UI": "A", "02_Comp": "B"}},
        )
        chunks = self.service.chunk_sample(sample)
        for chunk in chunks:
            self.assertIsNotNone(chunk.section_path)
            self.assertGreaterEqual(chunk.sibling_order, 0)


class JapaneseComponentIdTest(unittest.TestCase):
    """Japanese screen file name extracts component_id when present."""

    def setUp(self):
        self.service = ChunkingService()

    def test_extracts_component_id_from_screen_prefix(self):
        sample_id = "screen-N9P90M4X4004W009"
        self.assertEqual(_extract_component_id(sample_id), "N9P90M4X4004W009")

    def test_extracts_component_id_from_dd_sample_prefix(self):
        sample_id = "dd-screen-N9P90M4X4004W009"
        self.assertEqual(_extract_component_id(sample_id), "N9P90M4X4004W009")

    def test_sample_id_without_dash_returns_full_id(self):
        self.assertEqual(_extract_component_id("noDash"), "noDash")

    def test_chunk_metadata_contains_component_id(self):
        sample = _make_sample("screen-N9P90M4X4004W009")
        chunks = self.service.chunk_sample(sample)
        for chunk in chunks:
            self.assertEqual(chunk.metadata["component_id"], "N9P90M4X4004W009")

    def test_chunk_metadata_contains_required_fields(self):
        sample = _make_sample("screen-ABC123", module_type="screen")
        chunks = self.service.chunk_sample(sample)
        leaf = next(c for c in chunks if c.is_leaf)
        required_keys = [
            "doc_id", "doc_type", "module_type", "project_context",
            "approval_status", "component_id", "quality_score",
            "reused_count", "tags", "content_type", "section_path",
            "parent_chunk_id",
        ]
        for key in required_keys:
            self.assertIn(key, leaf.metadata, f"Missing metadata key: {key}")

    def test_approval_status_prefers_new_metadata_field(self):
        sample = _make_sample(
            "screen-ABC123",
            module_type="screen",
            extra_meta={"approval_status": "approved", "review_status": "reviewed"},
        )
        chunks = self.service.chunk_sample(sample)
        leaf = next(c for c in chunks if c.is_leaf)

        self.assertEqual(leaf.metadata["approval_status"], "approved")


class EmptySectionTest(unittest.TestCase):
    """Empty or whitespace-only sections are ignored."""

    def setUp(self):
        self.service = ChunkingService()

    def test_empty_detail_design_produces_only_root(self):
        content = json.dumps({"detailDesign": {}})
        sample = ReviewedDetailDesignSample(
            id="sample-empty",
            content=content,
            metadata={"module_type": "screen", "review_status": "reviewed"},
        )
        chunks = self.service.chunk_sample(sample)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].id, "sample-empty:root")

    def test_invalid_json_content_produces_only_root(self):
        sample = ReviewedDetailDesignSample(
            id="sample-bad",
            content="not json at all",
            metadata={"module_type": "screen", "review_status": "reviewed"},
        )
        chunks = self.service.chunk_sample(sample)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].id, "sample-bad:root")

    def test_whitespace_only_leaf_sections_are_ignored(self):
        sample = _make_sample(
            "sample-empty-leaf",
            headings={
                "screen": {
                    "01_UI_Design": "   ",
                    "02_Components": "",
                    "03_Data_Models": "User state model",
                }
            },
        )
        chunks = self.service.chunk_sample(sample)
        ids = {chunk.id for chunk in chunks}

        self.assertNotIn("sample-empty-leaf:screen:01_UI_Design", ids)
        self.assertNotIn("sample-empty-leaf:screen:02_Components", ids)
        self.assertIn("sample-empty-leaf:screen:03_Data_Models", ids)


class LongLeafSplitTest(unittest.TestCase):
    """Split long leaf chunks preserve same parent_chunk_id and increment sibling_order."""

    def setUp(self):
        self.service = ChunkingService()

    def test_short_leaf_not_split(self):
        result = _split_long_content("Short content", max_chars=1500)
        self.assertEqual(len(result), 1)

    def test_long_content_splits_by_paragraph(self):
        # Build content > 1500 chars with clear paragraph breaks
        paragraph = "word " * 60  # ~300 chars
        content = "\n\n".join([paragraph] * 8)  # ~2400 chars total
        parts = _split_long_content(content, max_chars=1500)
        self.assertGreater(len(parts), 1)
        for part in parts:
            self.assertLessEqual(len(part), 1500 + len(paragraph))  # graceful overflow

    def test_long_leaf_gets_split_chunks_with_same_parent(self):
        # Build a long text with newlines so the line-based splitter has split points
        line = "A very detailed API specification line covering request, response, and validation. "
        long_text = "\n".join([line.strip()] * 30)  # 30 lines × ~80 chars ≈ 2400 chars
        self.assertGreater(len(long_text), 1500, "Precondition: content must exceed split threshold")

        sample = _make_sample(
            "sample-long",
            headings={"api": {"01_Contract": long_text}},
        )
        chunks = self.service.chunk_sample(sample)
        split_chunks = [
            c for c in chunks
            if c.is_leaf and c.parent_chunk_id == "sample-long:api"
        ]
        self.assertGreater(len(split_chunks), 1)
        # All split parts share same parent
        parent_ids = {c.parent_chunk_id for c in split_chunks}
        self.assertEqual(parent_ids, {"sample-long:api"})
        # sibling_order increments
        orders = sorted(c.sibling_order for c in split_chunks)
        self.assertEqual(orders, list(range(len(split_chunks))))


    def test_short_leaf_flagged_for_parent_merge(self):
        short_text = "Short"  # < 120 chars
        sample = _make_sample(
            "sample-short",
            headings={"screen": {"01_UI_Design": short_text}},
        )
        chunks = self.service.chunk_sample(sample)
        leaf = next(c for c in chunks if c.id == "sample-short:screen:01_UI_Design")
        self.assertTrue(leaf.metadata.get("allow_parent_merge"))

    def test_parent_chunk_contains_compact_child_context(self):
        sample = _make_sample(
            "sample-parent-context",
            headings={
                "screen": {
                    "01_UI_Design": "Screen has a search form.",
                    "02_Components": "Search button and result list.",
                }
            },
        )
        chunks = self.service.chunk_sample(sample)
        parent = next(c for c in chunks if c.id == "sample-parent-context:screen")

        self.assertIn("01_UI_Design", parent.content)
        self.assertIn("Screen has a search form.", parent.content)
        self.assertIn("02_Components", parent.content)
        self.assertIn("Search button and result list.", parent.content)


class DeterministicIdTest(unittest.TestCase):
    """Chunk IDs are deterministic across repeated indexing runs."""

    def setUp(self):
        self.service = ChunkingService()

    def test_repeated_chunking_produces_identical_ids(self):
        sample = _make_sample(
            "sample-det",
            headings={"screen": {"01_UI": "Form"}, "api": {"01_Contract": "POST"}},
        )
        ids_run1 = [c.id for c in self.service.chunk_sample(sample)]
        ids_run2 = [c.id for c in self.service.chunk_sample(sample)]
        self.assertEqual(ids_run1, ids_run2)

    def test_chunk_sample_from_real_seed_data(self):
        """Exercise chunking against the real JSON seed samples."""
        from app.infrastructure.persistence.postgres.seed_loader import JsonSeedSampleLoader

        samples = JsonSeedSampleLoader().load()
        self.assertGreater(len(samples), 0)

        for sample in samples:
            chunks = self.service.chunk_sample(sample)
            # Each sample must produce at least a root chunk
            self.assertGreaterEqual(len(chunks), 1)
            # All chunk IDs must be unique within the sample
            ids = [c.id for c in chunks]
            self.assertEqual(len(ids), len(set(ids)), f"Duplicate IDs in {sample.id}")
            # Root chunk present
            root_ids = [c.id for c in chunks if not c.is_leaf and c.section_level == 0]
            self.assertEqual(len(root_ids), 1)

    def test_legacy_chunk_detail_design_still_works(self):
        """Backward compatibility: old flat chunking API should not break."""
        chunks = self.service.chunk_detail_design(
            "legacy-id",
            {"screen": {"01_UI": "Form"}, "api": {"01_Contract": "Spec"}},
        )
        self.assertEqual(len(chunks), 2)
        ids = {c.id for c in chunks}
        self.assertIn("legacy-id:screen:01_UI", ids)
        self.assertIn("legacy-id:api:01_Contract", ids)


if __name__ == "__main__":
    unittest.main()
