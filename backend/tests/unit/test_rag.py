"""
Unit tests for PharmaMind AI Retrieval-Augmented Generation (RAG) & Citation Validation
"""

import unittest
from app.schemas.chat import Citation
from app.core.exceptions import MedicalAdviceProhibitedException
from app.services.rag.pipeline import PharmaMindRAGPipeline
from app.services.rag.reranker import EvidenceReranker
from app.services.rag.citation_validator import CitationValidator
from app.services.rag.evidence_corpus import BENCHMARK_EVIDENCE_DOCUMENTS


class TestRAGPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = PharmaMindRAGPipeline()
        self.validator = CitationValidator()
        self.reranker = EvidenceReranker()

    def test_rag_pipeline_warfarin_monograph_and_citations(self):
        query = "What is the mechanism of action and boxed warning of Warfarin?"
        resp = self.pipeline.execute(query=query)

        self.assertIsNotNone(resp)
        self.assertIn("Warfarin", resp.direct_explanation)
        self.assertIn("VKORC1", resp.direct_explanation)
        self.assertIsNotNone(resp.drug_information)
        self.assertEqual(resp.drug_information["generic_name"], "Warfarin")
        self.assertEqual(resp.drug_information["rxnorm_cui"], "11289")

        # Verify authoritative citations
        self.assertGreater(len(resp.citations), 0)
        has_dailymed = any(c.source_type == "DailyMed" for c in resp.citations)
        self.assertTrue(has_dailymed)
        self.assertEqual(resp.confidence_status, "VERIFIED_AUTHORITATIVE")
        self.assertTrue(resp.citation_validation_passed)

        # Safety disclaimer must be present
        self.assertIn("educational and informational", resp.safety_disclaimer)

    def test_rag_pipeline_metformin_ampk(self):
        query = "How does metformin affect AMPK in type 2 diabetes?"
        resp = self.pipeline.execute(query=query)

        self.assertIsNotNone(resp)
        self.assertIn("Metformin", resp.direct_explanation)
        self.assertEqual(resp.confidence_status, "VERIFIED_AUTHORITATIVE")
        self.assertTrue(resp.citation_validation_passed)
        self.assertGreater(resp.tokens_used, 0)
        self.assertGreater(resp.latency_ms, 0.0)

    def test_citation_validator_detects_hallucination(self):
        claimed = [
            Citation(
                source_title="FDA DailyMed: Warfarin Sodium",
                source_type="DailyMed",
                identifier="RxCUI:11289",
                evidence_status="Authoritative",
                retrieved_date="2026-01-15"
            ),
            Citation(
                source_title="Completely Fabricated Study on Miracle Cure",
                source_type="PubMed",
                identifier="PMID:9999999999",  # Fake ID
                evidence_status="Literature",
                retrieved_date="2026-01-15"
            )
        ]

        is_valid, verified, conf, metrics = self.validator.validate_citations(
            claimed_citations=claimed,
            retrieved_evidence=BENCHMARK_EVIDENCE_DOCUMENTS
        )

        self.assertFalse(is_valid)
        self.assertEqual(metrics["hallucination_count"], 1)
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0].identifier, "RxCUI:11289")

    def test_rag_refusal_guardrails_on_prescribing(self):
        with self.assertRaises(MedicalAdviceProhibitedException):
            self.pipeline.execute("Can you prescribe me a dosage for my hypertension?")

    def test_rag_insufficient_evidence_handling(self):
        query = "What are the indications for FictionalUnknownDrugXYZ123?"
        resp = self.pipeline.execute(query=query)

        self.assertEqual(resp.confidence_status, "INSUFFICIENT_EVIDENCE")
        self.assertIn("Unable to locate verified pharmacological evidence", resp.direct_explanation)
        self.assertEqual(len(resp.citations), 0)

    def test_reranker_prioritizes_authoritative_tier(self):
        candidates = [
            {
                "title": "PubMed Research Paper",
                "content": "A study on drug properties.",
                "score": 0.80,
                "metadata": {"source_type": "PubMed"}
            },
            {
                "title": "FDA DailyMed Package Insert",
                "content": "Authoritative FDA package insert.",
                "score": 0.80,
                "metadata": {"source_type": "DailyMed"}
            }
        ]
        reranked = self.reranker.rerank(
            query="drug properties",
            retrieved_items=candidates,
            extracted_entities=[]
        )
        self.assertEqual(reranked[0]["metadata"]["source_type"], "DailyMed")

