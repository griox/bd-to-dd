# Generation Execution Trace Design

## Goal

Expose backend pipeline outputs step-by-step so users can review what the system produced during analysis, retrieval, fusion, detail design generation, and auto review directly in the frontend.

## Scope

- Keep the existing `pipeline.stages` summary for backward compatibility.
- Add a new `executionTrace.steps` array to generation results.
- Capture human-readable summaries plus raw JSON/output for key steps.
- Render the trace in the current frontend page as an accordion list.

## Backend Design

Each trace step will contain:

- `key`: stable programmatic id
- `label`: user-facing step name
- `status`: `completed` or `failed`
- `summary`: short human-readable summary
- `preview`: compact structured output for UI
- `raw`: raw JSON/result for debugging

Initial traced steps:

1. `basic_design_analytics`
2. `build_retrieval_query`
3. `dense_search`
4. `sparse_search`
5. `rrf_fusion`
6. `context_assembly`
7. `design_analysis_generation`
8. `detail_design_generation`
9. `detail_design_review`

`GenerationService` will build trace entries during analysis and review-loop execution, then store them in the generation result payload.

## Frontend Design

Add a new `Pipeline Trace` section on the existing page:

- one accordion item per step
- always show label, status, summary
- show a readable `preview` block by default
- show `raw` JSON inside an expandable details block

The UI will keep polling existing generation endpoints and render the latest trace state as the backend progresses.

## Constraints

- Do not break existing generation status polling.
- Do not remove or rename `pipeline.stages`.
- Keep trace payloads compact by truncating large candidate/raw lists to small previews.
- Avoid storing full embedding vectors in trace output.

## Testing

- Add backend tests proving `executionTrace.steps` is present and contains retrieval/generation steps.
- Add backend tests proving review-loop output appends detail design and review trace steps.
- Run targeted frontend/type checks if available, otherwise validate with project tests/build that cover `frontend/app/page.tsx`.
