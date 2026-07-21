from typing import Any, Callable, Dict, Protocol


class LlmRepository(Protocol):
    def build_json_chain(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: Callable[[Dict[str, Any]], Dict[str, Any]],
    ):
        ...
