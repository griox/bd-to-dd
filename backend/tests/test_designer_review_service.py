import unittest
from copy import deepcopy
from unittest.mock import patch

from app.application.use_cases.generate_detail_design import GenerationService
from app.application.use_cases.review_detail_design import DesignerReviewService


class DesignerReviewServiceTest(unittest.TestCase):
    def setUp(self):
        self.generation_service = GenerationService()
        self.generation_service.llm_service.enabled = False
        self.generation_service.llm_service.client = None
        self.review_service = DesignerReviewService()
        self.basic_design = (
            "User Registration lets User create Account and submit Profile data."
        )
        self.ui_design = "Registration screen includes form and summary panel."

    def test_generation_waits_for_designer_approval_before_export(self):
        updates = []
        result = self.generation_service.run(
            "project-1",
            "job-1",
            self.basic_design,
            self.ui_design,
            updates.append,
        )

        self.assertEqual(result["analysisReview"]["status"], "pending")
        self.assertIsNone(result["detailDesign"])
        self.assertEqual(result["manualReview"]["status"], "pending")
        self.assertEqual(result.get("artifacts"), None)
        self.assertIn("needs_analysis_review", updates)

    def test_request_analysis_update_keeps_job_at_analysis_review_gate(self):
        initial_result = self.generation_service.run(
            "project-1",
            "job-1",
            self.basic_design,
            self.ui_design,
            lambda _: None,
        )

        updates = []
        revised_result = self.review_service.request_analysis_update(
            generation_service=self.generation_service,
            project_id="project-1",
            job_id="job-1",
            basic_design=self.basic_design,
            ui_design=self.ui_design,
            current_result=initial_result,
            feedback="Clarify affected screens and remove unsupported API assumptions.",
            update_status=updates.append,
        )

        self.assertEqual(revised_result["analysisReview"]["status"], "pending")
        self.assertEqual(
            len(revised_result["analysisReview"]["feedbackHistory"]),
            1,
        )
        self.assertIn(
            "Clarify affected screens",
            revised_result["analysisReview"]["lastFeedback"],
        )
        self.assertIsNone(revised_result["detailDesign"])
        self.assertIn("generating_analysis", updates)
        self.assertIn("needs_analysis_review", updates)

    def test_request_analysis_update_refreshes_common_input_snapshot(self):
        initial_common_input = self.generation_service.common_input_service.get_common_input()
        revised_common_input = deepcopy(initial_common_input)
        revised_common_input["version"] = "revised-version"
        common_input_calls = iter([initial_common_input, revised_common_input])
        self.generation_service.common_input_service.get_common_input = (
            lambda: next(common_input_calls)
        )

        initial_result = self.generation_service.run(
            "project-1",
            "job-1",
            self.basic_design,
            self.ui_design,
            lambda _: None,
        )
        revised_result = self.review_service.request_analysis_update(
            generation_service=self.generation_service,
            project_id="project-1",
            job_id="job-1",
            basic_design=self.basic_design,
            ui_design=self.ui_design,
            current_result=initial_result,
            feedback="Refresh the analysis.",
            update_status=lambda _: None,
        )

        self.assertEqual(revised_result["commonInputSnapshot"], revised_common_input)
        self.assertEqual(
            revised_result["resourcesUsed"]["commonInputVersion"],
            "revised-version",
        )
        with self.assertRaises(StopIteration):
            next(common_input_calls)

    def test_analysis_approval_generates_detail_design_and_opens_dd_review(self):
        initial_result = self.generation_service.run(
            "project-1",
            "job-1",
            self.basic_design,
            self.ui_design,
            lambda _: None,
        )

        updates = []
        approved_analysis_result = self.review_service.approve_analysis(
            generation_service=self.generation_service,
            project_id="project-1",
            job_id="job-1",
            basic_design=self.basic_design,
            ui_design=self.ui_design,
            current_result=initial_result,
            update_status=updates.append,
        )

        self.assertEqual(approved_analysis_result["analysisReview"]["status"], "approved")
        self.assertEqual(approved_analysis_result["manualReview"]["status"], "pending")
        self.assertEqual(approved_analysis_result["review"]["status"], "PASS")
        self.assertIn("needs_manual_review", updates)

    def test_request_update_applies_feedback_and_keeps_manual_review_open(self):
        analysis_result = self.generation_service.run(
            "project-1",
            "job-1",
            self.basic_design,
            self.ui_design,
            lambda _: None,
        )
        initial_result = self.review_service.approve_analysis(
            generation_service=self.generation_service,
            project_id="project-1",
            job_id="job-1",
            basic_design=self.basic_design,
            ui_design=self.ui_design,
            current_result=analysis_result,
            update_status=lambda _: None,
        )

        updates = []
        revised_result = self.review_service.request_update(
            generation_service=self.generation_service,
            project_id="project-1",
            job_id="job-1",
            basic_design=self.basic_design,
            ui_design=self.ui_design,
            current_result=initial_result,
            feedback="Add audit log note for account activation.",
            update_status=updates.append,
        )

        self.assertEqual(revised_result["manualReview"]["status"], "pending")
        self.assertEqual(len(revised_result["manualReview"]["feedbackHistory"]), 1)
        self.assertIn("Add audit log note", revised_result["manualReview"]["lastFeedback"])
        self.assertIn("manual_updating", updates)
        self.assertIn(
            "Add audit log note",
            revised_result["detailDesign"]["api"]["02_Business_Logic"],
        )

    def test_approve_exports_artifacts_and_marks_review_complete(self):
        analysis_result = self.generation_service.run(
            "project-1",
            "job-1",
            self.basic_design,
            self.ui_design,
            lambda _: None,
        )
        initial_result = self.review_service.approve_analysis(
            generation_service=self.generation_service,
            project_id="project-1",
            job_id="job-1",
            basic_design=self.basic_design,
            ui_design=self.ui_design,
            current_result=analysis_result,
            update_status=lambda _: None,
        )

        with patch("app.application.use_cases.review_detail_design.export_artifacts") as export_mock:
            export_mock.return_value = {
                "jsonPath": "/tmp/project-1/job-1/detail-design.json",
                "markdownPath": "/tmp/project-1/job-1/detail-design.md",
            }
            approved_result = self.review_service.approve(
                project_id="project-1",
                job_id="job-1",
                current_result=initial_result,
            )

        self.assertEqual(approved_result["manualReview"]["status"], "approved")
        self.assertEqual(
            approved_result["artifacts"]["jsonPath"],
            "/tmp/project-1/job-1/detail-design.json",
        )


if __name__ == "__main__":
    unittest.main()
