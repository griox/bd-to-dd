import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.presentation.deps import (
    common_input_service,
    designer_review_service,
    generation_service,
    knowledge_base,
    vision_extractor,
)
from app.infrastructure.llm.vision_client import VisionExtractionError
from app.presentation.schemas.api import (
    AnalysisReviewAction,
    DesignerReviewAction,
    ProjectCreate,
)


router = APIRouter(prefix="/api/v1")
IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".csv"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _session_local():
    from app.infrastructure.persistence.postgres.database import SessionLocal

    return SessionLocal


def _load_document(project_id: str, kind: str):
    from app.infrastructure.persistence.postgres.document_store import load_document

    return load_document(project_id, kind)


def _save_document(project_id: str, kind: str, content: str):
    from app.infrastructure.persistence.postgres.document_store import save_document

    return save_document(project_id, kind, content)


def _generation_job_model():
    from app.infrastructure.persistence.postgres.models import GenerationJobModel

    return GenerationJobModel


def _project_model():
    from app.infrastructure.persistence.postgres.models import ProjectModel

    return ProjectModel


def _update_job_status(job_id: str, status: str) -> None:
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    try:
        job = db.query(GenerationJobModel).filter(GenerationJobModel.id == job_id).first()
        if job:
            job.status = status
            db.commit()
    finally:
        db.close()


def _progress_payload(status: str, step: str, summary: str) -> Dict[str, Any]:
    return {
        "status": status,
        "currentStep": step,
        "summary": summary,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def _decode_job_result(result: Optional[str]) -> Dict[str, Any]:
    if result and result.startswith("{"):
        return json.loads(result)
    return {}


def _set_job_progress(job, db, status: str, step: str, summary: str) -> None:
    payload = _decode_job_result(job.result)
    payload["generationProgress"] = _progress_payload(status, step, summary)
    job.status = status
    job.result = json.dumps(payload, ensure_ascii=False)
    db.commit()


def _run_generation_job(job_id: str, project_id: str) -> None:
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    job = None
    try:
        job = db.query(GenerationJobModel).filter(GenerationJobModel.id == job_id).first()
        if not job:
            return
        basic_design = _load_document(project_id, "basic-design")
        ui_design = _load_document(project_id, "ui-design")
        if not basic_design:
            job.status = "failed"
            job.result = "Basic design not uploaded"
            db.commit()
            return

        def update_status(status: str) -> None:
            job.status = status
            db.commit()

        update_status("analyzing")
        result = generation_service.run(project_id, job_id, basic_design, ui_design, update_status)
        job.result = json.dumps(result, ensure_ascii=False)
        db.commit()
    except Exception as exc:
        if job:
            job.status = "failed"
            job.result = str(exc)
            db.commit()
    finally:
        db.close()


def _run_detail_design_job(job_id: str, project_id: str) -> None:
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    job = None
    try:
        job = db.query(GenerationJobModel).filter(GenerationJobModel.id == job_id).first()
        if not job:
            return

        current_result = _decode_job_result(job.result)
        basic_design = _load_document(project_id, "basic-design")
        ui_design = _load_document(project_id, "ui-design")
        if not basic_design:
            _set_job_progress(
                job,
                db,
                "failed",
                "load_documents",
                "Basic design not uploaded.",
            )
            return

        def update_status(status: str, step: str = "", summary: str = "") -> None:
            _set_job_progress(
                job,
                db,
                status,
                step or status,
                summary or f"Detail design pipeline status: {status}.",
            )

        update_status("generating_dd", "start", "Starting detail design generation after analysis approval.")
        result = designer_review_service.approve_analysis(
            generation_service=generation_service,
            project_id=project_id,
            job_id=job_id,
            basic_design=basic_design,
            ui_design=ui_design or "",
            current_result=current_result,
            update_status=update_status,
        )
        result["generationProgress"] = _progress_payload(
            "needs_manual_review",
            "complete",
            "Detail design generated and auto-review completed.",
        )
        job.status = "needs_manual_review"
        job.result = json.dumps(result, ensure_ascii=False)
        db.commit()
    except Exception as exc:
        if job:
            _set_job_progress(
                job,
                db,
                "failed",
                "unexpected_error",
                f"Detail design generation failed: {exc}",
            )
    finally:
        db.close()


@router.post("/projects", status_code=201)
def create_project(req: ProjectCreate):
    SessionLocal = _session_local()
    ProjectModel = _project_model()
    db = SessionLocal()
    try:
        project = ProjectModel(id=str(uuid.uuid4()), name=req.name)
        db.add(project)
        db.commit()
        db.refresh(project)
        return {
            "data": {
                "projectId": project.id,
                "name": project.name,
                "createdAt": project.created_at,
            }
        }
    finally:
        db.close()


def _csv_to_markdown(raw: str) -> str:
    """Convert a raw CSV string to a Markdown table.

    Falls back to the original text if the CSV is malformed or empty.
    Strips UTF-8 BOM that Excel/Japanese tools often prepend.
    """
    raw = raw.lstrip("\ufeff")  # strip BOM (Excel UTF-8 with BOM)
    try:
        reader = csv.reader(io.StringIO(raw))
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    except csv.Error:
        return raw

    if not rows:
        return raw

    header = rows[0]
    col_count = len(header)
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * col_count) + " |",
    ]
    for row in rows[1:]:
        # pad or trim row to match header width
        padded = row + [""] * (col_count - len(row))
        lines.append("| " + " | ".join(padded[:col_count]) + " |")

    return "\n".join(lines)


