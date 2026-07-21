import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set

from app.core.config import INPUT_ROOT_PATH


_SCREEN_ID_RE = re.compile(r"(N[0-9A-Z]+)")
_TOKEN_RE = re.compile(r"[0-9A-Za-z_]+|[一-龯ぁ-んァ-ン]+")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class DocumentImageExtractor(Protocol):
    def extract_document_text(
        self,
        image_bytes: bytes,
        mime_type: str,
        context: str,
        filename: str = "uploaded-image",
    ) -> str:
        ...


@dataclass(frozen=True)
class InputReferenceCandidate:
    component_id: str
    name: str
    markdown_path: Optional[Path]
    csv_path: Optional[Path]
    image_paths: List[Path]
    searchable_text: str


def _extract_screen_id(path: Path) -> str:
    match = _SCREEN_ID_RE.search(path.stem)
    return match.group(1) if match else path.stem


def _extract_screen_name(path: Path, screen_id: str) -> str:
    name = path.stem
    prefix = f"{screen_id}_"
    return name[len(prefix):] if name.startswith(prefix) else name


def _tokens(text: str) -> Set[str]:
    return {
        token.lower()
        for token in _TOKEN_RE.findall(text)
        if len(token.strip("_")) >= 2
    }


class InputReferenceService:
    """Finds demo input examples for Basic Design Analytics reference context."""

    def __init__(
        self,
        root: Optional[Path] = None,
        image_extractor: Optional[DocumentImageExtractor] = None,
    ) -> None:
        self.root = Path(root or INPUT_ROOT_PATH)
        self.image_extractor = image_extractor

    def find_similar_references(
        self,
        basic_design: str,
        ui_design: str = "",
        limit: int = 3,
    ) -> Dict[str, Any]:
        candidates = self._load_candidates()
        query_tokens = _tokens(f"{basic_design}\n{ui_design}")
        if not candidates or not query_tokens or limit <= 0:
            return self._empty_result()

        ranked = sorted(
            (
                (self._score(candidate, query_tokens), candidate)
                for candidate in candidates
            ),
            key=lambda item: (-item[0], item[1].component_id),
        )
        selected = [
            candidate
            for score, candidate in ranked
            if score >= 0.18
        ][:limit]
        if not selected:
            return self._empty_result()

        references = [self._build_reference(candidate) for candidate in selected]
        return {
            "references": references,
            "referenceCount": len(references),
            "formatted": self._format_references(references),
        }

    def _load_candidates(self) -> List[InputReferenceCandidate]:
        input_root = self.root / "input"
        ui_dir = input_root / "01_UI層"
        csv_dir = input_root / "composable_list"
        if not ui_dir.exists():
            return []

        by_id: Dict[str, Dict[str, Any]] = {}
        for md_path in sorted(ui_dir.glob("*.md")):
            component_id = _extract_screen_id(md_path)
            item = by_id.setdefault(
                component_id,
                {
                    "component_id": component_id,
                    "name": _extract_screen_name(md_path, component_id),
                    "markdown_path": None,
                    "csv_path": None,
                    "image_paths": [],
                    "texts": [],
                },
            )
            text = md_path.read_text(encoding="utf-8")
            item["markdown_path"] = md_path
            item["texts"].append(text)
            item["texts"].append(md_path.stem)

        if csv_dir.exists():
            for csv_path in sorted(csv_dir.glob("*.csv")):
                component_id = _extract_screen_id(csv_path)
                item = by_id.setdefault(
                    component_id,
                    {
                        "component_id": component_id,
                        "name": _extract_screen_name(csv_path, component_id),
                        "markdown_path": None,
                        "csv_path": None,
                        "image_paths": [],
                        "texts": [],
                    },
                )
                item["csv_path"] = csv_path
                item["texts"].append(csv_path.read_text(encoding="utf-8"))
                item["texts"].append(csv_path.stem)

        for image_path in sorted(ui_dir.rglob("*")):
            if not image_path.is_file() or image_path.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            component_id = _extract_screen_id(image_path)
            item = by_id.setdefault(
                component_id,
                {
                    "component_id": component_id,
                    "name": _extract_screen_name(image_path, component_id),
                    "markdown_path": None,
                    "csv_path": None,
                    "image_paths": [],
                    "texts": [],
                },
            )
            item["image_paths"].append(image_path)
            item["texts"].append(image_path.stem)

        return [
            InputReferenceCandidate(
                component_id=str(item["component_id"]),
                name=str(item["name"]),
                markdown_path=item["markdown_path"],
                csv_path=item["csv_path"],
                image_paths=list(item["image_paths"]),
                searchable_text="\n".join(item["texts"]),
            )
            for item in by_id.values()
        ]

    def _score(
        self,
        candidate: InputReferenceCandidate,
        query_tokens: Set[str],
    ) -> float:
        candidate_tokens = _tokens(candidate.searchable_text)
        if not candidate_tokens:
            return 0.0
        overlap = query_tokens.intersection(candidate_tokens)
        return len(overlap) / max(len(query_tokens), 1)

    def _build_reference(self, candidate: InputReferenceCandidate) -> Dict[str, Any]:
        markdown = (
            candidate.markdown_path.read_text(encoding="utf-8")
            if candidate.markdown_path is not None
            else ""
        )
        csv = (
            candidate.csv_path.read_text(encoding="utf-8")
            if candidate.csv_path is not None
            else ""
        )
        image_descriptions = [
            self._extract_image_description(image_path)
            for image_path in candidate.image_paths
        ]
        return {
            "componentId": candidate.component_id,
            "name": candidate.name,
            "sourceFiles": [
                str(path)
                for path in [
                    candidate.markdown_path,
                    candidate.csv_path,
                    *candidate.image_paths,
                ]
                if path is not None
            ],
            "markdown": markdown,
            "csv": csv,
            "imageDescriptions": image_descriptions,
        }

    def _extract_image_description(self, image_path: Path) -> str:
        if self.image_extractor is None:
            raise RuntimeError(
                f"Gemini Flash vision extractor is required for input reference image: {image_path}"
            )
        try:
            mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
            return self.image_extractor.extract_document_text(
                image_path.read_bytes(),
                mime_type,
                "ui_design",
                image_path.name,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to extract input reference image {image_path}: {exc}"
            ) from exc

    def _format_references(self, references: List[Dict[str, Any]]) -> str:
        lines = [
            "REFERENCE INPUT EXAMPLES",
            "Use these examples only as non-authoritative reference patterns.",
            "Do not copy sample screen IDs, names, business rules, or data into the user's output unless they also appear in the user's input.",
            "When references conflict with the user's Basic Design or UI Design, the user's input wins.",
        ]
        for index, reference in enumerate(references, start=1):
            lines.extend(
                [
                    "",
                    f"Example {index}: {reference['componentId']} {reference['name']}",
                    "Source files:",
                ]
            )
            lines.extend(f"- {source_file}" for source_file in reference["sourceFiles"])
            if reference["markdown"]:
                lines.extend(["Markdown:", reference["markdown"]])
            if reference["csv"]:
                lines.extend(["Composable CSV:", reference["csv"]])
            if reference["imageDescriptions"]:
                lines.append("Gemini Flash image analysis:")
                lines.extend(reference["imageDescriptions"])
        return "\n".join(lines)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "references": [],
            "referenceCount": 0,
            "formatted": "REFERENCE INPUT EXAMPLES\nNo similar input examples found.",
        }
