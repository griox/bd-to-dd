import json
from pathlib import Path
from typing import Any, Dict

from app.core.config import ARTIFACTS_DIR


def _job_dir(project_id: str, job_id: str) -> Path:
    path = ARTIFACTS_DIR / project_id / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _to_markdown(payload: Dict[str, Any]) -> str:
    analysis = payload["analysis"]
    detail_design = payload["detailDesign"]
    review = payload["review"]
    lines = [
        "# Detail Design Artifact",
        "",
        "## Analysis Summary",
        analysis.get("summary", ""),
        "",
        "## Business Flows",
    ]
    for flow in analysis.get("businessFlows", []):
        lines.append(f"- {flow}")
    lines.extend(["", "## Detail Design"])
    for section_name, section_body in detail_design.items():
        lines.append(f"### {section_name}")
        if isinstance(section_body, dict):
            for key, value in section_body.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append(str(section_body))
    lines.extend(["", "## Review"])
    lines.append(f"- Status: {review['status']}")
    for finding in review["findings"]:
        lines.append(f"- {finding}")
    return "\n".join(lines)


def export_artifacts(project_id: str, job_id: str, payload: Dict[str, Any]) -> Dict[str, str]:
    job_dir = _job_dir(project_id, job_id)
    json_path = job_dir / "detail-design.json"
    markdown_path = job_dir / "detail-design.md"
    json_path.write_text(json.dumps(payload, indent=2))
    markdown_path.write_text(_to_markdown(payload))
    return {
        "jsonPath": str(json_path),
        "markdownPath": str(markdown_path),
    }
