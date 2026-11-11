"""
Unit tests for NLM RxNorm Integration Client
"""

import unittest
from app.integrations.data_sources.rxnorm_client import RxNormClient
from tests.test_utils import run_sync


class TestRxNormClient(unittest.TestCase):
    def setUp(self):
        self.client = RxNormClient()

    def test_get_rxcui_by_canonical_name(self):
        rxcui = run_sync(self.client.get_rxcui_by_name("metformin"))
        self.assertEqual(rxcui, "6809")

        rxcui_warfarin = run_sync(self.client.get_rxcui_by_name("warfarin"))
        self.assertEqual(rxcui_warfarin, "11289")

    def test_get_rxcui_case_insensitivity(self):
        rxcui = run_sync(self.client.get_rxcui_by_name("LISINOPRIL"))
        self.assertEqual(rxcui, "29046")

    def test_get_brand_names(self):
        brands = run_sync(self.client.get_brand_names("6809"))
        self.assertIn("Glucophage", brands)

        brands_warfarin = run_sync(self.client.get_brand_names("11289"))
        self.assertIn("Coumadin", brands_warfarin)

    def test_get_all_properties(self):
        props = run_sync(self.client.get_all_properties("36567"))
        self.assertIsNotNone(props)
        self.assertEqual(props.get("name"), "Simvastatin")
        self.assertEqual(props.get("atc_code"), "C10AA01")
        self.assertIn("HMG-CoA Reductase Inhibitor", props.get("drug_class", ""))

    def test_approximate_match_typo(self):
        matches = run_sync(self.client.approximate_match("metformn"))
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0]["rxcui"], "6809")

    def test_unknown_drug_returns_none(self):
        rxcui = run_sync(self.client.get_rxcui_by_name("nonexistent_fictional_drug_xyz"))
        self.assertIsNone(rxcui)

