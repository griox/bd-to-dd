from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class DesignerReviewAction(BaseModel):
    action: Literal["request_update", "approve"]
    feedback: Optional[str] = None


class AnalysisReviewAction(BaseModel):
    action: Literal["request_update", "approve"]
    feedback: Optional[str] = None


class ArtifactInfo(BaseModel):
    jsonPath: str
    markdownPath: str


class ReviewResult(BaseModel):
    status: Literal["PASS", "NG"]
    iteration: int
    findings: List[str]


class GenerationPayload(BaseModel):
    inputs: Dict[str, Any]
    resourcesUsed: Dict[str, Any]
    analysis: Dict[str, Any]
    detailDesign: Dict[str, Any]
    review: ReviewResult
    artifacts: Optional[ArtifactInfo] = None


class ProjectResponse(BaseModel):
    projectId: str
    name: str
    createdAt: datetime


class GenerationStatusResponse(BaseModel):
    status: str
    result: Optional[Any] = None
