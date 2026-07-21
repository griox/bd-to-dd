from dataclasses import replace
from typing import Any, Dict, List

from app.domain.entities.retrieval import AssembledContext, RetrievalCandidate


class ContextAssemblyService:
    def __init__(self) -> None:
        self._parent_cache: Dict[str, RetrievalCandidate] = {}

    def assemble(
        self,
        samples: List[str],
        common_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "samples": samples,
            "templates": common_input.get("templates", {}),
            "guidelines": common_input.get("guidelines", []),
            "checklists": common_input.get("checklists", {}),
        }

    def assemble_candidates(
        self,
        candidates: List[RetrievalCandidate],
        dense_store,
    ) -> AssembledContext:
        parent_ids: List[str] = []
        direct_candidates: List[RetrievalCandidate] = []

        for candidate in candidates:
            parent_id = candidate.metadata.get("parent_chunk_id")
            allow_parent_merge = bool(candidate.metadata.get("allow_parent_merge"))
            if parent_id and (allow_parent_merge or candidate.metadata.get("is_leaf", True)):
                if parent_id not in parent_ids:
                    parent_ids.append(parent_id)
            else:
                direct_candidates.append(candidate)

        missing_parent_ids = [
            parent_id for parent_id in parent_ids if parent_id not in self._parent_cache
        ]
        if missing_parent_ids:
            for parent in dense_store.get_by_chunk_ids(missing_parent_ids):
                self._parent_cache[parent.chunk_id] = parent

        parent_candidates = [
            self._parent_cache[parent_id]
            for parent_id in parent_ids
            if parent_id in self._parent_cache
        ]
        ordered = parent_candidates + direct_candidates
        seen = set()
        covered_sections = set()
        deduped: List[RetrievalCandidate] = []
        for candidate in ordered:
            if candidate.chunk_id in seen:
                continue
            seen.add(candidate.chunk_id)
            section_path = candidate.metadata.get("section_path", "")
            if section_path:
                covered_sections.add(str(section_path).split(" > ")[0])
            deduped.append(
                replace(
                    candidate,
                    metadata={
                        **candidate.metadata,
                        "context_role": "parent_or_direct",
                        "coverage_sections": sorted(covered_sections),
                    },
                )
            )
        return AssembledContext(references=deduped, reference_count=len(deduped))
