"""
PharmaMind AI - Scientific Publications and Source Records
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin

class Publication(Base, TimestampMixin):
    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pmid: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    pmcid: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mesh_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SourceRecord(Base, TimestampMixin):
    """
    Immutable raw source archive preserving original biomedical data provenance.
    """
    __tablename__ = "source_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # DailyMed, openFDA, RxNorm, PubMed
    source_identifier: Mapped[str] = mapped_column(String(255), index=True, nullable=False)  # NDC, SetID, RxCUI, PMID
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)  # DRUG_LABEL, FAERS_ADVERSE_SIGNAL, CITATION
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    license: Mapped[str] = mapped_column(String(100), default="Public Domain / Open Access", nullable=False)
    retrieved_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_src_name_ident", "source_name", "source_identifier"),
    )

