import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.infrastructure.persistence.postgres.export_repository import export_artifacts


class ExportServiceTest(unittest.TestCase):
    def test_export_artifacts_writes_json_and_markdown(self):
        payload = {
            "analysis": {"summary": "Summary", "businessFlows": ["Flow A"]},
            "detailDesign": {
                "screen": {
                    "01_UI_Design": "Subtotal confirmation layout with fixed header and action footer.",
                    "02_Components": [
                        {
                            "componentName": "NpBaseScreen",
                            "type": "DS",
                            "role": "Screen base component",
                            "notes": "-",
                        },
                        {
                            "componentName": "NpHalfModal",
                            "type": "DS",
                            "role": "Workflow adjustment modal",
                            "notes": "Shown when subtotal count > 0",
                        },
                    ],
                    "04_API_Integration": [
                        {
                            "endpoint": "/api/subtotal",
                            "method": "GET",
                            "timing": "On screen load",
                            "responseHandling": "Populate loading type and subtotal count",
                        }
                    ],
                    "06_State_Management": [
                        {
                            "stateName": "subtotalCount",
                            "type": "String",
                            "initialValue": "0",
                            "updateTiming": "Updated after subtotal API returns",
                        }
                    ],
                }
            },
            "review": {"status": "PASS", "findings": []},
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch(
                "app.infrastructure.persistence.postgres.export_repository.ARTIFACTS_DIR",
                Path(tmp_dir),
            ):
                artifacts = export_artifacts("project-1", "job-1", payload)

            self.assertTrue(os.path.exists(artifacts["jsonPath"]))
            self.assertTrue(os.path.exists(artifacts["markdownPath"]))
            self.assertEqual(json.loads(Path(artifacts["jsonPath"]).read_text())["analysis"]["summary"], "Summary")
            markdown = Path(artifacts["markdownPath"]).read_text()
            self.assertIn("# Detail Design Artifact", markdown)
            self.assertIn("## Screen Detail Design", markdown)
            self.assertIn("|Composable Function|Type|Role|Notes|", markdown)
            self.assertIn("|API / Endpoint|Method|Timing|Response Handling|", markdown)
            self.assertIn("|State Name|Type|Initial Value|Update Timing|", markdown)
            self.assertIn("NpBaseScreen", markdown)
            self.assertIn("/api/subtotal", markdown)

    def test_export_artifacts_falls_back_to_readable_markdown_for_string_sections(self):
        payload = {
            "analysis": {"summary": "Summary", "businessFlows": ["Flow A"]},
            "detailDesign": {
                "screen": {
                    "01_UI_Design": "Simple UI section",
                    "05_Business_Logic": "Validate subtotal and branch by loading type.",
                }
            },
            "review": {"status": "NG", "findings": ["Missing event definition table"]},
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch(
                "app.infrastructure.persistence.postgres.export_repository.ARTIFACTS_DIR",
                Path(tmp_dir),
            ):
                artifacts = export_artifacts("project-1", "job-2", payload)

            markdown = Path(artifacts["markdownPath"]).read_text()
            self.assertIn("## Screen Detail Design", markdown)
            self.assertIn("### UI Design", markdown)
            self.assertIn("Simple UI section", markdown)
            self.assertIn("### Business Logic", markdown)
            self.assertIn("Missing event definition table", markdown)


if __name__ == "__main__":
    unittest.main()
