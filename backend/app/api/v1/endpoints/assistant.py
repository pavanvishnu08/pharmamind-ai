"""
PharmaMind AI - Evidence-Grounded AI Drug Assistant Endpoint
Powered by the 11-step Retrieval-Augmented Generation (RAG) Pipeline.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.chat import ChatMessageRequest, ChatResponse
from app.api.v1.endpoints.drugs import seed_bootstrap_drugs_if_empty
from app.api.v1.endpoints.interactions import seed_bootstrap_relationships_if_empty
from app.services.rag.pipeline import PharmaMindRAGPipeline
from app.api.v1.endpoints.knowledge_graph import _kg, _predictor

router = APIRouter()

# Singleton instance of the end-to-end RAG pipeline
_rag_pipeline = PharmaMindRAGPipeline(kg=_kg, predictor=_predictor)


def _check_safety_guardrails(query: str):
    """Module-level safety guardrail check delegate."""
    _rag_pipeline.check_safety_guardrails(query)


@router.post("", response_model=ChatResponse)
async def ask_drug_assistant(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Evidence-grounded pharmaceutical information generation with strict citation validation.
    Integrates query normalization, NER, hybrid retrieval, knowledge graph traversal,
    reranking, structured evidence generation, and citation hallucination detection.
    """
    await seed_bootstrap_drugs_if_empty(db)
    await seed_bootstrap_relationships_if_empty(db)

    response = _rag_pipeline.execute(
        query=payload.query,
        conversation_id=payload.conversation_id,
        include_experimental=payload.include_experimental
    )
    return response
