# Persistent Image Cache & Markdown Cleaner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 
1. **Persistent Image Cache:** Store Gemini Vision image extraction results in the Database (`image_analysis_cache` table) keyed by SHA-256 hash so that identical images never need re-extraction across jobs.
2. **Markdown Cleaner:** Clean and compress input markdown text (strip HTML comments, normalize excessive blank lines and trailing spaces) to reduce token usage by 10-15%.

**Architecture:**
- **Part 1 (Persistent Cache):**
  - Add `ImageAnalysisCacheModel` in `backend/app/infrastructure/persistence/postgres/models.py`.
  - Add cache get/set methods to `InputReferenceService` (using DB session or fallback in-memory cache).
- **Part 2 (Markdown Cleaner):**
  - Add `clean_markdown_text` utility in `backend/app/application/services/input_reference_service.py` (or a dedicated text utility).
  - Apply `clean_markdown_text` to basic design docs and UI design docs in `generate_detail_design.py`.

**Tech Stack:** Python, SQLAlchemy, Regex

## Global Constraints

- Must gracefully handle database disconnects / missing DB tables without crashing (fallback to in-memory cache).
- Must not alter semantic content of Markdown documents.
- Keep tests passing.

---

### Task 1: Persistent Image Analysis Cache

**Files:**
- Modify: `backend/app/infrastructure/persistence/postgres/models.py`
- Modify: `backend/app/application/services/input_reference_service.py`

- [ ] **Step 1: Add `ImageAnalysisCacheModel` in `models.py`**

```python
class ImageAnalysisCacheModel(Base):
    __tablename__ = "image_analysis_cache"

    image_hash = Column(String, primary_key=True, index=True)
    extraction_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

- [ ] **Step 2: Update `input_reference_service.py` to check/store DB cache**

In `_extract_image_description`:
Check DB table `image_analysis_cache` by `content_hash`. If found, return cached JSON.
If not found, call `image_extractor.extract_document_text(...)`, store result in `self._image_cache` and upsert into DB `image_analysis_cache`.

- [ ] **Step 3: Run tests to verify it passes**

Run `python3 -m unittest discover -s backend/tests -q`.

---

### Task 2: Markdown Text Cleaner

**Files:**
- Create: `backend/app/application/services/markdown_cleaner.py`
- Modify: `backend/app/application/use_cases/generate_detail_design.py`

- [ ] **Step 1: Create `markdown_cleaner.py`**

```python
import re

def clean_markdown_text(text: str) -> str:
    if not text:
        return ""
    # Strip HTML comments
    cleaned = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Strip trailing whitespace on each line
    cleaned = re.sub(r'[ \t]+\n', '\n', cleaned)
    # Reduce 3+ consecutive newlines to 2 newlines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()
```

- [ ] **Step 2: Apply `clean_markdown_text` in `generate_detail_design.py`**

In `run_analysis_phase` and payload formatting:
Clean `context["basic_design_docs"]` and `context["ui_design_docs"]` using `clean_markdown_text`.

- [ ] **Step 3: Run tests to verify it passes**

Run `python3 -m unittest discover -s backend/tests -q`.

- [ ] **Step 4: Commit all changes**

Commit with message: `perf(cache/text): add persistent image analysis cache and markdown cleaner`.
