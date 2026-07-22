"""Application service: hierarchical chunking of reviewed Detail Design documents.

Chunking rules (from planning.md Phase 2):
1. One root chunk per source document.
2. One parent chunk per major heading (module_type level: screen/api/batch).
3. One leaf chunk per terminal section (e.g. 01_UI_Design, 02_Components).
4. Leaf content < 120 chars → keep but flag allow_parent_merge in metadata.
5. Leaf content > 1,500 chars → split by paragraph, then line break.
6. Preserve section_path, sibling_order, parent_chunk_id on every chunk.
7. Chunk IDs are deterministic across repeated indexing runs.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.sample_design import ReviewedDetailDesignSample

_LEAF_MERGE_THRESHOLD = 120   # chars: leaf kept but context assembly may pull parent
_LEAF_SPLIT_THRESHOLD = 1_500  # chars: leaf split by paragraph/line
_COMPONENT_ID_RE = re.compile(r"(N[0-9A-Z]+)")


def _make_id(*parts: str) -> str:
    """Build a deterministic, filesystem-safe chunk ID from path components."""
    return ":".join(p.strip() for p in parts if p.strip())


def _split_long_content(content: str, max_chars: int = _LEAF_SPLIT_THRESHOLD) -> List[str]:
    """Split content that exceeds max_chars first by paragraph, then by line.

    Always returns at least one element (the original content if splitting
    would produce empty strings).
    """
    if len(content) <= max_chars:
        return [content]

    # Try paragraph split first
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
    if len(paragraphs) > 1:
        # Group paragraphs into chunks that stay under max_chars
        groups: List[str] = []
        current: List[str] = []
        current_len = 0
        for para in paragraphs:
            if current_len + len(para) > max_chars and current:
                groups.append("\n\n".join(current))
                current = [para]
                current_len = len(para)
            else:
                current.append(para)
                current_len += len(para)
        if current:
            groups.append("\n\n".join(current))
        return groups if groups else [content]

    # Fallback: split by line
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    groups = []
    current = []
    current_len = 0
    for line in lines:
        if current_len + len(line) > max_chars and current:
            groups.append("\n".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line)
    if current:
        groups.append("\n".join(current))
    return groups if groups else [content]


def _extract_component_id(sample_id: str) -> str:
    """Extract the component ID from a sample ID such as 'screen-N9P90M4X4004W009'.

    Returns the part after the first '-', or the full ID if no '-' is present.
    """
    match = _COMPONENT_ID_RE.search(sample_id)
    if match:
        return match.group(1)
    parts = sample_id.split("-", 1)
    return parts[1] if len(parts) > 1 else sample_id


def _compact_parent_content(section_content: Any) -> str:
    """Create compact parent context from child sections."""
    if isinstance(section_content, str):
        return section_content.strip()
    if not isinstance(section_content, dict):
        return str(section_content).strip()

    lines: List[str] = []
    for key, value in section_content.items():
        text = str(value).strip()
        if text:
            lines.append(f"{key}: {text}")
    return "\n".join(lines)


class ChunkingService:
    """Converts reviewed DD samples into hierarchical KnowledgeChunk trees."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_sample(
        self,
        sample: ReviewedDetailDesignSample,
        project_context: str = "bd-to-dd-demo",
    ) -> List[KnowledgeChunk]:
        """Convert one ReviewedDetailDesignSample into a flat list of chunks.

        The list is ordered: root → section parents → leaf chunks.
        Deterministic IDs ensure repeated calls produce identical results.
        """
        import json

        sample_meta = sample.metadata or {}
        module_type: str = str(sample_meta.get("module_type", "unknown"))
        component_id = _extract_component_id(sample.id)

        # Resolve the detail_design dict from the JSON content string
        try:
            payload = json.loads(sample.content)
            detail_design: Dict[str, Any] = payload.get("detailDesign", {})
        except (json.JSONDecodeError, AttributeError):
            detail_design = {}

        doc_id = sample.id
        root_id = _make_id(doc_id, "root")

        base_metadata: Dict[str, Any] = {
            "doc_id": doc_id,
            "doc_type": "reviewed_dd",
            "module_type": module_type,
            "project_context": project_context,
            "approval_status": str(
                sample_meta.get(
                    "approval_status",
                    sample_meta.get("review_status", "reviewed"),
                )
            ),
            "component_id": component_id,
            "quality_score": float(sample_meta.get("quality_score", 1.0)),
            "reused_count": int(sample_meta.get("reused_count", 0)),
            "tags": sample_meta.get("tags", [module_type]),
            "content_type": "markdown",
        }

        chunks: List[KnowledgeChunk] = []

        # 1. Root chunk: represents the whole document
        root_chunk = KnowledgeChunk(
            id=root_id,
            content=sample.content[:_LEAF_SPLIT_THRESHOLD],  # summary slice
            metadata={**base_metadata, "section_path": doc_id, "parent_chunk_id": None},
            doc_id=doc_id,
            parent_chunk_id=None,
            root_chunk_id=root_id,
            section_path=(doc_id,),
            section_level=0,
            sibling_order=0,
            is_leaf=False,
        )
        chunks.append(root_chunk)

        # 2. Section-parent + leaf chunks per module_type in the detail design
        for section_order, (section_key, section_content) in enumerate(
            detail_design.items()
        ):
            parent_id = _make_id(doc_id, section_key)
            section_path_tuple: Tuple[str, ...] = (doc_id, section_key)
            section_path_str = f"{doc_id} > {section_key}"

            parent_content = _compact_parent_content(section_content)
            if not parent_content.strip():
                continue

            parent_chunk = KnowledgeChunk(
                id=parent_id,
                content=parent_content,
                metadata={
                    **base_metadata,
                    "section_path": section_path_str,
                    "parent_chunk_id": root_id,
                    "module_type": section_key,
                },
                doc_id=doc_id,
                parent_chunk_id=root_id,
                root_chunk_id=root_id,
                section_path=section_path_tuple,
                section_level=1,
                sibling_order=section_order,
                is_leaf=False,
            )
            chunks.append(parent_chunk)

            # 3. Leaf chunks: terminal sections within this module
            if isinstance(section_content, dict):
                leaf_sibling = 0
                for subsection_key, subsection_content in section_content.items():
                    leaf_content = str(subsection_content).strip()
                    if not leaf_content:
                        continue
                    leaf_path_tuple = section_path_tuple + (subsection_key,)
                    leaf_path_str = f"{section_path_str} > {subsection_key}"
                    leaf_meta = {
                        **base_metadata,
                        "section_path": leaf_path_str,
                        "parent_chunk_id": parent_id,
                        "subsection": subsection_key,
                        "module_type": section_key,
                    }

                    # Rule 5: split long content
                    parts = _split_long_content(leaf_content)

                    for part_index, part_content in enumerate(parts):
                        leaf_id = (
                            _make_id(doc_id, section_key, subsection_key)
                            if len(parts) == 1
                            else _make_id(doc_id, section_key, subsection_key, str(part_index))
                        )
                        # Rule 4: mark short leaves for context assembly
                        allow_merge = len(part_content) < _LEAF_MERGE_THRESHOLD
                        chunks.append(
                            KnowledgeChunk(
                                id=leaf_id,
                                content=part_content,
                                metadata={
                                    **leaf_meta,
                                    "allow_parent_merge": allow_merge,
                                },
                                doc_id=doc_id,
                                parent_chunk_id=parent_id,
                                root_chunk_id=root_id,
                                section_path=leaf_path_tuple,
                                section_level=2,
                                sibling_order=leaf_sibling,
                                is_leaf=True,
                            )
                        )
                        leaf_sibling += 1

        return chunks

    def chunk_samples(
        self,
        samples: List[ReviewedDetailDesignSample],
        project_context: str = "bd-to-dd-demo",
    ) -> List[KnowledgeChunk]:
        """Chunk all samples and return a flat list of all chunks."""
        all_chunks: List[KnowledgeChunk] = []
        for sample in samples:
            all_chunks.extend(self.chunk_sample(sample, project_context))
        return [c for c in all_chunks if c.content and c.content.strip()]

    # ------------------------------------------------------------------
    # Legacy method kept for callers that still pass a flat detailDesign dict.
    # ------------------------------------------------------------------

    def chunk_detail_design(
        self,
        detail_design_id: str,
        detail_design: Dict[str, Dict[str, Any]],
    ) -> List[KnowledgeChunk]:
        """Original flat chunker — delegates to the structure-aware logic."""
        chunks: List[KnowledgeChunk] = []
        for module_type, sections in detail_design.items():
            for section, content in sections.items():
                chunks.append(
                    KnowledgeChunk(
                        id=_make_id(detail_design_id, module_type, section),
                        content=str(content),
                        metadata={
                            "module_type": module_type,
                            "sub_section": section,
                        },
                        doc_id=detail_design_id,
                        parent_dd_id=detail_design_id,  # legacy
                    )
                )
        return chunks
