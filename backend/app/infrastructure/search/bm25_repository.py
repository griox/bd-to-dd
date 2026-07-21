"""Infrastructure adapter: BM25 local sparse keyword index.

Implements the SparseKeywordIndex port defined in
``app.domain.repositories.vector_store_repository``.

Design decisions:
- Uses ``rank_bm25.BM25Okapi`` (pure Python, no self-hosted model).
- Tokenizes with a multilingual-safe regex: splits on whitespace and
  punctuation, lowercases, drops empty tokens.
- Persists the full index to JSON after every upsert so it survives restarts.
- Metadata filtering is applied post-scoring (BM25 scores all docs, then
  filter eliminates non-matching candidates).
- Replaceable by SPLADE/miniCOIL later without changing application use cases —
  only this file and its wiring in deps.py would change.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import BM25_INDEX_PATH, BM25_TOP_K
from app.domain.entities.chunk import KnowledgeChunk
from app.domain.entities.retrieval import RetrievalCandidate


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[^\w\u3000-\u9fff]+", re.UNICODE)


class _FallbackBM25Okapi:
    def __init__(self, corpus: List[List[str]]) -> None:
        self._corpus = corpus
        self._doc_freqs = Counter()
        self._term_freqs: List[Counter] = []
        self._doc_lengths: List[int] = []

        for doc in corpus:
            term_counts = Counter(doc)
            self._term_freqs.append(term_counts)
            self._doc_lengths.append(len(doc))
            self._doc_freqs.update(term_counts.keys())

        self._doc_count = len(corpus)
        self._avgdl = (
            sum(self._doc_lengths) / self._doc_count if self._doc_count else 0.0
        )
        self._k1 = 1.5
        self._b = 0.75

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        scores: List[float] = []
        for term_counts, doc_len in zip(self._term_freqs, self._doc_lengths):
            score = 0.0
            for token in query_tokens:
                tf = term_counts.get(token, 0)
                if tf == 0:
                    continue
                df = self._doc_freqs.get(token, 0)
                idf = math.log(1 + ((self._doc_count - df + 0.5) / (df + 0.5)))
                denom = tf + self._k1 * (
                    1 - self._b + self._b * (doc_len / (self._avgdl or 1.0))
                )
                score += idf * ((tf * (self._k1 + 1)) / denom)
            scores.append(score)
        return scores


def _tokenize(text: str) -> List[str]:
    """Multilingual-safe tokenizer: split on non-word chars, lowercase.

    Handles ASCII, Japanese (CJK range included), and mixed technical text
    such as ``screen_id``, API names, and class names.
    For CJK text where whitespace splitting is insufficient, individual
    characters are retained as tokens.
    """
    tokens = []
    for part in _TOKEN_RE.split(text.lower()):
        part = part.strip()
        if part:
            tokens.append(part)
    return tokens


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _index_to_dict(
    chunk_ids: List[str],
    contents: List[str],
    metadatas: List[Dict[str, Any]],
    token_lists: List[List[str]],
) -> Dict[str, Any]:
    return {
        "chunk_ids": chunk_ids,
        "contents": contents,
        "metadatas": metadatas,
        "token_lists": token_lists,
    }


def _dict_to_index(data: Dict[str, Any]):
    return (
        data["chunk_ids"],
        data["contents"],
        data["metadatas"],
        data["token_lists"],
    )


# ---------------------------------------------------------------------------
# BM25Repository
# ---------------------------------------------------------------------------

class BM25Repository:
    """BM25 local sparse index implementing SparseKeywordIndex protocol.

    Application layer must depend on SparseKeywordIndex Protocol,
    not this class directly (except in dependency wiring / deps.py).
    """

    def __init__(
        self,
        index_path: str = BM25_INDEX_PATH,
        top_k: int = BM25_TOP_K,
    ) -> None:
        self._index_path = Path(index_path)
        self._top_k = top_k

        # In-memory state
        self._chunk_ids: List[str] = []
        self._contents: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._token_lists: List[List[str]] = []
        self._bm25 = None  # rank_bm25.BM25Okapi instance

        self._load_index()

    # ------------------------------------------------------------------
    # SparseKeywordIndex protocol
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all sparse documents from memory and persisted storage."""
        self._chunk_ids = []
        self._contents = []
        self._metadatas = []
        self._token_lists = []
        self._bm25 = None
        self._save_index()

    def upsert_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """Index chunks and persist to disk.

        Existing chunk IDs are updated in-place (idempotent upsert).
        """
        if not chunks:
            return

        # Build lookup for fast update
        id_to_pos = {cid: i for i, cid in enumerate(self._chunk_ids)}

        for chunk in chunks:
            tokens = _tokenize(chunk.content)
            meta = dict(chunk.metadata)
            if chunk.id in id_to_pos:
                pos = id_to_pos[chunk.id]
                self._contents[pos] = chunk.content
                self._metadatas[pos] = meta
                self._token_lists[pos] = tokens
            else:
                id_to_pos[chunk.id] = len(self._chunk_ids)
                self._chunk_ids.append(chunk.id)
                self._contents.append(chunk.content)
                self._metadatas.append(meta)
                self._token_lists.append(tokens)

        self._rebuild_bm25()
        self._save_index()

    def query_sparse(
        self,
        query: str,
        limit: int,
        filters: Dict[str, Any],
    ) -> List[RetrievalCandidate]:
        """BM25 keyword search with optional metadata post-filtering.

        Returns up to ``limit`` candidates sorted by descending BM25 score.
        Empty query → empty result.
        """
        if not query.strip() or self._bm25 is None or not self._chunk_ids:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Pair (index, score), apply metadata filter, sort desc
        ranked = sorted(
            (
                (i, float(scores[i]))
                for i in range(len(self._chunk_ids))
                if self._matches_filter(self._metadatas[i], filters)
            ),
            key=lambda x: x[1],
            reverse=True,
        )

        candidates = []
        for idx, score in ranked[:limit]:
            candidates.append(
                RetrievalCandidate(
                    chunk_id=self._chunk_ids[idx],
                    content=self._contents[idx],
                    metadata=self._metadatas[idx],
                    score=score,
                    source="sparse",
                )
            )
        return candidates

    def status(self) -> Dict[str, Any]:
        """Return provider metadata for the KB status endpoint."""
        return {
            "provider": "bm25",
            "indexPath": str(self._index_path),
            "chunkCount": len(self._chunk_ids),
            "indexLoaded": self._bm25 is not None,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _matches_filter(
        self, metadata: Dict[str, Any], filters: Dict[str, Any]
    ) -> bool:
        """Return True if all filter key=value conditions are satisfied."""
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True

    def _rebuild_bm25(self) -> None:
        """Reconstruct BM25Okapi from current token lists."""
        try:
            from rank_bm25 import BM25Okapi  # noqa: PLC0415
        except ImportError:
            BM25Okapi = _FallbackBM25Okapi

        if self._token_lists:
            self._bm25 = BM25Okapi(self._token_lists)
        else:
            self._bm25 = None

    def _save_index(self) -> None:
        """Persist the current index to disk as JSON."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        data = _index_to_dict(
            self._chunk_ids,
            self._contents,
            self._metadatas,
            self._token_lists,
        )
        self._index_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def _load_index(self) -> None:
        """Load index from disk if it exists; otherwise start empty."""
        if not self._index_path.exists():
            return
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
            (
                self._chunk_ids,
                self._contents,
                self._metadatas,
                self._token_lists,
            ) = _dict_to_index(data)
            if self._token_lists:
                self._rebuild_bm25()
        except Exception:
            # Corrupt index → start fresh
            self._chunk_ids = []
            self._contents = []
            self._metadatas = []
            self._token_lists = []
            self._bm25 = None
