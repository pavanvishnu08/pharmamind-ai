"""
PharmaMind AI - Semantic & Hybrid Search Endpoints
Exposes dense semantic retrieval, BM25 keyword fusion, and biomedical transformer model benchmarks.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
import numpy as np

from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResultItem,
    HybridSearchRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelCardResponse
)
from app.services.embeddings.biomedical_embedder import BiomedicalEmbeddingService
from app.services.semantic_search.vector_store import create_vector_store
from app.services.semantic_search.hybrid_search import HybridSearchEngine
from app.services.biomedical_nlp.transformer_benchmark import BiomedicalTransformerManager, BIOMEDICAL_MODEL_CARDS

router = APIRouter()

# Singletons for Search Engine
_embedder = BiomedicalEmbeddingService()
_vector_store = create_vector_store(dimension=_embedder.dimension)
_hybrid_engine = HybridSearchEngine(embedder=_embedder, vector_store=_vector_store, dense_weight=0.65)
_transformer_manager = BiomedicalTransformerManager()

# Curated Initial Corpus for High-Precision Biomedical Retrieval
INITIAL_SEARCH_CORPUS: List[Dict[str, Any]] = [
    {
        "id": "doc-metformin-monograph",
        "title": "Metformin Hydrochloride - FDA Monograph",
        "content": "First-line biguanide oral antihyperglycemic indicated for type 2 diabetes mellitus. Lowers blood glucose by activating AMP-activated protein kinase (AMPK), reducing hepatic gluconeogenesis and improving peripheral insulin sensitivity.",
        "description": "DailyMed SPL Monograph: Type 2 Diabetes, AMPK mechanism, Lactic acidosis warning.",
        "doc_type": "monograph",
        "mesh_terms": ["Metformin", "Diabetes Mellitus, Type 2", "AMPK", "Gluconeogenesis"]
    },
    {
        "id": "doc-warfarin-monograph",
        "title": "Warfarin Sodium - FDA Monograph",
        "content": "Vitamin K antagonist anticoagulant indicated for prophylaxis and treatment of venous thrombosis, pulmonary embolism, and thromboembolic complications from atrial fibrillation. Inhibits VKORC1 enzyme.",
        "description": "DailyMed SPL Monograph: Deep vein thrombosis, atrial fibrillation, VKORC1, Bleeding risk boxed warning.",
        "doc_type": "monograph",
        "mesh_terms": ["Warfarin", "Anticoagulants", "VKORC1", "Thrombosis", "Hemorrhage"]
    },
    {
        "id": "doc-aspirin-monograph",
        "title": "Aspirin (Acetylsalicylic Acid) - Monograph",
        "content": "Nonsteroidal anti-inflammatory drug (NSAID) and antiplatelet agent. Irreversibly acetylates platelet cyclooxygenase-1 (COX-1) and COX-2, preventing thromboxane A2 synthesis for platelet lifespan.",
        "description": "DailyMed SPL Monograph: Platelet aggregation inhibitor, vascular prophylaxis, GI ulceration.",
        "doc_type": "monograph",
        "mesh_terms": ["Aspirin", "Antiplatelet", "Cyclooxygenase 1", "Thromboxane A2", "Myocardial Infarction"]
    },
    {
        "id": "doc-simvastatin-monograph",
        "title": "Simvastatin (Zocor) - FDA Monograph",
        "content": "HMG-CoA reductase inhibitor (statin) used for hyperlipidemia and cardiovascular risk reduction. Metabolized by CYP3A4. Concomitant use with strong CYP3A4 inhibitors increases myopathy and rhabdomyolysis risk.",
        "description": "DailyMed SPL Monograph: Hyperlipidemia, CAD, CYP3A4 metabolism, Rhabdomyolysis warning.",
        "doc_type": "monograph",
        "mesh_terms": ["Simvastatin", "HMG-CoA Reductase Inhibitors", "CYP3A4", "Rhabdomyolysis", "Hyperlipidemia"]
    },
    {
        "id": "doc-lisinopril-monograph",
        "title": "Lisinopril (Prinivil) - FDA Monograph",
        "content": "Angiotensin-converting enzyme (ACE) inhibitor indicated for hypertension and heart failure. Suppresses renin-angiotensin-aldosterone system (RAAS). Adverse effects include persistent dry cough and angioedema.",
        "description": "DailyMed SPL Monograph: Essential hypertension, heart failure, ACE inhibition, Angioedema warning.",
        "doc_type": "monograph",
        "mesh_terms": ["Lisinopril", "ACE Inhibitors", "Hypertension", "Renin-Angiotensin System", "Angioedema"]
    },
    {
        "id": "doc-lit-11502884",
        "title": "Pharmacokinetic drug interactions with statins (PMID: 11502884)",
        "content": "Simvastatin, lovastatin, and atorvastatin are metabolized primarily by CYP3A4. Concomitant administration of potent CYP3A4 inhibitors markedly increases statin plasma concentrations, elevating the risk of myopathy.",
        "description": "Clinical Pharmacokinetics (2006): CYP3A4 inhibition, Statin pharmacokinetics, Rhabdomyolysis.",
        "doc_type": "literature",
        "mesh_terms": ["Cytochrome P-450 CYP3A", "Simvastatin", "Drug Interactions", "Rhabdomyolysis"]
    },
    {
        "id": "doc-lit-14761947",
        "title": "Oral anticoagulant therapy guidelines: Warfarin and bleeding (PMID: 14761947)",
        "content": "Warfarin produces anticoagulation by interfering with VKORC1 cyclic interconversion of vitamin K. Co-administration of NSAIDs, antiplatelets, or CYP2C9 inhibitors significantly potentiates bleeding risk.",
        "description": "Chest Evidence-Based Guidelines: Warfarin, VKORC1, Bleeding risks, INR monitoring.",
        "doc_type": "literature",
        "mesh_terms": ["Anticoagulants", "Warfarin", "Hemorrhage", "Vitamin K", "INR"]
    }
]

# Bootstrap indexing
_hybrid_engine.index_documents(INITIAL_SEARCH_CORPUS, text_field="content")


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(payload: SemanticSearchRequest):
    """
    Perform dense vector semantic retrieval using normalized 384-dimensional biomedical embeddings.
    """
    query_vec = _embedder.embed_text(payload.query)
    raw_results = _vector_store.search(query_vec, top_k=payload.top_k, filters=payload.filters)

    items = [
        SearchResultItem(
            id=doc.get("id", ""),
            title=doc.get("title", "Untitled Document"),
            content=doc.get("content", ""),
            doc_type=doc.get("doc_type", "general"),
            similarity_score=doc.get("similarity_score", 0.0),
            metadata={
                "mesh_terms": doc.get("mesh_terms", []),
                "description": doc.get("description", "")
            }
        )
        for doc in raw_results
    ]

    return SemanticSearchResponse(
        query=payload.query,
        search_type="dense_semantic",
        total_results=len(items),
        results=items
    )


@router.post("/hybrid", response_model=SemanticSearchResponse)
async def hybrid_search(payload: HybridSearchRequest):
    """
    Execute hybrid search fusing dense vector similarity with sparse BM25 keyword matching.
    """
    _hybrid_engine.dense_weight = payload.dense_weight
    raw_results = _hybrid_engine.search(payload.query, top_k=payload.top_k, filters=payload.filters)

    items = [
        SearchResultItem(
            id=doc.get("id", ""),
            title=doc.get("title", "Untitled Document"),
            content=doc.get("content", ""),
            doc_type=doc.get("doc_type", "general"),
            similarity_score=doc.get("hybrid_score", 0.0),
            dense_score=doc.get("dense_score"),
            sparse_score=doc.get("sparse_score"),
            hybrid_score=doc.get("hybrid_score"),
            metadata={
                "mesh_terms": doc.get("mesh_terms", []),
                "description": doc.get("description", "")
            }
        )
        for doc in raw_results
    ]

    return SemanticSearchResponse(
        query=payload.query,
        search_type="hybrid_fused",
        total_results=len(items),
        results=items
    )


@router.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(payload: EmbeddingRequest):
    """
    Generate and return a dense embedding vector preview with dimension and L2 norm validation.
    """
    vec = _embedder.embed_text(payload.text)
    norm = float(np.linalg.norm(vec))
    preview = [float(round(v, 4)) for v in vec[:8]]

    return EmbeddingResponse(
        model_name=_embedder.model_name,
        dimension=_embedder.dimension,
        vector_preview=preview,
        l2_norm=round(norm, 4)
    )


@router.get("/models", response_model=List[ModelCardResponse])
async def list_model_cards():
    """
    Retrieve comparative architectural benchmark cards for PubMedBERT, BioBERT, and ClinicalBERT.
    """
    cards = _transformer_manager.get_benchmark_cards()
    return [
        ModelCardResponse(
            model_name=c["model_name"],
            model_id=c["model_id"],
            pretraining_corpus=c["pretraining_corpus"],
            vocabulary_type=c["vocabulary_type"],
            parameters=c["parameters"],
            checkpoint_size_mb=c["checkpoint_size_mb"],
            recommended_tasks=c["recommended_tasks"],
            justification=c["justification"],
            cpu_latency_est_ms=c["cpu_latency_est_ms"],
            is_primary_choice=c["is_primary_choice"]
        )
        for c in cards
    ]

