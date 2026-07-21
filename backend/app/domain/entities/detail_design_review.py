from typing import Any, Dict, List

from app.domain.common_inputs.checklists import CHECKLISTS


def _resolve_path(payload: Dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def review_detail_design(payload: Dict[str, Any], iteration: int) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    checklist = CHECKLISTS["detail_design"]
    rules = checklist.get("rules", checklist) if isinstance(checklist, dict) else checklist

    for rule in rules:
        if isinstance(rule, dict):
            path = rule["path"]
            rule_id = rule["id"]
            severity = rule.get("severity", "error")
            message = rule.get("message", f"Missing or empty section: {path}")
        else:
            path = rule
            rule_id = path
            severity = "error"
            message = f"Missing or empty section: {path}"

        value = _resolve_path(payload, path)
        if value in (None, "", [], {}):
            findings.append(
                {
                    "ruleId": rule_id,
                    "severity": severity,
                    "path": path,
                    "message": message,
                }
            )

    has_error = any(finding["severity"] == "error" for finding in findings)
    status = "NG" if has_error else "PASS"
    return {
        "status": status,
        "iteration": iteration,
        "findings": findings,
    }
