"""
PharmaMind AI - Knowledge Graph Entities and Provenance-Backed Relationships
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Boolean, Float, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin

class Disease(Base, TimestampMixin):
    __tablename__ = "diseases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mesh_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    icd10_code: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    doid: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AdverseEffect(Base, TimestampMixin):
    __tablename__ = "adverse_effects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meddra_term: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    meddra_code: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    severity_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Mild, Moderate, Severe
    faers_signal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_causal_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DrugRelationship(Base, TimestampMixin):
    """
    Biomedical relationship with mandatory provenance, evidence level, and confidence.
    Relationship Types:
    - CONTAINS_INGREDIENT
    - TREATS
    - ASSOCIATED_WITH_ADVERSE_EFFECT
    - INTERACTS_WITH
    - BELONGS_TO_CLASS
    - TARGETS
    - CONTRAINDICATED_IN
    """
    __tablename__ = "drug_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DRUG, INGREDIENT, DISEASE, TARGET
    target_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    
    # Clinical & Provenance Details
    clinical_effect: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_level: Mapped[str] = mapped_column(String(50), default="VERIFIED_AUTHORITATIVE", nullable=False)
    # Evidence Levels:
    # 1. VERIFIED_AUTHORITATIVE (DailyMed, RxNorm, FDA Labeling)
    # 2. SCIENTIFIC_LITERATURE (Peer-reviewed PubMed/PMC findings)
    # 3. EXPERIMENTAL_ML_PREDICTION (Node2Vec, GraphSAGE, Link Prediction)
    # 4. UNCERTAIN_SIGNAL (FAERS signal only, unconfirmed causality)
    
    provenance_source: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. DailyMed, PubMed, openFDA
    provenance_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g. PMID:12345, SetID
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    retrieved_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_drug_rel_src_tgt", "source_id", "target_id", "relationship_type"),
    )

