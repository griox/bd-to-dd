# Similar Input Reference Design

## Goal

During Basic Design Analytics, the system should look at `INPUT/input` as demo input examples, find the most similar example to the user's uploaded input, and pass it to the LLM as reference context only.

## Approved Behavior

- User uploaded Basic Design and UI Design remain the authoritative input.
- `INPUT/input` is not inserted into the knowledge base.
- Reviewed DD samples in `INPUT/DD` remain the only source for KB indexing and "Get Sample Design".
- Similar input examples are injected only into the Basic Design Analytics prompt under a clearly labeled reference section.
- If a selected example contains images, Gemini Flash vision extraction is required. Missing or broken Gemini vision configuration must raise an explicit error.
- If no similar input example is found, the pipeline continues with an empty reference section.

## Architecture

Add an application service that builds a lightweight catalog from `INPUT/input`. The catalog reads markdown and CSV text plus image filenames for cheap matching. It ranks examples with deterministic token overlap, selects the top examples, then calls Gemini Flash only for images belonging to selected examples.

GenerationService calls this service before Basic Design Analytics. It sends the formatted reference text as `input_reference_examples`, adds selected reference metadata to `resourcesUsed`, and keeps `basic_design` / `ui_design` unchanged.

## Data Flow

1. User uploads `.md`, optional UI images, and optional `.csv`.
2. Backend saves the user input as project documents.
3. Analysis phase loads common input.
4. Analysis phase finds similar examples from `INPUT/input`.
5. Selected example images are extracted by Gemini Flash.
6. Basic Design Analytics receives user input, common input, and a separate reference examples section.
7. KB retrieval still runs against reviewed DD only.

## Error Handling

- Missing `INPUT/input` returns no references.
- Selected image without a configured vision extractor raises `RuntimeError`.
- Vision extraction failure includes the image path in the error.

## Testing

- Unit tests cover matching, no-match behavior, selected-image-only Gemini calls, and missing extractor errors.
- Pipeline tests verify Basic Design Analytics receives reference examples and user input is not replaced.
