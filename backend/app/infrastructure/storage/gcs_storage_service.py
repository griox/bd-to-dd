"""Infrastructure adapter: Google Cloud Storage Service.

Handles persistent object storage for production artifacts and uploaded documents
when GCS_BUCKET_NAME is configured. Seamlessly falls back to local disk storage
when running in local or demo environments.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import ARTIFACTS_DIR, GCS_BUCKET_NAME, GCS_PREFIX


class GCSStorageService:
    def __init__(
        self,
        bucket_name: Optional[str] = GCS_BUCKET_NAME,
        prefix: str = GCS_PREFIX,
    ) -> None:
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self._client = None
        self._bucket = None
        self._enabled = False
        self._init_client()

    def _init_client(self) -> None:
        if not self.bucket_name:
            self._enabled = False
            return
        try:
            from google.cloud import storage  # noqa: PLC0415
            self._client = storage.Client()
            self._bucket = self._client.bucket(self.bucket_name)
            self._enabled = True
        except Exception:
            self._client = None
            self._bucket = None
            self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def save_bytes(self, destination_blob_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Save bytes data to GCS if enabled, or to local ARTIFACTS_DIR as fallback."""
        key = f"{self.prefix}/{destination_blob_name.lstrip('/')}" if self.prefix else destination_blob_name.lstrip('/')
        if self._enabled and self._bucket:
            blob = self._bucket.blob(key)
            blob.upload_from_string(data, content_type=content_type)
            return f"gs://{self.bucket_name}/{key}"
        
        # Local fallback
        local_path = ARTIFACTS_DIR / destination_blob_name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        return str(local_path)

    def save_text(self, destination_blob_name: str, text: str, encoding: str = "utf-8") -> str:
        """Save text data to GCS if enabled, or to local ARTIFACTS_DIR as fallback."""
        return self.save_bytes(
            destination_blob_name,
            text.encode(encoding),
            content_type="text/plain; charset=utf-8",
        )

    def load_bytes(self, source_blob_name: str) -> Optional[bytes]:
        """Load bytes data from GCS if enabled, or from local ARTIFACTS_DIR as fallback."""
        key = f"{self.prefix}/{source_blob_name.lstrip('/')}" if self.prefix else source_blob_name.lstrip('/')
        if self._enabled and self._bucket:
            blob = self._bucket.blob(key)
            if blob.exists():
                return blob.download_as_bytes()
            return None

        # Local fallback
        local_path = ARTIFACTS_DIR / source_blob_name
        if local_path.exists():
            return local_path.read_bytes()
        return None

    def status(self) -> Dict[str, Any]:
        return {
            "provider": "google_cloud_storage" if self._enabled else "local_disk",
            "enabled": self._enabled,
            "bucket": self.bucket_name,
            "prefix": self.prefix,
        }
