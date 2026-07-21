import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.domain.common_inputs.checklists import CHECKLISTS as DEFAULT_CHECKLISTS
from app.domain.common_inputs.common_components import (
    COMMON_COMPONENTS as DEFAULT_COMMON_COMPONENTS,
)
from app.domain.common_inputs.guidelines import GUIDELINES as DEFAULT_GUIDELINES
from app.domain.common_inputs.planning_skills import (
    PLANNING_SKILLS as DEFAULT_SKILLS,
)
from app.domain.common_inputs.templates import TEMPLATES as DEFAULT_TEMPLATES
from app.application.services.prompt_runtime_service import PromptRuntimeService
from app.infrastructure.llm.vision_client import GeminiVisionDesignExtractor


INPUT_COMMON_ROOT = Path("INPUT/common")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class CommonInputService:
    def __init__(self, root: Optional[Path] = None, image_extractor=None) -> None:
        self.root = Path(root or INPUT_COMMON_ROOT)
        self.prompt_runtime_service = PromptRuntimeService(self.root / "prompts")
        self.image_extractor = image_extractor or GeminiVisionDesignExtractor()
        self._image_cache: Dict[str, Dict[str, Any]] = {}

    def _load_json(self, relative_path: str, fallback: Any) -> Tuple[Any, List[str]]:
        path = self.root / relative_path
        if not path.exists():
            return fallback, []
        return json.loads(path.read_text(encoding="utf-8")), [str(path)]

    def _compute_version(
        self,
        source_files: List[str],
        image_references: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        digest = hashlib.sha256()
        for file_path in sorted(source_files):
            digest.update(file_path.encode("utf-8"))
            path = Path(file_path)
            if path.exists():
                digest.update(path.read_bytes())
        digest.update(
            json.dumps(
                image_references or [],
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        )
        return f"input-common-{digest.hexdigest()[:12]}"

    def _load_image_references(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        references = []
        source_files = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            image_bytes = path.read_bytes()
            content_hash = hashlib.sha256(image_bytes).hexdigest()
            if content_hash not in self._image_cache:
                mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
                self._image_cache[content_hash] = (
                    self.image_extractor.extract_common_reference(
                        image_bytes,
                        mime_type,
                        path.name,
                    )
                )
            references.append(
                {
                    "sourcePath": str(path),
                    **self._image_cache[content_hash],
                }
            )
            source_files.append(str(path))
        return references, source_files

    def _load_guidelines(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        catalog, source_files = self._load_json(
            "guidelines/guideline_catalog.json",
            DEFAULT_GUIDELINES,
        )
        return catalog, source_files

    def _load_templates(self) -> Tuple[Dict[str, Any], List[str]]:
        templates, source_files = self._load_json(
            "templates/template_catalog.json",
            DEFAULT_TEMPLATES,
        )
        raw_template_files = sorted(
            str(path)
            for path in (self.root / "templates").rglob("*.md")
            if path.is_file()
        )
        return templates, source_files + raw_template_files

    def _load_checklists(self) -> Tuple[Dict[str, Any], List[str]]:
        checklists, source_files = self._load_json(
            "checklists/detail_design.json",
            DEFAULT_CHECKLISTS,
        )
        return checklists, source_files

    def _load_skills(self) -> Tuple[Dict[str, Any], List[str]]:
        skills, source_files = self._load_json(
            "skills/skills.json",
            DEFAULT_SKILLS,
        )
        return skills, source_files

    def _load_common_components(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        components, source_files = self._load_json(
            "common-components/component_catalog.json",
            DEFAULT_COMMON_COMPONENTS,
        )
        return components, source_files

    def get_common_input(self) -> Dict[str, Any]:
        templates, template_files = self._load_templates()
        checklists, checklist_files = self._load_checklists()
        skills, skill_files = self._load_skills()
        guidelines, guideline_files = self._load_guidelines()
        common_components, component_files = self._load_common_components()
        image_references, image_files = self._load_image_references()

        source_files = sorted(
            set(
                template_files
                + checklist_files
                + skill_files
                + guideline_files
                + component_files
                + image_files
            )
        )
        return {
            "version": self._compute_version(source_files, image_references),
            "templates": templates,
            "checklists": checklists,
            "skills": skills,
            "guidelines": guidelines,
            "commonComponents": common_components,
            "imageReferences": image_references,
            "sourceFiles": source_files,
            "sourceRoot": str(self.root),
        }

    def get_status(self) -> Dict[str, Any]:
        common_input = self.get_common_input()
        prompt_runtime = self.prompt_runtime_service.get_prompt_status()
        return {
            "status": "ready",
            "version": common_input["version"],
            "sourceRoot": common_input["sourceRoot"],
            "sourceFiles": common_input["sourceFiles"],
            "sourceFileCount": len(common_input["sourceFiles"]),
            "templates": list(common_input["templates"].keys()),
            "checklists": list(common_input["checklists"].keys()),
            "skills": list(common_input["skills"].keys()),
            "skillCount": len(common_input["skills"]),
            "skillStages": {
                key: value["stage"] for key, value in common_input["skills"].items()
            },
            "guidelines": len(common_input["guidelines"]),
            "commonComponents": common_input["commonComponents"],
            "imageReferenceCount": len(common_input["imageReferences"]),
            "promptRuntime": prompt_runtime,
        }
