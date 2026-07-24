import unittest
from copy import deepcopy
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from app.application.use_cases.generate_detail_design import GenerationService
from app.domain.entities.retrieval import AssembledContext, RetrievalCandidate


class GenerationPipelineTest(unittest.TestCase):
    def test_fallback_pipeline_stops_after_analysis_review_gate(self):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        updates = []
        result = service.run(
            "project-1",
            "job-1",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            updates.append,
        )

        self.assertIn("analysis", result)
        self.assertIsNone(result["detailDesign"])
        self.assertIsNone(result["review"])
        self.assertIn("generating_analysis", updates)
        self.assertIn("needs_analysis_review", updates)
        self.assertIn("pipeline", result)
        self.assertEqual(result["manualReview"]["status"], "pending")
        self.assertEqual(result["analysisReview"]["status"], "pending")
        self.assertIsNone(result.get("artifacts"))
        self.assertEqual(
            [stage["name"] for stage in result["pipeline"]["stages"]],
            [
                "Basic Design Analytics",
                "Get Sample Design",
                "Design Analysis Generation",
            ],
        )
        self.assertEqual(
            result["resourcesUsed"]["langchainStages"],
            [
                "Basic Design Analytics",
                "Get Sample Design",
                "Design Analysis Generation",
                "Detail Design Generation",
                "Detail Design Review",
            ],
        )
        self.assertIn("skills", result["resourcesUsed"])
        self.assertIn("write_bd", result["resourcesUsed"]["skills"])
        self.assertIn("write_dd", result["resourcesUsed"]["skills"])
        self.assertIn("write_master_design", result["resourcesUsed"]["skills"])
        self.assertEqual(
            result["resourcesUsed"]["skills"]["write_dd"]["stage"],
            "detail_design",
        )
        self.assertIn("commonInputVersion", result["resourcesUsed"])
        self.assertTrue(
            result["resourcesUsed"]["commonInputVersion"].startswith("input-common-")
        )
        self.assertIn("commonComponents", result["resourcesUsed"])
        self.assertIn("knowledgeBase", result["resourcesUsed"])
        self.assertIn("embedding", result["resourcesUsed"]["knowledgeBase"])
        self.assertIn("executionTrace", result)
        self.assertIn("steps", result["executionTrace"])

        step_keys = [step["key"] for step in result["executionTrace"]["steps"]]
        self.assertEqual(
            step_keys,
            [
                "basic_design_analytics",
                "build_retrieval_query",
                "dense_search",
                "sparse_search",
                "rrf_fusion",
                "context_assembly",
                "design_analysis_generation",
            ],
        )
        retrieval_step = next(
            step for step in result["executionTrace"]["steps"] if step["key"] == "build_retrieval_query"
        )
        self.assertIn("preview", retrieval_step)
        self.assertIn("raw", retrieval_step)
        self.assertIn("filters", retrieval_step["raw"])

    @patch("app.application.use_cases.generate_detail_design.logger")
    def test_analysis_phase_emits_step_logs(self, mock_logger):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        service.run(
            "project-analysis-log",
            "job-analysis-log",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            lambda _: None,
        )

        log_messages = [call.args[0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("[analysis_phase] start" in message for message in log_messages))
        self.assertTrue(any("phase=bootstrap" in message for message in log_messages))
        self.assertTrue(any("phase=basic_design_analytics" in message for message in log_messages))
        self.assertTrue(any("phase=retrieve_samples" in message for message in log_messages))
        self.assertTrue(any("phase=design_analysis_generation" in message for message in log_messages))
        self.assertTrue(any("[analysis_phase] finish" in message for message in log_messages))

    def test_pipeline_normalizes_structured_llm_lists(self):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None
        service._build_chains()
        service.basic_design_analytics_chain = RunnableLambda(
            lambda _: {
                "summary": "Structured analytics",
                "modules": [{"name": "screen"}],
                "screens": [{"name": "Registration"}],
                "entities": [{"name": "User"}],
                "businessFlows": [{"step": "Submit registration"}],
                "apiCandidates": [{"path": "/api/register"}],
                "externalInterfaces": [{"name": "Qdrant"}],
                "uiSignals": [{"screen": "Registration"}],
                "assumptions": [{"message": "UI is partial"}],
            }
        )
        service._build_chains = lambda: None

        updates = []
        result = service.run(
            "project-1",
            "job-2",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            updates.append,
        )

        self.assertIsNone(result["review"])
        self.assertEqual(result["basicDesignAnalytics"]["entities"], ['{\n  "name": "User"\n}'])
        self.assertEqual(
            result["analysis"]["apiCandidates"],
            ['{\n  "path": "/api/register"\n}'],
        )

    def test_analysis_approval_resumes_detail_design_generation(self):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        initial_result = service.run(
            "project-1",
            "job-3",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            lambda _: None,
        )

        updates = []
        result = service.run_detail_design_phase(
            "project-1",
            "job-3",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            initial_result,
            updates.append,
        )

        self.assertEqual(result["analysisReview"]["status"], "approved")
        self.assertEqual(result["review"]["status"], "PASS")
        self.assertIsNotNone(result["detailDesign"])
        self.assertIn("generating_dd", updates)
        self.assertIn("validating", updates)
        self.assertIn("needs_manual_review", updates)
        self.assertEqual(
            [stage["name"] for stage in result["pipeline"]["stages"]],
            [
                "Basic Design Analytics",
                "Get Sample Design",
                "Design Analysis Generation",
                "Detail Design Generation",
                "Detail Design Review",
            ],
        )
        trace_keys = [step["key"] for step in result["executionTrace"]["steps"]]
        self.assertEqual(
            trace_keys,
            [
                "basic_design_analytics",
                "build_retrieval_query",
                "dense_search",
                "sparse_search",
                "rrf_fusion",
                "context_assembly",
                "design_analysis_generation",
                "detail_design_generation",
                "detail_design_review",
            ],
        )
        review_step = next(
            step for step in result["executionTrace"]["steps"] if step["key"] == "detail_design_review"
        )
        self.assertEqual(review_step["status"], "completed")
        self.assertIn("preview", review_step)
        self.assertIn("raw", review_step)

    @patch("app.application.use_cases.generate_detail_design.logger")
    def test_review_loop_emits_generation_and_validation_logs(self, mock_logger):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        initial_result = service.run(
            "project-log",
            "job-log",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            lambda _: None,
        )

        service.run_detail_design_phase(
            "project-log",
            "job-log",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            initial_result,
            lambda _: None,
        )

        log_messages = [call.args[0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("[review_loop] start" in message for message in log_messages))
        self.assertTrue(any("phase=generate_dd" in message for message in log_messages))
        self.assertTrue(any("phase=validate" in message for message in log_messages))
        self.assertTrue(any("[review_loop] finish" in message for message in log_messages))

    def test_detail_design_uses_analysis_common_input_snapshot(self):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        analysis_common_input = service.common_input_service.get_common_input()
        expected_components = service._format_common_components(
            analysis_common_input["commonComponents"]
        )
        changed_common_input = deepcopy(analysis_common_input)
        changed_common_input["commonComponents"] = [
            {"id": "changed-component", "name": "Changed Component", "appliesTo": []}
        ]
        changed_common_input["version"] = "changed-version"
        common_input_calls = iter([analysis_common_input, changed_common_input])
        service.common_input_service.get_common_input = lambda: next(common_input_calls)

        initial_result = service.run(
            "project-1",
            "job-snapshot",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            lambda _: None,
        )
        result = service.run_detail_design_phase(
            "project-1",
            "job-snapshot",
            "User Registration lets User create Account and submit Profile data.",
            "Registration screen includes form and summary panel.",
            initial_result,
            lambda _: None,
        )

        self.assertEqual(result["commonInputSnapshot"], analysis_common_input)
        self.assertEqual(
            result["detailDesign"]["screen"]["02_Components"],
            expected_components,
        )
        self.assertNotIn(
            "Changed Component",
            result["detailDesign"]["screen"]["02_Components"],
        )
        self.assertEqual(result["resourcesUsed"]["commonInputVersion"], analysis_common_input["version"])

    def test_sample_retrieval_uses_confident_metadata_filters(self):
        service = GenerationService()
        service.llm_service.enabled = False
        service.llm_service.client = None

        assembled_context = AssembledContext(
            references=[
                RetrievalCandidate(
                    chunk_id="chunk-1",
                    content='{"detailDesign": {"screen": {"01_UI": "sample"}}}',
                    metadata={"section_path": "doc > screen", "sources": ["dense"]},
                    score=0.9,
                    source="dense",
                )
            ],
            reference_count=1,
        )
        with patch.object(
            service.kb_service,
            "retrieve_debug_bundle",
            return_value={
                "denseResults": [],
                "sparseResults": [],
                "fusedResults": [],
                "rerankedResults": [],
                "selectedCandidates": [],
                "assembledContext": assembled_context,
            },
        ) as retrieve_mock:
            result = service._retrieve_sample_designs(
                {
                    "basic_design": "Implement screen N9P90M4X4004W002 registration flow",
                    "basic_design_analytics": {
                        "summary": "Screen detail design",
                        "modules": ["screen"],
                        "screens": ["N9P90M4X4004W002 Registration"],
                        "entities": ["User"],
                        "businessFlows": ["Open screen", "Submit form"],
                    },
                }
            )

        self.assertEqual(result["referenceCount"], 1)
        retrieve_mock.assert_called_once()
        _, kwargs = retrieve_mock.call_args
        self.assertEqual(kwargs["filters"]["approval_status"], "reviewed")
        self.assertEqual(kwargs["filters"]["module_type"], "screen")
        self.assertEqual(kwargs["filters"]["component_id"], "N9P90M4X4004W002")

    def test_basic_design_analytics_receives_input_reference_without_replacing_user_input(self):
        service = GenerationService()
        captured_payloads = []
        user_basic_design = "User uploaded BD for Invoice Approval."

        service.input_reference_service.find_similar_references = lambda basic_design, ui_design: {
            "references": [
                {
                    "componentId": "N9P90M4X4004W002",
                    "name": "Sample Registration",
                    "sourceFiles": ["INPUT/input/01_UI層/N9P90M4X4004W002_Registration.md"],
                }
            ],
            "referenceCount": 1,
            "formatted": "REFERENCE INPUT EXAMPLES\nSample Registration reference only.",
        }
        service.sample_retrieval_chain = RunnableLambda(
            lambda _: {"references": [], "referenceCount": 0, "knowledgeBase": {}}
        )

        def build_chain(system_prompt, user_prompt, fallback, chain_name=None):
            if chain_name == "basic_design_analytics":
                def capture(payload):
                    captured_payloads.append(payload)
                    return {
                        "summary": "analytics",
                        "modules": ["screen"],
                        "screens": ["Invoice Approval"],
                        "entities": ["Invoice"],
                        "businessFlows": ["Approve invoice"],
                        "apiCandidates": ["/api/invoices"],
                        "externalInterfaces": [],
                        "uiSignals": [],
                        "assumptions": [],
                    }
                return RunnableLambda(capture)
            if chain_name == "design_analysis_generation":
                return RunnableLambda(
                    lambda _: {
                        "summary": "analysis",
                        "scope": "scope",
                        "entities": ["Invoice"],
                        "businessFlows": ["Approve invoice"],
                        "apiCandidates": ["/api/invoices"],
                        "uiSignals": [],
                        "risks": [],
                        "assumptions": [],
                    }
                )
            return RunnableLambda(lambda _: {})

        service.llm_service.build_json_chain = build_chain

        result = service.run(
            "project-input-reference",
            "job-input-reference",
            user_basic_design,
            "Invoice approval UI",
            lambda _: None,
        )

        self.assertEqual(captured_payloads[0]["basic_design"], user_basic_design)
        self.assertIn(
            "Sample Registration reference only.",
            captured_payloads[0]["input_reference_examples"],
        )
        self.assertEqual(result["resourcesUsed"]["inputReferences"]["referenceCount"], 1)
        self.assertEqual(
            result["resourcesUsed"]["inputReferences"]["references"][0]["componentId"],
            "N9P90M4X4004W002",
        )

    def test_detail_design_string_modules_are_normalized_to_document_sections(self):
        service = GenerationService()

        normalized = service._normalize_detail_design(
            {
                "screen": "# Screen設計\nボックスNo.入力画面",
                "api": {"01_Contract": "API contract"},
                "batch": ["Batch job definition"],
            }
        )

        self.assertEqual(
            normalized["screen"],
            {"00_Document": "# Screen設計\nボックスNo.入力画面"},
        )
        self.assertEqual(normalized["api"], {"01_Contract": "API contract"})
        self.assertEqual(normalized["batch"], {"00_Document": "Batch job definition"})

    def test_build_chains_reads_prompts_from_runtime_loader(self):
        service = GenerationService()
        runtime_prompts = {
            "basic_design_analytics": {"system": "runtime analytics system", "user": "runtime analytics user"},
            "design_analysis_generation": {"system": "runtime analysis system", "user": "runtime analysis user"},
            "detail_design_generation": {"system": "runtime dd system", "user": "runtime dd user"},
            "detail_design_review": {"system": "runtime review system", "user": "runtime review user"},
        }
        captured = []

        service.prompt_runtime_service.get_prompt_catalog = lambda: runtime_prompts
        service.llm_service.build_json_chain = (
            lambda system_prompt, user_prompt, fallback, chain_name=None: captured.append(
                (system_prompt, user_prompt, fallback.__name__)
            ) or RunnableLambda(lambda _: {})
        )

        service._build_chains()

        self.assertEqual(
            captured,
            [
                ("runtime analytics system", "runtime analytics user", "_fallback_basic_design_analytics"),
                ("runtime analysis system", "runtime analysis user", "_fallback_design_analysis"),
                ("runtime dd system", "runtime dd user", "_fallback_detail_design"),
                ("runtime dd system", "runtime dd user", "_fallback_detail_design"),
                ("runtime dd system", "runtime dd user", "_fallback_detail_design"),
                ("runtime review system", "runtime review user", "_fallback_detail_design_review"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
