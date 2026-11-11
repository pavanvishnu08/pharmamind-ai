"""
Integration tests for Biomedical Data Ingestion Pipeline & Phase 2 Endpoints
"""

import unittest
from app.services.data_ingestion.pipeline import DataIngestionPipeline
from app.api.v1.endpoints.drugs import normalize_drug, extract_biomedical_entities, ingest_drug
from app.api.v1.endpoints.interactions import get_faers_signals
from app.schemas.drug import DrugNormalizationRequest, EntityExtractionRequest, DrugIngestionRequest
from tests.test_utils import run_sync


class TestDataIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = DataIngestionPipeline()

    def test_full_monograph_ingestion_metformin(self):
        result = run_sync(self.pipeline.ingest_drug_monograph("Metformin HCl"))
        self.assertIsNotNone(result)
        self.assertEqual(result.generic_name, "Metformin")
        self.assertEqual(result.rxcui, "6809")
        self.assertEqual(result.atc_code, "A10BA02")

        # Sections
        sections = result.monograph_sections
        self.assertIn("boxed_warning", sections)
        self.assertIn("LACTIC ACIDOSIS", sections["boxed_warning"])
        self.assertIn("indications_and_usage", sections)

        # FAERS Postmarketing Signals
        faers = result.faers_signals
        self.assertFalse(faers["is_causal_confirmed"])
        self.assertIn("does NOT establish pharmacological causality", faers["disclaimer"])

        # Quality Report
        qr = result.quality_report
        self.assertTrue(qr.is_valid)
        self.assertGreater(qr.quality_score, 0.70)
        self.assertEqual(qr.deduplication_status, "NEW_RECORD")

        # Provenance Retention
        prov = result.provenance_records
        self.assertGreaterEqual(len(prov), 3)
        sources = {p["source_name"] for p in prov}
        self.assertIn("NLM RxNorm", sources)
        self.assertIn("FDA DailyMed", sources)
        self.assertIn("FDA Adverse Event Reporting System (FAERS)", sources)

    def test_deduplication_detection(self):
        # First ingestion
        res1 = run_sync(self.pipeline.ingest_drug_monograph("Warfarin"))
        self.assertEqual(res1.quality_report.deduplication_status, "NEW_RECORD")

        # Second ingestion with brand name "Coumadin" resolving to Warfarin
        res2 = run_sync(self.pipeline.ingest_drug_monograph("Coumadin"))
        self.assertEqual(res2.quality_report.deduplication_status, "MERGED_EXISTING")

    def test_normalization_api_endpoint(self):
        req = DrugNormalizationRequest(query="Glucophage 500mg")
        resp = run_sync(normalize_drug(req))
        self.assertEqual(resp.canonical_name, "metformin")
        self.assertEqual(resp.display_name, "Metformin")
        self.assertEqual(resp.rxcui, "6809")
        self.assertEqual(resp.match_type, "BRAND_MAPPING")

    def test_entity_extraction_api_endpoint(self):
        req = EntityExtractionRequest(
            text="Warfarin inhibits VKORC1 to prevent deep vein thrombosis, but risk of major hemorrhage exists."
        )
        resp = run_sync(extract_biomedical_entities(req))
        self.assertGreater(resp.entity_count, 2)
        labels = {e.label for e in resp.entities}
        self.assertIn("INGREDIENT", labels)
        self.assertIn("PROTEIN", labels)
        self.assertIn("DISEASE", labels)

    def test_ingestion_api_endpoint(self):
        req = DrugIngestionRequest(drug_name="Simvastatin")
        resp = run_sync(ingest_drug(req))
        self.assertEqual(resp.generic_name, "Simvastatin")
        self.assertEqual(resp.rxcui, "36567")
        self.assertFalse(resp.faers_signals["is_causal_confirmed"])
        self.assertTrue(resp.quality_report["is_valid"])

    def test_faers_signals_api_endpoint(self):
        resp = run_sync(get_faers_signals("warfarin"))
        self.assertEqual(resp.drug_name, "Warfarin")
        self.assertFalse(resp.is_causal_confirmed)
        self.assertIn("does NOT establish pharmacological causality", resp.disclaimer)
        self.assertGreater(len(resp.top_adverse_reactions), 0)

