from typing import Any, Dict

from app.application.services.retrieval_query_service import build_retrieval_request
from app.application.use_cases.ingest_reviewed_dd import KnowledgeBaseService


class GetSampleDesignUseCase:
    def __init__(self, knowledge_base: KnowledgeBaseService | None = None) -> None:
        self.knowledge_base = knowledge_base or KnowledgeBaseService()

    def execute(
        self,
        basic_design: str,
        basic_design_analytics: Dict[str, Any],
    ) -> Dict[str, Any]:
        retrieval_request = build_retrieval_request(
            basic_design,
            basic_design_analytics,
        )
        references = self.knowledge_base.retrieve_context(
            retrieval_request["query"],
            filters=retrieval_request["filters"],
        )
        return {
            "references": references,
            "referenceCount": len(references),
            "knowledgeBase": self.knowledge_base.get_status(),
        }
