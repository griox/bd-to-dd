"""Phase 4 tests: Qdrant Dense Store And Payload Indexing.

Review gate: Application layer must depend on DenseVectorStore protocol,
not QdrantVectorStore directly. All tests mock qdrant_client.
"""

import unittest
from types import MappingProxyType
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.retrieval import RetrievalCandidate
from app.infrastructure.vectorstore.qdrant_repository import (
    QdrantVectorStore,
    _build_filter,
    _build_payload,
    _chunk_id_to_uuid,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk(
    chunk_id: str = "screen-ABC:screen:01_UI",
    content: str = "UI design section",
    embedding: List[float] = None,
    **kwargs: Any,
) -> KnowledgeChunk:
    meta: Dict[str, Any] = {
        "doc_type": "reviewed_dd",
        "module_type": "screen",
        "approval_status": "reviewed",
        "quality_score": 1.0,
        "reused_count": 0,
        "tags": ["screen"],
    }
    if embedding is not None:
        meta["embedding"] = embedding
    meta.update(kwargs.pop("extra_meta", {}))
    return KnowledgeChunk(
        id=chunk_id,
        content=content,
        metadata=meta,
        doc_id="screen-ABC",
        parent_chunk_id="screen-ABC:screen",
        root_chunk_id="screen-ABC:root",
        section_path=("screen-ABC", "screen", "01_UI"),
        section_level=2,
        sibling_order=0,
        is_leaf=True,
        **kwargs,
    )


def _make_store(available: bool = True) -> QdrantVectorStore:
    """Return a QdrantVectorStore with a mocked internal client."""
    store = QdrantVectorStore.__new__(QdrantVectorStore)
    store._url = "http://localhost:6333"
    store._collection = "bd_to_dd_chunks"
    store._vector_size = 1536
    store._available = available
    store._client = MagicMock() if available else None
    if available:
        # Stub get_collections so _ensure_collection thinks collection exists
        mock_col = MagicMock()
        mock_col.name = "bd_to_dd_chunks"
        store._client.get_collections.return_value = MagicMock(collections=[mock_col])
    return store


# ---------------------------------------------------------------------------
# UUID helper
# ---------------------------------------------------------------------------

class ChunkIdToUuidTest(unittest.TestCase):
    def test_deterministic_for_same_input(self):
        uid1 = _chunk_id_to_uuid("screen-ABC:01_UI")
        uid2 = _chunk_id_to_uuid("screen-ABC:01_UI")
        self.assertEqual(uid1, uid2)

    def test_different_ids_produce_different_uuids(self):
        self.assertNotEqual(
            _chunk_id_to_uuid("chunk-A"),
            _chunk_id_to_uuid("chunk-B"),
        )

    def test_output_is_valid_uuid_string(self):
        import uuid as uuid_mod
        uid = _chunk_id_to_uuid("some-chunk")
        # Should not raise
        uuid_mod.UUID(uid)


# ---------------------------------------------------------------------------
# Collection creation
# ---------------------------------------------------------------------------

class CollectionCreationTest(unittest.TestCase):
    """Repository creates collection when missing."""

    def test_creates_collection_when_not_present(self):
        store = _make_store()
        # Simulate collection NOT existing
        store._client.get_collections.return_value = MagicMock(collections=[])

        chunk = _chunk(embedding=[0.1] * 1536)
        store.upsert_chunks([chunk])

        store._client.create_collection.assert_called_once()
        call_kwargs = store._client.create_collection.call_args.kwargs
        self.assertEqual(call_kwargs["collection_name"], "bd_to_dd_chunks")

    def test_does_not_recreate_existing_collection(self):
        store = _make_store()
        # Collection already exists
        mock_col = MagicMock()
        mock_col.name = "bd_to_dd_chunks"
        store._client.get_collections.return_value = MagicMock(collections=[mock_col])

        store.upsert_chunks([_chunk(embedding=[0.1] * 1536)])
        store._client.create_collection.assert_not_called()

    def test_clear_deletes_and_recreates_collection(self):
        store = _make_store()

        store.clear()

        store._client.delete_collection.assert_called_once_with(
            collection_name="bd_to_dd_chunks"
        )
        store._client.create_collection.assert_called_once()



# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

class UpsertTest(unittest.TestCase):
    """Upsert maps KnowledgeChunk into Qdrant point with payload."""

    def test_upsert_calls_qdrant_with_correct_payload(self):
        store = _make_store()
        chunk = _chunk(
            chunk_id="screen-ABC:screen:01_UI",
            content="Form component",
            embedding=[0.5] * 1536,
        )
        store.upsert_chunks([chunk])

        store._client.upsert.assert_called_once()
        call_args = store._client.upsert.call_args
        points = call_args.kwargs.get("points") or call_args.args[1]
        self.assertEqual(len(points), 1)

        point = points[0]
        self.assertEqual(point.payload["chunk_id"], "screen-ABC:screen:01_UI")
        self.assertEqual(point.payload["content"], "Form component")
        self.assertEqual(point.payload["module_type"], "screen")
        self.assertEqual(point.payload["approval_status"], "reviewed")

    def test_upsert_uses_deterministic_uuid_as_point_id(self):
        store = _make_store()
        chunk = _chunk(chunk_id="screen-ABC:screen:01_UI", embedding=[0.1] * 1536)
        store.upsert_chunks([chunk])

        points = store._client.upsert.call_args.kwargs.get("points") or \
                 store._client.upsert.call_args.args[1]
        expected_uuid = _chunk_id_to_uuid("screen-ABC:screen:01_UI")
        self.assertEqual(str(points[0].id), expected_uuid)

    def test_upsert_raises_value_error_when_embedding_missing(self):
        store = _make_store()
        chunk = _chunk()  # no embedding in metadata
        with self.assertRaises(ValueError) as ctx:
            store.upsert_chunks([chunk])
        self.assertIn("embedding", str(ctx.exception))

    def test_upsert_noop_when_unavailable(self):
        store = _make_store(available=False)
        # Should not raise even without a client
        store.upsert_chunks([_chunk(embedding=[0.1] * 1536)])

    def test_upsert_noop_for_empty_list(self):
        store = _make_store()
        store.upsert_chunks([])
        store._client.upsert.assert_not_called()


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

class QueryTest(unittest.TestCase):
    """Query returns candidates sorted by Qdrant score."""

    def _make_hit(self, chunk_id: str, content: str, score: float) -> MagicMock:
        hit = MagicMock()
        hit.id = _chunk_id_to_uuid(chunk_id)
        hit.score = score
        hit.payload = {
            "chunk_id": chunk_id,
            "content": content,
            "module_type": "screen",
            "approval_status": "reviewed",
        }
        return hit

    def test_query_returns_retrieval_candidates(self):
        store = _make_store()
        store._client.query_points.return_value = MagicMock(points=[
            self._make_hit("chunk-A", "content A", 0.9),
            self._make_hit("chunk-B", "content B", 0.7),
        ])

        results = store.query_dense(
            query_vector=[0.1] * 1536,
            limit=5,
            filters={},
        )

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], RetrievalCandidate)
        self.assertEqual(results[0].chunk_id, "chunk-A")
        self.assertAlmostEqual(results[0].score, 0.9)
        self.assertEqual(results[0].source, "dense")

    def test_query_passes_filter_to_qdrant(self):
        store = _make_store()
        store._client.query_points.return_value = MagicMock(points=[])

        store.query_dense(
            query_vector=[0.1] * 3,
            limit=5,
            filters={"module_type": "screen", "approval_status": "reviewed"},
        )

        call_kwargs = store._client.query_points.call_args.kwargs
        self.assertIsNotNone(call_kwargs.get("query_filter"))
        must = call_kwargs["query_filter"]["must"]
        keys = {cond["key"] for cond in must}
        self.assertIn("module_type", keys)
        self.assertIn("approval_status", keys)

    def test_query_handles_clients_returning_plain_point_lists(self):
        store = _make_store()
        store._client.query_points.return_value = [
            self._make_hit("chunk-A", "content A", 0.9),
        ]

        results = store.query_dense(
            query_vector=[0.1] * 3,
            limit=5,
            filters={},
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk-A")

    def test_query_returns_empty_when_unavailable(self):
        store = _make_store(available=False)
        result = store.query_dense([0.1] * 3, limit=5, filters={})
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# Filter builder
# ---------------------------------------------------------------------------

class FilterBuilderTest(unittest.TestCase):
    """Filter maps module_type=screen and approval_status=reviewed."""

    def test_empty_filters_returns_none(self):
        self.assertIsNone(_build_filter({}))

    def test_single_field_filter(self):
        f = _build_filter({"module_type": "screen"})
        self.assertIsNotNone(f)
        self.assertEqual(len(f["must"]), 1)
        self.assertEqual(f["must"][0]["key"], "module_type")
        self.assertEqual(f["must"][0]["match"]["value"], "screen")

    def test_multiple_fields_produce_must_conditions(self):
        f = _build_filter({"module_type": "screen", "approval_status": "reviewed"})
        keys = {cond["key"] for cond in f["must"]}
        self.assertEqual(keys, {"module_type", "approval_status"})


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class StatusTest(unittest.TestCase):
    """Unavailable Qdrant returns is_available() == False."""

    def test_unavailable_store_reports_available_false(self):
        store = _make_store(available=False)
        self.assertFalse(store.is_available())
        s = store.status()
        self.assertFalse(s["available"])
        self.assertEqual(s["provider"], "qdrant")

    def test_available_store_reports_provider_and_collection(self):
        store = _make_store(available=True)
        store._client.get_collection.return_value = MagicMock(points_count=42)

        s = store.status()
        self.assertTrue(s["available"])
        self.assertEqual(s["provider"], "qdrant")
        self.assertEqual(s["collection"], "bd_to_dd_chunks")
        self.assertIn("pointCount", s)


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

class PayloadTest(unittest.TestCase):
    def test_build_payload_contains_required_fields(self):
        chunk = _chunk(
            chunk_id="screen-ABC:screen:01_UI",
            content="UI section",
            embedding=[0.1],
        )
        payload = _build_payload(chunk)

        for key in [
            "chunk_id", "content", "doc_id", "parent_chunk_id",
            "doc_type", "module_type", "approval_status",
            "quality_score", "reused_count", "tags",
        ]:
            self.assertIn(key, payload, f"Missing payload key: {key}")

    def test_section_path_is_string(self):
        chunk = _chunk()
        payload = _build_payload(chunk)
        self.assertIsInstance(payload["section_path"], str)


if __name__ == "__main__":
    unittest.main()
