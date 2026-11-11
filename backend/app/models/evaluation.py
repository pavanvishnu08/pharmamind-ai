"""
PharmaMind AI - Evaluation, Experiment Tracking, and Vector Metadata Models
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin

class EmbeddingRecord(Base, TimestampMixin):
    """
    Metadata for stored biomedical embeddings (FAISS/pgvector index references).
    """
    __tablename__ = "embedding_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # DRUG, PUBLICATION, TARGET
    entity_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)  # PubMedBERT, BioBERT, etc.
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Index offset or pgvector id


class ModelExperiment(Base, TimestampMixin):
    """
    Tracks reproducible ML and Graph experiments (Node2Vec, GraphSAGE, Semantic Search).
    """
    __tablename__ = "model_experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)  # GRAPH_ML, BIOMEDICAL_TRANSFORMER, RAG_RETRIEVER
    model_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    hyperparameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)  # RUNNING, COMPLETED, FAILED
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class EvaluationResult(Base, TimestampMixin):
    """
    Actual rigorous evaluation metrics (AUROC, AUPRC, Recall@K, Faithfulness, Latency).
    """
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # NER, RETRIEVAL, GRAPH_LINK_PRED, RAG
    metric_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # F1, AUROC, RECALL@K, FAITHFULNESS
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    dataset_split: Mapped[str] = mapped_column(String(50), default="test", nullable=False)  # train, val, test
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_eval_task_metric", "task_type", "metric_name"),
    )

