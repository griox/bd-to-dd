import json
import unittest
from unittest.mock import MagicMock

from fastapi import BackgroundTasks
from fastapi import HTTPException

from app.presentation.api.v1 import router as api_router
from app.presentation.schemas.api import AnalysisReviewAction, DesignerReviewAction


class _FakeJob:
    def __init__(self, result, status="needs_analysis_review"):
        self.id = "job-1"
        self.project_id = "project-1"
        self.status = status
        self.result = json.dumps(result)


class _FakeQuery:
    def __init__(self, job):
        self.job = job

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.job


class _FakeDB:
    def __init__(self, job):
        self.job = job
        self.commit_count = 0

    def query(self, model):
        return _FakeQuery(self.job)

    def commit(self):
        self.commit_count += 1

    def close(self):
        return None


class _FakeGenerationJobModel:
    id = "id"
    project_id = "project_id"


class GenerationRouterTest(unittest.TestCase):
    def setUp(self):
        self.original_session_local = api_router._session_local
        self.original_generation_job_model = api_router._generation_job_model
        self.original_load_document = api_router._load_document
        self.original_designer_review_service = api_router.designer_review_service
        self.original_generation_service = api_router.generation_service

    def tearDown(self):
        api_router._session_local = self.original_session_local
        api_router._generation_job_model = self.original_generation_job_model
        api_router._load_document = self.original_load_document
        api_router.designer_review_service = self.original_designer_review_service
        api_router.generation_service = self.original_generation_service

    def test_analysis_review_approve_resumes_detail_design_generation(self):
        current_result = {
            "analysis": {"summary": "ready"},
            "analysisReview": {"status": "pending"},
            "basicDesignAnalytics": {"summary": "analytics"},
            "sampleDesigns": [],
            "manualReview": {"status": "pending"},
            "pipeline": {"stages": []},
        }
        fake_job = _FakeJob(current_result)
        fake_db = _FakeDB(fake_job)
        fake_service = MagicMock()

        api_router._session_local = lambda: (lambda: fake_db)
        api_router._generation_job_model = lambda: _FakeGenerationJobModel
        api_router._load_document = lambda project_id, kind: "BD content"
        api_router.designer_review_service = fake_service

        response = api_router.submit_analysis_review(
            "project-1",
            "job-1",
            AnalysisReviewAction(action="approve"),
            BackgroundTasks(),
        )

        self.assertEqual(response["data"]["status"], "generating_dd")
        self.assertEqual(response["data"]["result"]["analysisReview"]["status"], "approved")
        self.assertIsNone(response["data"]["result"].get("detailDesign"))
        self.assertEqual(
            response["data"]["result"]["generationProgress"]["currentStep"],
            "queued",
        )
        fake_service.approve_analysis.assert_not_called()

    def test_analysis_review_request_update_requires_feedback_and_keeps_gate(self):
        current_result = {
            "analysis": {"summary": "ready"},
            "analysisReview": {"status": "pending"},
            "basicDesignAnalytics": {"summary": "analytics"},
            "sampleDesigns": [],
            "manualReview": {"status": "pending"},
            "pipeline": {"stages": []},
        }
        updated_result = {
            **current_result,
            "analysis": {"summary": "updated"},
            "analysisReview": {
                "status": "pending",
                "feedbackHistory": ["Clarify API scope"],
                "lastFeedback": "Clarify API scope",
            },
        }
        fake_job = _FakeJob(current_result)
        fake_db = _FakeDB(fake_job)
        fake_service = MagicMock()
        fake_service.request_analysis_update.return_value = updated_result

        api_router._session_local = lambda: (lambda: fake_db)
        api_router._generation_job_model = lambda: _FakeGenerationJobModel
        api_router._load_document = lambda project_id, kind: "BD content"
        api_router.designer_review_service = fake_service

        response = api_router.submit_analysis_review(
            "project-1",
            "job-1",
            AnalysisReviewAction(action="request_update", feedback="Clarify API scope"),
            BackgroundTasks(),
        )

        self.assertEqual(response["data"]["result"]["analysis"]["summary"], "updated")
        self.assertEqual(response["data"]["result"]["analysisReview"]["status"], "pending")
        fake_service.request_analysis_update.assert_called_once()

    def test_designer_review_is_blocked_until_detail_design_exists(self):
        fake_job = _FakeJob(
            {
                "analysis": {"summary": "ready"},
                "analysisReview": {"status": "pending"},
                "detailDesign": None,
            }
        )
        fake_db = _FakeDB(fake_job)

        api_router._session_local = lambda: (lambda: fake_db)
        api_router._generation_job_model = lambda: _FakeGenerationJobModel

        with self.assertRaises(HTTPException) as ctx:
            api_router.submit_designer_review(
                "project-1",
                "job-1",
                DesignerReviewAction(action="approve"),
            )

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("Approve the analysis first", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
