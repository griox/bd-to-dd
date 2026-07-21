import json
import mimetypes
from pathlib import Path
from typing import Any, Dict

from app.core.config import GEMINI_LLM_API_KEY, GEMINI_LLM_MODEL

NORMALIZED_SCREEN_SECTION_FALLBACKS = {
    "01_UI_Design": "UI image was attached but could not be captioned automatically.",
    "02_Components": "Manual review required for component extraction.",
    "03_Data_Models": "No data model detected from image fallback.",
    "04_API_Integration": "No API integration detected from image fallback.",
    "05_Business_Logic": "No business logic detected from image fallback.",
    "06_State_Management": "No state management detected from image fallback.",
}


class VisionExtractionError(Exception):
    """Raised when image-to-JSON extraction fails."""


class GeminiVisionDesignExtractor:
    """Extracts normalized Detail Design screen sections from UI images."""

    def __init__(
        self,
        api_key: str = GEMINI_LLM_API_KEY,
        model: str = GEMINI_LLM_MODEL,
    ) -> None:
        self._api_key = api_key
        self._model = model

    def extract_screen_sections(self, image_path: Path) -> Dict[str, str]:
        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
        payload = self._generate_payload(
            image_path.read_bytes(),
            mime_type,
            self._prompt_for("reviewed_dd"),
        )
        return self._extract_sections(payload)

    def extract_document_text(
        self,
        image_bytes: bytes,
        mime_type: str,
        context: str,
        filename: str = "uploaded-image",
    ) -> str:
        payload = self._generate_payload(
            image_bytes,
            mime_type,
            self._prompt_for(context),
        )
        if not isinstance(payload, dict) or not payload:
            raise VisionExtractionError("Gemini vision response was empty.")
        return json.dumps(
            {
                "source": {
                    "type": "image",
                    "filename": filename,
                    "model": self._model,
                },
                "context": context,
                "extraction": payload,
            },
            ensure_ascii=False,
            indent=2,
        )

    def extract_common_reference(
        self,
        image_bytes: bytes,
        mime_type: str,
        filename: str,
    ) -> Dict[str, Any]:
        payload = self._generate_payload(
            image_bytes,
            mime_type,
            self._prompt_for("common_input"),
        )
        if not isinstance(payload, dict) or not payload.get("summary"):
            raise VisionExtractionError(
                "Gemini vision response missing common input summary."
            )
        return {
            "sourceName": filename,
            "sourceType": "image",
            "extractionModel": self._model,
            **payload,
        }

    def _prompt_for(self, context: str) -> str:
        prompts = {
            "basic_design": (
                "Analyze this Basic Design image. Return only valid JSON with keys "
                "summary, visibleText, requirements, modules, screens, entities, "
                "businessFlows, apiCandidates, assumptions."
            ),
            "ui_design": (
                "Analyze this UI Design image. Return only valid JSON with keys "
                "summary, visibleText, screens, components, interactions, states, "
                "validations, apiSignals, assumptions."
            ),
            "common_input": (
                "Analyze this shared design input image. Return only valid JSON with "
                "keys summary, visibleText, rules, components, layoutSignals, "
                "templateSignals, assumptions."
            ),
            "reviewed_dd": (
                "Analyze this UI/detail-design image and return only valid JSON. "
                "Normalize the result to this shape: "
                "{\"detailDesign\":{\"screen\":{\"01_UI_Design\":\"...\","
                "\"02_Components\":\"...\",\"03_Data_Models\":\"...\","
                "\"04_API_Integration\":\"...\",\"05_Business_Logic\":\"...\","
                "\"06_State_Management\":\"...\"}}}."
            ),
        }
        if context not in prompts:
            raise VisionExtractionError(f"Unsupported image context: {context}")
        return prompts[context]

    def _generate_payload(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
    ) -> Dict[str, Any]:
        if not self._api_key or self._api_key == "dummy":
            raise VisionExtractionError("GEMINI_LLM_API_KEY is not configured.")
        if not image_bytes:
            raise VisionExtractionError("Image content is empty.")

        try:
            from google import genai  # noqa: PLC0415
            from google.genai import types  # noqa: PLC0415
        except ImportError as exc:
            raise VisionExtractionError(
                "google-genai package is not installed. Add 'google-genai' to requirements.txt."
            ) from exc

        client = genai.Client(api_key=self._api_key)
        try:
            response = client.models.generate_content(
                model=self._model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config={"response_mime_type": "application/json"},
            )
            payload = json.loads(response.text or "{}")
        except Exception as exc:
            raise VisionExtractionError(f"Gemini vision extraction failed: {exc}") from exc

        if not isinstance(payload, dict) or not payload:
            raise VisionExtractionError("Gemini vision response was empty.")
        return payload

    def _extract_sections(self, payload: Dict[str, Any]) -> Dict[str, str]:
        screen = (
            payload.get("detailDesign", {})
            .get("screen", {})
        )
        if not isinstance(screen, dict):
            raise VisionExtractionError("Gemini vision response missing detailDesign.screen.")

        sections = {
            str(key): str(value).strip()
            for key, value in screen.items()
            if str(value).strip()
        }
        if not sections:
            raise VisionExtractionError("Gemini vision response did not contain screen sections.")
        normalized = dict(NORMALIZED_SCREEN_SECTION_FALLBACKS)
        normalized.update(sections)
        return normalized


class VisionClient:
    def describe_ui(self, content: bytes) -> str:
        return "Vision UI analysis is not configured."
