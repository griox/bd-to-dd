import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.application.services.prompt_catalog import DEFAULT_PROMPTS


PROMPT_ROOT = Path("INPUT/common/prompts")
PROMPT_MANIFEST = "prompt_catalog.json"


class PromptRuntimeService:
    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root or PROMPT_ROOT)

    def get_prompt_catalog(self) -> Dict[str, Dict[str, str]]:
        runtime_catalog = self._load_runtime_catalog()
        if runtime_catalog is None:
            return self._clone_defaults()
        return runtime_catalog

    def get_prompt_status(self) -> Dict[str, Any]:
        manifest_path = self.root / PROMPT_MANIFEST
        runtime_catalog = self._load_runtime_catalog()
        if runtime_catalog is None:
            default_files = ["backend/app/application/services/prompt_catalog.py"]
            return {
                "source": "backend_fallback",
                "sourceRoot": str(self.root),
                "manifestPath": str(manifest_path),
                "version": self._compute_version(default_files),
                "stageNames": list(DEFAULT_PROMPTS.keys()),
                "fileCount": len(default_files),
                "sourceFiles": default_files,
            }

        source_files = self._collect_runtime_source_files(manifest_path, runtime_catalog)
        return {
            "source": "input_common_prompts",
            "sourceRoot": str(self.root),
            "manifestPath": str(manifest_path),
            "version": self._compute_version(source_files),
            "stageNames": list(runtime_catalog.keys()),
            "fileCount": len(source_files),
            "sourceFiles": source_files,
        }

    def _load_runtime_catalog(self) -> Optional[Dict[str, Dict[str, str]]]:
        manifest_path = self.root / PROMPT_MANIFEST
        if not manifest_path.exists():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            catalog: Dict[str, Dict[str, str]] = {}
            for stage_name, fallback_prompt in DEFAULT_PROMPTS.items():
                stage_payload = manifest.get(stage_name, {})
                if not isinstance(stage_payload, dict):
                    stage_payload = {}
                catalog[stage_name] = {
                    "system": self._compose_prompt(stage_payload, "system"),
                    "user": self._compose_prompt(stage_payload, "user"),
                }
                if not catalog[stage_name]["system"].strip():
                    catalog[stage_name]["system"] = fallback_prompt["system"]
                if not catalog[stage_name]["user"].strip():
                    catalog[stage_name]["user"] = fallback_prompt["user"]
            return catalog
        except Exception:
            return None

    def _compose_prompt(self, payload: Dict[str, Any], prefix: str) -> str:
        base_text = str(payload.get(prefix, "")).strip()
        include_key = f"{prefix}Includes"
        includes = payload.get(include_key, [])
        fragments: List[str] = [base_text] if base_text else []
        if not isinstance(includes, list):
            raise ValueError(f"{include_key} must be a list")
        for include_path in includes:
            relative_path = Path(str(include_path))
            full_path = self.root / relative_path
            fragments.append(
                self._escape_template_literal(
                    full_path.read_text(encoding="utf-8").strip()
                )
            )
        return "\n\n".join(fragment for fragment in fragments if fragment)

    def _escape_template_literal(self, text: str) -> str:
        return text.replace("{", "{{").replace("}", "}}")

    def _collect_runtime_source_files(
        self,
        manifest_path: Path,
        runtime_catalog: Dict[str, Dict[str, str]],
    ) -> List[str]:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = {str(manifest_path)}
        for stage_name in runtime_catalog:
            payload = manifest.get(stage_name, {})
            for include_key in ("systemIncludes", "userIncludes"):
                for include_path in payload.get(include_key, []):
                    files.add(str(self.root / str(include_path)))
        return sorted(files)

    def _compute_version(self, source_files: List[str]) -> str:
        digest = hashlib.sha256()
        for file_path in sorted(source_files):
            digest.update(file_path.encode("utf-8"))
            path = Path(file_path)
            if path.exists():
                digest.update(path.read_bytes())
        return f"input-prompts-{digest.hexdigest()[:12]}"

    def _clone_defaults(self) -> Dict[str, Dict[str, str]]:
        return json.loads(json.dumps(DEFAULT_PROMPTS))
