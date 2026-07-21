import io
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, UploadFile

from app.infrastructure.llm.vision_client import VisionExtractionError
from app.presentation.api.v1 import router


def _upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers={"content-type": content_type},
    )


class ImageUploadApiTest(unittest.TestCase):
    def setUp(self):
        self.original_extractor = router.vision_extractor
        router.vision_extractor = MagicMock()

    def tearDown(self):
        router.vision_extractor = self.original_extractor

    def test_basic_design_image_is_extracted_before_save(self):
        router.vision_extractor.extract_document_text.return_value = '{"summary":"BD"}'
        image = _upload("bd.png", b"png-bytes", "image/png")

        with patch.object(router, "_save_document") as save:
            response = router.upload_basic_design("project-1", image)

        router.vision_extractor.extract_document_text.assert_called_once_with(
            b"png-bytes", "image/png", "basic_design", "bd.png"
        )
        save.assert_called_once_with("project-1", "basic-design", '{"summary":"BD"}')
        self.assertEqual(response["data"]["sourceType"], "image")

    def test_ui_design_image_uses_ui_context(self):
        router.vision_extractor.extract_document_text.return_value = '{"summary":"UI"}'
        image = _upload("ui.webp", b"webp-bytes", "image/webp")

        with patch.object(router, "_save_document"):
            router.upload_ui_design("project-1", image)

        self.assertEqual(
            router.vision_extractor.extract_document_text.call_args.args[2],
            "ui_design",
        )

    def test_text_upload_does_not_call_vision(self):
        text = _upload("bd.md", b"# Basic Design", "text/markdown")

        with patch.object(router, "_save_document") as save:
            response = router.upload_basic_design("project-1", text)

        router.vision_extractor.extract_document_text.assert_not_called()
        save.assert_called_once_with("project-1", "basic-design", "# Basic Design")
        self.assertEqual(response["data"]["sourceType"], "text")

    def test_missing_gemini_configuration_returns_503_and_saves_nothing(self):
        router.vision_extractor.extract_document_text.side_effect = VisionExtractionError(
            "GEMINI_LLM_API_KEY is not configured."
        )
        image = _upload("bd.jpg", b"jpg-bytes", "image/jpeg")

        with patch.object(router, "_save_document") as save:
            with self.assertRaises(HTTPException) as raised:
                router.upload_basic_design("project-1", image)

        self.assertEqual(raised.exception.status_code, 503)
        save.assert_not_called()

    def test_knowledge_base_image_indexes_extracted_content(self):
        router.vision_extractor.extract_document_text.return_value = '{"summary":"Sample"}'
        router.knowledge_base = MagicMock()
        router.knowledge_base.add_sample.return_value = {"status": "indexed"}
        image = _upload("sample.png", b"png-bytes", "image/png")

        response = router.upload_sample(file=image, content=None)

        router.knowledge_base.add_sample.assert_called_once_with('{"summary":"Sample"}')
        self.assertEqual(response["data"]["status"], "indexed")

    def test_knowledge_base_rejects_both_file_and_content(self):
        image = _upload("sample.png", b"png-bytes", "image/png")

        with self.assertRaises(HTTPException) as raised:
            router.upload_sample(file=image, content="raw text")

        self.assertEqual(raised.exception.status_code, 400)

    def test_design_input_bundle_saves_markdown_and_combined_ui_context(self):
        router.vision_extractor.extract_document_text.side_effect = [
            "First screen extracted by Gemini Flash",
            "Second screen extracted by Gemini Flash",
        ]
        design = _upload("screen.md", b"# Basic Design", "text/markdown")
        images = [
            _upload("screen-1.png", b"png-1", "image/png"),
            _upload("screen-2.webp", b"webp-2", "image/webp"),
        ]
        composable = _upload(
            "composable.csv",
            b"Composable,Type\nNpButton,DS\n",
            "text/csv",
        )

        with patch.object(router, "_save_document") as save:
            response = router.upload_design_input_bundle(
                "project-1",
                design,
                images,
                composable,
            )

        self.assertEqual(save.call_args_list[0].args, ("project-1", "basic-design", "# Basic Design"))
        ui_content = save.call_args_list[1].args[2]
        self.assertIn("First screen extracted by Gemini Flash", ui_content)
        self.assertIn("Second screen extracted by Gemini Flash", ui_content)
        self.assertIn("NpButton", ui_content)
        self.assertEqual(response["data"]["imageCount"], 2)
        self.assertTrue(response["data"]["hasComposableList"])

    def test_design_input_bundle_requires_markdown_design(self):
        design = _upload("screen.csv", b"a,b", "text/csv")

        with patch.object(router, "_save_document") as save:
            with self.assertRaises(HTTPException) as raised:
                router.upload_design_input_bundle("project-1", design, [], None)

        self.assertEqual(raised.exception.status_code, 400)
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
