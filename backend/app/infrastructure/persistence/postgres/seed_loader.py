import json
from pathlib import Path
from typing import List, Optional

from app.core.config import SEED_SAMPLES_PATH
from app.domain.entities.sample_design import (
    ReviewedDetailDesignSample,
    to_reviewed_sample,
)


class JsonSeedSampleLoader:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or SEED_SAMPLES_PATH

    def load(self) -> List[ReviewedDetailDesignSample]:
        if not self.path.exists():
            return []
        raw_samples = json.loads(self.path.read_text())
        return [to_reviewed_sample(sample) for sample in raw_samples]

    def source(self) -> str:
        return str(self.path)

    def append(self, raw_sample: dict) -> None:
        if not self.path.exists():
            raw_samples = []
        else:
            try:
                raw_samples = json.loads(self.path.read_text())
            except Exception:
                raw_samples = []
        
        existing_ids = {s.get("id") for s in raw_samples}
        if raw_sample.get("id") not in existing_ids:
            raw_samples.append(raw_sample)
            self.path.write_text(json.dumps(raw_samples, ensure_ascii=False, indent=2))
