# Similar Input Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add similar `INPUT/input` examples to Basic Design Analytics without adding them to KB or replacing user input.

**Architecture:** Create a focused `InputReferenceService` that catalogs demo inputs, ranks them with text overlap, extracts selected images through Gemini Flash, and formats a prompt section. Wire it into `GenerationService` before Basic Design Analytics.

**Tech Stack:** Python 3.12, unittest, LangChain RunnableLambda, existing GeminiVisionDesignExtractor.

## Global Constraints

- User input is authoritative and must not be overwritten.
- `INPUT/input` must not be loaded into KB.
- Only selected sample images call Gemini Flash.
- Missing Gemini vision configuration must fail explicitly when a selected sample image exists.

---

### Task 1: Input Reference Service

**Files:**
- Create: `backend/app/application/services/input_reference_service.py`
- Test: `backend/tests/test_input_reference_service.py`

**Interfaces:**
- Produces: `InputReferenceService(root: Optional[Path] = None, image_extractor: Optional[DocumentImageExtractor] = None)`
- Produces: `find_similar_references(basic_design: str, ui_design: str = "", limit: int = 3) -> Dict[str, Any]`

- [ ] Write tests for selecting a similar sample from markdown and CSV.
- [ ] Write tests proving only selected sample images are passed to Gemini.
- [ ] Write tests proving selected images require a configured extractor.
- [ ] Implement the catalog, ranking, image extraction, and formatted prompt output.
- [ ] Run `PYTHONPATH=backend python -m pytest backend/tests/test_input_reference_service.py -q`.

### Task 2: Generation Pipeline Wiring

**Files:**
- Modify: `backend/app/application/use_cases/generate_detail_design.py`
- Modify: `backend/app/application/services/prompt_catalog.py`
- Modify: `backend/app/presentation/deps.py`
- Test: `backend/tests/test_generation_pipeline.py`

**Interfaces:**
- Consumes: `InputReferenceService.find_similar_references(...)`
- Produces: `resourcesUsed["inputReferences"]`

- [ ] Write a failing pipeline test showing `input_reference_examples` reaches Basic Design Analytics while `basic_design` stays equal to the user's text.
- [ ] Add `input_reference_service` to `GenerationService`.
- [ ] Include `input_reference_examples` in the Basic Design Analytics prompt.
- [ ] Include selected references in `resourcesUsed`.
- [ ] Run focused generation tests.

### Task 3: Validation

**Files:**
- Validate backend tests and syntax.

- [ ] Run `PYTHONPATH=backend python -m pytest backend/tests/test_input_reference_service.py backend/tests/test_generation_pipeline.py -q`.
- [ ] Run broader relevant backend tests if focused tests pass.
- [ ] Report any unrelated pre-existing failures separately.
