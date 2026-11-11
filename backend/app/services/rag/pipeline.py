"""
PharmaMind AI - End-to-End Retrieval-Augmented Generation (RAG) Pipeline
Coordinates the complete 11-step evidence-grounded generation pipeline:
1. User question
2. Query normalization
3. Biomedical entity extraction
4. Semantic retrieval
5. Keyword retrieval (BM25)
6. Knowledge graph lookup
7. Result fusion
8. Evidence reranking
9. Evidence selection & context window management
10. Structured response generation
11. Citation validation & hallucination check
"""

from typing import List, Dict, Any, Optional
import uuid
import logging
from app.schemas.chat import ChatResponse
from app.core.exceptions import MedicalAdviceProhibitedException
from app.services.drug_normalization.normalizer import DrugNormalizer
from app.services.entity_extraction.extractor import BiomedicalEntityExtractor
from app.services.semantic_search.hybrid_search import HybridSearchEngine
from app.services.knowledge_graph.graph_engine import BiomedicalKnowledgeGraph, build_default_biomedical_graph
from app.services.graph_ml.link_predictor import GraphLinkPredictor
from app.services.rag.evidence_corpus import create_and_populate_evidence_corpus
from app.services.rag.reranker import EvidenceReranker
from app.services.rag.response_generator import ResponseGenerator

logger = logging.getLogger("pharmamind.services.rag.pipeline")

PROHIBITED_INTENT_KEYWORDS = [
    "prescribe", "dosage for me", "how much should i take",
    "diagnose me", "do i have", "can i replace my doctor",
    "stop taking my medication", "what dose should my child take"
]


BIOMEDICAL_SCAFFOLDING_TERMS = {
    "what", "are", "the", "for", "and", "in", "of", "with", "is", "an", "to", "how", "does", "do", "tell", "me", "about",
    "indications", "indication", "mechanism", "action", "dosage", "boxed", "warning", "warnings",
    "tablets", "tablet", "capsule", "capsules", "drug", "drugs", "medicine", "medicines", "clinical", "pharmacology", "fda"
}


class PharmaMindRAGPipeline:
    """
    Production-grade RAG pipeline implementing all 11 stages with strict evidence grounding.
    """

    def __init__(
        self,
        hybrid_engine: Optional[HybridSearchEngine] = None,
        kg: Optional[BiomedicalKnowledgeGraph] = None,
        predictor: Optional[GraphLinkPredictor] = None
    ):
        self.normalizer = DrugNormalizer()
        self.entity_extractor = BiomedicalEntityExtractor()
        self.hybrid_engine = hybrid_engine or create_and_populate_evidence_corpus()
        self.kg = kg or build_default_biomedical_graph()
        self.predictor = predictor
        self.reranker = EvidenceReranker(max_context_tokens=1500, max_evidence_items=4)
        self.generator = ResponseGenerator()

    def check_safety_guardrails(self, query: str):
        """Refuse queries asking for personal prescriptions, personalized doses, or clinical diagnoses."""
        q_low = query.lower()
        for phrase in PROHIBITED_INTENT_KEYWORDS:
            if phrase in q_low:
                raise MedicalAdviceProhibitedException(
                    f"PharmaMind AI cannot provide personalized clinical decisions, diagnoses, or dosage recommendations regarding '{phrase}'. "
                    "Please consult a licensed medical doctor or clinical pharmacist."
                )

    def execute(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        include_experimental: bool = False
    ) -> ChatResponse:
        """
        Execute the 11-step evidence retrieval and response synthesis pipeline.
        """
        # Step 1: User question & Safety Guardrail Check
        self.check_safety_guardrails(query)
        conv_id = conversation_id or str(uuid.uuid4())

        # Step 2: Query Normalization
        cleaned_query = self.normalizer.clean_text(query)

        # Step 3: Biomedical Entity Extraction
        raw_entities = self.entity_extractor.extract_entities(cleaned_query)
        extracted_entities = []
        normalized_names = []

        for ent in raw_entities:
            ent_dict = ent.to_dict()
            ent_dict["category"] = ent.label
            if ent.label in ("DRUG", "INGREDIENT"):
                norm = self.normalizer.normalize(ent.text)
                ent_dict["canonical_name"] = norm.canonical_name
                ent_dict["rxnorm_cui"] = norm.rxcui
                normalized_names.append(norm.canonical_name)
            extracted_entities.append(ent_dict)

        # Extract substantive terms from query outside scaffolding stopwords
        import re
        query_words = set(re.findall(r"\b[a-zA-Z0-9-]{3,}\b", cleaned_query.lower()))
        substantive_query_terms = query_words - BIOMEDICAL_SCAFFOLDING_TERMS

        # Steps 4, 5, 7: Semantic Retrieval + BM25 Keyword Retrieval + Result Fusion
        search_results = self.hybrid_engine.search(query=cleaned_query, top_k=6)
        raw_retrieved_items = []
        for r in search_results:
            sparse_score = r.get("sparse_score", 0.0)
            hybrid_score = r.get("hybrid_score", 0.0)
            doc_text = (r.get("title", "") + " " + r.get("content", "")).lower()

            if normalized_names:
                # When drug entities are recognized, document must match at least one entity or have high semantic alignment
                is_relevant = (
                    any(n.lower() in doc_text for n in normalized_names) or
                    hybrid_score >= 0.55
                )
            else:
                # When no known drug entity was extracted, require substantive query terms to match document text
                has_substantive_term_match = any(term in doc_text for term in substantive_query_terms)
                is_relevant = has_substantive_term_match and hybrid_score >= 0.35

            if is_relevant:
                raw_retrieved_items.append({
                    "doc_id": r.get("id", r.get("doc_id", "")),
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "score": hybrid_score,
                    "dense_score": r.get("dense_score", 0.0),
                    "sparse_score": sparse_score,
                    "metadata": r.get("metadata", {}),
                    "source_type": r.get("source_type", r.get("metadata", {}).get("source_type", "DailyMed"))
                })

        # Step 6: Knowledge Graph Lookup
        graph_facts = []
        for name in normalized_names:
            capitalized = name.capitalize()
            hood = self.kg.get_neighborhood(capitalized, radius=1)
            for edge in hood.get("edges", []):
                graph_facts.append({
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "relationship": edge.get("relationship"),
                    "evidence_level": edge.get("evidence_level"),
                    "provenance_source": edge.get("provenance_source"),
                    "provenance_id": edge.get("provenance_id")
                })

        # Optional Step 6b: Experimental Graph ML Link Prediction (if requested)
        experimental_preds = []
        if include_experimental and self.predictor and len(normalized_names) >= 2:
            pred = self.predictor.predict_link(
                normalized_names[0].capitalize(),
                normalized_names[1].capitalize()
            )
            experimental_preds.append(pred)

        # Step 8: Reranking & Result Fusion
        reranked_evidence = self.reranker.rerank(
            query=cleaned_query,
            retrieved_items=raw_retrieved_items,
            extracted_entities=extracted_entities
        )

        # Step 9, 10, 11: Evidence Selection, Response Generation & Citation Validation
        response = self.generator.generate_response(
            query=query,
            conversation_id=conv_id,
            extracted_entities=extracted_entities,
            retrieved_evidence=reranked_evidence,
            graph_facts=graph_facts,
            experimental_predictions=experimental_preds
        )

        return response
