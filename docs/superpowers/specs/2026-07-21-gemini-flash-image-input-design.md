# Gemini Flash Image Input Design

## Goal

Support images consistently across Basic Design, UI Design, Knowledge Base samples, repository input folders, and Common Input. Every accepted image must be processed by Gemini Flash before its extracted representation enters generation or indexing.

If Gemini Flash is not configured or extraction fails, the upload or reindex operation must fail clearly. The system must not silently skip an accepted image or replace it with placeholder content.

Supported images are PNG, JPEG, and WebP. PDF, Word, and Excel are outside this change.

## Architecture

### Shared extraction boundary

Introduce one application-facing image extraction service around GeminiVisionDesignExtractor. It will:

1. Validate extension, MIME type, and upload size.
2. Validate the Gemini API key and model configuration.
3. Send original image bytes to Gemini Flash.
4. Parse and normalize the JSON response for the requested context.
5. Raise typed, user-readable errors for configuration, provider, and response failures.

Callers select a context—Basic Design, UI Design, reviewed DD, or Common Input—but do not duplicate SDK or error-handling logic.

### Error contract

- Missing API key: reject with a configuration error.
- Unsupported image type: reject with a validation error.
- Gemini request failure: reject with an extraction error.
- Invalid or empty Gemini JSON: reject with an extraction error.
- Reindex with an unreadable image: mark reindex failed and expose the image path and safe failure summary.

Text inputs retain their current behavior.

## Data flows

### Basic Design and UI Design

The frontend retains the original selected File instead of converting images with file.text().

~~~text
Browser File
-> multipart upload
-> backend detects text or image
-> text: decode and save
-> image: Gemini Flash extraction
-> save normalized extraction as the project text document
-> return source type and extraction model metadata
~~~

GenerationService continues consuming textual basic-design and ui-design documents, so its downstream contract remains unchanged.

### Knowledge Base sample API

Change POST /admin/knowledge-base/samples from a string-only input to multipart:

- file: optional text or image file.
- content: optional raw text.
- Exactly one must be supplied.

Images go through Gemini Flash before KnowledgeBaseService.add_sample receives normalized text.

### Repository Knowledge Base input

InputReviewedDdLoader recursively discovers images under:

- INPUT/input/01_UI層/**
- INPUT/DD/**

This includes INPUT/input/01_UI層/images/.

An image is no longer discarded because Markdown has the same screen ID. Text and image evidence for the same screen are merged into one reviewed sample where possible.

### Common Input

CommonInputService recursively discovers supported images under INPUT/common/**. Each image becomes a normalized reference containing:

- source path and source type;
- extraction model;
- summary;
- visible rules, components, layout, or template signals.

Common input gains an additive imageReferences list. Image source paths participate in sourceFiles, and image bytes plus normalized extraction participate in versioning. Image references are included in prompt guidance.

Extraction results are cached by image content hash during the process so unchanged Common Input images do not call Gemini repeatedly. Failures are not cached as successes.

## Models

Image understanding uses GEMINI_LLM_MODEL, default gemini-2.5-flash.

Knowledge Base vector creation remains separate and uses GEMINI_EMBEDDING_MODEL, default gemini-embedding-001.

The sequence is:

~~~text
image
-> Gemini Flash structured text
-> chunking
-> Gemini Embedding
-> Qdrant and BM25
~~~

## API behavior

Existing project document routes remain unchanged. Successful responses add sourceType and extractionModel without removing existing fields.

Expected image errors:

- HTTP 400: unsupported type, oversized upload, or invalid multipart input.
- HTTP 503: Gemini is not configured.
- HTTP 502: Gemini request or response parsing failed.

The Knowledge Base sample route accepts multipart file or content and rejects both/neither.

## Frontend behavior

Maintain separate state for typed text and selected files for BD and UI Design.

- Text files may be previewed.
- Image files retain their original bytes and show filename/source type.
- A selected file takes precedence over typed text.
- Any failed upload stops generation and surfaces the backend message.

## Security

- Validate MIME type and extension together.
- Never use a client filename as a storage path.
- Store normalized extracted text as the project document.
- Enforce a conservative upload size limit.
- Never expose API keys or provider credentials in errors.

## Testing strategy

Implementation follows test-driven development.

Backend coverage:

1. BD and UI image uploads call the extractor and store normalized text.
2. Text uploads do not call the extractor.
3. Missing configuration and provider failures return the intended HTTP errors and save nothing.
4. Knowledge Base sample upload accepts images and indexes extracted text.
5. Ambiguous Knowledge Base sample input is rejected.
6. Loader recursively finds INPUT/input/01_UI層/images/.
7. Same-screen Markdown and image evidence are merged.
8. Nested INPUT/DD images remain supported.
9. Common Input discovers images, returns imageReferences, and uses content-hash caching.
10. Common Input and reindex failures identify the offending image safely.

Frontend and regression coverage:

1. Images retain the original File.
2. Typed text still creates text uploads.
3. Failed uploads stop the workflow and display the error.
4. Existing text generation, Markdown/CSV ingestion, embedding, and Qdrant tests pass.
5. Frontend lint, type checking, and production build pass.

## Compatibility

No database migration is required. Generation continues reading normalized text documents from the existing document store.

The Knowledge Base sample request encoding changes; external scripts must migrate to multipart. The repository frontend does not currently call this endpoint.

The common-input imageReferences field and upload response metadata are additive.

## Acceptance criteria

1. Image BD and UI uploads are processed by Gemini Flash and enter generation.
2. Image Knowledge Base uploads are processed before indexing.
3. Nested images under INPUT/input/01_UI層/** and INPUT/DD/** are processed.
4. Images under INPUT/common/** are processed and included in prompt guidance.
5. Missing configuration or extraction failure stops the affected operation clearly.
6. No accepted image is silently ignored.
7. Text-only workflows remain functional.
8. Focused tests and project validation pass.
