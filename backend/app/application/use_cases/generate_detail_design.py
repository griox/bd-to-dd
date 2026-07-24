import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.application.services.common_input_service import CommonInputService
from app.application.services.input_reference_service import InputReferenceService
from app.application.services.prompt_catalog import (
    COMMON_COMPONENTS,
    STAGE_NAMES,
)
from app.application.services.prompt_runtime_service import PromptRuntimeService
from app.application.services.retrieval_query_service import build_retrieval_request
from app.application.use_cases.ingest_reviewed_dd import KnowledgeBaseService
from app.core.config import MAX_REVIEW_ITERATIONS
from app.core.logging import logger
from app.domain.entities.detail_design_review import review_detail_design
from app.infrastructure.langchain.chains import LLMService


class GenerationService:
    def __init__(self) -> None:
        self.common_input_service = CommonInputService()
        self.input_reference_service = InputReferenceService()
        self.prompt_runtime_service = PromptRuntimeService()
        self.kb_service = KnowledgeBaseService()
        self.llm_service = LLMService()
        self._build_chains()

    def _build_chains(self) -> None:
        prompt_catalog = self.prompt_runtime_service.get_prompt_catalog()
        self.common_input_chain = RunnableLambda(
            lambda _: self.common_input_service.get_common_input()
        )
        self.basic_design_analytics_chain = self.llm_service.build_json_chain(
            prompt_catalog["basic_design_analytics"]["system"],
            prompt_catalog["basic_design_analytics"]["user"],
            self._fallback_basic_design_analytics,
            chain_name="basic_design_analytics",
        )
        self.sample_retrieval_chain = RunnableLambda(self._retrieve_sample_designs)
        self.design_analysis_chain = self.llm_service.build_json_chain(
            prompt_catalog["design_analysis_generation"]["system"],
            prompt_catalog["design_analysis_generation"]["user"],
            self._fallback_design_analysis,
            chain_name="design_analysis_generation",
        )
        self.detail_design_chain = self.llm_service.build_json_chain(
            prompt_catalog["detail_design_generation"]["system"],
            prompt_catalog["detail_design_generation"]["user"],
            self._fallback_detail_design,
            chain_name="detail_design_generation",
        )
        ui_prompt = prompt_catalog.get("detail_design_ui_generation", prompt_catalog["detail_design_generation"])
        logic_prompt = prompt_catalog.get("detail_design_logic_generation", prompt_catalog["detail_design_generation"])
        self.detail_design_ui_chain = self.llm_service.build_json_chain(
            ui_prompt["system"],
            ui_prompt["user"],
            self._fallback_detail_design,
            chain_name="detail_design_ui_generation",
        )
        self.detail_design_logic_chain = self.llm_service.build_json_chain(
            logic_prompt["system"],
            logic_prompt["user"],
            self._fallback_detail_design,
            chain_name="detail_design_logic_generation",
        )
        self.detail_design_review_chain = self.llm_service.build_json_chain(
            prompt_catalog["detail_design_review"]["system"],
            prompt_catalog["detail_design_review"]["user"],
            self._fallback_detail_design_review,
            chain_name="detail_design_review",
        )
        self.bootstrap_chain = RunnablePassthrough.assign(
            common_input=self.common_input_chain
        )
        self.review_loop_chain = RunnableLambda(self._run_review_loop)

    def _stringify_prompt_value(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return "\n".join(self._stringify_prompt_value(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, indent=2, ensure_ascii=False)
        return str(value)

    def _format_common_guidance(
        self,
        common_input: Dict[str, Any],
        analytics: Optional[Dict[str, Any]] = None,
    ) -> str:
        guidance = ["Guidelines:"]
        for item in common_input.get("guidelines", []):
            if isinstance(item, dict):
                guidance.append(
                    f"- [{item.get('id')}] {item.get('stage')} "
                    f"({item.get('severity')}): {item.get('rule')}"
                )
            else:
                guidance.append(f"- {item}")
        guidance.append("")

        # Extract active signals for dynamic filtering
        ui_signals = set(
            s.lower() for s in (analytics.get("uiSignals", []) if analytics else [])
        )
        active_modules = set(
            m.lower() for m in (analytics.get("modules", []) if analytics else [])
        )

        guidance.append("Common input image references:")
        for reference in common_input.get("imageReferences", []):
            guidance.append(
                f"- {reference.get('sourcePath')}: "
                f"{reference.get('summary', self._stringify_prompt_value(reference))}"
            )
        guidance.append("")
        guidance.append("Planning skills:")
        for key, skill in common_input.get("skills", {}).items():
            guidance.append(
                f"- {key} ({skill['stage']}): {skill['purpose']}"
            )
            guidance.append(
                "  Inputs: " + ", ".join(skill.get("inputs", []))
            )
            guidance.append(
                "  Outputs: " + ", ".join(skill.get("outputs", []))
            )
            guidance.append(
                "  Required sections: "
                + ", ".join(skill.get("templateSections", [])[:8])
            )
        guidance.append("")
        guidance.append("Common components:")
        components = common_input.get("commonComponents", [])
        for component in components:
            if isinstance(component, dict):
                comp_id = str(component.get("id", "")).lower()
                comp_applies = [str(a).lower() for a in component.get("appliesTo", [])]
                # Filter if analytics signals are available
                if ui_signals or active_modules:
                    matches_signal = any(s in comp_id for s in ui_signals) or any(
                        s in a for s in ui_signals for a in comp_applies
                    )
                    matches_module = any(m in comp_id for m in active_modules) or any(
                        m in a for m in active_modules for a in comp_applies
                    )
                    if not (matches_signal or matches_module):
                        continue
                guidance.append(
                    f"- {component.get('id')}: {component.get('ddUsage')}"
                )
            else:
                guidance.append(f"- {component}")
        return "\n".join(guidance)

    def _format_common_components(self, components: Any) -> str:
        if not isinstance(components, list):
            return self._stringify_prompt_value(components)
        names = []
        for component in components:
            if isinstance(component, dict):
                names.append(
                    f"{component.get('name', component.get('id'))} "
                    f"({', '.join(component.get('appliesTo', []))})"
                )
            else:
                names.append(str(component))
        return ", ".join(names)

    def _normalize_string_list(self, value: Any) -> List[str]:
        if value in (None, ""):
            return []
        if not isinstance(value, (list, tuple)):
            return [self._stringify_prompt_value(value)]
        return [self._stringify_prompt_value(item) for item in value]

    def _normalize_basic_design_analytics(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}
        normalized = dict(payload)
        normalized["summary"] = self._stringify_prompt_value(
            payload.get("summary", "")
        )
        for key in [
            "modules",
            "screens",
            "entities",
            "businessFlows",
            "apiCandidates",
            "externalInterfaces",
            "uiSignals",
            "assumptions",
        ]:
            normalized[key] = self._normalize_string_list(payload.get(key, []))
        return normalized

    def _normalize_design_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}
        normalized = dict(payload)
        normalized["summary"] = self._stringify_prompt_value(
            payload.get("summary", "")
        )
        normalized["scope"] = self._stringify_prompt_value(payload.get("scope", ""))
        for key in [
            "entities",
            "businessFlows",
            "apiCandidates",
            "uiSignals",
            "risks",
            "assumptions",
        ]:
            normalized[key] = self._normalize_string_list(payload.get(key, []))
        return normalized

    def _normalize_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}
        normalized = dict(payload)
        if "status" in payload:
            status = self._stringify_prompt_value(payload["status"]).upper()
            normalized["status"] = status if status in {"PASS", "NG"} else "NG"
        else:
            normalized["status"] = "PASS" if payload.get("is_passed") is True else "NG"

        findings = payload.get("findings")
        if findings is None:
            findings = payload.get("issues", [])
        next_actions = payload.get("nextActions")
        if next_actions is None:
            next_actions = payload.get("suggestions", [])

        normalized["findings"] = self._normalize_string_list(findings)
        normalized["strengths"] = self._normalize_string_list(
            payload.get("strengths", [])
        )
        normalized["nextActions"] = self._normalize_string_list(next_actions)
        return normalized

    def _normalize_detail_design(self, payload: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        if not isinstance(payload, dict):
            payload = {}
        normalized: Dict[str, Dict[str, str]] = {}
        for module_name in ["screen", "api", "batch"]:
            module_value = payload.get(module_name, {})
            if isinstance(module_value, dict):
                normalized[module_name] = {
                    self._stringify_prompt_value(key): self._stringify_prompt_value(value)
                    for key, value in module_value.items()
                }
                continue
            normalized[module_name] = {
                "00_Document": self._stringify_prompt_value(module_value)
            }
        for module_name, module_value in payload.items():
            if module_name in normalized:
                continue
            if isinstance(module_value, dict):
                normalized[module_name] = {
                    self._stringify_prompt_value(key): self._stringify_prompt_value(value)
                    for key, value in module_value.items()
                }
            else:
                normalized[module_name] = {
                    "00_Document": self._stringify_prompt_value(module_value)
                }
        return normalized

    def _analysis_review_state(
        self,
        current_analysis_review: Optional[Dict[str, Any]] = None,
        status: str = "pending",
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        history = list((current_analysis_review or {}).get("feedbackHistory", []))
        last_feedback = (current_analysis_review or {}).get("lastFeedback")
        if feedback:
            history.append(feedback)
            last_feedback = feedback
        return {
            "status": status,
            "feedbackHistory": history,
            "lastFeedback": last_feedback,
        }

    def _empty_manual_review_state(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "feedbackHistory": [],
            "lastFeedback": None,
            "autoReviewStatus": None,
            "autoReviewFindings": [],
        }

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _preview_text(self, value: Any, max_length: int = 220) -> str:
        text = self._stringify_prompt_value(value).strip()
        if len(text) <= max_length:
            return text
        return f"{text[: max_length - 3]}..."

    def _serialize_candidate(self, candidate: Any) -> Dict[str, Any]:
        return {
            "chunkId": getattr(candidate, "chunk_id", ""),
            "score": round(float(getattr(candidate, "score", 0.0)), 4),
            "source": getattr(candidate, "source", ""),
            "sectionPath": getattr(candidate, "metadata", {}).get("section_path", ""),
            "moduleType": getattr(candidate, "metadata", {}).get("module_type", ""),
            "componentId": getattr(candidate, "metadata", {}).get("component_id", ""),
            "sources": getattr(candidate, "metadata", {}).get("sources"),
            "contentPreview": self._preview_text(getattr(candidate, "content", "")),
        }

    def _serialize_candidates(self, candidates: List[Any], limit: int = 5) -> List[Dict[str, Any]]:
        return [self._serialize_candidate(candidate) for candidate in candidates[:limit]]

    def _append_trace_step(
        self,
        trace_steps: List[Dict[str, Any]],
        key: str,
        label: str,
        summary: str,
        preview: Any,
        raw: Any,
        status: str = "completed",
    ) -> None:
        trace_steps.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "summary": summary,
                "preview": preview,
                "raw": raw,
                "completedAt": self._now_iso(),
            }
        )

    def _rehydrate_sample_designs(self, result: Dict[str, Any]) -> Dict[str, Any]:
        references = result.get("sampleDesigns", [])
        resources = result.get("resourcesUsed", {})
        return {
            "references": references,
            "referenceCount": len(references),
            "knowledgeBase": resources.get("knowledgeBase", {}),
        }

    def _build_resources_used(
        self,
        common_input: Dict[str, Any],
        sample_designs: Dict[str, Any],
        input_references: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "commonInputVersion": common_input["version"],
            "sourceFiles": common_input["sourceFiles"],
            "templates": list(common_input["templates"].keys()),
            "checklists": list(common_input["checklists"].keys()),
            "skills": common_input["skills"],
            "guidelines": common_input["guidelines"],
            "commonComponents": common_input["commonComponents"],
            "referencesFound": sample_designs["referenceCount"],
            "inputReferences": {
                "referenceCount": (input_references or {}).get("referenceCount", 0),
                "references": [
                    {
                        "componentId": reference.get("componentId"),
                        "name": reference.get("name"),
                        "sourceFiles": reference.get("sourceFiles", []),
                    }
                    for reference in (input_references or {}).get("references", [])
                ],
            },
            "knowledgeBase": sample_designs["knowledgeBase"],
            "langchainStages": STAGE_NAMES,
        }

    def _fallback_basic_design_analytics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        basic_design = payload["basic_design"]
        ui_design = payload.get("ui_design") or ""
        summary_parts = ["Basic Design analyzed."]
        if ui_design:
            summary_parts.append("UI Design input included.")
        entities = sorted(
            {
                word.strip(".,:;()")
                for word in basic_design.split()
                if word[:1].isupper() and len(word) > 3
            }
        )[:8]
        screens = [
            line.strip("- ").strip()
            for line in ui_design.splitlines()
            if line.strip()
        ][:5]
        flows = [
            line.strip("- ").strip()
            for line in basic_design.splitlines()
            if line.strip()
        ][:5]
        api_candidates = [f"/api/{entity.lower()}" for entity in entities[:3]]
        return {
            "summary": " ".join(summary_parts),
            "modules": ["screen", "api", "batch"],
            "screens": screens or ["Main workflow screen"],
            "entities": entities or ["User", "Request"],
            "businessFlows": flows or ["Review requirements", "Generate detail design"],
            "apiCandidates": api_candidates or ["/api/projects", "/api/generations"],
            "externalInterfaces": ["Gemini LLM API", "Gemini Embeddings API", "Qdrant"],
            "uiSignals": [
                "Screens and components inferred from UI design"
                if ui_design
                else "No UI design provided"
            ],
            "assumptions": [
                "Basic Design is the primary business source.",
                "UI Design is optional and used as interaction guidance.",
            ],
        }

    def _retrieve_sample_designs(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        retrieval_request = build_retrieval_request(
            basic_design=payload["basic_design"],
            basic_design_analytics=payload["basic_design_analytics"],
        )
        retrieval_bundle = self.kb_service.retrieve_debug_bundle(
            retrieval_request["denseQuery"],
            filters=retrieval_request["filters"],
            sparse_query=retrieval_request["sparseQuery"],
        )
        assembled_context = retrieval_bundle["assembledContext"]
        references = [candidate.content for candidate in assembled_context.references]
        return {
            "references": references,
            "referenceCount": len(references),
            "knowledgeBase": self.kb_service.get_status(),
            "retrieval": {
                "filters": retrieval_request["filters"],
                "segments": retrieval_request["segments"],
                "denseQueryLength": len(retrieval_request["denseQuery"]),
                "sparseQueryLength": len(retrieval_request["sparseQuery"]),
            },
            "trace": {
                "query": retrieval_request,
                "denseResults": self._serialize_candidates(
                    retrieval_bundle["denseResults"]
                ),
                "sparseResults": self._serialize_candidates(
                    retrieval_bundle["sparseResults"]
                ),
                "rrfResults": self._serialize_candidates(
                    retrieval_bundle["fusedResults"]
                ),
                "contextAssembly": assembled_context.to_dict(),
            },
        }

    def _fallback_design_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        analytics = payload["basic_design_analytics"]
        sample_designs = payload["sample_designs"]
        feedback = (payload.get("analysis_feedback") or "").strip()
        assumptions = list(analytics["assumptions"]) + [
            f"{sample_designs['referenceCount']} reviewed sample(s) were retrieved.",
        ]
        if feedback:
            assumptions.append(f"Designer feedback to address: {feedback}")
        return {
            "summary": analytics["summary"],
            "scope": "Generate detail design for the provided module scope.",
            "entities": analytics["entities"],
            "businessFlows": analytics["businessFlows"],
            "apiCandidates": analytics["apiCandidates"],
            "uiSignals": analytics["uiSignals"],
            "risks": [
                "Knowledge base may not contain a close reference sample.",
                "Some assumptions may need designer confirmation.",
            ],
            "assumptions": assumptions,
        }

    def _fallback_detail_design(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        analysis = payload["design_analysis"]
        ui_design = payload.get("ui_design") or ""
        sample_designs = payload["sample_designs"]
        common_input = payload.get("common_input", {})
        common_components = common_input.get("commonComponents", COMMON_COMPONENTS)
        review_feedback_value = payload.get("review_feedback") or []
        if isinstance(review_feedback_value, str):
            review_feedback = [review_feedback_value] if review_feedback_value else []
        else:
            review_feedback = [
                self._stringify_prompt_value(item)
                for item in review_feedback_value
            ]
        detail_design = {
            "screen": {
                "01_UI_Design": (
                    "Use uploaded UI Design as the primary interaction reference."
                    if ui_design
                    else "Create a simple workflow-driven screen with upload, generation, and review states."
                ),
                "02_Components": self._format_common_components(common_components),
                "03_Data_Models": ", ".join(analysis["entities"]),
                "04_API_Integration": ", ".join(analysis["apiCandidates"]),
                "05_Business_Logic": "Handle uploads, trigger staged generation, and display review findings.",
                "06_State_Management": "Track projectId, document availability, job status, review findings, and artifacts.",
            },
            "api": {
                "01_Contract": "Expose project creation, BD/UI upload, generation trigger, generation status, and artifact download metadata.",
                "02_Business_Logic": "Separate analytics, retrieval, design analysis, DD generation, and review as LangChain stages.",
                "03_Data_Access": (
                    "Persist jobs in SQL and use vector retrieval when references exist "
                    f"({sample_designs['referenceCount']} retrieved)."
                ),
            },
            "batch": {
                "01_Job_Definition": "Background generation job with staged status transitions.",
                "02_Processing_Logic": "Analyze -> retrieve samples -> generate design analysis -> generate detail design -> validate -> export.",
                "03_Data_Access": "Read source documents from temp storage and write artifacts to the artifacts directory.",
            },
        }
        if review_feedback:
            detail_design["api"]["02_Business_Logic"] += " Feedback addressed: " + "; ".join(
                review_feedback
            )
        return detail_design

    def _fallback_detail_design_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        review = review_detail_design(
            {
                "analysis": payload["design_analysis"],
                "detailDesign": payload["detail_design"],
            },
            payload["iteration"],
        )
        review["strengths"] = [
            "Stage outputs were generated in the expected architecture order."
        ]
        review["nextActions"] = (
            ["Export artifacts and continue to implementation."]
            if review["status"] == "PASS"
            else review["findings"]
        )
        return review

    def _run_review_loop(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        review_feedback: List[str] = []
        manual_feedback = (payload.get("manual_feedback") or "").strip()
        if manual_feedback:
            review_feedback.append(manual_feedback)
        detail_design: Dict[str, Any] = {}
        review: Dict[str, Any] = {
            "status": "NG",
            "iteration": 0,
            "findings": [],
            "strengths": [],
            "nextActions": [],
        }
        project_id = self._stringify_prompt_value(payload.get("project_id", "unknown"))
        job_id = self._stringify_prompt_value(payload.get("job_id", "unknown"))
        update_status = payload["update_status"]
        trace_steps: List[Dict[str, Any]] = []

        def notify(status: str, step: str, summary: str) -> None:
            try:
                update_status(status, step, summary)
            except TypeError:
                update_status(status)

        logger.info(
            "[review_loop] start project_id=%s job_id=%s max_iterations=%s manual_feedback=%s",
            project_id,
            job_id,
            MAX_REVIEW_ITERATIONS,
            bool(manual_feedback),
        )

        for iteration in range(1, MAX_REVIEW_ITERATIONS + 1):
            logger.info(
                "[review_loop] iteration=%s project_id=%s job_id=%s phase=generate_dd feedback_count=%s",
                iteration,
                project_id,
                job_id,
                len(review_feedback),
            )
            notify(
                "generating_dd",
                "generate_dd",
                f"Generating detail design iteration {iteration}.",
            )
            try:
                chain_payload = {
                    **payload,
                    "templates": payload["common_input"]["templates"],
                    "guidelines": self._format_common_guidance(
                        payload["common_input"], payload.get("basic_design_analytics")
                    ),
                    "sample_designs": payload["sample_designs"],
                    "review_feedback": self._stringify_prompt_value(review_feedback),
                }
                
                if not self.llm_service.enabled:
                    detail_design = self.detail_design_chain.invoke(chain_payload)
                else:
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        fut_ui = executor.submit(self.detail_design_ui_chain.invoke, chain_payload)
                        fut_logic = executor.submit(self.detail_design_logic_chain.invoke, chain_payload)
                        res_ui = fut_ui.result()
                        res_logic = fut_logic.result()
                    
                    merged = {}
                    if isinstance(res_ui, dict):
                        merged.update(res_ui)
                    if isinstance(res_logic, dict):
                        merged.update(res_logic)
                    detail_design = merged if merged else self._fallback_detail_design(chain_payload)

                detail_design = self._normalize_detail_design(detail_design)
            except Exception:
                logger.exception(
                    "[review_loop] iteration=%s project_id=%s job_id=%s phase=generate_dd failed",
                    iteration,
                    project_id,
                    job_id,
                )
                raise
            logger.info(
                "[review_loop] iteration=%s project_id=%s job_id=%s phase=generate_dd completed modules=%s",
                iteration,
                project_id,
                job_id,
                ",".join(sorted(detail_design.keys())) if isinstance(detail_design, dict) else "unknown",
            )
            self._append_trace_step(
                trace_steps,
                key="detail_design_generation",
                label="Detail Design Generation",
                summary=(
                    f"Generated detail design iteration {iteration} "
                    f"for modules: {', '.join(sorted(detail_design.keys()))}."
                ),
                preview={
                    "iteration": iteration,
                    "modules": sorted(detail_design.keys()),
                    "screenSections": list(detail_design.get("screen", {}).keys())[:6],
                    "apiSections": list(detail_design.get("api", {}).keys())[:6],
                    "batchSections": list(detail_design.get("batch", {}).keys())[:6],
                },
                raw=detail_design,
            )

            logger.info(
                "[review_loop] iteration=%s project_id=%s job_id=%s phase=validate",
                iteration,
                project_id,
                job_id,
            )
            notify(
                "validating",
                "validate",
                f"Validating generated detail design iteration {iteration}.",
            )
            try:
                review = self.detail_design_review_chain.invoke(
                    {
                        **payload,
                        "detail_design": detail_design,
                        "design_analysis": payload["design_analysis"],
                        "checklist": payload["common_input"]["checklists"],
                        "iteration": iteration,
                    }
                )
            except Exception:
                logger.exception(
                    "[review_loop] iteration=%s project_id=%s job_id=%s phase=validate failed",
                    iteration,
                    project_id,
                    job_id,
                )
                raise
            review = self._normalize_review(review)
            review["iteration"] = iteration
            logger.info(
                "[review_loop] iteration=%s project_id=%s job_id=%s phase=validate completed status=%s findings=%s",
                iteration,
                project_id,
                job_id,
                review["status"],
                len(review.get("findings", [])),
            )
            self._append_trace_step(
                trace_steps,
                key="detail_design_review",
                label="Detail Design Auto Review",
                summary=(
                    f"Auto-review iteration {iteration} returned "
                    f"{review['status']} with {len(review.get('findings', []))} finding(s)."
                ),
                preview={
                    "iteration": iteration,
                    "status": review["status"],
                    "findings": review.get("findings", [])[:5],
                    "nextActions": review.get("nextActions", [])[:5],
                },
                raw=review,
            )
            if review["status"] == "PASS":
                logger.info(
                    "[review_loop] iteration=%s project_id=%s job_id=%s phase=complete result=pass",
                    iteration,
                    project_id,
                    job_id,
                )
                break
            review_feedback = [
                self._stringify_prompt_value(item)
                for item in review.get("findings", [])
            ]
            if not review_feedback:
                logger.warning(
                    "[review_loop] iteration=%s project_id=%s job_id=%s phase=retry_skipped reason=no_findings",
                    iteration,
                    project_id,
                    job_id,
                )
                notify(
                    "needs_manual_review",
                    "review_inconclusive",
                    "Auto-review returned NG without actionable findings; manual review is required.",
                )
                break
            logger.info(
                "[review_loop] iteration=%s project_id=%s job_id=%s phase=retry next_feedback=%s",
                iteration,
                project_id,
                job_id,
                len(review_feedback),
            )
            notify(
                "generating_dd",
                "retry",
                f"Auto-review returned {len(review_feedback)} finding(s); retrying.",
            )

        logger.info(
            "[review_loop] finish project_id=%s job_id=%s final_status=%s final_iteration=%s",
            project_id,
            job_id,
            review.get("status"),
            review.get("iteration"),
        )

        return {
            "detail_design": detail_design,
            "review": review,
            "traceSteps": trace_steps,
        }

    def _manual_review_state(
        self,
        current_manual_review: Optional[Dict[str, Any]],
        review: Dict[str, Any],
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        history = list((current_manual_review or {}).get("feedbackHistory", []))
        last_feedback = (current_manual_review or {}).get("lastFeedback")
        if feedback:
            history.append(feedback)
            last_feedback = feedback
        return {
            "status": "pending",
            "feedbackHistory": history,
            "lastFeedback": last_feedback,
            "autoReviewStatus": review["status"],
            "autoReviewFindings": review.get("findings", []),
        }

    def _stage_output(self, name: str, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            if "summary" in payload:
                summary = payload["summary"]
            elif "referenceCount" in payload:
                summary = f"{payload['referenceCount']} reference sample(s) retrieved"
            elif "status" in payload:
                summary = payload["status"]
            else:
                summary = ", ".join(payload.keys())
        else:
            summary = str(payload)
        return {"name": name, "summary": summary}

    def run(
        self,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: Optional[str],
        update_status,
    ) -> Dict[str, Any]:
        return self.run_analysis_phase(
            project_id=project_id,
            job_id=job_id,
            basic_design=basic_design,
            ui_design=ui_design,
            update_status=update_status,
        )

    def run_analysis_phase(
        self,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: Optional[str],
        update_status,
    ) -> Dict[str, Any]:
        self._build_chains()
        base_payload = {
            "project_id": project_id,
            "job_id": job_id,
            "basic_design": basic_design,
            "ui_design": ui_design or "",
            "update_status": update_status,
        }

        logger.info(
            "[analysis_phase] start project_id=%s job_id=%s has_ui_design=%s",
            project_id,
            job_id,
            bool(ui_design),
        )
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=bootstrap",
            project_id,
            job_id,
        )
        try:
            context = self.bootstrap_chain.invoke(base_payload)
        except Exception:
            logger.exception(
                "[analysis_phase] project_id=%s job_id=%s phase=bootstrap failed",
                project_id,
                job_id,
            )
            raise
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=bootstrap completed common_input_version=%s",
            project_id,
            job_id,
            context.get("common_input", {}).get("version"),
        )
        pipeline_stages: List[Dict[str, Any]] = []
        trace_steps: List[Dict[str, Any]] = []

        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=find_input_references",
            project_id,
            job_id,
        )
        try:
            input_references = self.input_reference_service.find_similar_references(
                basic_design=basic_design,
                ui_design=ui_design or "",
            )
        except Exception:
            logger.exception(
                "[analysis_phase] project_id=%s job_id=%s phase=find_input_references failed",
                project_id,
                job_id,
            )
            raise
        context["input_reference_examples"] = input_references["formatted"]
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=find_input_references completed references=%s",
            project_id,
            job_id,
            input_references.get("referenceCount"),
        )

        update_status("analyzing")
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=basic_design_analytics",
            project_id,
            job_id,
        )
        try:
            basic_design_analytics = self.basic_design_analytics_chain.invoke(
                {
                    **context,
                    "common_input": json.dumps(context["common_input"], ensure_ascii=False),
                }
            )
        except Exception:
            logger.exception(
                "[analysis_phase] project_id=%s job_id=%s phase=basic_design_analytics failed",
                project_id,
                job_id,
            )
            raise
        basic_design_analytics = self._normalize_basic_design_analytics(
            basic_design_analytics
        )
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=basic_design_analytics completed modules=%s entities=%s flows=%s",
            project_id,
            job_id,
            len(basic_design_analytics.get("modules", [])),
            len(basic_design_analytics.get("entities", [])),
            len(basic_design_analytics.get("businessFlows", [])),
        )
        self._append_trace_step(
            trace_steps,
            key="basic_design_analytics",
            label="Basic Design Analytics",
            summary=basic_design_analytics.get("summary", "Basic design analyzed."),
            preview={
                "modules": basic_design_analytics.get("modules", []),
                "entities": basic_design_analytics.get("entities", [])[:5],
                "businessFlows": basic_design_analytics.get("businessFlows", [])[:5],
                "apiCandidates": basic_design_analytics.get("apiCandidates", [])[:5],
            },
            raw=basic_design_analytics,
        )
        pipeline_stages.append(
            self._stage_output(STAGE_NAMES[0], basic_design_analytics)
        )

        update_status("retrieving_samples")
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=retrieve_samples",
            project_id,
            job_id,
        )
        try:
            sample_designs = self.sample_retrieval_chain.invoke(
                {
                    **context,
                    "basic_design_analytics": basic_design_analytics,
                }
            )
        except Exception:
            logger.exception(
                "[analysis_phase] project_id=%s job_id=%s phase=retrieve_samples failed",
                project_id,
                job_id,
            )
            raise
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=retrieve_samples completed references=%s",
            project_id,
            job_id,
            sample_designs.get("referenceCount"),
        )
        retrieval_trace = sample_designs.get("trace", {})
        self._append_trace_step(
            trace_steps,
            key="build_retrieval_query",
            label="Build Retrieval Query",
            summary="Built dense query, sparse query, and metadata filters for KB lookup.",
            preview={
                "filters": retrieval_trace.get("query", {}).get("filters", {}),
                "segments": retrieval_trace.get("query", {}).get("segments", [])[:5],
                "denseQueryPreview": self._preview_text(
                    retrieval_trace.get("query", {}).get("denseQuery", "")
                ),
                "sparseQueryPreview": self._preview_text(
                    retrieval_trace.get("query", {}).get("sparseQuery", "")
                ),
            },
            raw=retrieval_trace.get("query", sample_designs.get("retrieval", {})),
        )
        self._append_trace_step(
            trace_steps,
            key="dense_search",
            label="Dense Search",
            summary=f"Dense retrieval returned {len(retrieval_trace.get('denseResults', []))} candidate(s).",
            preview=retrieval_trace.get("denseResults", []),
            raw=retrieval_trace.get("denseResults", []),
        )
        self._append_trace_step(
            trace_steps,
            key="sparse_search",
            label="Keyword Search",
            summary=f"Sparse retrieval returned {len(retrieval_trace.get('sparseResults', []))} candidate(s).",
            preview=retrieval_trace.get("sparseResults", []),
            raw=retrieval_trace.get("sparseResults", []),
        )
        self._append_trace_step(
            trace_steps,
            key="rrf_fusion",
            label="RRF Fusion",
            summary=f"Reciprocal Rank Fusion merged results into {len(retrieval_trace.get('rrfResults', []))} ranked candidate(s).",
            preview=retrieval_trace.get("rrfResults", []),
            raw=retrieval_trace.get("rrfResults", []),
        )
        context_preview = retrieval_trace.get("contextAssembly", {})
        self._append_trace_step(
            trace_steps,
            key="context_assembly",
            label="Context Assembly",
            summary=f"Context assembly selected {context_preview.get('referenceCount', sample_designs.get('referenceCount', 0))} reference sample(s).",
            preview=(context_preview.get("references") or [])[:5],
            raw=context_preview,
        )
        pipeline_stages.append(self._stage_output(STAGE_NAMES[1], sample_designs))

        update_status("generating_analysis")
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=design_analysis_generation",
            project_id,
            job_id,
        )
        try:
            design_analysis = self.design_analysis_chain.invoke(
                {
                    **context,
                    "basic_design_analytics": basic_design_analytics,
                    "sample_designs": sample_designs,
                    "guidelines": self._format_common_guidance(context["common_input"], basic_design_analytics),
                }
            )
        except Exception:
            logger.exception(
                "[analysis_phase] project_id=%s job_id=%s phase=design_analysis_generation failed",
                project_id,
                job_id,
            )
            raise
        design_analysis = self._normalize_design_analysis(design_analysis)
        logger.info(
            "[analysis_phase] project_id=%s job_id=%s phase=design_analysis_generation completed entities=%s risks=%s assumptions=%s",
            project_id,
            job_id,
            len(design_analysis.get("entities", [])),
            len(design_analysis.get("risks", [])),
            len(design_analysis.get("assumptions", [])),
        )
        self._append_trace_step(
            trace_steps,
            key="design_analysis_generation",
            label="Design Analysis Generation",
            summary=design_analysis.get("summary", "Design analysis generated."),
            preview={
                "scope": design_analysis.get("scope", ""),
                "entities": design_analysis.get("entities", [])[:5],
                "risks": design_analysis.get("risks", [])[:5],
                "assumptions": design_analysis.get("assumptions", [])[:5],
            },
            raw=design_analysis,
        )
        pipeline_stages.append(self._stage_output(STAGE_NAMES[2], design_analysis))

        common_input_snapshot = deepcopy(context["common_input"])
        result = {
            "inputs": {
                "hasBasicDesign": True,
                "hasUiDesign": bool(ui_design),
            },
            "resourcesUsed": self._build_resources_used(
                common_input_snapshot,
                sample_designs,
                input_references,
            ),
            "commonInputSnapshot": common_input_snapshot,
            "basicDesignAnalytics": basic_design_analytics,
            "sampleDesigns": sample_designs["references"],
            "analysis": design_analysis,
            "analysisReview": self._analysis_review_state(),
            "detailDesign": None,
            "review": None,
            "manualReview": self._empty_manual_review_state(),
            "pipeline": {"stages": pipeline_stages},
            "executionTrace": {"steps": trace_steps},
            "artifacts": None,
        }

        update_status("needs_analysis_review")
        logger.info(
            "[analysis_phase] finish project_id=%s job_id=%s status=needs_analysis_review",
            project_id,
            job_id,
        )
        return result

    def run_detail_design_phase(
        self,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: Optional[str],
        current_result: Dict[str, Any],
        update_status,
    ) -> Dict[str, Any]:
        self._build_chains()
        common_input = current_result.get("commonInputSnapshot", {})
        sample_designs = self._rehydrate_sample_designs(current_result)
        loop_result = self.review_loop_chain.invoke(
            {
                "project_id": project_id,
                "job_id": job_id,
                "basic_design": basic_design,
                "ui_design": ui_design or "",
                "update_status": update_status,
                "common_input": common_input,
                "basic_design_analytics": current_result["basicDesignAnalytics"],
                "sample_designs": sample_designs,
                "design_analysis": current_result["analysis"],
            }
        )
        revised_result = deepcopy(current_result)
        revised_result["commonInputSnapshot"] = deepcopy(common_input)
        revised_result["analysisReview"] = self._analysis_review_state(
            current_result.get("analysisReview"),
            status="approved",
        )
        revised_result["detailDesign"] = loop_result["detail_design"]
        revised_result["review"] = loop_result["review"]
        revised_result["manualReview"] = self._manual_review_state(
            current_result.get("manualReview"),
            loop_result["review"],
        )
        revised_result["artifacts"] = None
        revised_result["pipeline"] = {
            "stages": current_result["pipeline"]["stages"]
            + [
                self._stage_output(STAGE_NAMES[3], loop_result["detail_design"]),
                self._stage_output(STAGE_NAMES[4], loop_result["review"]),
            ]
        }
        revised_result["executionTrace"] = {
            "steps": current_result.get("executionTrace", {}).get("steps", [])
            + loop_result.get("traceSteps", [])
        }
        update_status("needs_manual_review")
        return revised_result

    def revise_analysis(
        self,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: Optional[str],
        current_result: Dict[str, Any],
        feedback: str,
        update_status,
    ) -> Dict[str, Any]:
        self._build_chains()
        logger.info(
            "[analysis_revise] start project_id=%s job_id=%s feedback_length=%s",
            project_id,
            job_id,
            len(feedback.strip()),
        )
        try:
            context = self.bootstrap_chain.invoke(
                {
                    "project_id": project_id,
                    "job_id": job_id,
                    "basic_design": basic_design,
                    "ui_design": ui_design or "",
                    "update_status": update_status,
                }
            )
        except Exception:
            logger.exception(
                "[analysis_revise] project_id=%s job_id=%s phase=bootstrap failed",
                project_id,
                job_id,
            )
            raise
        update_status("generating_analysis")
        sample_designs = self._rehydrate_sample_designs(current_result)
        logger.info(
            "[analysis_revise] project_id=%s job_id=%s phase=design_analysis_generation references=%s",
            project_id,
            job_id,
            sample_designs.get("referenceCount"),
        )
        try:
            design_analysis = self.design_analysis_chain.invoke(
                {
                    **context,
                    "basic_design_analytics": current_result["basicDesignAnalytics"],
                    "sample_designs": sample_designs,
                    "guidelines": self._format_common_guidance(context["common_input"], current_result["basicDesignAnalytics"]),
                    "analysis_feedback": feedback,
                }
            )
        except Exception:
            logger.exception(
                "[analysis_revise] project_id=%s job_id=%s phase=design_analysis_generation failed",
                project_id,
                job_id,
            )
            raise
        design_analysis = self._normalize_design_analysis(design_analysis)
        logger.info(
            "[analysis_revise] project_id=%s job_id=%s phase=design_analysis_generation completed assumptions=%s",
            project_id,
            job_id,
            len(design_analysis.get("assumptions", [])),
        )
        revised_result = deepcopy(current_result)
        revised_result["commonInputSnapshot"] = deepcopy(context["common_input"])
        revised_result["resourcesUsed"] = self._build_resources_used(
            context["common_input"],
            sample_designs,
        )
        revised_result["analysis"] = design_analysis
        revised_result["analysisReview"] = self._analysis_review_state(
            current_result.get("analysisReview"),
            feedback=feedback,
        )
        revised_result["detailDesign"] = None
        revised_result["review"] = None
        revised_result["manualReview"] = self._empty_manual_review_state()
        revised_result["artifacts"] = None
        revised_result["pipeline"] = {
            "stages": current_result["pipeline"]["stages"]
            + [
                {"name": "Analysis Review Update", "summary": feedback},
                self._stage_output(STAGE_NAMES[2], design_analysis),
            ]
        }
        trace_steps = list(current_result.get("executionTrace", {}).get("steps", []))
        self._append_trace_step(
            trace_steps,
            key="design_analysis_generation",
            label="Design Analysis Generation",
            summary=design_analysis.get("summary", "Design analysis updated."),
            preview={
                "feedback": feedback,
                "scope": design_analysis.get("scope", ""),
                "entities": design_analysis.get("entities", [])[:5],
                "risks": design_analysis.get("risks", [])[:5],
            },
            raw=design_analysis,
        )
        revised_result["executionTrace"] = {"steps": trace_steps}
        update_status("needs_analysis_review")
        logger.info(
            "[analysis_revise] finish project_id=%s job_id=%s status=needs_analysis_review",
            project_id,
            job_id,
        )
        return revised_result

    def revise(
        self,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: Optional[str],
        current_result: Dict[str, Any],
        feedback: str,
        update_status,
    ) -> Dict[str, Any]:
        self._build_chains()
        common_input = current_result.get("commonInputSnapshot", {})
        update_status("manual_updating")
        loop_result = self.review_loop_chain.invoke(
            {
                "project_id": project_id,
                "job_id": job_id,
                "basic_design": basic_design,
                "ui_design": ui_design or "",
                "update_status": update_status,
                "common_input": common_input,
                "basic_design_analytics": current_result["basicDesignAnalytics"],
                "sample_designs": {
                    "references": current_result.get("sampleDesigns", []),
                    "referenceCount": len(current_result.get("sampleDesigns", [])),
                },
                "design_analysis": current_result["analysis"],
                "manual_feedback": feedback,
            }
        )
        revised_result = deepcopy(current_result)
        revised_result["detailDesign"] = loop_result["detail_design"]
        revised_result["review"] = loop_result["review"]
        revised_result["manualReview"] = self._manual_review_state(
            current_result.get("manualReview"),
            loop_result["review"],
            feedback,
        )
        revised_result["artifacts"] = None
        revised_result["pipeline"] = {
            "stages": current_result["pipeline"]["stages"]
            + [
                {"name": "Designer Review Update", "summary": feedback},
                self._stage_output(STAGE_NAMES[3], loop_result["detail_design"]),
                self._stage_output(STAGE_NAMES[4], loop_result["review"]),
            ]
        }
        revised_result["executionTrace"] = {
            "steps": current_result.get("executionTrace", {}).get("steps", [])
            + loop_result.get("traceSteps", [])
        }
        update_status("needs_manual_review")
        return revised_result
