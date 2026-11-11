"""
Unit and Functional tests for PharmaMind AI Drug Interaction Intelligence
"""

import unittest
from app.schemas.interaction import InteractionCheckRequest
from app.api.v1.endpoints.interactions import check_drug_interactions
from tests.test_utils import run_sync
from app.database.session import get_sessionmaker
from fastapi import HTTPException


class TestDrugInteractions(unittest.TestCase):
    def test_interaction_check_requires_at_least_two_drugs(self):
        with self.assertRaises(ValueError):
            InteractionCheckRequest(drug_names=["Warfarin"])

    def test_interaction_check_warfarin_aspirin_documented(self):
        req = InteractionCheckRequest(drug_names=["Warfarin", "Aspirin"])
        resp = run_sync(check_drug_interactions(req, None))

        self.assertIsNotNone(resp)
        self.assertEqual(len(resp.normalized_drugs), 2)
        self.assertGreaterEqual(resp.total_interactions_found, 1)

        # Check interaction details
        item = resp.interactions[0]
        self.assertIn("Warfarin", [item.source_drug, item.target_drug])
        self.assertIn("Aspirin", [item.source_drug, item.target_drug])
        self.assertEqual(item.evidence_level, "VERIFIED_AUTHORITATIVE")
        self.assertFalse(item.is_experimental)
        self.assertTrue("bleeding" in item.clinical_effect.lower() or "hemorrhage" in item.clinical_effect.lower())
        self.assertIn("DailyMed", item.provenance_source)
        self.assertGreaterEqual(item.confidence_score, 0.90)

        # Safety notice must be present
        self.assertIn("Educational and informational notice", resp.clinical_safety_notice)

    def test_interaction_check_brand_synonym_resolution(self):
        # Coumadin is brand for Warfarin
        req = InteractionCheckRequest(drug_names=["Coumadin", "Aspirin"])
        resp = run_sync(check_drug_interactions(req, None))

        self.assertIn("Warfarin", resp.normalized_drugs)
        self.assertGreaterEqual(resp.total_interactions_found, 1)

    def test_interaction_check_uncataloged_pair_uncertainty(self):
        # Metformin and Aspirin (no direct interaction in bootstrap graph)
        req = InteractionCheckRequest(drug_names=["Metformin", "Simvastatin"], include_experimental=False)
        resp = run_sync(check_drug_interactions(req, None))

        self.assertIsNotNone(resp.uncertainty_statement)
        self.assertIn("No authoritative interaction record", resp.uncertainty_statement)

    def test_interaction_check_experimental_prediction_labeling(self):
        # Query uncataloged pair with include_experimental=True
        req = InteractionCheckRequest(drug_names=["Metformin", "Simvastatin"], include_experimental=True)
        resp = run_sync(check_drug_interactions(req, None))

        # Check for experimental prediction item
        exp_items = [it for it in resp.interactions if it.is_experimental]
        self.assertGreater(len(exp_items), 0)
        exp_item = exp_items[0]
        self.assertTrue(exp_item.is_experimental)
        self.assertEqual(exp_item.evidence_level, "EXPERIMENTAL_ML_PREDICTION")
        self.assertIn("EXPERIMENTAL ML PREDICTION", exp_item.warning_notice)
        self.assertIn("NOT a verified clinical drug interaction", exp_item.warning_notice)

    def test_interaction_check_three_way_combination(self):
        req = InteractionCheckRequest(drug_names=["Warfarin", "Aspirin", "Simvastatin"])
        resp = run_sync(check_drug_interactions(req, None))

        self.assertEqual(len(resp.normalized_drugs), 3)
        # Should check (Warfarin, Aspirin), (Warfarin, Simvastatin), (Aspirin, Simvastatin)
        self.assertGreaterEqual(resp.total_interactions_found, 2)
