import copy
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from app.application.services.chunking_service import ChunkingService
from app.application.services.context_assembly_service import ContextAssemblyService
from app.application.services.hybrid_search_service import HybridSearchService
from app.application.services.rerank_service import RerankService
from app.domain.repositories.vector_store_repository import (
    DenseEmbeddingService,
    DenseVectorStore,
    EmbeddingDescriptor,
    RagSampleLoader,
    SparseKeywordIndex,
    VectorStore,
)
from app.application.services.retrieval_query_service import (
    build_retrieval_query,
    build_retrieval_request,
)
from app.core.config import (
    RETRIEVAL_MAX_TOP_K,
    RETRIEVAL_MIN_TOP_K,
    RETRIEVAL_SCORE_GAP,
)
from app.domain.entities.sample_design import ReviewedDetailDesignSample
from app.infrastructure.embedding.gemini_embedder import GeminiEmbeddingService
from app.infrastructure.persistence.postgres.seed_loader import JsonSeedSampleLoader
from app.infrastructure.search.bm25_repository import BM25Repository
from app.infrastructure.vectorstore.qdrant_repository import QdrantVectorStore


class KnowledgeBaseService:
    def __init__(
        self,
        sample_loader: Optional[RagSampleLoader] = None,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingDescriptor] = None,
        dense_vector_store: Optional[DenseVectorStore] = None,
        dense_embedding_service: Optional[DenseEmbeddingService] = None,
        chunking_service: Optional[ChunkingService] = None,
        sparse_keyword_index: Optional[SparseKeywordIndex] = None,
        auto_seed: bool = True,
    ) -> None:
        self.sample_loader = sample_loader or JsonSeedSampleLoader()
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.dense_vector_store = dense_vector_store or QdrantVectorStore()
        self.dense_embedding_service = dense_embedding_service or GeminiEmbeddingService()
        self.chunking_service = chunking_service or ChunkingService()
        self.sparse_keyword_index = sparse_keyword_index or BM25Repository()
        self.hybrid_search_service = HybridSearchService()
        self.rerank_service = RerankService()
        self.context_assembly_service = ContextAssemblyService()
        self.top_k = RETRIEVAL_MAX_TOP_K
        self._progress_lock = Lock()
        self._progress = self._empty_progress()
        if auto_seed:
            try:
                self.seed_default_samples()
            except Exception as exc:
                code, summary, output = self._progress_error_payload(
                    "Automatic KB seed failed",
                    exc,
                )
                self._fail_progress(code, summary, output)

    def add_sample(self, content: str) -> Dict[str, Any]:
        if self._uses_dense_store():
            if not self.dense_vector_store.is_available():
                return {"status": "unavailable"}
            sample_id = f"uploaded-{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"
            sample = ReviewedDetailDesignSample(
                id=sample_id,
                content=content,
                metadata={
                    "module_type": "screen",
                    "approval_status": "reviewed",
                    "review_status": "reviewed",
                    "quality_score": 1.0,
                    "reused_count": 0,
                    "source_type": "upload",
                },
            )
            chunks = self.chunking_service.chunk_sample(sample)
            embeddings = self.dense_embedding_service.embed_documents(
                [chunk.content for chunk in chunks]
            )
            if len(embeddings) != len(chunks):
                raise RuntimeError(
                    "Embedding count mismatch while indexing uploaded sample."
                )
            embedded_chunks = [
                replace(
                    chunk,
                    metadata={**dict(chunk.metadata), "embedding": embedding},
                )
                for chunk, embedding in zip(chunks, embeddings)
            ]
            self.dense_vector_store.upsert_chunks(embedded_chunks)
            if self.sparse_keyword_index is not None:
                self.sparse_keyword_index.upsert_chunks(
                    [
                        replace(
                            chunk,
                            metadata={
                                key: value
                                for key, value in dict(chunk.metadata).items()
                                if key != "embedding"
                            },
                        )
                        for chunk in embedded_chunks
                    ]
                )
            return {
                "status": "indexed",
                "sampleId": sample_id,
                "chunkCount": len(embedded_chunks),
            }
        if self.vector_store is None or not self.vector_store.is_available():
            return {"status": "unavailable"}
        self.vector_store.add_document(content, {"type": "sample"})
        return {"status": "indexed"}

    def seed_default_samples(self) -> Dict[str, Any]:
        if self._uses_dense_store():
            dense_status = self.dense_vector_store.status()
            point_count = int(dense_status.get("pointCount", 0) or 0)
            if point_count > 0:
                return {
                    "status": "already_seeded",
                    "seeded": point_count,
                    "embedding": self.dense_embedding_service.describe(),
                    "vectorDb": dense_status,
                }
            return self._seed_dense_samples()

        if not self.vector_store.is_available():
            return self._seed_status("unavailable", 0)

        samples = self.sample_loader.load()
        if not samples:
            return self._seed_status("missing_seed_file", 0)

        self.vector_store.upsert_samples(samples)
        return {
            **self._seed_status("seeded", len(samples)),
            "reviewedDetailDesigns": [sample.id for sample in samples],
        }

    def reindex(self) -> Dict[str, Any]:
        """Explicitly rebuild the knowledge base from reviewed DD samples."""
        self._ensure_progress_runtime()
        try:
            if not self._uses_dense_store():
                raise RuntimeError(
                    "Explicit reindex requires configured dense vector and embedding services."
                )
            result = self._seed_dense_samples(replace_existing=True)
            if result.get("status") == "unavailable":
                raise RuntimeError("Qdrant is unavailable; knowledge base was not reindexed.")
            if result.get("status") == "missing_seed_file":
                raise RuntimeError(
                    "No reviewed DD samples were found in INPUT/DD; knowledge base was not reindexed."
                )
            return result
        except Exception as exc:
            self._fail_progress(*self._progress_error_payload("Reindex failed", exc))
            raise

    def get_status(self) -> Dict[str, Any]:
        self._ensure_progress_runtime()
        seed_samples = self.sample_loader.load()
        if self._uses_dense_store():
            vector_status = self.dense_vector_store.status()
            sparse_status = (
                self.sparse_keyword_index.status()
                if self.sparse_keyword_index is not None
                else None
            )
            point_count = int(vector_status.get("pointCount", 0) or 0)
            base_status = {
                "reviewedDetailDesigns": {
                    "source": self.sample_loader.source(),
                    "seedSamples": len(seed_samples),
                    "sampleIds": [sample.id for sample in seed_samples],
                },
                "embedding": self.dense_embedding_service.describe(),
                "vectorDb": vector_status,
                "dense": vector_status,
                "chunkCount": point_count,
            }
            if sparse_status is not None:
                base_status["sparseIndex"] = sparse_status
                base_status["sparse"] = sparse_status

            if not self.dense_vector_store.is_available():
                return {
                    **base_status,
                    "progress": self.get_progress(),
                    "status": "unavailable",
                    "sampleCount": 0,
                }
            return {
                **base_status,
                "progress": self.get_progress(),
                "status": "ready",
                "sampleCount": point_count,
            }

        base_status = {
            "reviewedDetailDesigns": {
                "source": self.sample_loader.source(),
                "seedSamples": len(seed_samples),
                "sampleIds": [sample.id for sample in seed_samples],
            },
            "embedding": self.embedding_service.describe(),
            "vectorDb": self.vector_store.status(),
        }
        if not self.vector_store.is_available():
            return {
                **base_status,
                "progress": self.get_progress(),
                "status": "unavailable",
                "sampleCount": 0,
            }
        return {
            **base_status,
            "progress": self.get_progress(),
            "status": "ready",
            "sampleCount": self.vector_store.count(),
        }

    def get_progress(self) -> Dict[str, Any]:
        self._ensure_progress_runtime()
        with self._progress_lock:
            return copy.deepcopy(self._progress)

    def queue_reindex(self) -> Dict[str, Any]:
        self._ensure_progress_runtime()
        with self._progress_lock:
            if self._progress.get("status") in {"queued", "running"}:
                return copy.deepcopy(self._progress)
            self._progress = self._empty_progress(
                operation="reindex_reviewed_dd",
                status="queued",
                summary="Reindex request queued.",
            )
            return copy.deepcopy(self._progress)

    def retrieve_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sparse_query: Optional[str] = None,
    ) -> List[str]:
        if not query.strip():
            return []

        if self._uses_dense_store():
            assembled = self.retrieve_debug_bundle(
                query,
                filters=filters,
                sparse_query=sparse_query,
            )["assembledContext"]
            return [candidate.content for candidate in assembled.references]

        if self.vector_store is None or not self.vector_store.is_available():
            return []
        return self.vector_store.query(query[:500], limit=2)

    def retrieve_candidates(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sparse_query: Optional[str] = None,
    ) -> List:
        return self.retrieve_debug_bundle(
            query,
            filters=filters,
            sparse_query=sparse_query,
        )["selectedCandidates"]

    def retrieve_debug_bundle(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sparse_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        filters = filters or {}
        dense_results = []
        if self.dense_vector_store.is_available():
            query_vector = self.dense_embedding_service.embed_query(query[:500])
            dense_results = self.dense_vector_store.query_dense(
                query_vector=query_vector,
                limit=20,
                filters=filters,
            )
        sparse_results = (
            self.sparse_keyword_index.query_sparse(
                (sparse_query or query)[:500],
                limit=20,
                filters=filters,
            )
            if self.sparse_keyword_index is not None
            else []
            )
        fused = self.hybrid_search_service.fuse(dense_results, sparse_results, limit=20)
        reranked = self.rerank_service.rerank(query, fused, limit=RETRIEVAL_MAX_TOP_K)
        selected = self.rerank_service.select_adaptive_top_k(
            reranked,
            min_limit=RETRIEVAL_MIN_TOP_K,
            max_limit=RETRIEVAL_MAX_TOP_K,
            score_gap=RETRIEVAL_SCORE_GAP,
        )
        assembled = self.context_assembly_service.assemble_candidates(
            selected,
            self.dense_vector_store,
        )
        return {
            "denseResults": dense_results,
            "sparseResults": sparse_results,
            "fusedResults": fused,
            "rerankedResults": reranked,
            "selectedCandidates": selected,
            "assembledContext": assembled,
        }

    def _seed_status(self, status: str, count: int) -> Dict[str, Any]:
        return {
            "status": status,
            "seeded": count,
            "embedding": self.embedding_service.describe(),
        }

    def _uses_dense_store(self) -> bool:
        return bool(self.dense_vector_store and self.dense_embedding_service)

    def _seed_dense_samples(self, replace_existing: bool = False) -> Dict[str, Any]:
        self._ensure_progress_runtime()
        self._start_progress(
            operation="reindex_reviewed_dd",
            summary="Preparing reviewed DD ingestion pipeline.",
        )
        if not self.dense_vector_store.is_available():
            result = {
                "status": "unavailable",
                "seeded": 0,
                "embedding": self.dense_embedding_service.describe(),
                "vectorDb": self.dense_vector_store.status(),
            }
            self._fail_progress(
                "qdrant_unavailable",
                "Qdrant is unavailable, cannot start dense ingestion.",
                result,
            )
            return result

        samples = self.sample_loader.load()
        self._append_progress_step(
            key="load_samples",
            label="Load reviewed DD samples",
            status="completed",
            message=f"Loaded {len(samples)} reviewed DD samples from source.",
            output={
                "source": self.sample_loader.source(),
                "sampleCount": len(samples),
                "sampleIds": [sample.id for sample in samples[:8]],
            },
        )
        if not samples:
            result = {
                "status": "missing_seed_file",
                "seeded": 0,
                "embedding": self.dense_embedding_service.describe(),
                "vectorDb": self.dense_vector_store.status(),
            }
            self._fail_progress(
                "missing_seed_file",
                "No reviewed DD samples were found for ingestion.",
                result,
            )
            return result

        self._set_progress_state(
            status="running",
            current_step="chunking",
            summary="Chunking reviewed DD samples.",
        )
        chunks = self.chunking_service.chunk_samples(samples)
        self._append_progress_step(
            key="chunking",
            label="Chunk reviewed DD",
            status="completed",
            message=f"Created {len(chunks)} chunks from {len(samples)} samples.",
            output={
                "chunkCount": len(chunks),
                "preview": [
                    {
                        "chunkId": chunk.id,
                        "parentChunkId": chunk.parent_chunk_id,
                        "sectionPath": list(chunk.section_path),
                        "isLeaf": chunk.is_leaf,
                    }
                    for chunk in chunks[:5]
                ],
            },
        )

        self._set_progress_state(
            status="running",
            current_step="embedding",
            summary="Embedding chunk content with Gemini.",
        )
        texts = [chunk.content for chunk in chunks]
        embeddings = self.dense_embedding_service.embed_documents(texts)
        if len(embeddings) != len(chunks):
            self._fail_progress(
                "embedding_mismatch",
                "Embedding count mismatch detected.",
                {
                    "expectedChunks": len(chunks),
                    "actualEmbeddings": len(embeddings),
                },
            )
            raise RuntimeError(
                "Embedding count mismatch: "
                f"expected {len(chunks)}, got {len(embeddings)}"
            )
        self._append_progress_step(
            key="embedding",
            label="Embed chunks",
            status="completed",
            message=f"Generated {len(embeddings)} embedding vectors.",
            output={
                "embeddingCount": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0,
                "preview": [
                    {
                        "chunkId": chunk.id,
                        "vectorDimensions": len(embedding),
                        "vectorPreview": embedding[:5],
                    }
                    for chunk, embedding in list(zip(chunks, embeddings))[:3]
                ],
            },
        )

        self._set_progress_state(
            status="running",
            current_step="metadata",
            summary="Attaching embedding metadata to chunks.",
        )
        embedded_chunks = [
            replace(
                chunk,
                metadata={
                    **dict(chunk.metadata),
                    "embedding": embedding,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        self._append_progress_step(
            key="metadata",
            label="Attach metadata",
            status="completed",
            message="Attached embedding vectors into chunk metadata for dense storage.",
            output={
                "chunkCount": len(embedded_chunks),
                "preview": [
                    {
                        "chunkId": chunk.id,
                        "metadataKeys": sorted(dict(chunk.metadata).keys())[:12],
                        "hasEmbedding": "embedding" in chunk.metadata,
                    }
                    for chunk in embedded_chunks[:5]
                ],
            },
        )

        if replace_existing:
            self._set_progress_state(
                status="running",
                current_step="clear_indexes",
                summary="Clearing existing dense and sparse knowledge indexes.",
            )
            self.dense_vector_store.clear()
            if self.sparse_keyword_index is not None:
                self.sparse_keyword_index.clear()
            self._append_progress_step(
                key="clear_indexes",
                label="Clear existing knowledge indexes",
                status="completed",
                message="Removed all existing dense and sparse KB entries.",
                output={"denseCleared": True, "sparseCleared": self.sparse_keyword_index is not None},
            )

        self._set_progress_state(
            status="running",
            current_step="qdrant_upsert",
            summary="Upserting embedded chunks into Qdrant.",
        )
        self.dense_vector_store.upsert_chunks(embedded_chunks)
        dense_status = self.dense_vector_store.status()
        self._append_progress_step(
            key="qdrant_upsert",
            label="Upsert to Qdrant",
            status="completed",
            message=f"Stored {len(embedded_chunks)} chunks in Qdrant.",
            output={
                "collection": dense_status.get("collection"),
                "pointCount": dense_status.get("pointCount"),
                "indexedChunks": len(embedded_chunks),
            },
        )

        bm25_chunk_count = 0
        if self.sparse_keyword_index is not None:
            self._set_progress_state(
                status="running",
                current_step="bm25_index",
                summary="Preparing sparse BM25 index.",
            )
            bm25_chunks = [
                replace(
                    chunk,
                    metadata={
                        k: v for k, v in dict(chunk.metadata).items()
                        if k != "embedding"
                    },
                )
                for chunk in embedded_chunks
            ]
            self.sparse_keyword_index.upsert_chunks(bm25_chunks)
            bm25_chunk_count = len(bm25_chunks)
            sparse_status = self.sparse_keyword_index.status()
            self._append_progress_step(
                key="bm25_index",
                label="Build BM25 sparse index",
                status="completed",
                message=f"Indexed {bm25_chunk_count} chunks for sparse retrieval.",
                output={
                    "indexedChunks": bm25_chunk_count,
                    "indexStatus": sparse_status,
                    "preview": [
                        {
                            "chunkId": chunk.id,
                            "metadataKeys": sorted(dict(chunk.metadata).keys())[:12],
                            "hasEmbedding": "embedding" in chunk.metadata,
                        }
                        for chunk in bm25_chunks[:5]
                    ],
                },
            )

        result: Dict[str, Any] = {
            "status": "seeded",
            "seeded": len(samples),
            "chunkCount": len(embedded_chunks),
            "reviewedDetailDesigns": [sample.id for sample in samples],
            "embedding": self.dense_embedding_service.describe(),
            "vectorDb": self.dense_vector_store.status(),
        }
        if self.sparse_keyword_index is not None:
            result["sparseIndex"] = {
                **self.sparse_keyword_index.status(),
                "indexedChunks": bm25_chunk_count,
            }
            result["sparse"] = result["sparseIndex"]
        result["dense"] = result["vectorDb"]
        result["sampleCount"] = len(samples)
        self._complete_progress(
            "Reindex completed successfully.",
            {
                "seeded": len(samples),
                "chunkCount": len(embedded_chunks),
                "sampleIds": [sample.id for sample in samples[:8]],
                "dense": result["dense"],
                "sparse": result.get("sparse"),
            },
        )
        return result

    def ingest_generated_reviewed_dd(
        self,
        project_id: str,
        job_id: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._ensure_progress_runtime()
        try:
            self._start_progress(
                operation="ingest_generated_reviewed_dd",
                summary="Preparing approved detail design for KB ingestion.",
            )
            content = {
                "id": f"reviewed-{project_id}-{job_id}",
                "detailDesign": result.get("detailDesign", {}),
                "metadata": {
                    "module_type": "generated",
                    "approval_status": "reviewed",
                    "quality_score": 1.0,
                    "tags": ["generated", "designer-approved"],
                },
            }
            raw_sample = {
                "id": content["id"],
                "metadata": content["metadata"],
                "content": json.dumps(content, ensure_ascii=False)
            }
            if hasattr(self.sample_loader, "append"):
                self.sample_loader.append(raw_sample)

            sample = ReviewedDetailDesignSample(
                id=content["id"],
                content=json.dumps(content),
                metadata=content["metadata"],
            )
            self._append_progress_step(
                key="build_generated_sample",
                label="Build reviewed DD sample",
                status="completed",
                message="Wrapped approved detail design into a reviewed DD sample.",
                output={
                    "sampleId": sample.id,
                    "metadata": sample.metadata,
                    "projectId": project_id,
                    "jobId": job_id,
                },
            )
            self._set_progress_state(
                status="running",
                current_step="chunking",
                summary="Chunking generated reviewed DD.",
            )
            chunks = self.chunking_service.chunk_samples([sample])
            self._append_progress_step(
                key="chunking",
                label="Chunk generated sample",
                status="completed",
                message=f"Created {len(chunks)} chunks from approved detail design.",
                output={
                    "chunkCount": len(chunks),
                    "preview": [
                        {
                            "chunkId": chunk.id,
                            "sectionPath": list(chunk.section_path),
                            "isLeaf": chunk.is_leaf,
                        }
                        for chunk in chunks[:5]
                    ],
                },
            )
            self._set_progress_state(
                status="running",
                current_step="embedding",
                summary="Embedding generated detail design chunks.",
            )
            embeddings = self.dense_embedding_service.embed_documents(
                [chunk.content for chunk in chunks]
            )
            self._append_progress_step(
                key="embedding",
                label="Embed generated chunks",
                status="completed",
                message=f"Generated {len(embeddings)} embedding vectors for approved DD.",
                output={
                    "embeddingCount": len(embeddings),
                    "dimensions": len(embeddings[0]) if embeddings else 0,
                },
            )
            self._set_progress_state(
                status="running",
                current_step="metadata",
                summary="Attaching embeddings to generated DD chunks.",
            )
            embedded_chunks = [
                replace(chunk, metadata={**dict(chunk.metadata), "embedding": embedding})
                for chunk, embedding in zip(chunks, embeddings)
            ]
            self._append_progress_step(
                key="metadata",
                label="Attach metadata",
                status="completed",
                message="Attached embedding vectors to generated DD chunks.",
                output={
                    "chunkCount": len(embedded_chunks),
                    "preview": [
                        {
                            "chunkId": chunk.id,
                            "metadataKeys": sorted(dict(chunk.metadata).keys())[:12],
                            "hasEmbedding": "embedding" in chunk.metadata,
                        }
                        for chunk in embedded_chunks[:5]
                    ],
                },
            )
            self._set_progress_state(
                status="running",
                current_step="qdrant_upsert",
                summary="Upserting generated DD chunks into Qdrant.",
            )
            self.dense_vector_store.upsert_chunks(embedded_chunks)
            self._append_progress_step(
                key="qdrant_upsert",
                label="Upsert to Qdrant",
                status="completed",
                message=f"Stored {len(embedded_chunks)} generated chunks in Qdrant.",
                output=self.dense_vector_store.status(),
            )
            if self.sparse_keyword_index is not None:
                self._set_progress_state(
                    status="running",
                    current_step="bm25_index",
                    summary="Updating sparse BM25 index for generated DD.",
                )
                bm25_chunks = [
                    replace(
                        chunk,
                        metadata={
                            k: v for k, v in dict(chunk.metadata).items() if k != "embedding"
                        },
                    )
                    for chunk in embedded_chunks
                ]
                self.sparse_keyword_index.upsert_chunks(
                    bm25_chunks
                )
                self._append_progress_step(
                    key="bm25_index",
                    label="Build BM25 sparse index",
                    status="completed",
                    message=f"Indexed {len(bm25_chunks)} generated chunks for sparse retrieval.",
                    output=self.sparse_keyword_index.status(),
                )
            result_payload = {
                "status": "seeded",
                "chunkCount": len(embedded_chunks),
                "sampleId": sample.id,
            }
            self._complete_progress(
                "Generated detail design has been ingested into the knowledge base.",
                result_payload,
            )
            return result_payload
        except Exception as exc:
            error_code, summary, result_preview = self._progress_error_payload(
                "Generated DD ingestion failed",
                exc,
            )
            result_preview["projectId"] = project_id
            result_preview["jobId"] = job_id
            self._fail_progress(error_code, summary, result_preview)
            raise

    def _ensure_progress_runtime(self) -> None:
        if not hasattr(self, "_progress_lock"):
            self._progress_lock = Lock()
        if not hasattr(self, "_progress"):
            self._progress = self._empty_progress()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _empty_progress(
        self,
        operation: str = "idle",
        status: str = "idle",
        summary: str = "Knowledge base pipeline is idle.",
    ) -> Dict[str, Any]:
        return {
            "operation": operation,
            "status": status,
            "summary": summary,
            "currentStep": None,
            "startedAt": None,
            "updatedAt": self._now(),
            "completedAt": None,
            "steps": [],
            "resultPreview": None,
            "error": None,
        }

    def _start_progress(self, operation: str, summary: str) -> None:
        with self._progress_lock:
            queued = self._progress.get("status") == "queued" and self._progress.get("operation") == operation
            self._progress = self._empty_progress(
                operation=operation,
                status="running",
                summary=summary,
            )
            self._progress["startedAt"] = self._now()
            if queued:
                self._progress["summary"] = summary

    def _set_progress_state(
        self,
        *,
        status: str,
        current_step: Optional[str],
        summary: str,
    ) -> None:
        with self._progress_lock:
            self._progress["status"] = status
            self._progress["currentStep"] = current_step
            self._progress["summary"] = summary
            self._progress["updatedAt"] = self._now()

    def _append_progress_step(
        self,
        *,
        key: str,
        label: str,
        status: str,
        message: str,
        output: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._progress_lock:
            self._progress["steps"].append(
                {
                    "key": key,
                    "label": label,
                    "status": status,
                    "message": message,
                    "output": output,
                    "timestamp": self._now(),
                }
            )
            self._progress["updatedAt"] = self._now()

    def _complete_progress(self, summary: str, result_preview: Dict[str, Any]) -> None:
        with self._progress_lock:
            self._progress["status"] = "completed"
            self._progress["summary"] = summary
            self._progress["currentStep"] = None
            self._progress["completedAt"] = self._now()
            self._progress["updatedAt"] = self._now()
            self._progress["resultPreview"] = result_preview
            self._progress["error"] = None

    def _fail_progress(
        self,
        error_code: str,
        summary: str,
        result_preview: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._progress_lock:
            self._progress["status"] = "failed"
            self._progress["summary"] = summary
            self._progress["currentStep"] = error_code
            self._progress["completedAt"] = self._now()
            self._progress["updatedAt"] = self._now()
            self._progress["resultPreview"] = result_preview
            self._progress["error"] = {"code": error_code, "message": summary}

    def _progress_error_payload(
        self,
        prefix: str,
        exc: Exception,
    ) -> tuple[str, str, Dict[str, Any]]:
        message = str(exc)
        if "at most 100 requests can be in one batch" in message:
            return (
                "embedding_batch_limit",
                (
                    f"{prefix}: Gemini embedding batch exceeded API limit. "
                    "The request was split too large before reaching the embedding API."
                ),
                {"error": message, "recommendedBatchSize": 100},
            )
        return (
            "unexpected_error",
            f"{prefix}: {message}",
            {"error": message},
        )


def load_seed_samples() -> List[Dict[str, Any]]:
    return [
        {
            "id": sample.id,
            "content": sample.content,
            "metadata": sample.metadata,
        }
        for sample in JsonSeedSampleLoader().load()
    ]


__all__ = [
    "KnowledgeBaseService",
    "ReviewedDetailDesignSample",
    "build_retrieval_query",
    "load_seed_samples",
]
