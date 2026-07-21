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
            "detailDesign": {"screen": {"01_UI_Design": "UI"}},
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


if __name__ == "__main__":
    unittest.main()
