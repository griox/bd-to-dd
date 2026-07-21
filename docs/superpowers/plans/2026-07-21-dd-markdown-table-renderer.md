# DD Markdown Table Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render exported detail design Markdown artifacts as table-based documents aligned with the sample DD templates while keeping the internal JSON pipeline unchanged.

**Architecture:** Add a dedicated renderer between the structured `detailDesign` payload and `export_artifacts()`. Keep `detailDesign` JSON as the machine-readable source of truth, and generate the human-facing `.md` artifact from that structure with template-aware Markdown tables and graceful fallbacks.

**Tech Stack:** Python backend, FastAPI application layer, unittest-based tests, Markdown artifact export

## Global Constraints

- Keep `detailDesign` JSON as the internal source of truth.
- Do not change the review-loop contract from JSON to Markdown.
- Preserve the `.json` artifact output exactly.
- Replace only the Markdown artifact rendering path.
- Renderer must support current string-based section values and future richer structured values.

---

### Task 1: Define Renderer Contract

**Files:**
- Create: `backend/app/infrastructure/persistence/postgres/dd_markdown_renderer.py`
- Modify: `backend/tests/test_export_service.py`

**Interfaces:**
- Consumes: `payload: Dict[str, Any]` with `analysis`, `detailDesign`, and `review`
- Produces: `render_detail_design_markdown(payload: Dict[str, Any]) -> str`

### Task 2: Add Table Rendering Helpers

**Files:**
- Create: `backend/app/infrastructure/persistence/postgres/dd_markdown_renderer.py`
- Modify: `backend/tests/test_export_service.py`

**Interfaces:**
- Consumes: strings, lists, dictionaries, section values
- Produces: normalized rows and Markdown table strings

### Task 3: Render Screen-Focused Document Layout

**Files:**
- Create: `backend/app/infrastructure/persistence/postgres/dd_markdown_renderer.py`
- Modify: `backend/tests/test_export_service.py`

**Interfaces:**
- Consumes: `detailDesign["screen"]`
- Produces: screen Markdown sections with table-based output for components, events, state, and API references where possible

### Task 4: Wire Renderer Into Artifact Export

**Files:**
- Modify: `backend/app/infrastructure/persistence/postgres/export_repository.py`
- Modify: `backend/tests/test_export_service.py`

**Interfaces:**
- Consumes: `render_detail_design_markdown(payload)`
- Produces: `detail-design.md` via the renderer instead of the current inline `_to_markdown()`

### Task 5: Backward-Compatible Fallback Output

**Files:**
- Modify: `backend/app/infrastructure/persistence/postgres/dd_markdown_renderer.py`
- Modify: `backend/tests/test_export_service.py`

**Interfaces:**
- Consumes: legacy string-only sections
- Produces: readable Markdown sections even when rich table rows are not available
