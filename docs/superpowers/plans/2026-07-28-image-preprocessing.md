# Image Preprocessing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce Gemini Vision API latency and token usage by downscaling, converting to WebP, and slicing large input images before sending them to the LLM.

**Architecture:**
1. **Dependency:** Add `Pillow` to `backend/requirements.txt`.
2. **Utility:** Create a new helper function `preprocess_image` in `backend/app/infrastructure/llm/vision_client.py` that takes raw image bytes and returns a list of processed image bytes (WebP format, resized, and sliced if necessary).
3. **Integration:** Update `_generate_payload` in `VisionClient` to use the preprocessor and attach multiple `types.Part` objects to the Gemini request if the image was sliced.

**Tech Stack:** Python, Pillow, Google GenAI

## Global Constraints

- Must gracefully fallback to original bytes if `Pillow` fails or image is corrupted.
- Preserve aspect ratio when resizing.
- Support both `router.py` (user uploads) and `input_reference_service.py` (GCS reads) seamlessly by placing the logic in `vision_client.py`.

---

### Task 1: Add Pillow Dependency

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add Pillow**
Add `Pillow>=10.0.0` to `requirements.txt`.

---

### Task 2: Implement Image Preprocessing Logic

**Files:**
- Modify: `backend/app/infrastructure/llm/vision_client.py`

- [ ] **Step 1: Create `preprocess_image` method**

Add the following logic inside `vision_client.py` (e.g. as a static method or module-level function):

```python
import logging
from io import BytesIO
from typing import List

logger = logging.getLogger(__name__)

def _preprocess_image(image_bytes: bytes, max_dimension: int = 2048, slice_threshold: float = 3.0) -> List[bytes]:
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not installed. Skipping image preprocessing.")
        return [image_bytes]
        
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Slicing logic for very long images
        width, height = img.size
        images = []
        if height / width > slice_threshold:
            num_slices = int(height / (width * 1.5)) + 1
            slice_height = height // num_slices
            for i in range(num_slices):
                top = i * slice_height
                bottom = height if i == num_slices - 1 else (i + 1) * slice_height
                images.append(img.crop((0, top, width, bottom)))
        else:
            images.append(img)
            
        processed_bytes_list = []
        for chunk in images:
            c_width, c_height = chunk.size
            if max(c_width, c_height) > max_dimension:
                ratio = max_dimension / float(max(c_width, c_height))
                new_size = (int(c_width * ratio), int(c_height * ratio))
                chunk = chunk.resize(new_size, Image.Resampling.LANCZOS)
                
            out_io = BytesIO()
            # WebP handles transparency natively
            chunk.save(out_io, format="WEBP", quality=80)
            processed_bytes_list.append(out_io.getvalue())
            
        return processed_bytes_list
    except Exception as exc:
        logger.warning(f"Image preprocessing failed: {exc}. Using original bytes.")
        return [image_bytes]
```

- [ ] **Step 2: Update `_generate_payload`**

Modify `_generate_payload` in `VisionClient` to process the image and append all parts to `contents`:

```python
        # Replace the single types.Part with multiple parts
        processed_images = _preprocess_image(image_bytes)
        
        parts = [prompt]
        for p_bytes in processed_images:
            # We enforce WebP mime type after processing
            parts.append(types.Part.from_bytes(data=p_bytes, mime_type="image/webp"))
            
        try:
            response = client.models.generate_content(
                model=self._model,
                contents=parts,
                config={"response_mime_type": "application/json"},
            )
```

- [ ] **Step 3: Test and Commit**
Run `python3 -m unittest discover -s backend/tests -q`.
Commit changes.
