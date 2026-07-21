# BD-to-DD Toolkit

## Team Demo

`docker-compose.yml` is the only compose file the team needs for demo usage:

- Backend runs without `--reload`
- Frontend runs with `next start`
- Uploaded documents and runtime artifacts are stored in a dedicated Docker volume
- `INPUT` is mounted read-only

Prepare environment variables:

```bash
cp backend/.env.example backend/.env
```

Set these values in `backend/.env`:

- `GEMINI_LLM_API_KEY`
- `GEMINI_EMBEDDING_API_KEY`

Start the stack:

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/v1`
- Qdrant: `http://localhost:6333`

## Knowledge Base Notes

- Qdrant data persists in the `qdrant_data` Docker volume.
- Backend runtime files, uploaded documents, SQLite DB, BM25 index, and exported artifacts persist in the `backend_runtime` Docker volume.
- On a fresh machine, click `Reindex KB` once after startup to rebuild the KB from `INPUT`.
- To ship a prebuilt KB, restore the Docker volumes/snapshots instead of relying on the image alone.
