import unittest

from langchain_core.runnables import RunnableLambda

from app.application.use_cases.generate_detail_design import GenerationService


class GenerationReviewLoopTest(unittest.TestCase):
    def test_normalize_review_maps_gemini_schema_to_public_contract(self):
        service = GenerationService()
        issues = [
            {
                "severity": "error",
                "section": "API",
                "description": "Add the login response contract.",
            }
        ]

        review = service._normalize_review(
            {
                "is_passed": False,
                "score": 15,
                "issues": issues,
                "suggestions": ["Document POST /auth/login."],
            }
        )

        self.assertEqual(review["status"], "NG")
        self.assertEqual(len(review["findings"]), 1)
        self.assertIn("Add the login response contract.", review["findings"][0])
        self.assertEqual(review["nextActions"], ["Document POST /auth/login."])
        self.assertEqual(review["score"], 15)

    def test_normalize_review_maps_passed_gemini_review_to_pass(self):
        service = GenerationService()

        review = service._normalize_review(
            {
                "is_passed": True,
                "score": 95,
                "issues": [],
                "suggestions": [],
            }
        )

        self.assertEqual(review["status"], "PASS")
        self.assertEqual(review["findings"], [])

    def test_review_loop_handles_structured_findings_without_join_error(self):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        call_count = {"review": 0}
        service.detail_design_chain = RunnableLambda(
            lambda payload: service._fallback_detail_design(payload)
        )

        def review_step(payload):
            call_count["review"] += 1
            if call_count["review"] == 1:
                return {
                    "status": "NG",
                    "findings": [{"message": "Add audit logging"}],
                    "strengths": [],
                    "nextActions": [],
                }
            return {
                "status": "PASS",
                "findings": [],
                "strengths": [],
                "nextActions": [],
            }

        service.detail_design_review_chain = RunnableLambda(review_step)

        result = service._run_review_loop(
            {
                "common_input": {
                    "templates": {"screen": {"sections": ["01_UI_Design"]}},
                    "guidelines": ["Prefer explicit contracts."],
                    "checklists": {"detail_design": ["detailDesign.api"]},
                },
                "sample_designs": {"references": [], "referenceCount": 0},
                "design_analysis": {
                    "entities": ["User"],
                    "apiCandidates": ["/api/users"],
                },
                "ui_design": "",
                "update_status": lambda _: None,
            }
        )

        self.assertEqual(result["review"]["status"], "PASS")
        self.assertIn(
            '"message": "Add audit logging"',
            result["detail_design"]["api"]["02_Business_Logic"],
        )
    def test_review_loop_retries_with_gemini_issues_as_feedback(self):
        service = GenerationService()
        generated_feedback = []
        reviews = iter(
            [
                {
                    "is_passed": False,
                    "issues": [{"description": "Add login error handling."}],
                    "suggestions": [],
                },
                {
                    "is_passed": True,
                    "issues": [],
                    "suggestions": [],
                },
            ]
        )

        def generate_step(payload):
            generated_feedback.append(payload["review_feedback"])
            return service._fallback_detail_design(payload)

        service.detail_design_chain = RunnableLambda(generate_step)
        service.detail_design_ui_chain = RunnableLambda(generate_step)
        service.detail_design_logic_chain = RunnableLambda(generate_step)
        service.detail_design_review_chain = RunnableLambda(lambda _: next(reviews))

        result = service._run_review_loop(
            {
                "common_input": {
                    "templates": {"screen": {"sections": ["01_UI_Design"]}},
                    "guidelines": ["Prefer explicit contracts."],
                    "checklists": {"detail_design": ["detailDesign.api"]},
                },
                "sample_designs": {"references": [], "referenceCount": 0},
                "design_analysis": {
                    "entities": ["User"],
                    "apiCandidates": ["POST /auth/login"],
                },
                "ui_design": "",
                "update_status": lambda *_: None,
            }
        )

        self.assertEqual(result["review"]["status"], "PASS")
        self.assertEqual(generated_feedback[0], "")
        self.assertIn("Add login error handling.", generated_feedback[-1])

    def test_review_loop_stops_when_ng_review_has_no_feedback(self):
        service = GenerationService()
        call_count = {"generation": 0}

        def generate_step(payload):
            call_count["generation"] += 1
            return service._fallback_detail_design(payload)

        service.detail_design_chain = RunnableLambda(generate_step)
        service.detail_design_ui_chain = RunnableLambda(generate_step)
        service.detail_design_logic_chain = RunnableLambda(generate_step)
        service.detail_design_review_chain = RunnableLambda(
            lambda _: {
                "status": "NG",
                "findings": [],
                "strengths": [],
                "nextActions": [],
            }
        )

        result = service._run_review_loop(
            {
                "common_input": {
                    "templates": {"screen": {"sections": ["01_UI_Design"]}},
                    "guidelines": ["Prefer explicit contracts."],
                    "checklists": {"detail_design": ["detailDesign.api"]},
                },
                "sample_designs": {"references": [], "referenceCount": 0},
                "design_analysis": {
                    "entities": ["User"],
                    "apiCandidates": ["POST /auth/login"],
                },
                "ui_design": "",
                "update_status": lambda *_: None,
            }
        )

        self.assertEqual(result["review"]["status"], "NG")
        self.assertGreaterEqual(call_count["generation"], 1)


if __name__ == "__main__":
    unittest.main()
