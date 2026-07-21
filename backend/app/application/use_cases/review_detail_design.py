import json
from typing import Any, Dict

from app.application.use_cases.generate_detail_design import GenerationService
from app.infrastructure.persistence.postgres.export_repository import export_artifacts


class DesignerReviewService:
    def request_analysis_update(
        self,
        generation_service: GenerationService,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: str,
        current_result: Dict[str, Any],
        feedback: str,
        update_status,
    ) -> Dict[str, Any]:
        return generation_service.revise_analysis(
            project_id=project_id,
            job_id=job_id,
            basic_design=basic_design,
            ui_design=ui_design,
            current_result=current_result,
            feedback=feedback,
            update_status=update_status,
        )

    def approve_analysis(
        self,
        generation_service: GenerationService,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: str,
        current_result: Dict[str, Any],
        update_status,
    ) -> Dict[str, Any]:
        return generation_service.run_detail_design_phase(
            project_id=project_id,
            job_id=job_id,
            basic_design=basic_design,
            ui_design=ui_design,
            current_result=current_result,
            update_status=update_status,
        )

    def request_update(
        self,
        generation_service: GenerationService,
        project_id: str,
        job_id: str,
        basic_design: str,
        ui_design: str,
        current_result: Dict[str, Any],
        feedback: str,
        update_status,
    ) -> Dict[str, Any]:
        return generation_service.revise(
            project_id=project_id,
            job_id=job_id,
            basic_design=basic_design,
            ui_design=ui_design,
            current_result=current_result,
            feedback=feedback,
            update_status=update_status,
        )

    def approve(
        self,
        project_id: str,
        job_id: str,
        current_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = json.loads(json.dumps(current_result))
        manual_review = dict(result.get("manualReview", {}))
        manual_review["status"] = "approved"
        result["manualReview"] = manual_review
        result["artifacts"] = export_artifacts(project_id, job_id, result)
        return result
