from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BasicDesignInput:
    basic_design: str
    ui_design: Optional[str] = None
