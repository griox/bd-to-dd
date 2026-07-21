import tempfile
import unittest
from pathlib import Path

from app.application.services.input_reference_service import InputReferenceService


class FakeDocumentImageExtractor:
    def __init__(self) -> None:
        self.calls = []

    def extract_document_text(
        self,
        image_bytes: bytes,
        mime_type: str,
        context: str,
        filename: str = "uploaded-image",
    ) -> str:
        self.calls.append(
            {
                "bytes": image_bytes,
                "mime_type": mime_type,
                "context": context,
                "filename": filename,
            }
        )
        return f"Gemini Flash description for {filename}"


class InputReferenceServiceTest(unittest.TestCase):
    def test_finds_similar_input_reference_from_markdown_and_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "input" / "01_UI層"
            csv_dir = root / "input" / "composable_list"
            ui_dir.mkdir(parents=True)
            csv_dir.mkdir(parents=True)
            (ui_dir / "N9P90M4X4004W002_Registration.md").write_text(
                "# Registration\nUser Registration lets User create Account.\n",
                encoding="utf-8",
            )
            (csv_dir / "N9P90M4X4004W002_Registration.csv").write_text(
                "component,type\nsubmitButton,Button\n",
                encoding="utf-8",
            )
            (ui_dir / "N9P90M4X4004W003_Search.md").write_text(
                "# Search\nFlight search filters.\n",
                encoding="utf-8",
            )

            result = InputReferenceService(root).find_similar_references(
                basic_design="Build User Registration Account creation.",
                ui_design="submit button appears on the registration form.",
            )

            self.assertEqual(result["referenceCount"], 1)
            self.assertEqual(result["references"][0]["componentId"], "N9P90M4X4004W002")
            self.assertIn("Registration", result["formatted"])
            self.assertIn("submitButton", result["formatted"])

    def test_returns_empty_reference_section_when_no_sample_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "input" / "01_UI層"
            ui_dir.mkdir(parents=True)
            (ui_dir / "N9P90M4X4004W002_Registration.md").write_text(
                "# Registration\nUser Registration lets User create Account.\n",
                encoding="utf-8",
            )

            result = InputReferenceService(root).find_similar_references(
                basic_design="Batch process archives old invoices nightly.",
                ui_design="",
            )

            self.assertEqual(result["referenceCount"], 0)
            self.assertEqual(result["references"], [])
            self.assertIn("No similar input examples found.", result["formatted"])

    def test_extracts_images_only_for_selected_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "input" / "01_UI層"
            image_dir = ui_dir / "images"
            ui_dir.mkdir(parents=True)
            image_dir.mkdir(parents=True)
            (ui_dir / "N9P90M4X4004W002_Registration.md").write_text(
                "# Registration\nUser Registration lets User create Account.\n",
                encoding="utf-8",
            )
            (ui_dir / "N9P90M4X4004W003_Search.md").write_text(
                "# Search\nFlight search filters.\n",
                encoding="utf-8",
            )
            (image_dir / "N9P90M4X4004W002_Registration.png").write_bytes(b"selected")
            (image_dir / "N9P90M4X4004W003_Search.png").write_bytes(b"ignored")
            extractor = FakeDocumentImageExtractor()

            result = InputReferenceService(
                root,
                image_extractor=extractor,
            ).find_similar_references(
                basic_design="Build User Registration Account creation.",
                ui_design="",
            )

            self.assertEqual(result["referenceCount"], 1)
            self.assertEqual(len(extractor.calls), 1)
            self.assertEqual(extractor.calls[0]["filename"], "N9P90M4X4004W002_Registration.png")
            self.assertEqual(extractor.calls[0]["context"], "ui_design")
            self.assertIn("Gemini Flash description", result["formatted"])

    def test_selected_image_requires_configured_gemini_flash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ui_dir = root / "input" / "01_UI層"
            image_dir = ui_dir / "images"
            ui_dir.mkdir(parents=True)
            image_dir.mkdir(parents=True)
            (ui_dir / "N9P90M4X4004W002_Registration.md").write_text(
                "# Registration\nUser Registration lets User create Account.\n",
                encoding="utf-8",
            )
            (image_dir / "N9P90M4X4004W002_Registration.png").write_bytes(b"selected")

            with self.assertRaisesRegex(RuntimeError, "Gemini Flash vision extractor is required"):
                InputReferenceService(root).find_similar_references(
                    basic_design="Build User Registration Account creation.",
                    ui_design="",
                )


if __name__ == "__main__":
    unittest.main()
