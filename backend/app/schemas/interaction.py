"""
PharmaMind AI - Drug Interaction Schemas
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class InteractionCheckRequest(BaseModel):
    drug_names: List[str] = Field(..., min_length=2, description="At least two drug names to check for documented interactions")
    include_experimental: bool = Field(False, description="Whether to include experimental Graph ML interaction predictions for uncataloged pairs")


class InteractionEvidenceItem(BaseModel):
    source_drug: str
    target_drug: str
    relationship_type: str = "INTERACTS_WITH"
    clinical_effect: str
    evidence_level: str = Field(..., description="VERIFIED_AUTHORITATIVE, SCIENTIFIC_LITERATURE, EXPERIMENTAL_ML_PREDICTION, or UNCERTAIN_SIGNAL")
    provenance_source: str
    provenance_id: Optional[str] = None
    confidence_score: float
    retrieved_date: str
    is_experimental: bool = False
    warning_notice: str


class InteractionCheckResponse(BaseModel):
    queried_drugs: List[str]
    normalized_drugs: List[str]
    total_interactions_found: int
    interactions: List[InteractionEvidenceItem]
    clinical_safety_notice: str = (
        "Educational and informational notice: This interaction information is retrieved from documented biomedical records. "
        "It does not constitute personalized medical advice, prescribing guidance, or dosage instruction. "
        "Always consult a qualified pharmacist or physician before making any medication changes."
    )
    uncertainty_statement: Optional[str] = None


class FAERSReactionSignal(BaseModel):
    term: str
    count: int


class FAERSSignalResponse(BaseModel):
    drug_name: str
    is_causal_confirmed: bool = False
    signal_type: str
    signal_count: int
    top_adverse_reactions: List[FAERSReactionSignal]
    disclaimer: str
    provenance_source: str
    provenance_id: str
    confidence_status: str
