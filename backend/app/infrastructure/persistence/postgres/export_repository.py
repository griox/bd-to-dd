import json
from pathlib import Path
from typing import Any, Dict

from app.core.config import ARTIFACTS_DIR


def _job_dir(project_id: str, job_id: str) -> Path:
    path = ARTIFACTS_DIR / project_id / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _to_markdown(payload: Dict[str, Any]) -> str:
    detail_design = payload.get("detailDesign", {})
    
    # If the new multi-file format is used, combine them for a single preview
    is_multi_file = any(isinstance(v, dict) and "content" in v for v in detail_design.values())
    if is_multi_file:
        combined = []
        for section_name, section_body in detail_design.items():
            if isinstance(section_body, dict) and "content" in section_body:
                combined.append(f"<!-- FILE: {section_name}.md -->\n{section_body['content']}")
        if combined:
            return "\n\n".join(combined)

    analysis = payload.get("analysis", {})
    review = payload.get("review", {})
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
    if review:
        lines.append(f"- Status: {review.get('status', 'N/A')}")
        for finding in review.get("findings", []):
            lines.append(f"- {finding}")
    return "\n".join(lines)


def export_artifacts(project_id: str, job_id: str, payload: Dict[str, Any]) -> Dict[str, str]:
    job_dir = _job_dir(project_id, job_id)
    json_path = job_dir / "detail-design.json"
    markdown_path = job_dir / "detail-design.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    
    markdown_content = _to_markdown(payload)
    markdown_path.write_text(markdown_content)

    detail_design = payload.get("detailDesign", {})
    is_multi_file = any(isinstance(v, dict) and "content" in v for v in detail_design.values())
    
    from app.core.config import INPUT_ROOT_PATH
    input_dd_dir = INPUT_ROOT_PATH / "DD"
    
    if is_multi_file:
        for section_name, section_body in detail_design.items():
            if isinstance(section_body, dict) and "content" in section_body:
                # Clean filename
                safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in section_name)
                # Write individual file to job_dir for ZIP export
                (job_dir / f"{safe_name}.md").write_text(section_body["content"])
                
                # Write to INPUT/DD as seed sample
                if input_dd_dir.exists():
                    target_dir = input_dd_dir / "generated" / job_id[:8]
                    target_dir.mkdir(parents=True, exist_ok=True)
                    (target_dir / f"{safe_name}.md").write_text(section_body["content"])
    else:
        # Fallback for old format
        if input_dd_dir.exists():
            seed_path = input_dd_dir / f"generated_{job_id[:8]}.md"
            seed_path.write_text(markdown_content)

    return {
        "jsonPath": str(json_path),
        "markdownPath": str(markdown_path),
    }