def _read_uploaded_document(file: UploadFile, context: str):
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Uploaded file exceeds 10 MB.")

    if suffix in IMAGE_MIME_TYPES:
        expected_mime = IMAGE_MIME_TYPES[suffix]
        if content_type != expected_mime:
            raise HTTPException(
                status_code=400,
                detail=f"Image extension and MIME type do not match: {filename}",
            )
        try:
            content = vision_extractor.extract_document_text(
                data,
                content_type,
                context,
                filename,
            )
        except VisionExtractionError as exc:
            status_code = 503 if "not configured" in str(exc).lower() else 502
            raise HTTPException(status_code=status_code, detail=str(exc)) from exc
        return content, {
            "sourceType": "image",
            "extractionModel": vision_extractor._model,
        }

    if suffix not in TEXT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Supported files are .md, .txt, .json, .csv, .png, .jpg, .jpeg, and .webp.",
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Text file must be UTF-8.") from exc

    if suffix == ".csv":
        text = _csv_to_markdown(text)
        return text, {"sourceType": "text", "extractionModel": None, "converted": "csv_to_markdown"}

    return text, {"sourceType": "text", "extractionModel": None}


def _upload_document(project_id: str, kind: str, context: str, file: UploadFile):
    content, metadata = _read_uploaded_document(file, context)
    _save_document(project_id, kind, content)
    return {
        "data": {
            "status": "uploaded",
            "filename": file.filename,
            "documentType": kind,
            **metadata,
        }
    }


@router.post("/projects/{project_id}/documents/basic-design", status_code=201)
def upload_basic_design(project_id: str, file: UploadFile = File(...)):
    return _upload_document(project_id, "basic-design", "basic_design", file)


@router.post("/projects/{project_id}/documents/ui-design", status_code=201)
def upload_ui_design(project_id: str, file: UploadFile = File(...)):
    return _upload_document(project_id, "ui-design", "ui_design", file)


