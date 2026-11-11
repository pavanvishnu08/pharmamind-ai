"""
PharmaMind AI - AI Drug Assistant and RAG Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    source_title: str
    source_type: str  # DailyMed, RxNorm, PubMed, openFDA
    identifier: str  # PMID, SetID, NDC, RxCUI
    url: Optional[str] = None
    evidence_status: str  # Authoritative, Literature, Experimental
    retrieved_date: str


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str = Field(..., min_length=2, description="Biomedical or pharmacological query")
    include_experimental: bool = Field(False, description="Whether to include experimental ML predictions clearly labeled")


class ChatResponse(BaseModel):
    conversation_id: str
    direct_explanation: str
    drug_information: Optional[Dict[str, Any]] = None
    evidence_summary: str
    citations: List[Citation]
    confidence_status: str = Field(
        ...,
        description="VERIFIED_AUTHORITATIVE, LITERATURE_SUPPORTED, EXPERIMENTAL_ML_PREDICTION, or INSUFFICIENT_EVIDENCE"
    )
    safety_disclaimer: str = (
        "Informational purpose only. Not clinical or prescribing advice. "
        "Consult a qualified healthcare professional before taking or altering any medication."
    )
    prompt_version: str = "2026.1-pharmamind-evidence"
    model_name: str = "PubMedBERT-RAG-Engine"
    entities_detected: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_evidence_count: int = 0
    citation_validation_passed: bool = True
    tokens_used: int = 0
    latency_ms: float = 0.0

