"""Dependency wiring for the FastAPI presentation layer.

This is the only place where infrastructure adapters (Gemini, Qdrant, BM25)
are instantiated and injected into application services. Application use cases
depend only on domain Protocols, never on concrete infra classes directly.
"""

from app.application.services.common_input_service import CommonInputService
from app.application.services.input_reference_service import InputReferenceService
from app.application.use_cases.generate_detail_design import GenerationService
from app.application.use_cases.ingest_reviewed_dd import KnowledgeBaseService
from app.application.use_cases.review_detail_design import DesignerReviewService
from app.infrastructure.embedding.gemini_embedder import GeminiEmbeddingService
from app.infrastructure.llm.vision_client import GeminiVisionDesignExtractor
from app.infrastructure.persistence.input_loader import InputReviewedDdLoader
from app.infrastructure.search.bm25_repository import BM25Repository
from app.infrastructure.vectorstore.qdrant_repository import QdrantVectorStore


common_input_service = CommonInputService()
generation_service = GenerationService()
designer_review_service = DesignerReviewService()

# ---------------------------------------------------------------------------
# Hybrid knowledge base (Qdrant dense + BM25 sparse)
# ---------------------------------------------------------------------------
_gemini_embedder = GeminiEmbeddingService()
_vision_extractor = GeminiVisionDesignExtractor()
vision_extractor = _vision_extractor
generation_service.input_reference_service = InputReferenceService(
    image_extractor=_vision_extractor
)
_qdrant_store = QdrantVectorStore()
_bm25_index = BM25Repository()

knowledge_base = KnowledgeBaseService(
    sample_loader=InputReviewedDdLoader(image_extractor=_vision_extractor),
    dense_embedding_service=_gemini_embedder,
    dense_vector_store=_qdrant_store,
    sparse_keyword_index=_bm25_index,
    auto_seed=False,
)
