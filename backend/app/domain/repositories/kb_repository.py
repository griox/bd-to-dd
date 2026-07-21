from typing import Any, Dict, List, Optional, Protocol


class KnowledgeBaseRepository(Protocol):
    def add_sample(self, content: str) -> Dict[str, Any]:
        ...

    def seed_default_samples(self) -> Dict[str, Any]:
        ...

    def get_status(self) -> Dict[str, Any]:
        ...

    def retrieve_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        ...
