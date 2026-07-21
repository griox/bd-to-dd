import json
import tempfile
import unittest
from pathlib import Path

from app.infrastructure.persistence.input_loader import InputReviewedDdLoader


class FakeVisionExtractor:
    def __init__(self) -> None:
        self.paths = []

    def extract_screen_sections(self, image_path: Path) -> dict:
        self.paths.append(image_path)
        return {
            "01_UI_Design": "Extracted layout from image",
            "02_Components": "Extracted button and table components",
        }


class InputReviewedDdLoaderTest(unittest.TestCase):
    def test_load_ignores_demo_input_and_returns_only_reviewed_dd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input" / "01_UI層"
            dd_dir = root / "DD" / "01_UI層" / "01_Screen設計"
            input_dir.mkdir(parents=True)
            dd_dir.mkdir(parents=True)
            (input_dir / "N9P90M4X4004W001_デモ入力.md").write_text(
                "## Demo input\nThis must not enter KB.\n",
                encoding="utf-8",
            )
            (dd_dir / "Screen設計_N9P90M4X4004W002_レビュー済み.md").write_text(
                "## Reviewed DD\nThis is approved knowledge.\n",
                encoding="utf-8",
            )

            samples = InputReviewedDdLoader(root).load()

            self.assertEqual(
                [sample.id for sample in samples],
                ["dd-screen-N9P90M4X4004W002"],
            )
            self.assertNotIn("This must not enter KB.", samples[0].content)

    def test_loads_screen_and_viewmodel_dd_as_one_reviewed_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            screen_dir = root / "DD" / "01_UI層" / "01_Screen設計"
            viewmodel_dir = root / "DD" / "01_UI層" / "02_ViewModel設計"
            screen_dir.mkdir(parents=True)
            viewmodel_dir.mkdir(parents=True)
            (screen_dir / "Screen設計_N9P90M4X4004W002_搭載種別選択画面.md").write_text(
                "## 1. Composable関数設計\nscreen body\n",
                encoding="utf-8",
            )
            (viewmodel_dir / "ViewModel設計_N9P90M4X4004W002_搭載種別選択画面.md").write_text(
                "## 1. UI State設計\nviewmodel body\n",
                encoding="utf-8",
            )

            samples = InputReviewedDdLoader(root).load()

            self.assertEqual(len(samples), 1)
            sample = samples[0]
            self.assertEqual(sample.id, "dd-screen-N9P90M4X4004W002")
            self.assertEqual(sample.metadata["approval_status"], "reviewed")
            screen = json.loads(sample.content)["detailDesign"]["screen"]
            self.assertIn("01_Screen_Design_1_Composable関数設計", screen)
            self.assertIn("02_ViewModel_Design_1_UI_State設計", screen)

    def test_loads_dd_images_through_vision_extractor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            screen_dir = root / "DD" / "01_UI層" / "01_Screen設計"
            screen_dir.mkdir(parents=True)
            image_path = screen_dir / "Screen設計_N9P90M4X4004W010_画像画面.png"
            image_path.write_bytes(b"fake-png")
            extractor = FakeVisionExtractor()

            samples = InputReviewedDdLoader(root, image_extractor=extractor).load()

            self.assertEqual(extractor.paths, [image_path])
            screen = json.loads(samples[0].content)["detailDesign"]["screen"]
            self.assertIn("01_Screen_Design_01_UI_Design", screen)
            self.assertEqual(samples[0].metadata["extraction_method"], "gemini_vision")

    def test_dd_image_requires_configured_gemini_vision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            screen_dir = root / "DD" / "01_UI層" / "01_Screen設計"
            screen_dir.mkdir(parents=True)
            (screen_dir / "Screen設計_N9P90M4X4004W010_画像画面.png").write_bytes(
                b"fake-png"
            )

            with self.assertRaisesRegex(RuntimeError, "Gemini vision extractor is required"):
                InputReviewedDdLoader(root).load()

    def test_missing_dd_directory_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            samples = InputReviewedDdLoader(Path(tmp)).load()

            self.assertEqual(samples, [])

    def test_source_reports_input_root(self):
        loader = InputReviewedDdLoader(Path("/tmp/example-input"))

        self.assertEqual(loader.source(), "/tmp/example-input")


if __name__ == "__main__":
    unittest.main()
