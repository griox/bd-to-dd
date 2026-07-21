import unittest
from unittest.mock import patch

from app.infrastructure.llm.vision_client import (
    GeminiVisionDesignExtractor,
    VisionExtractionError,
)


class GeminiVisionDesignExtractorTest(unittest.TestCase):
    def test_extract_document_text_normalizes_context_payload(self):
        extractor = GeminiVisionDesignExtractor(api_key="test-key", model="gemini-2.5-flash")
        payload = {
            "summary": "Registration screen",
            "visibleText": ["Email", "Submit"],
            "requirements": ["Validate email"],
            "components": ["Text field", "Button"],
            "flows": ["Submit registration"],
        }

        with patch.object(extractor, "_generate_payload", return_value=payload) as generate:
            content = extractor.extract_document_text(
                b"image-bytes",
                "image/png",
                context="basic_design",
                filename="registration.png",
            )

        generate.assert_called_once()
        self.assertIn("Registration screen", content)
        self.assertIn("Validate email", content)
        self.assertIn("registration.png", content)

    def test_extract_document_text_requires_gemini_configuration(self):
        extractor = GeminiVisionDesignExtractor(api_key="")

        with self.assertRaisesRegex(VisionExtractionError, "not configured"):
            extractor.extract_document_text(
                b"image-bytes",
                "image/png",
                context="ui_design",
            )

    def test_extract_common_reference_returns_structured_metadata(self):
        extractor = GeminiVisionDesignExtractor(api_key="test-key", model="gemini-2.5-flash")
        payload = {
            "summary": "Shared navigation rule",
            "visibleText": ["Back"],
            "rules": ["Always preserve back navigation"],
            "components": ["Navigation bar"],
        }

        with patch.object(extractor, "_generate_payload", return_value=payload):
            reference = extractor.extract_common_reference(
                b"image-bytes",
                "image/webp",
                "navigation.webp",
            )

        self.assertEqual(reference["summary"], "Shared navigation rule")
        self.assertEqual(reference["extractionModel"], "gemini-2.5-flash")
        self.assertEqual(reference["sourceType"], "image")
        self.assertEqual(reference["sourceName"], "navigation.webp")

    def test_extract_sections_fills_missing_normalized_keys_with_fallback_text(self):
        extractor = GeminiVisionDesignExtractor(api_key="test-key")

        sections = extractor._extract_sections({
            "detailDesign": {
                "screen": {
                    "01_UI_Design": "Layout",
                    "02_Components": "Button",
                }
            }
        })

        self.assertEqual(sections["01_UI_Design"], "Layout")
        self.assertEqual(sections["02_Components"], "Button")
        self.assertIn("03_Data_Models", sections)
        self.assertIn("06_State_Management", sections)

    def test_extract_sections_returns_normalized_screen_dict(self):
        extractor = GeminiVisionDesignExtractor(api_key="test-key")

        sections = extractor._extract_sections({
            "detailDesign": {
                "screen": {
                    "01_UI_Design": " Layout ",
                    "02_Components": "Button",
                    "03_Empty": " ",
                }
            }
        })

        self.assertEqual(
            sections["01_UI_Design"],
            "Layout",
        )
        self.assertEqual(sections["02_Components"], "Button")
        self.assertIn("03_Data_Models", sections)
        self.assertIn("06_State_Management", sections)

    def test_extract_sections_rejects_missing_screen_sections(self):
        extractor = GeminiVisionDesignExtractor(api_key="test-key")

        with self.assertRaises(VisionExtractionError):
            extractor._extract_sections({"detailDesign": {"screen": {}}})


if __name__ == "__main__":
    unittest.main()
