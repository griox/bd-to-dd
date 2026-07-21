from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DesignAnalysis:
    summary: str
    scope: str
    entities: List[str] = field(default_factory=list)
    business_flows: List[str] = field(default_factory=list)
    api_candidates: List[str] = field(default_factory=list)
    ui_signals: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
