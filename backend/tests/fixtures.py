from app.domain.entities.retrieval import RetrievalCandidate


def make_candidate(chunk_id, content, score, source, metadata=None):
    return RetrievalCandidate(
        chunk_id=chunk_id,
        content=content,
        metadata=metadata or {},
        score=score,
        source=source,
    )


class FakeEmbedder:
    def describe(self):
        return {"provider": "fake", "configured": True}

    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]


class FakeDenseStore:
    def __init__(self, results=None, parents=None, available=True):
        self.results = results or []
        self.parents = parents or {}
        self.available = available
        self.upserted = []
        self.last_filters = None

    def is_available(self):
        return self.available

    def status(self):
        return {
            "provider": "fake-qdrant",
            "available": self.available,
            "pointCount": len(self.results),
        }

    def query_dense(self, query_vector, limit, filters):
        self.last_filters = filters
        return self.results[:limit]

    def upsert_chunks(self, chunks):
        self.upserted = chunks
        self.results = list(chunks)

    def get_by_chunk_ids(self, chunk_ids):
        return [self.parents[cid] for cid in chunk_ids if cid in self.parents]


class FakeSparseIndex:
    def __init__(self, results=None):
        self.results = results or []
        self.upserted = []
        self.last_filters = None

    def status(self):
        return {"provider": "fake-bm25", "chunkCount": len(self.results)}

    def query_sparse(self, query, limit, filters):
        self.last_filters = filters
        return self.results[:limit]

    def upsert_chunks(self, chunks):
        self.upserted = chunks
