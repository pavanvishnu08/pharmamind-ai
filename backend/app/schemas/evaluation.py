"""
PharmaMind AI - Evaluation and Benchmarking Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MetricItem(BaseModel):
    task: str  # NER, RETRIEVAL, GRAPH_ML, RAG, SYSTEM
    metric_name: str
    value: float
    target_threshold: Optional[float] = None
    dataset: str
    sample_size: int
    is_tested: bool = True
    benchmark_status: str  # "PASS", "WARN", "UNTESTED"
    notes: Optional[str] = None


class SystemPerformanceMetrics(BaseModel):
    api_latency_ms: float
    model_inference_latency_ms: float
    ram_usage_mb: float
    free_ram_mb: float
    token_throughput_per_sec: float
    failure_rate_pct: float


class EvaluationDashboardResponse(BaseModel):
    system_metrics: SystemPerformanceMetrics
    nlp_metrics: List[MetricItem]
    retrieval_metrics: List[MetricItem]
    graph_ml_metrics: List[MetricItem]
    rag_metrics: List[MetricItem]
    total_experiments: int
    evaluated_at: str

