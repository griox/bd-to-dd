from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class DetailDesign:
    screen: Dict[str, Any] = field(default_factory=dict)
    api: Dict[str, Any] = field(default_factory=dict)
    batch: Dict[str, Any] = field(default_factory=dict)
