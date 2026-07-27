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
    try:
        from app.infrastructure.storage.gcs_storage_service import GCSStorageService
        gcs = GCSStorageService()
        if gcs.is_enabled():
            gcs.save_text(f"projects/{project_id}/{kind}.txt", content)
    except Exception:
        pass
    return path


def load_document(project_id: str, kind: str) -> Optional[str]:
    path = _project_dir(project_id) / f"{kind}.txt"
    if path.exists():
        return path.read_text()
    try:
        from app.infrastructure.storage.gcs_storage_service import GCSStorageService
        gcs = GCSStorageService()
        if gcs.is_enabled():
            data = gcs.load_bytes(f"projects/{project_id}/{kind}.txt")
            if data:
                text = data.decode("utf-8")
                path.write_text(text)
                return text
    except Exception:
        pass
    return None


def document_exists(project_id: str, kind: str) -> bool:
    return load_document(project_id, kind) is not None

