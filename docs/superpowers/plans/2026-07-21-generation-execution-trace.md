# Generation Execution Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-step backend execution trace data and render it in the frontend as an accordion with summary plus raw JSON.

**Architecture:** Extend `GenerationService` to collect compact trace entries during analysis, retrieval, fusion, context assembly, DD generation, and review. Persist trace data inside generation results so the existing polling endpoint can drive a richer frontend without new APIs.

**Tech Stack:** Python backend, FastAPI, Next.js/React frontend, unittest-based backend tests

## Global Constraints

- Keep existing `pipeline.stages` intact for backward compatibility.
- Store trace under `executionTrace.steps`.
- Each trace step must include `key`, `label`, `status`, `summary`, `preview`, and `raw`.
- Do not include full embedding vectors in trace payloads.
- Frontend must render trace inline on the current page as accordions.

---

### Task 1: Backend Execution Trace Contract

**Files:**
- Modify: `backend/tests/test_generation_pipeline.py`
- Modify: `backend/app/application/use_cases/generate_detail_design.py`

**Interfaces:**
- Consumes: existing generation payload structure from `GenerationService.run(...)`
- Produces: `result["executionTrace"] = {"steps": list[dict]}`

### Task 2: Retrieval Trace Capture

**Files:**
- Modify: `backend/tests/test_generation_pipeline.py`
- Modify: `backend/app/application/use_cases/generate_detail_design.py`

**Interfaces:**
- Consumes: `KnowledgeBaseService.retrieve_candidates(...)`, `ContextAssemblyService.assemble_candidates(...)`
- Produces: trace steps for retrieval query, dense search, sparse search, RRF fusion, and context assembly

### Task 3: Review Loop Trace Capture

**Files:**
- Modify: `backend/tests/test_generation_pipeline.py`
- Modify: `backend/app/application/use_cases/generate_detail_design.py`

**Interfaces:**
- Consumes: review-loop DD generation and review outputs
- Produces: trace steps for `detail_design_generation` and `detail_design_review`

### Task 4: Frontend Accordion Rendering

**Files:**
- Modify: `frontend/app/page.tsx`

**Interfaces:**
- Consumes: `payload.executionTrace.steps`
- Produces: `Pipeline Trace` accordion with summary view and raw JSON disclosure

### Task 5: Verification

**Files:**
- Modify: none

**Interfaces:**
- Consumes: updated backend/frontend code
- Produces: test evidence for targeted backend behavior and frontend compile/type safety where available
