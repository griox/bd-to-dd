# Gemini Flash Image Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Process every accepted BD, UI, Knowledge Base, nested INPUT, and Common Input image with Gemini Flash, failing clearly when Gemini is unavailable.

**Architecture:** Extend the existing GeminiVisionDesignExtractor into a context-aware shared boundary that accepts paths or bytes. Presentation routes normalize images to text before existing document/KB services consume them. Repository and Common Input loaders recursively discover images and use the same injected extractor.

**Tech Stack:** Python 3, FastAPI, google-genai, unittest, Next.js 16, React 19, TypeScript.

## Global Constraints

- Supported images: PNG, JPEG, WebP.
- Default vision model: gemini-2.5-flash through GEMINI_LLM_MODEL.
- Never silently skip an accepted image.
- Missing Gemini configuration fails with HTTP 503; provider/JSON failures use HTTP 502.
- Preserve text-only workflows and existing GenerationService document contracts.
- No database migration.

---

### Task 1: Shared context-aware Gemini image extraction

**Files:**
- Modify: backend/app/infrastructure/llm/vision_client.py
- Modify: backend/app/domain/repositories/vector_store_repository.py
- Test: backend/tests/test_vision_extractor.py

**Interfaces:**
- Produces: extract_image(image_bytes: bytes, mime_type: str, context: str) -> dict
- Preserves: extract_screen_sections(image_path: Path) -> Dict[str, str]

- [ ] Write failing tests proving BD/UI/common contexts produce non-empty normalized text and missing configuration raises VisionExtractionError.
- [ ] Run: cd backend && python -m unittest tests.test_vision_extractor -v
- [ ] Implement one generate_content call boundary, context-specific prompts, response validation, and safe error messages.
- [ ] Re-run the focused test and confirm PASS.
- [ ] Run Python syntax validation for modified files.
- [ ] Commit if a Git worktree becomes available; otherwise record that the workspace has no .git directory.

### Task 2: Image-aware project document and Knowledge Base APIs

**Files:**
- Modify: backend/app/presentation/api/v1/router.py
- Modify: backend/app/presentation/deps.py
- Test: create backend/tests/test_image_upload_api.py
- Test: modify backend/tests/test_ingestion_use_case.py

**Interfaces:**
- Consumes: shared extractor from Task 1.
- Produces: normalize_uploaded_document(file: UploadFile, context: str) -> extracted content and metadata.

- [ ] Write failing API-unit tests for BD image, UI image, text bypass, missing config, extraction failure, KB image, and ambiguous KB sample input.
- [ ] Run focused tests and verify failures are caused by the missing image-aware route behavior.
- [ ] Implement extension/MIME/size validation and map typed errors to HTTP 400/502/503.
- [ ] Save project documents only after successful extraction.
- [ ] Change the KB sample route to multipart file/content with exactly-one validation.
- [ ] Re-run focused tests and confirm PASS.
- [ ] Run all affected backend route/ingestion tests.

### Task 3: Recursive Knowledge Base and Common Input image loading

**Files:**
- Modify: backend/app/infrastructure/persistence/input_loader.py
- Modify: backend/app/application/services/common_input_service.py
- Modify: backend/app/application/use_cases/generate_detail_design.py
- Test: backend/tests/test_input_loader.py
- Test: backend/tests/test_common_input_service.py

**Interfaces:**
- Consumes: extract_screen_sections and context-aware common-image extraction.
- Produces: commonInput.imageReferences: list[dict].

- [ ] Write failing tests for recursive input/images discovery and same-screen Markdown/image merge.
- [ ] Run input-loader tests and verify RED.
- [ ] Implement recursive discovery and grouped evidence merging without skipping images.
- [ ] Re-run input-loader tests and verify GREEN.
- [ ] Write failing Common Input tests for recursive imageReferences, content-hash cache, sourceFiles/version participation, and extraction failure.
- [ ] Implement extractor injection, recursive image discovery, successful-result caching, and image guidance formatting.
- [ ] Re-run Common Input and generation-pipeline tests and verify GREEN.

### Task 4: Frontend preserves and uploads original images

**Files:**
- Modify: frontend/app/page.tsx

**Interfaces:**
- Consumes unchanged project document routes from Task 2.
- Produces separate typed text and selected File state for BD and UI.

- [ ] Add pure helper behavior for supported-image detection and upload-source selection in page.tsx.
- [ ] Preserve original image File; preview text files only.
- [ ] Make handleGenerate check every HTTP response and stop before generation on upload failure.
- [ ] Display safe backend detail messages and selected image filenames.
- [ ] Run: cd frontend && npm run lint
- [ ] Run: cd frontend && npx tsc --noEmit
- [ ] Run: cd frontend && npm run build

### Task 5: Full verification and documentation

**Files:**
- Modify: PROJECT_FLOW_EXPLAINED_VI.md
- Modify: .env.example
- Modify: backend/.env.example

**Interfaces:**
- Documents GEMINI_LLM_API_KEY, GEMINI_LLM_MODEL, supported image formats, error behavior, and reindex flow.

- [ ] Update documentation and example configuration.
- [ ] Run: cd backend && python -m unittest discover -s tests -v
- [ ] Run Python compile validation over backend/app and backend/tests.
- [ ] Re-run frontend lint, TypeScript, and production build.
- [ ] Review git-style diff output even though this workspace currently lacks Git metadata.
- [ ] Confirm each acceptance criterion in the approved design has a passing test or validation command.