@router.post("/projects/{project_id}/documents/design-input", status_code=201)
def upload_design_input_bundle(
    project_id: str,
    design: UploadFile = File(...),
    images: List[UploadFile] = File(default=[]),
    composable: Optional[UploadFile] = File(None),
):
    if Path(design.filename or "").suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="Design input must be a Markdown (.md) file.")
    if composable is not None and Path(composable.filename or "").suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="Composable list must be a CSV (.csv) file.")

    design_content, _ = _read_uploaded_document(design, "basic_design")
    ui_sections = []
    image_names = []
    for image in images:
        image_content, metadata = _read_uploaded_document(image, "ui_design")
        if metadata["sourceType"] != "image":
            raise HTTPException(status_code=400, detail=f"UI file is not an image: {image.filename}")
        image_names.append(image.filename)
        ui_sections.append(f"## UI Image: {image.filename}\n\n{image_content}")

    if composable is not None:
        csv_content, _ = _read_uploaded_document(composable, "ui_design")
        ui_sections.append(f"## Composable List: {composable.filename}\n\n{csv_content}")

    _save_document(project_id, "basic-design", design_content)
    if ui_sections:
        _save_document(project_id, "ui-design", "\n\n".join(ui_sections))

    return {
        "data": {
            "status": "uploaded",
            "documentType": "design-input",
            "designFilename": design.filename,
            "imageCount": len(image_names),
            "imageFilenames": image_names,
            "hasComposableList": composable is not None,
            "composableFilename": composable.filename if composable is not None else None,
        }
    }


@router.post("/projects/{project_id}/generate", status_code=202)
def generate_detail_design(project_id: str, background_tasks: BackgroundTasks):
    if not _load_document(project_id, "basic-design"):
        raise HTTPException(status_code=400, detail="Basic design not uploaded")

    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    try:
        job_id = str(uuid.uuid4())
        job = GenerationJobModel(id=job_id, project_id=project_id, status="pending")
        db.add(job)
        db.commit()
        background_tasks.add_task(_run_generation_job, job_id, project_id)
        return {"data": {"jobId": job_id, "status": "pending"}}
    finally:
        db.close()


@router.get("/projects/{project_id}/generations/{job_id}")
def get_generation(project_id: str, job_id: str):
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    try:
        job = (
            db.query(GenerationJobModel)
            .filter(GenerationJobModel.id == job_id, GenerationJobModel.project_id == project_id)
            .first()
        )
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        result = job.result
        if result and result.startswith("{"):
            result = json.loads(result)
        return {"data": {"status": job.status, "result": result}}
    finally:
        db.close()


@router.post("/projects/{project_id}/generations/{job_id}/designer-review")
def submit_designer_review(
    project_id: str, job_id: str, action: DesignerReviewAction
):
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    try:
        job = (
            db.query(GenerationJobModel)
            .filter(GenerationJobModel.id == job_id, GenerationJobModel.project_id == project_id)
            .first()
        )
        if not job or not job.result:
            raise HTTPException(status_code=404, detail="Job not found")

        current_result = json.loads(job.result) if job.result.startswith("{") else {}
        if not current_result.get("detailDesign"):
            raise HTTPException(
                status_code=409,
                detail="Detail design is not ready. Approve the analysis first.",
            )

        def update_status(status: str) -> None:
            job.status = status
            db.commit()

        if action.action == "approve":
            current_result = designer_review_service.approve(
                project_id=project_id,
                job_id=job_id,
                current_result=current_result,
            )
            current_result["knowledgeBaseFeedback"] = (
                knowledge_base.ingest_generated_reviewed_dd(
                    project_id=project_id,
                    job_id=job_id,
                    result=current_result,
                )
            )
            job.status = "completed"
        else:
            feedback = (action.feedback or "").strip()
            if not feedback:
                raise HTTPException(status_code=400, detail="Feedback is required")
            basic_design = _load_document(project_id, "basic-design")
            ui_design = _load_document(project_id, "ui-design")
            if not basic_design:
                raise HTTPException(status_code=400, detail="Basic design not uploaded")
            current_result = designer_review_service.request_update(
                generation_service=generation_service,
                project_id=project_id,
                job_id=job_id,
                basic_design=basic_design,
                ui_design=ui_design or "",
                current_result=current_result,
                feedback=feedback,
                update_status=update_status,
            )

        job.result = json.dumps(current_result, ensure_ascii=False)
        db.commit()
        return {"data": {"status": job.status, "result": current_result}}
    finally:
        db.close()


