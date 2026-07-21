import unittest

from app.application.services.context_assembly_service import ContextAssemblyService
from tests.fixtures import FakeDenseStore, make_candidate


class ContextAssemblyServiceTest(unittest.TestCase):
    def test_fetches_unique_parent_chunks_for_short_leaf_candidates(self):
        leaf_1 = make_candidate(
            "leaf-1",
            "short",
            0.9,
            "rerank",
            {"parent_chunk_id": "parent-1", "allow_parent_merge": True},
        )
        leaf_2 = make_candidate(
            "leaf-2",
            "short also",
            0.8,
            "rerank",
            {"parent_chunk_id": "parent-1", "allow_parent_merge": True},
        )
        parent = make_candidate("parent-1", "full parent context", 1.0, "rrf")
        store = FakeDenseStore(parents={"parent-1": parent})

        assembled = ContextAssemblyService().assemble_candidates([leaf_1, leaf_2], store)

        self.assertEqual(assembled.reference_count, 1)
        self.assertEqual(assembled.references[0].chunk_id, "parent-1")
        self.assertEqual(assembled.references[0].content, "full parent context")


if __name__ == "__main__":
    unittest.main()
