import json
import re
from typing import Any, Dict, List, Optional

MODULE_TYPES = {"screen", "api", "batch"}
COMPONENT_ID_PATTERN = re.compile(r"\bN[A-Z0-9]{5,}\b")


def _stringify_list(values: List[Any]) -> List[str]:
    normalized: List[str] = []
    for value in values:
        if isinstance(value, str):
            normalized.append(value)
        else:
            normalized.append(json.dumps(value, ensure_ascii=True))
    return normalized


def build_retrieval_query(
    basic_design: str, basic_design_analytics: Dict[str, Any]
) -> str:
    entities = _stringify_list(basic_design_analytics.get("entities", []))
    business_flows = _stringify_list(
        basic_design_analytics.get("businessFlows", [])
    )
    return "\n".join(
        [
            basic_design,
            basic_design_analytics.get("summary", ""),
            " ".join(entities),
            " | ".join(business_flows),
        ]
    )


def build_sparse_query(
    basic_design: str,
    basic_design_analytics: Dict[str, Any],
) -> str:
    """Build keyword-heavy query text for sparse retrieval.

    The dense query keeps broader requirement context, while sparse query
    emphasizes exact identifiers such as screen IDs, endpoint names, entities,
    and flow names.
    """
    exact_terms: List[str] = []
    for key in ("screens", "entities", "apiCandidates", "businessFlows", "uiSignals"):
        exact_terms.extend(_stringify_list(basic_design_analytics.get(key, [])))
    component_id = infer_component_id_filter(basic_design, basic_design_analytics)
    if component_id:
        exact_terms.append(component_id)
    exact_terms.append(basic_design_analytics.get("summary", ""))
    return "\n".join(term for term in exact_terms if str(term).strip())


def build_query_segments(
    basic_design: str,
    basic_design_analytics: Dict[str, Any],
) -> List[Dict[str, str]]:
    segments = [{"kind": "basic_design", "text": basic_design}]
    for key in ("summary", "screens", "entities", "businessFlows", "apiCandidates", "uiSignals"):
        value = basic_design_analytics.get(key, "")
        if isinstance(value, list):
            text = "\n".join(_stringify_list(value))
        else:
            text = str(value)
        if text.strip():
            segments.append({"kind": key, "text": text})
    return segments


def build_retrieval_request(
    basic_design: str,
    basic_design_analytics: Dict[str, Any],
) -> Dict[str, Any]:
    filters: Dict[str, Any] = {"approval_status": "reviewed"}
    module_type = infer_module_type_filter(basic_design, basic_design_analytics)
    if module_type is not None:
        filters["module_type"] = module_type
    component_id = infer_component_id_filter(basic_design, basic_design_analytics)
    if component_id is not None:
        filters["component_id"] = component_id
    dense_query = build_retrieval_query(basic_design, basic_design_analytics)
    sparse_query = build_sparse_query(basic_design, basic_design_analytics)
    return {
        "query": dense_query,
        "denseQuery": dense_query,
        "sparseQuery": sparse_query,
        "filters": filters,
        "segments": build_query_segments(basic_design, basic_design_analytics),
    }


def infer_module_type_filter(
    basic_design: str,
    basic_design_analytics: Dict[str, Any],
) -> Optional[str]:
    modules = [
        str(module).strip().lower()
        for module in basic_design_analytics.get("modules", [])
        if str(module).strip().lower() in MODULE_TYPES
    ]
    unique_modules = sorted(set(modules))
    if len(unique_modules) == 1:
        return unique_modules[0]

    query_text = build_retrieval_query(basic_design, basic_design_analytics).lower()
    hinted_modules = {
        module_type for module_type in MODULE_TYPES if re.search(rf"\b{module_type}\b", query_text)
    }
    if len(hinted_modules) == 1:
        return next(iter(hinted_modules))
    return None


def infer_component_id_filter(
    basic_design: str,
    basic_design_analytics: Dict[str, Any],
) -> Optional[str]:
    raw_values: List[str] = [basic_design]
    for key in ("summary",):
        raw_values.append(str(basic_design_analytics.get(key, "")))
    for key in ("screens", "entities", "businessFlows", "apiCandidates", "uiSignals"):
        raw_values.extend(_stringify_list(basic_design_analytics.get(key, [])))

    matches = {
        match.group(0)
        for value in raw_values
        for match in COMPONENT_ID_PATTERN.finditer(value)
    }
    if len(matches) == 1:
        return next(iter(matches))
    return None
