"""
PharmaMind AI - Drug Schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IngredientResponse(BaseModel):
    id: str
    name: str
    unii: Optional[str] = None
    pubchem_cid: Optional[str] = None
    chemical_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    strength: Optional[str] = None

    class Config:
        from_attributes = True


class DrugSynonymResponse(BaseModel):
    id: str
    synonym: str
    source: str
    language: str

    class Config:
        from_attributes = True


class DrugBase(BaseModel):
    generic_name: str
    brand_name: Optional[str] = None
    rxnorm_cui: Optional[str] = None
    atc_code: Optional[str] = None
    drug_class: Optional[str] = None
    description: Optional[str] = None
    mechanism_of_action: Optional[str] = None
    route_of_administration: Optional[str] = None
    is_fda_approved: bool = True


class DrugCreate(DrugBase):
    pass


class DrugResponse(DrugBase):
    id: str
    synonyms: List[DrugSynonymResponse] = []
    ingredients: List[IngredientResponse] = []

    class Config:
        from_attributes = True


class DrugSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Drug generic name, brand name, or synonym")
    limit: int = Field(10, ge=1, le=50)


# Phase 2 Schemas: Normalization, Entity Extraction, and Ingestion

class DrugNormalizationRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Raw drug or brand name to normalize")


class DrugNormalizationResponse(BaseModel):
    input_text: str
    canonical_name: str
    display_name: str
    rxcui: Optional[str] = None
    atc_code: Optional[str] = None
    drug_class: Optional[str] = None
    match_type: str
    confidence_score: float
    salt_removed: Optional[str] = None
    original_brand: Optional[str] = None


class EntityExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Biomedical, clinical, or pharmacological text")


class ExtractedEntityResponse(BaseModel):
    text: str
    label: str
    start_char: int
    end_char: int
    normalized_name: str
    normalized_id: str
    confidence: float


class EntityExtractionResponse(BaseModel):
    text: str
    entity_count: int
    entities: List[ExtractedEntityResponse]


class DrugIngestionRequest(BaseModel):
    drug_name: str = Field(..., min_length=1, description="Drug name or identifier for full pipeline ingestion")


class DrugIngestionResponse(BaseModel):
    drug_id: str
    generic_name: str
    brand_names: List[str]
    rxcui: str
    atc_code: Optional[str] = None
    drug_class: Optional[str] = None
    monograph_sections: Dict[str, Any]
    faers_signals: Dict[str, Any]
    literature_citations: List[Dict[str, Any]]
    quality_report: Dict[str, Any]
    provenance_records: List[Dict[str, Any]]
