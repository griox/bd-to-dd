from typing import Optional, Protocol


class DesignRepository(Protocol):
    def save_document(self, project_id: str, kind: str, content: str) -> None:
        ...

    def load_document(self, project_id: str, kind: str) -> Optional[str]:
        ...
