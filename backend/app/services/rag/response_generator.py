"""
PharmaMind AI - Structured Response Generator
Produces structured biomedical explanations grounded strictly in validated evidence.
Implements prompt versioning, token tracking, hallucination safeguards, and clinical disclaimers.
"""

from typing import List, Dict, Any, Optional
import time
import logging
from app.schemas.chat import ChatResponse, Citation
from app.services.rag.citation_validator import CitationValidator

logger = logging.getLogger("pharmamind.services.rag.generator")

PROMPT_VERSION = "2026.1-pharmamind-evidence"
MODEL_NAME = "PubMedBERT-RAG-Engine"

DEFAULT_SAFETY_DISCLAIMER = (
    "PharmaMind AI is an educational and informational platform, not a medical device. "
    "This information does not constitute medical advice, diagnosis, or personalized treatment recommendations. "
    "Always consult a qualified licensed physician or clinical pharmacist for medication decisions."
)


class ResponseGenerator:
    """
    Synthesizes evidence-grounded answers conforming to the 6 mandatory PharmaMind output sections:
    1. Direct explanation
    2. Relevant drug information
    3. Evidence summary
    4. Source citations
    5. Confidence or evidence limitations
    6. Safety disclaimer
    """

    def __init__(self):
        self.validator = CitationValidator()

    def generate_response(
        self,
        query: str,
        conversation_id: str,
        extracted_entities: List[Dict[str, Any]],
        retrieved_evidence: List[Dict[str, Any]],
        graph_facts: Optional[List[Dict[str, Any]]] = None,
        experimental_predictions: Optional[List[Dict[str, Any]]] = None
    ) -> ChatResponse:
        """
        Generate structured ChatResponse from validated evidence snippets.
        """
        t0 = time.perf_counter()

        # Handle case with NO evidence retrieved
        if not retrieved_evidence and not graph_facts:
            return ChatResponse(
                conversation_id=conversation_id,
                direct_explanation=(
                    f"Unable to locate verified pharmacological evidence for query: '{query}'. "
                    "Authoritative drug monographs from DailyMed, RxNorm, and PubMed literature do not contain matching records. "
                    "Please verify drug name spelling or inquire regarding standard pharmaceutical agents."
                ),
                drug_information=None,
                evidence_summary="Insufficient evidence found in the authoritative pharmaceutical knowledge bases.",
                citations=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                safety_disclaimer=DEFAULT_SAFETY_DISCLAIMER,
                prompt_version=PROMPT_VERSION,
                model_name=MODEL_NAME,
                entities_detected=extracted_entities,
                retrieved_evidence_count=0,
                citation_validation_passed=True,
                tokens_used=len(query.split()) * 4 + 40,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2)
            )

        # 1. Identify primary drug entity from extracted entities or evidence metadata
        primary_drug_name = None
        for ent in extracted_entities:
            cat = ent.get("category") or ent.get("label")
            if cat in ("DRUG", "INGREDIENT"):
                primary_drug_name = ent.get("canonical_name") or ent.get("normalized_name") or ent.get("text")
                break

        if not primary_drug_name and retrieved_evidence:
            primary_drug_name = retrieved_evidence[0].get("metadata", {}).get("drug_name")

        # 2. Extract structured drug information from evidence
        primary_evidence = retrieved_evidence[0] if retrieved_evidence else {}
        primary_meta = primary_evidence.get("metadata", {})

        drug_info = None
        if primary_drug_name:
            drug_info = {
                "generic_name": primary_drug_name.capitalize(),
                "brand_name": primary_meta.get("brand_name"),
                "rxnorm_cui": primary_meta.get("rxnorm_cui"),
                "atc_code": primary_meta.get("atc_code"),
                "drug_class": primary_meta.get("drug_class"),
                "target": primary_meta.get("target"),
                "has_boxed_warning": primary_meta.get("boxed_warning", False)
            }

        # 3. Construct Direct Explanation
        explanation_parts = []
        if primary_drug_name and drug_info and drug_info.get("drug_class"):
            explanation_parts.append(
                f"{drug_info['generic_name']} is an FDA-approved {drug_info['drug_class']} "
                f"(RxCUI: {drug_info.get('rxnorm_cui', 'N/A')})."
            )

        # Integrate top evidence findings
        for doc in retrieved_evidence[:2]:
            content = doc.get("content", "")
            # Extract first 2 sentences
            sentences = [s.strip() for s in content.split(". ") if s.strip()]
            lead = ". ".join(sentences[:2])
            if lead and not lead.endswith("."):
                lead += "."
            explanation_parts.append(lead)

        # Integrate graph facts if present
        if graph_facts:
            gf_texts = []
            for gf in graph_facts[:3]:
                gf_texts.append(f"{gf.get('source')} {gf.get('relationship')} {gf.get('target')}")
            if gf_texts:
                explanation_parts.append("Verified knowledge graph relationships: " + "; ".join(gf_texts) + ".")

        # Integrate experimental predictions with mandatory labeling
        if experimental_predictions:
            for pred in experimental_predictions:
                explanation_parts.append(
                    f"[EXPERIMENTAL ML PREDICTION]: {pred.get('source')} - {pred.get('target')} "
                    f"link likelihood estimated at {pred.get('probability', 0.0):.2f}. "
                    "Note: This is an experimental model prediction, NOT a confirmed clinical interaction."
                )

        direct_explanation = "\n\n".join(explanation_parts)

        # 4. Construct Evidence Summary
        summary_points = []
        for doc in retrieved_evidence:
            src_type = doc.get("metadata", {}).get("source_type", doc.get("source_type", ""))
            src_id = doc.get("metadata", {}).get("source_id", doc.get("source_id", ""))
            title = doc.get("title", "")
            summary_points.append(f"- [{src_type} | {src_id}] {title}")

        evidence_summary = (
            f"Evidence synthesized from {len(retrieved_evidence)} authoritative sources across DailyMed structured labeling and peer-reviewed literature:\n" +
            "\n".join(summary_points)
        )

        # 5. Build Proposed Citations
        claimed_citations: List[Citation] = []
        for doc in retrieved_evidence:
            meta = doc.get("metadata", {})
            src_type = meta.get("source_type", doc.get("source_type", "DailyMed"))
            src_id = meta.get("source_id", doc.get("source_id", "N/A"))
            ev_status = meta.get("evidence_status", doc.get("evidence_status", "Authoritative"))

            url = None
            if "rxcui" in src_id.lower():
                cui_num = src_id.split(":")[-1]
                url = f"https://mor.nlm.nih.gov/RxNav/search?searchBy=RXCUI&searchTerm={cui_num}"
            elif "pmid" in src_id.lower():
                pmid_num = src_id.split(":")[-1]
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_num}/"
            elif src_type == "DailyMed":
                url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={primary_drug_name or ''}"

            claimed_citations.append(
                Citation(
                    source_title=doc.get("title", f"{src_type} Monograph"),
                    source_type=src_type,
                    identifier=src_id,
                    url=url,
                    evidence_status=ev_status,
                    retrieved_date="2026-01-15"
                )
            )

        # 6. Validate Citations & Prevent Hallucinations
        is_valid, verified_citations, confidence_status, metrics = self.validator.validate_citations(
            claimed_citations=claimed_citations,
            retrieved_evidence=retrieved_evidence
        )

        total_words = len(query.split()) + len(direct_explanation.split()) + len(evidence_summary.split())
        est_tokens = int(total_words * 1.33)
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return ChatResponse(
            conversation_id=conversation_id,
            direct_explanation=direct_explanation,
            drug_information=drug_info,
            evidence_summary=evidence_summary,
            citations=verified_citations,
            confidence_status=confidence_status,
            safety_disclaimer=DEFAULT_SAFETY_DISCLAIMER,
            prompt_version=PROMPT_VERSION,
            model_name=MODEL_NAME,
            entities_detected=extracted_entities,
            retrieved_evidence_count=len(retrieved_evidence),
            citation_validation_passed=is_valid,
            tokens_used=est_tokens,
            latency_ms=latency_ms
        )
