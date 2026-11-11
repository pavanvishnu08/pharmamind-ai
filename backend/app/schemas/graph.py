"""
PharmaMind AI - Knowledge Graph & Graph ML Schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # DRUG, INGREDIENT, DISEASE, ADVERSE_EFFECT, TARGET, PROTEIN, DRUG_CLASS
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    evidence_level: str
    provenance_source: str
    provenance_id: Optional[str] = None
    confidence_score: float
    retrieved_date: Optional[str] = None
    is_experimental: bool = False
    clinical_effect: Optional[str] = None


class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
    graph_engine: str = "LocalNetworkX"
    provenance_summary: Dict[str, int] = {}


class SubgraphResponse(BaseModel):
    center_node: str
    radius: int
    total_nodes: int
    total_edges: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class PathSegment(BaseModel):
    step: int
    from_node: Dict[str, Any]
    to_node: Dict[str, Any]
    relationship: str
    evidence_level: str
    provenance_source: str
    direction: str = "forward"


class GraphPathResponse(BaseModel):
    source: str
    target: str
    path_found: bool
    length: int
    path: List[PathSegment] = []


class LinkPredictionRequest(BaseModel):
    source_id: str = Field(..., min_length=1, description="First entity node identifier (e.g. Warfarin)")
    target_id: str = Field(..., min_length=1, description="Second entity node identifier (e.g. Simvastatin)")


class LinkPredictionResponse(BaseModel):
    source: str
    target: str
    probability: float
    predicted_link: bool
    confidence_score: float
    evidence_level: str = "EXPERIMENTAL_ML_PREDICTION"
    is_experimental: bool = True
    warning_notice: str
    algorithm: str
    evaluation_context: Optional[Dict[str, Any]] = None


class GraphMLBenchmarkResponse(BaseModel):
    model_architecture: str
    edge_operator: str
    embedding_dimension: int
    train_samples: int
    test_samples: int
    auroc: float
    auprc: float
    precision: float
    recall: float
    f1_score: float
    brier_score_calibration: float
    negative_sampling_ratio: str
    leakage_prevention_verified: bool
    disclaimer: str
