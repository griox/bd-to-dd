from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple


@dataclass(frozen=True)
class KnowledgeChunk:
    """A hierarchical chunk of a reviewed Detail Design document.

    Hierarchy fields allow parent-child context assembly and deterministic
    re-indexing without duplicating Qdrant points.
    """

    id: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    # Document-level linkage
    doc_id: Optional[str] = None

    # Hierarchy fields (Phase 1+)
    parent_chunk_id: Optional[str] = None
    root_chunk_id: Optional[str] = None
    section_path: Tuple[str, ...] = ()
    section_level: int = 0
    sibling_order: int = 0
    is_leaf: bool = True

    # Legacy aliases kept for backward compatibility with older callers.
    parent_dd_id: Optional[str] = None  # deprecated: use doc_id
    is_split: bool = False              # deprecated: use sibling_order > 0
    part_of: Optional[str] = None      # deprecated: use parent_chunk_id

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
