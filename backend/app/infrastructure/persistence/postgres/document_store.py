from pathlib import Path
from typing import Optional

from app.core.config import TMP_DIR


def _project_dir(project_id: str) -> Path:
    path = TMP_DIR / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_document(project_id: str, kind: str, content: str) -> Path:
    path = _project_dir(project_id) / f"{kind}.txt"
    path.write_text(content)
    return path


def load_document(project_id: str, kind: str) -> Optional[str]:
    path = _project_dir(project_id) / f"{kind}.txt"
    if not path.exists():
        return None
    return path.read_text()


def document_exists(project_id: str, kind: str) -> bool:
    return (_project_dir(project_id) / f"{kind}.txt").exists()
