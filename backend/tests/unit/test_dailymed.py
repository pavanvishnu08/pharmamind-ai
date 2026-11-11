"""
Unit tests for FDA DailyMed SPL Integration Client
"""

import unittest
from app.integrations.data_sources.dailymed_client import DailyMedClient
from tests.test_utils import run_sync


class TestDailyMedClient(unittest.TestCase):
    def setUp(self):
        self.client = DailyMedClient()

    def test_get_spl_metformin_sections(self):
        spl = run_sync(self.client.get_spl_by_drug_name("metformin"))
        self.assertIsNotNone(spl)
        self.assertEqual(spl.get("generic_name"), "Metformin Hydrochloride")
        self.assertEqual(spl.get("brand_name"), "Glucophage")

        sections = spl.get("sections", {})
        self.assertIn("boxed_warning", sections)
        self.assertIn("LACTIC ACIDOSIS", sections["boxed_warning"])
        self.assertIn("indications_and_usage", sections)
        self.assertIn("type 2 diabetes", sections["indications_and_usage"].lower())
        self.assertIn("contraindications", sections)
        self.assertIn("severe renal impairment", sections["contraindications"].lower())

    def test_get_spl_warfarin_boxed_warning(self):
        spl = run_sync(self.client.get_spl_by_drug_name("warfarin"))
        self.assertIsNotNone(spl)
        sections = spl.get("sections", {})
        self.assertIn("BLEEDING RISK", sections.get("boxed_warning", ""))
        self.assertIn("VKORC1", sections.get("mechanism_of_action", ""))

    def test_get_spl_aspirin_no_boxed_warning(self):
        spl = run_sync(self.client.get_spl_by_drug_name("aspirin"))
        self.assertIsNotNone(spl)
        sections = spl.get("sections", {})
        self.assertIsNone(sections.get("boxed_warning"))
        self.assertIn("cyclooxygenase-1", sections.get("mechanism_of_action", "").lower())

    def test_unknown_drug_spl_returns_none(self):
        spl = run_sync(self.client.get_spl_by_drug_name("unknown_placebo_substance_999"))
        self.assertIsNone(spl)

