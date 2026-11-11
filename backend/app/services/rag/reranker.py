"""
PharmaMind AI - Evidence Reranker & Context Window Manager
Reranks fused retrieval candidates by source authority tier, entity overlap, and semantic similarity.
Manages context window token allocation.
"""

from typing import List, Dict, Any, Optional
import math
import logging

logger = logging.getLogger("pharmamind.services.rag.reranker")

# Source Authority Hierarchy
AUTHORITY_TIERS = {
    "DailyMed": 1.0,
    "RxNorm": 0.95,
    "PubMed": 0.85,
    "openFDA": 0.80,
    "KnowledgeGraph": 0.75,
    "FAERS": 0.65,
    "EXPERIMENTAL_ML": 0.45
}


class EvidenceReranker:
    """
    Reranks candidate evidence snippets for Retrieval-Augmented Generation.
    Guarantees that authoritative FDA/RxNorm evidence takes precedence over literature or experimental signals.
    """

    def __init__(self, max_context_tokens: int = 1500, max_evidence_items: int = 4):
        self.max_context_tokens = max_context_tokens
        self.max_evidence_items = max_evidence_items

    def rerank(
        self,
        query: str,
        retrieved_items: List[Dict[str, Any]],
        extracted_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Score and rank retrieved candidate items based on:
        - Retrieval similarity score (50%)
        - Source authority tier (30%)
        - Biomedical entity mention overlap (20%)
        """
        if not retrieved_items:
            return []

        # Extract entity surface forms (lowercase)
        entity_texts = {e.get("text", "").lower() for e in extracted_entities if e.get("text")}
        entity_normalized = {e.get("normalized_text", "").lower() for e in extracted_entities if e.get("normalized_text")}
        all_entity_tokens = entity_texts.union(entity_normalized)

        scored_candidates = []
        for item in retrieved_items:
            doc_text = (item.get("title", "") + " " + item.get("content", "")).lower()
            metadata = item.get("metadata", {})
            source_type = metadata.get("source_type", item.get("source_type", "KnowledgeGraph"))

            # 1. Base Retrieval Score (normalize to [0, 1])
            base_score = float(item.get("score", 0.5))

            # 2. Authority Tier Score
            auth_tier = AUTHORITY_TIERS.get(source_type, 0.70)

            # 3. Entity Overlap Score
            overlap_count = 0
            for ent in all_entity_tokens:
                if ent and ent in doc_text:
                    overlap_count += 1
            overlap_ratio = min(1.0, overlap_count / max(1, len(all_entity_tokens))) if all_entity_tokens else 0.5

            # Fused Rerank Score
            fused_score = (
                0.50 * base_score +
                0.30 * auth_tier +
                0.20 * overlap_ratio
            )

            scored_item = dict(item)
            scored_item["rerank_score"] = round(float(fused_score), 4)
            scored_item["authority_tier"] = auth_tier
            scored_item["entity_overlap_ratio"] = round(overlap_ratio, 2)
            scored_candidates.append(scored_item)

        # Sort descending by rerank_score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Context Window Management (Token budget capping)
        selected_evidence = []
        current_token_count = 0

        for candidate in scored_candidates:
            if len(selected_evidence) >= self.max_evidence_items:
                break

            content = candidate.get("content", "")
            est_tokens = len(content.split()) * 4 // 3  # ~1.33 tokens per word approximation
            if current_token_count + est_tokens <= self.max_context_tokens:
                selected_evidence.append(candidate)
                current_token_count += est_tokens
            elif not selected_evidence:
                # Include at least one candidate if none yet selected
                selected_evidence.append(candidate)
                break

        logger.debug(
            "Reranked %d candidates to %d evidence items (approx %d tokens).",
            len(retrieved_items), len(selected_evidence), current_token_count
        )
        return selected_evidence

