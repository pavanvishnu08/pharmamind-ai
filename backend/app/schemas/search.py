"""
PharmaMind AI - Semantic & Hybrid Search Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Clinical inquiry, mechanism, or drug query")
    top_k: int = Field(5, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters (e.g. {'doc_type': 'monograph'})")


class SearchResultItem(BaseModel):
    id: str
    title: str
    content: str
    doc_type: str  # monograph, literature, interaction, adverse_effect
    similarity_score: float
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class SemanticSearchResponse(BaseModel):
    query: str
    search_type: str  # dense_semantic or hybrid_fused
    total_results: int
    results: List[SearchResultItem]


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Biomedical inquiry")
    top_k: int = Field(5, ge=1, le=50)
    dense_weight: float = Field(0.65, ge=0.0, le=1.0, description="Weighting of dense semantic vs sparse BM25 scores")
    filters: Optional[Dict[str, Any]] = None


class EmbeddingRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to embed")


class EmbeddingResponse(BaseModel):
    model_name: str
    dimension: int
    vector_preview: List[float] = Field(..., description="First 8 dimensions of the normalized embedding vector")
    l2_norm: float


class ModelCardResponse(BaseModel):
    model_name: str
    model_id: str
    pretraining_corpus: str
    vocabulary_type: str
    parameters: str
    checkpoint_size_mb: float
    recommended_tasks: List[str]
    justification: str
    cpu_latency_est_ms: float
    is_primary_choice: bool

