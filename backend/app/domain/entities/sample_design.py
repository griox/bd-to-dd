from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ReviewedDetailDesignSample:
    id: str
    content: str
    metadata: Dict[str, Any]


def to_reviewed_sample(payload: Dict[str, Any]) -> ReviewedDetailDesignSample:
    return ReviewedDetailDesignSample(
        id=str(payload["id"]),
        content=str(payload["content"]),
        metadata=dict(payload.get("metadata", {})),
    )
