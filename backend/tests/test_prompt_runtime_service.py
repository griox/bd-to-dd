import json
import tempfile
import unittest
from pathlib import Path

from app.application.services.prompt_catalog import DEFAULT_PROMPTS
from app.application.services.prompt_runtime_service import PromptRuntimeService


class PromptRuntimeServiceTest(unittest.TestCase):
    def test_loads_manifest_and_resolves_include_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "common").mkdir(parents=True)
            (root / "generate").mkdir(parents=True)
            (root / "fill").mkdir(parents=True)
            (root / "common" / "quality_reflection.md").write_text(
                'Quality Rules {"severity": "error"}',
                encoding="utf-8",
            )
            (root / "generate" / "screen.md").write_text("Generate Screen", encoding="utf-8")
            (root / "fill" / "screen.md").write_text("Fill Screen", encoding="utf-8")
            manifest = {
                stage_name: {
                    "system": f"{stage_name} system",
                    "user": f"{stage_name} user",
                    "systemIncludes": ["common/quality_reflection.md"],
                    "userIncludes": ["generate/screen.md", "fill/screen.md"],
                }
                for stage_name in DEFAULT_PROMPTS
            }
            (root / "prompt_catalog.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            catalog = PromptRuntimeService(root=root).get_prompt_catalog()

            self.assertIn("Quality Rules", catalog["basic_design_analytics"]["system"])
            self.assertIn('{{"severity": "error"}}', catalog["basic_design_analytics"]["system"])
            self.assertIn("Generate Screen", catalog["detail_design_review"]["user"])
            self.assertIn("Fill Screen", catalog["detail_design_review"]["user"])

    def test_missing_manifest_falls_back_to_backend_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog = PromptRuntimeService(root=Path(tmpdir)).get_prompt_catalog()
            self.assertEqual(catalog, DEFAULT_PROMPTS)

    def test_invalid_manifest_falls_back_to_backend_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "prompt_catalog.json").write_text("{invalid", encoding="utf-8")

            catalog = PromptRuntimeService(root=root).get_prompt_catalog()

            self.assertEqual(catalog, DEFAULT_PROMPTS)

    def test_prompt_status_reports_runtime_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "common").mkdir(parents=True)
            include_path = root / "common" / "quality_reflection.md"
            include_path.write_text("Quality Rules", encoding="utf-8")
            manifest = {
                stage_name: {
                    "system": f"{stage_name} system",
                    "user": f"{stage_name} user",
                    "systemIncludes": ["common/quality_reflection.md"],
                    "userIncludes": [],
                }
                for stage_name in DEFAULT_PROMPTS
            }
            manifest_path = root / "prompt_catalog.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            status = PromptRuntimeService(root=root).get_prompt_status()

            self.assertEqual(status["source"], "input_common_prompts")
            self.assertEqual(status["manifestPath"], str(manifest_path))
            self.assertIn(str(include_path), status["sourceFiles"])
            self.assertEqual(set(status["stageNames"]), set(DEFAULT_PROMPTS.keys()))
            self.assertTrue(status["version"].startswith("input-prompts-"))


if __name__ == "__main__":
    unittest.main()
