import json
from typing import Any

from .runnables import Runnable


class JsonOutputParser(Runnable):
    def invoke(self, payload: Any) -> Any:
        if isinstance(payload, str):
            return json.loads(payload)
        if hasattr(payload, "content"):
            return json.loads(payload.content)
        return payload
