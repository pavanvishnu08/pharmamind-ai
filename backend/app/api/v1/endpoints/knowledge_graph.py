"""
PharmaMind AI - Knowledge Graph Explorer & Graph ML Endpoints
Provides multi-hop path traversal, neighborhood expansion, and link prediction with strict experimental labeling.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.graph import (
    KnowledgeGraphResponse,
    GraphNode,
    GraphEdge,
    SubgraphResponse,
    GraphPathResponse,
    PathSegment,
    LinkPredictionRequest,
    LinkPredictionResponse,
    GraphMLBenchmarkResponse
)
from app.services.knowledge_graph.graph_engine import (
    BiomedicalKnowledgeGraph,
    build_default_biomedical_graph
)
from app.services.graph_ml.link_predictor import (
    GraphLinkPredictor,
    MANDATORY_EXPERIMENTAL_DISCLAIMER
)

router = APIRouter()

# Singletons for Knowledge Graph & Graph ML Link Predictor
_kg: BiomedicalKnowledgeGraph = build_default_biomedical_graph()
_predictor: GraphLinkPredictor = GraphLinkPredictor(dimension=64, random_seed=42)
# Initial training and evaluation at startup
_predictor.train_and_evaluate(_kg, test_ratio=0.20)


@router.get("", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    node_type: Optional[str] = Query(None, description="Filter by node type (DRUG, TARGET, DISEASE, ADVERSE_EFFECT, etc.)"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship (TREATS, TARGETS, INTERACTS_WITH, etc.)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Explore the verified biomedical knowledge graph with provenance attributes and summary stats.
    """
    raw_graph = _kg.export_graph()

    # Filter nodes
    filtered_nodes = []
    node_ids = set()
    for n in raw_graph["nodes"]:
        if node_type and n["node_type"].upper() != node_type.strip().upper():
            continue
        filtered_nodes.append(GraphNode(**n))
        node_ids.add(n["id"])

    # Filter edges
    filtered_edges = []
    provenance_summary = {}

    for e in raw_graph["edges"]:
        if relationship_type and e["relationship_type"].upper() != relationship_type.strip().upper():
            continue
        # If node_type was specified, ensure both ends exist in filtered nodes
        if node_type and (e["source"] not in node_ids or e["target"] not in node_ids):
            continue

        filtered_edges.append(GraphEdge(**e))
        src = e["provenance_source"]
        provenance_summary[src] = provenance_summary.get(src, 0) + 1

    return KnowledgeGraphResponse(
        nodes=filtered_nodes,
        edges=filtered_edges,
        total_nodes=len(filtered_nodes),
        total_edges=len(filtered_edges),
        graph_engine="NetworkX MultiDiGraph (Heterogeneous)",
        provenance_summary=provenance_summary
    )


@router.get("/subgraph/{entity_id}", response_model=SubgraphResponse)
async def get_entity_subgraph(
    entity_id: str,
    radius: int = Query(1, ge=1, le=3, description="Neighborhood radius (k-hop expansion)")
):
    """
    Extract a k-hop subgraph centered around a specific biomedical entity.
    """
    hood = _kg.get_neighborhood(entity_id, radius=radius)
    if not hood["nodes"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{entity_id}' not found in the biomedical knowledge graph."
        )

    return SubgraphResponse(
        center_node=hood["center_node"],
        radius=hood["radius"],
        total_nodes=hood["total_nodes"],
        total_edges=hood["total_edges"],
        nodes=[GraphNode(**n) for n in hood["nodes"]],
        edges=[GraphEdge(**e) for e in hood["edges"]]
    )


@router.get("/path", response_model=GraphPathResponse)
async def get_explanatory_path(
    source: str = Query(..., description="Starting entity identifier (e.g. Warfarin)"),
    target: str = Query(..., description="Destination entity identifier (e.g. Thrombosis)")
):
    """
    Traverse the knowledge graph to discover multi-hop explanatory paths connecting two entities.
    """
    path_segments = _kg.find_shortest_path(source, target)
    if not path_segments:
        return GraphPathResponse(
            source=source,
            target=target,
            path_found=False,
            length=0,
            path=[]
        )

    return GraphPathResponse(
        source=source,
        target=target,
        path_found=True,
        length=len(path_segments),
        path=[PathSegment(**seg) for seg in path_segments]
    )


@router.post("/predict-interaction", response_model=LinkPredictionResponse)
async def predict_graph_link(payload: LinkPredictionRequest):
    """
    Predict link likelihood between two entities using Node2Vec biased random walks + calibrated classifier.
    MANDATORY CLINICAL WARNING: Results are experimental predictions and NOT confirmed clinical interactions.
    """
    prediction = _predictor.predict_link(payload.source_id, payload.target_id)
    return LinkPredictionResponse(
        source=prediction["source"],
        target=prediction["target"],
        probability=prediction["probability"],
        predicted_link=prediction["predicted_link"],
        confidence_score=prediction["confidence_score"],
        evidence_level=prediction["evidence_level"],
        is_experimental=prediction["is_experimental"],
        warning_notice=prediction["warning_notice"],
        algorithm=prediction.get("algorithm", "Node2Vec + Logistic Edge Classifier"),
        evaluation_context=prediction.get("evaluation_context")
    )


@router.get("/ml-benchmark", response_model=GraphMLBenchmarkResponse)
async def get_graph_ml_benchmarks():
    """
    Retrieve empirical evaluation metrics for the Graph ML link prediction model:
    AUROC, AUPRC, Precision, Recall, F1 score, and Brier calibration.
    """
    res = _predictor.evaluation_results
    return GraphMLBenchmarkResponse(
        model_architecture=res.get("model_architecture", "Node2Vec + Logistic Edge Classifier"),
        edge_operator=res.get("edge_operator", "hadamard"),
        embedding_dimension=res.get("embedding_dimension", 64),
        train_samples=res.get("train_samples", 0),
        test_samples=res.get("test_samples", 0),
        auroc=res.get("auroc", 0.0),
        auprc=res.get("auprc", 0.0),
        precision=res.get("precision", 0.0),
        recall=res.get("recall", 0.0),
        f1_score=res.get("f1_score", 0.0),
        brier_score_calibration=res.get("brier_score_calibration", 0.0),
        negative_sampling_ratio=res.get("negative_sampling_ratio", "1:1"),
        leakage_prevention_verified=res.get("leakage_prevention_verified", True),
        disclaimer=MANDATORY_EXPERIMENTAL_DISCLAIMER
    )