@router.post("/projects/{project_id}/generations/{job_id}/analysis-review")
def submit_analysis_review(
    project_id: str,
    job_id: str,
    action: AnalysisReviewAction,
    background_tasks: BackgroundTasks,
):
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    try:
        job = (
            db.query(GenerationJobModel)
            .filter(GenerationJobModel.id == job_id, GenerationJobModel.project_id == project_id)
            .first()
        )
        if not job or not job.result:
            raise HTTPException(status_code=404, detail="Job not found")

        current_result = json.loads(job.result) if job.result.startswith("{") else {}
        if not current_result.get("analysis"):
            raise HTTPException(status_code=409, detail="Design analysis is not ready")

        def update_status(status: str) -> None:
            job.status = status
            db.commit()

        basic_design = _load_document(project_id, "basic-design")
        ui_design = _load_document(project_id, "ui-design")
        if not basic_design:
            raise HTTPException(status_code=400, detail="Basic design not uploaded")

        if action.action == "approve":
            analysis_review = dict(current_result.get("analysisReview", {}))
            analysis_review["status"] = "approved"
            current_result["analysisReview"] = analysis_review
            current_result["generationProgress"] = _progress_payload(
                "generating_dd",
                "queued",
                "Analysis approved. Detail design generation is queued.",
            )
            job.status = "generating_dd"
            job.result = json.dumps(current_result, ensure_ascii=False)
            db.commit()
            background_tasks.add_task(_run_detail_design_job, job_id, project_id)
            return {"data": {"status": job.status, "result": current_result}}
        else:
            feedback = (action.feedback or "").strip()
            if not feedback:
                raise HTTPException(status_code=400, detail="Feedback is required")
            current_result = designer_review_service.request_analysis_update(
                generation_service=generation_service,
                project_id=project_id,
                job_id=job_id,
                basic_design=basic_design,
                ui_design=ui_design or "",
                current_result=current_result,
                feedback=feedback,
                update_status=update_status,
            )

        job.result = json.dumps(current_result, ensure_ascii=False)
        db.commit()
        return {"data": {"status": job.status, "result": current_result}}
    finally:
        db.close()


@router.get("/projects/{project_id}/generations/{job_id}/artifacts/{artifact_name}")
def download_artifact(project_id: str, job_id: str, artifact_name: str):
    SessionLocal = _session_local()
    GenerationJobModel = _generation_job_model()
    db = SessionLocal()
    try:
        job = (
            db.query(GenerationJobModel)
            .filter(GenerationJobModel.id == job_id, GenerationJobModel.project_id == project_id)
            .first()
        )
        if not job or not job.result:
            raise HTTPException(status_code=404, detail="Artifact not found")
        result = json.loads(job.result) if job.result.startswith("{") else {}
        artifacts = result.get("artifacts", {})
        file_path = artifacts.get(artifact_name)
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(path=file_path, filename=Path(file_path).name)
    finally:
        db.close()


@router.post("/admin/knowledge-base/samples", status_code=201)
def upload_sample(
    file: Optional[UploadFile] = File(None),
    content: Optional[str] = Form(None),
):
    if (file is None) == (content is None):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one of file or content.",
        )
    if file is not None:
        sample_content, _ = _read_uploaded_document(file, "reviewed_dd")
    else:
        sample_content = (content or "").strip()
        if not sample_content:
            raise HTTPException(status_code=400, detail="Sample content is empty.")
    return {"data": knowledge_base.add_sample(sample_content)}


@router.get("/admin/knowledge-base/status")
def get_knowledge_base_status():
    return {"data": knowledge_base.get_status()}


@router.post("/admin/knowledge-base/reindex", status_code=202)
def reindex_knowledge_base(background_tasks: BackgroundTasks):
    progress = knowledge_base.queue_reindex()
    if progress.get("status") == "queued":
        background_tasks.add_task(knowledge_base.reindex)
    return {"data": progress}


@router.get("/admin/common-input/status")
def get_common_input_status():
    return {"data": common_input_service.get_status()}
