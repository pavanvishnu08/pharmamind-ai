"""
PharmaMind AI - API v1 Master Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    drugs,
    interactions,
    knowledge_graph,
    literature,
    assistant,
    evaluation,
    auth,
    search,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["System Health & Diagnostics"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & User Management"])
api_router.include_router(drugs.router, prefix="/drugs", tags=["Drug Information & Monographs"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["Drug Interaction Intelligence"])
api_router.include_router(knowledge_graph.router, prefix="/graph", tags=["Biomedical Knowledge Graph"])
api_router.include_router(literature.router, prefix="/literature", tags=["Research Literature Explorer"])
api_router.include_router(search.router, prefix="/search", tags=["Semantic & Hybrid Search"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Evidence-Grounded AI Assistant"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["AI Evaluation & Research Dashboard"])
