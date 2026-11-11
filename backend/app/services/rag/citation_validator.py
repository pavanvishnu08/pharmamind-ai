"""
PharmaMind AI - Citation Validator & Hallucination Detector
Verifies that all generated citations map strictly to retrieved evidence snippets.
Detects ungrounded claims and computes evidence confidence tiers.
"""

from typing import List, Dict, Any, Tuple
import logging
from app.schemas.chat import Citation

logger = logging.getLogger("pharmamind.services.rag.citation_validator")


class CitationValidator:
    """
    Validates factual grounding and citation authenticity against retrieved evidence context.
    Prevents hallucinated PubMed IDs, RxCUIs, or invented FDA labeling references.
    """

    def validate_citations(
        self,
        claimed_citations: List[Citation],
        retrieved_evidence: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Citation], str, Dict[str, Any]]:
        """
        Validate claimed citations against retrieved evidence documents.
        Returns:
            (is_valid, verified_citations, confidence_status, validation_metrics)
        """
        if not retrieved_evidence:
            logger.warning("No retrieved evidence provided for citation validation.")
            return False, [], "INSUFFICIENT_EVIDENCE", {
                "total_claimed": len(claimed_citations),
                "total_verified": 0,
                "hallucination_count": len(claimed_citations),
                "citation_accuracy": 0.0
            }

        # Build set of valid identifiers and source documents from evidence
        valid_identifiers = set()
        valid_titles = set()
        has_authoritative = False
        has_literature = False
        has_experimental = False

        for doc in retrieved_evidence:
            metadata = doc.get("metadata", {})
            src_type = metadata.get("source_type", doc.get("source_type", ""))
            src_id = metadata.get("source_id", doc.get("source_id", ""))
            rxcui = metadata.get("rxnorm_cui")
            pmid = metadata.get("pmid")

            if src_id:
                valid_identifiers.add(src_id.lower())
                # Also add bare numbers / tokens
                valid_identifiers.add(src_id.replace("RxCUI:", "").replace("PMID:", "").lower())
            if rxcui:
                valid_identifiers.add(f"rxcui:{rxcui}".lower())
                valid_identifiers.add(str(rxcui).lower())
            if pmid:
                valid_identifiers.add(f"pmid:{pmid}".lower())
                valid_identifiers.add(str(pmid).lower())

            valid_titles.add(doc.get("title", "").lower())

            if src_type in ("DailyMed", "RxNorm", "openFDA"):
                has_authoritative = True
            elif src_type == "PubMed":
                has_literature = True
            elif "EXPERIMENTAL" in src_type or "EXPERIMENTAL" in str(doc.get("evidence_status", "")):
                has_experimental = True

        verified_citations: List[Citation] = []
        hallucination_count = 0

        for cit in claimed_citations:
            cit_id = cit.identifier.strip().lower()
            cit_title = cit.source_title.strip().lower()

            # Match against valid identifiers or title substrings
            is_grounded = (
                cit_id in valid_identifiers or
                any(cit_id in valid_id or valid_id in cit_id for valid_id in valid_identifiers) or
                any(cit_title in t or t in cit_title for t in valid_titles)
            )

            if is_grounded:
                verified_citations.append(cit)
            else:
                hallucination_count += 1
                logger.warning("Detected hallucinated or ungrounded citation: %s (%s)", cit.source_title, cit.identifier)

        total_claimed = len(claimed_citations)
        accuracy = round(len(verified_citations) / max(1, total_claimed), 2)
        all_valid = (hallucination_count == 0 and len(verified_citations) > 0)

        # Assign confidence status
        if has_authoritative:
            confidence_status = "VERIFIED_AUTHORITATIVE"
        elif has_literature:
            confidence_status = "LITERATURE_SUPPORTED"
        elif has_experimental:
            confidence_status = "EXPERIMENTAL_ML_PREDICTION"
        else:
            confidence_status = "INSUFFICIENT_EVIDENCE"

        metrics = {
            "total_claimed": total_claimed,
            "total_verified": len(verified_citations),
            "hallucination_count": hallucination_count,
            "citation_accuracy": accuracy
        }

        return all_valid, verified_citations, confidence_status, metrics

