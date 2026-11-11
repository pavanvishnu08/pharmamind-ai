"""
Unit tests for openFDA Labeling & FAERS Adverse Event Client
"""

import unittest
from app.integrations.data_sources.openfda_client import OpenFDAClient, FAERS_CAUSALITY_DISCLAIMER
from tests.test_utils import run_sync


class TestOpenFDAClient(unittest.TestCase):
    def setUp(self):
        self.client = OpenFDAClient()

    def test_get_drug_labeling(self):
        label = run_sync(self.client.get_drug_labeling("simvastatin"))
        self.assertIsNotNone(label)
        self.assertEqual(label.get("generic_name"), "Simvastatin")
        self.assertIn("myopathy", label.get("warnings", "").lower())
        self.assertEqual(label.get("provenance_source"), "openFDA Drug Labeling API")

    def test_faers_signals_enforces_non_causality_guardrails(self):
        signals = run_sync(self.client.get_adverse_event_signals("warfarin"))
        self.assertIsNotNone(signals)
        # CRITICAL TEST: Must NEVER claim causality
        self.assertFalse(signals["is_causal_confirmed"])
        self.assertEqual(signals["confidence_status"], "EPIDEMIOLOGICAL_SIGNAL_ONLY")
        self.assertIn("does NOT establish pharmacological causality", signals["disclaimer"])

        # Check MedDRA terms
        reactions = signals["top_adverse_reactions"]
        self.assertGreater(len(reactions), 0)
        terms = [r["term"] for r in reactions]
        self.assertIn("HAEMORRHAGE", terms)
        self.assertGreater(signals["signal_count"], 0)

    def test_faers_signals_simvastatin(self):
        signals = run_sync(self.client.get_adverse_event_signals("simvastatin"))
        self.assertFalse(signals["is_causal_confirmed"])
        terms = [r["term"] for r in signals["top_adverse_reactions"]]
        self.assertIn("RHABDOMYOLYSIS", terms)

    def test_faers_signals_unknown_drug_preserves_disclaimer(self):
        signals = run_sync(self.client.get_adverse_event_signals("fictional_unregistered_molecule"))
        self.assertFalse(signals["is_causal_confirmed"])
        self.assertEqual(len(signals["top_adverse_reactions"]), 0)
        self.assertEqual(signals["signal_count"], 0)
        self.assertIn("does NOT establish pharmacological causality", signals["disclaimer"])

