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


def _preprocess_image(image_bytes: bytes, max_dimension: int = 2048, slice_threshold: float = 3.0) -> list[tuple[bytes, str]]:
    import logging  # noqa: PLC0415
    from io import BytesIO  # noqa: PLC0415

    logger = logging.getLogger(__name__)

    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        logger.warning("Pillow not installed. Skipping image preprocessing.")
        return [(image_bytes, "image/png")]

    try:
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        images = []

        # Slice very long vertical images (e.g. scrolling screens)
        if height / width > slice_threshold:
            num_slices = int(height / (width * 1.5)) + 1
            slice_height = height // num_slices
            for i in range(num_slices):
                top = i * slice_height
                bottom = height if i == num_slices - 1 else (i + 1) * slice_height
                images.append(img.crop((0, top, width, bottom)))
        else:
            images.append(img)

        processed_list = []
        for chunk in images:
            c_width, c_height = chunk.size
            if max(c_width, c_height) > max_dimension:
                ratio = max_dimension / float(max(c_width, c_height))
                new_size = (int(c_width * ratio), int(c_height * ratio))
                chunk = chunk.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to WebP for maximum compression and fast API upload
            out_io = BytesIO()
            # If RGBA, save as WEBP handles transparency smoothly
            if chunk.mode not in ("RGB", "RGBA"):
                chunk = chunk.convert("RGBA")
            chunk.save(out_io, format="WEBP", quality=80)
            processed_list.append((out_io.getvalue(), "image/webp"))

        return processed_list
    except Exception as exc:
        logger.warning("Image preprocessing failed: %s. Using original bytes.", exc)
        return [(image_bytes, "image/png")]



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
            processed_images = _preprocess_image(image_bytes)
            contents = [prompt]
            for img_data, img_mime in processed_images:
                contents.append(types.Part.from_bytes(data=img_data, mime_type=img_mime))

            response = client.models.generate_content(
                model=self._model,
                contents=contents,
                config={"response_mime_type": "application/json"},
            )
            text = response.text or "{}"
            if text.startswith("```json"):
                text = text.split("```json", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()
            
            import re  # noqa: PLC0415
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*\]', ']', text)
            
            payload = json.loads(text)
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
