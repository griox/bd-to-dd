# DD Markdown Table Renderer Design

## Goal

Keep the current JSON-based detail design pipeline for generation, review, and tracing, but render the exported Markdown artifact in a table-based format that visually matches the sample documents in `INPUT/DD` and `INPUT/common/templates`.

## Current Problem

The current pipeline asks Gemini to return JSON with `screen`, `api`, and `batch` keys. That is good for machine processing, but the exported Markdown artifact is currently a simple bullet-list dump. As a result:

- the exported `.md` does not resemble the sample DD documents;
- the output is difficult for business users and designers to review;
- the project loses one of its strongest references: the document structure already defined in the sample templates.

## Decision

Use a two-layer output model:

1. **Internal representation stays JSON**
   - `detailDesign` remains structured data for review-loop, checklist validation, `executionTrace`, and persistence.
2. **External artifact becomes rendered Markdown**
   - add a renderer layer that converts structured `detailDesign` data into Markdown tables and section blocks aligned with the sample templates.

This keeps the pipeline stable while improving the human-facing output.

## Rendering Strategy

### 1. Keep generation schema structured

Do not switch the LLM output to free-form Markdown. Instead, make the JSON payload richer and more renderer-friendly where needed.

Examples:

- screen sections should support table-like rows such as parameter definitions, component lists, event definitions, API integration entries, and state definitions;
- API and batch sections should also support repeated row structures instead of one long string per section.

The renderer will accept both:

- the current flat string-based JSON
- the richer future structured JSON

This allows backward compatibility during migration.

### 2. Add a dedicated Markdown renderer

Create a focused renderer module responsible only for converting `detailDesign` JSON to a human-readable Markdown artifact.

Renderer responsibilities:

- choose the correct template style by module type (`screen`, `api`, `batch`);
- render headings in the same style as sample docs;
- render repeated structured content as Markdown tables;
- fall back gracefully when only free-text strings are available.

### 3. Use template-aligned section mapping

For screen output, map current sections such as:

- `01_UI_Design`
- `02_Components`
- `03_Data_Models`
- `04_API_Integration`
- `05_Business_Logic`
- `06_State_Management`

into a document layout closer to the sample screen DD:

- screen overview
- composable design
- parameter table
- component table
- event definition table
- state management table
- API integration table
- notes / assumptions

The first implementation does not need to reproduce every Japanese sample field exactly, but it must switch from raw JSON/bullets to stable Markdown tables with clear columns.

## Scope

### In scope

- improve export `.md` output
- optionally improve frontend Markdown preview if it uses the exported content later
- add renderer tests
- preserve existing `.json` artifact output

### Out of scope

- replacing the internal JSON contract with Markdown
- redesigning the auto-review loop
- changing Qdrant/BM25 storage
- reproducing every sample document variant exactly in the first pass

## Compatibility Rules

- existing generation result schema must continue to work
- `review_detail_design` and `executionTrace` must keep using structured JSON
- renderer must not require reindexing the knowledge base
- renderer must tolerate missing optional sections

## Output Requirements

The new Markdown artifact must:

- look like a document, not a debug dump
- use Markdown tables where the content is tabular
- preserve headings and section order consistently
- be understandable to a human reviewer without reading the JSON artifact

## Suggested Implementation Units

- a new renderer module for DD markdown generation
- small helpers for table rendering and value normalization
- export repository updated to call the renderer instead of `_to_markdown()`
- targeted tests for screen-heavy output and fallback output

## Testing

- verify exported Markdown contains table syntax (`| ... |`)
- verify component, event, state, and API sections render as tables
- verify string-only legacy data still renders a readable fallback document
- verify JSON artifact output remains unchanged
