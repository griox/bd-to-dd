import unittest
import tempfile
from pathlib import Path

from app.application.services.common_input_service import CommonInputService


class CommonInputServiceTest(unittest.TestCase):
    def test_common_input_recursively_extracts_and_caches_images(self):
        class FakeExtractor:
            def __init__(self):
                self.calls = 0

            def extract_common_reference(self, image_bytes, mime_type, filename):
                self.calls += 1
                return {
                    "sourceName": filename,
                    "sourceType": "image",
                    "extractionModel": "gemini-2.5-flash",
                    "summary": "Shared layout",
                    "rules": ["Use shared header"],
                }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_dir = root / "templates" / "images"
            image_dir.mkdir(parents=True)
            image_path = image_dir / "shared.png"
            image_path.write_bytes(b"png-bytes")
            extractor = FakeExtractor()
            service = CommonInputService(root, image_extractor=extractor)

            first = service.get_common_input()
            second = service.get_common_input()

            self.assertEqual(extractor.calls, 1)
            self.assertEqual(first["imageReferences"][0]["summary"], "Shared layout")
            self.assertEqual(first["imageReferences"], second["imageReferences"])
            self.assertIn(str(image_path), first["sourceFiles"])
            self.assertNotEqual(first["version"], "input-common-e3b0c44298fc")

    def test_common_input_image_failure_is_not_silently_ignored(self):
        class FailingExtractor:
            def extract_common_reference(self, image_bytes, mime_type, filename):
                raise RuntimeError("vision failed")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.mkdir(exist_ok=True)
            (root / "rules.webp").write_bytes(b"webp-bytes")
            service = CommonInputService(root, image_extractor=FailingExtractor())

            with self.assertRaisesRegex(RuntimeError, "vision failed"):
                service.get_common_input()

    def test_common_input_exposes_all_architecture_inputs(self):
        common_input = CommonInputService().get_common_input()

        self.assertIn("version", common_input)
        self.assertIn("templates", common_input)
        self.assertIn("checklists", common_input)
        self.assertIn("skills", common_input)
        self.assertIn("guidelines", common_input)
        self.assertIn("commonComponents", common_input)
        self.assertIn("sourceFiles", common_input)
        self.assertIn("sourceRoot", common_input)
        self.assertIn("INPUT/common/skills/skills.json", common_input["sourceFiles"])
        self.assertIn("create_idea_file", common_input["skills"])
        self.assertIn("write_master_design", common_input["skills"])
        self.assertIn("write_bd", common_input["skills"])
        self.assertIn("write_dd", common_input["skills"])

    def test_planning_skills_are_detailed_common_input_resources(self):
        common_input = CommonInputService().get_common_input()

        expected = {
            "create_idea_file": "idea",
            "write_master_design": "master_design",
            "write_bd": "basic_design",
            "write_dd": "detail_design",
        }
        for skill_key, stage in expected.items():
            skill = common_input["skills"][skill_key]
            self.assertEqual(skill["stage"], stage)
            self.assertIn("sourceFile", skill)
            self.assertGreaterEqual(len(skill["executionSteps"]), 3)
            self.assertGreaterEqual(len(skill["templateSections"]), 3)
            self.assertGreaterEqual(len(skill["selfReviewChecklist"]), 3)
            self.assertIn("inputs", skill)
            self.assertIn("outputs", skill)

        dd_skill = common_input["skills"]["write_dd"]
        self.assertIn("API detailed specification", dd_skill["executionSteps"])
        self.assertIn("Sequence Diagrams", dd_skill["templateSections"])
        self.assertIn(
            "Every function/endpoint has Trigger, Auth, Processing Logic, Input, Output, Errors",
            dd_skill["selfReviewChecklist"],
        )

    def test_common_input_status_summarizes_skill_detail(self):
        status = CommonInputService().get_status()

        self.assertEqual(status["status"], "ready")
        self.assertTrue(status["version"].startswith("input-common-"))
        self.assertEqual(status["skillCount"], 4)
        self.assertEqual(status["sourceRoot"], "INPUT/common")
        self.assertIn("write_dd", status["skills"])
        self.assertEqual(status["skillStages"]["write_dd"], "detail_design")
        self.assertIn("promptRuntime", status)
        self.assertEqual(status["promptRuntime"]["source"], "input_common_prompts")
        self.assertTrue(status["promptRuntime"]["version"].startswith("input-prompts-"))
        self.assertIn("detail_design_generation", status["promptRuntime"]["stageNames"])

    def test_templates_match_basic_and_detail_design_architecture(self):
        templates = CommonInputService().get_common_input()["templates"]

        self.assertIn("basic_design", templates)
        self.assertIn("detail_design", templates)
        self.assertIn("01_Screen", templates["basic_design"]["modules"])
        self.assertIn("02_API", templates["basic_design"]["modules"])
        self.assertIn("03_Batch", templates["basic_design"]["modules"])

        screen = templates["detail_design"]["modules"]["01_Screen"]
        self.assertEqual(screen["artifact"], "detail-design")
        self.assertIn("schemaPath", screen)
        self.assertIn("reviewChecklistIds", screen)
        section_ids = [section["id"] for section in screen["sections"]]
        self.assertEqual(
            section_ids,
            [
                "01_UI_Design",
                "02_Components",
                "03_Data_Models",
                "04_API_Integration",
                "05_Business_Logic",
                "06_State_Management",
            ],
        )
        self.assertTrue(all(section["required"] for section in screen["sections"]))

    def test_checklists_are_rule_based_with_severity_and_paths(self):
        checklists = CommonInputService().get_common_input()["checklists"]

        detail_rules = checklists["detail_design"]["rules"]
        self.assertGreaterEqual(len(detail_rules), 10)
        first_rule = detail_rules[0]
        self.assertIn("id", first_rule)
        self.assertIn("severity", first_rule)
        self.assertIn("path", first_rule)
        self.assertIn("message", first_rule)
        rule_ids = {rule["id"] for rule in detail_rules}
        self.assertIn("DD-API-CONTRACT", rule_ids)
        self.assertIn("DD-TEST-CASES", rule_ids)

    def test_guidelines_are_stage_specific_rules(self):
        guidelines = CommonInputService().get_common_input()["guidelines"]

        self.assertGreaterEqual(len(guidelines), 8)
        self.assertTrue(all("id" in guideline for guideline in guidelines))
        self.assertTrue(all("stage" in guideline for guideline in guidelines))
        self.assertTrue(all("rule" in guideline for guideline in guidelines))
        stages = {guideline["stage"] for guideline in guidelines}
        self.assertIn("basic_design_analytics", stages)
        self.assertIn("detail_design_generation", stages)
        self.assertIn("detail_design_review", stages)

    def test_common_components_are_reusable_design_blocks(self):
        components = CommonInputService().get_common_input()["commonComponents"]

        self.assertGreaterEqual(len(components), 6)
        component_ids = {component["id"] for component in components}
        self.assertIn("api_error_envelope", component_ids)
        self.assertIn("audit_log", component_ids)
        self.assertIn("pagination", component_ids)
        for component in components:
            self.assertIn("appliesTo", component)
            self.assertIn("contract", component)
            self.assertIn("ddUsage", component)


if __name__ == "__main__":
    unittest.main()
