import json
import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Tuple

from app.core.config import INPUT_ROOT_PATH
from app.domain.repositories.vector_store_repository import VisionDesignExtractor
from app.domain.entities.sample_design import ReviewedDetailDesignSample
from app.infrastructure.llm.vision_client import NORMALIZED_SCREEN_SECTION_FALLBACKS


_SCREEN_ID_RE = re.compile(r"(N[0-9A-Z]+)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
_TEXT_EXTENSIONS = {".md", ".csv", ".txt", ".json"}


def _extract_screen_id(path: Path) -> str:
    match = _SCREEN_ID_RE.search(path.stem)
    return match.group(1) if match else path.stem


def _extract_screen_name(path: Path, screen_id: str) -> str:
    name = path.stem
    prefix = f"{screen_id}_"
    return name[len(prefix):] if name.startswith(prefix) else name


def _normalize_key(label: str) -> str:
    text = re.sub(r"\s+", "_", label.strip())
    text = re.sub(r"[^\w一-龯ぁ-んァ-ン]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "Section"


def _infer_module_type(path: Path) -> str:
    parts = "/".join(path.parts)
    if "01_UI層" in parts:
        return "screen"
    if "02_API" in parts or "API" in parts:
        return "api"
    if "03_Batch" in parts or "Batch" in parts:
        return "batch"
    return "screen"


def _document_section_prefix(path: Path) -> str:
    stem = path.stem
    if stem.startswith("Screen設計"):
        return "01_Screen_Design"
    if stem.startswith("ViewModel設計"):
        return "02_ViewModel_Design"
    if path.suffix.lower() == ".csv":
        return "98_Tabular_Content"
    if path.suffix.lower() in _IMAGE_EXTENSIONS:
        return "97_Image_Analysis"
    return _normalize_key(path.parent.name or stem)


def _parse_markdown_sections(markdown: str) -> Dict[str, str]:
    sections: Dict[str, List[str]] = {}
    current_key = "00_Document"
    sections[current_key] = []

    for line in markdown.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            current_key = match.group(2).strip()
            sections.setdefault(current_key, [])
            continue
        sections.setdefault(current_key, []).append(line)

    parsed = {
        key: "\n".join(lines).strip()
        for key, lines in sections.items()
        if "\n".join(lines).strip()
    }
    return parsed or {"00_Document": markdown.strip()}


def _find_matching_csv(csv_dir: Path, screen_id: str) -> Optional[Path]:
    if not csv_dir.exists():
        return None
    matches = sorted(csv_dir.glob(f"{screen_id}_*.csv"))
    return matches[0] if matches else None


def _normalize_screen_sections(screen_sections: Dict[str, str], source_type: str) -> Dict[str, str]:
    if source_type != "image":
        return screen_sections
    normalized = dict(NORMALIZED_SCREEN_SECTION_FALLBACKS)
    normalized.update(screen_sections)
    return normalized


class InputReviewedDdLoader:
    """Loads reviewed design inputs from the project INPUT directory.

    The loader converts each screen markdown file into the JSON content shape
    consumed by ChunkingService, optionally merging the matching composable CSV
    into the same screen section.
    """

    def __init__(
        self,
        root: Optional[Path] = None,
        image_extractor: Optional[VisionDesignExtractor] = None,
    ) -> None:
        self.root = Path(root or INPUT_ROOT_PATH)
        self.image_extractor = image_extractor

    def load(self) -> List[ReviewedDetailDesignSample]:
        return self._load_dd_samples()

    def source(self) -> str:
        return str(self.root)

    def _extract_image_sections(self, image_path: Path) -> Dict[str, str]:
        if self.image_extractor is None:
            raise RuntimeError(
                f"Gemini vision extractor is required for image: {image_path}"
            )
        try:
            return self.image_extractor.extract_screen_sections(image_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to extract image {image_path}: {exc}"
            ) from exc

    def _load_input_samples(self) -> List[ReviewedDetailDesignSample]:
        ui_dir = self.root / "input" / "01_UI層"
        csv_dir = self.root / "input" / "composable_list"
        if not ui_dir.exists():
            return []

        grouped_sections: DefaultDict[str, Dict[str, str]] = defaultdict(dict)
        grouped_files: DefaultDict[str, List[str]] = defaultdict(list)
        grouped_types: DefaultDict[str, List[str]] = defaultdict(list)
        primary_paths: Dict[str, Path] = {}

        for md_path in sorted(ui_dir.glob("*.md")):
            screen_id = _extract_screen_id(md_path)
            grouped_sections[screen_id].update(
                _parse_markdown_sections(md_path.read_text(encoding="utf-8"))
            )
            grouped_files[screen_id].append(str(md_path))
            grouped_types[screen_id].append("markdown")
            primary_paths[screen_id] = md_path

        for image_path in sorted(ui_dir.rglob("*")):
            if not image_path.is_file() or image_path.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            screen_id = _extract_screen_id(image_path)
            image_sections = _normalize_screen_sections(
                self._extract_image_sections(image_path),
                "image",
            )
            if grouped_sections[screen_id]:
                image_sections = {
                    f"97_Image_Analysis_{_normalize_key(key)}": value
                    for key, value in image_sections.items()
                }
            grouped_sections[screen_id].update(image_sections)
            grouped_files[screen_id].append(str(image_path))
            grouped_types[screen_id].append("image")
            primary_paths.setdefault(screen_id, image_path)

        samples: List[ReviewedDetailDesignSample] = []
        for screen_id, sections in sorted(grouped_sections.items()):
            source_types = sorted(set(grouped_types[screen_id]))
            samples.append(
                self._build_sample(
                    primary_paths[screen_id],
                    sections,
                    csv_dir,
                    "+".join(source_types),
                    source_files=grouped_files[screen_id],
                )
            )
        return samples

    def _load_dd_samples(self) -> List[ReviewedDetailDesignSample]:
        dd_root = self.root / "DD"
        if not dd_root.exists():
            return []

        grouped_sections: DefaultDict[Tuple[str, str], Dict[str, str]] = defaultdict(dict)
        grouped_files: DefaultDict[Tuple[str, str], List[str]] = defaultdict(list)
        grouped_names: Dict[Tuple[str, str], str] = {}
        grouped_types: DefaultDict[Tuple[str, str], List[str]] = defaultdict(list)

        for path in sorted(dd_root.rglob("*")):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in _TEXT_EXTENSIONS and suffix not in _IMAGE_EXTENSIONS:
                continue

            screen_id = _extract_screen_id(path)
            module_type = _infer_module_type(path)
            group_key = (module_type, screen_id)
            grouped_names[group_key] = _extract_screen_name(path, screen_id)
            grouped_files[group_key].append(str(path))

            if suffix in _IMAGE_EXTENSIONS:
                grouped_types[group_key].append("image")
                image_sections = _normalize_screen_sections(
                    self._extract_image_sections(path),
                    "image",
                )
                prefix = _document_section_prefix(path)
                for key, value in image_sections.items():
                    grouped_sections[group_key][f"{prefix}_{_normalize_key(key)}"] = value
                continue

            grouped_types[group_key].append("text")
            prefix = _document_section_prefix(path)
            if suffix == ".md":
                parsed_sections = _parse_markdown_sections(path.read_text(encoding="utf-8"))
                for key, value in parsed_sections.items():
                    grouped_sections[group_key][f"{prefix}_{_normalize_key(key)}"] = value
            else:
                grouped_sections[group_key][prefix] = path.read_text(encoding="utf-8")

        samples: List[ReviewedDetailDesignSample] = []
        for (module_type, screen_id), sections in sorted(grouped_sections.items()):
            if not sections:
                continue
            payload = json.dumps({"detailDesign": {module_type: sections}}, ensure_ascii=False)
            source_types = sorted(set(grouped_types[(module_type, screen_id)]))
            samples.append(
                ReviewedDetailDesignSample(
                    id=f"dd-{module_type}-{screen_id}",
                    content=payload,
                    metadata={
                        "module_type": module_type,
                        "approval_status": "reviewed",
                        "review_status": "reviewed",
                        "component_id": screen_id,
                        "screen_name": grouped_names.get((module_type, screen_id), screen_id),
                        "source_path": str(dd_root),
                        "source_files": grouped_files[(module_type, screen_id)],
                        "source_type": "+".join(source_types) if source_types else "text",
                        "extraction_method": (
                            "mixed_dd_loader"
                            if len(source_types) > 1
                            else (
                                "gemini_vision"
                                if source_types == ["image"]
                                else "dd_document_parser"
                            )
                        ),
                        "quality_score": 1.0,
                        "reused_count": 0,
                        "tags": [module_type, "dd", "reviewed"] + source_types,
                    },
                )
            )
        return samples

    def _build_sample(
        self,
        source_path: Path,
        screen_sections: Dict[str, str],
        csv_dir: Path,
        source_type: str,
        source_files: Optional[List[str]] = None,
    ) -> ReviewedDetailDesignSample:
        screen_id = _extract_screen_id(source_path)
        screen_name = _extract_screen_name(source_path, screen_id)
        source_files = list(source_files or [str(source_path)])
        if source_type == "image":
            screen_sections = _normalize_screen_sections(screen_sections, source_type)

        csv_path = _find_matching_csv(csv_dir, screen_id)
        if csv_path is not None:
            screen_sections = dict(screen_sections)
            screen_sections["99_Composable_List"] = csv_path.read_text(encoding="utf-8")
            source_files.append(str(csv_path))

        content = json.dumps(
            {"detailDesign": {"screen": screen_sections}},
            ensure_ascii=False,
        )
        return ReviewedDetailDesignSample(
            id=f"screen-{screen_id}",
            content=content,
            metadata={
                "module_type": "screen",
                "approval_status": "reviewed",
                "review_status": "reviewed",
                "component_id": screen_id,
                "screen_name": screen_name,
                "source_path": str(source_path),
                "source_files": source_files,
                "source_type": source_type,
                "extraction_method": (
                    "mixed_input_loader"
                    if "+" in source_type
                    else ("gemini_vision" if source_type == "image" else "markdown_parser")
                ),
                "quality_score": 1.0,
                "reused_count": 0,
                "tags": ["screen", "input", "ui"] + source_type.split("+"),
            },
        )
