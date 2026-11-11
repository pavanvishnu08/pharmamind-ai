"""
Unit tests for NCBI PubMed Literature Client
"""

import unittest
from app.integrations.data_sources.pubmed_client import PubMedClient
from tests.test_utils import run_sync


class TestPubMedClient(unittest.TestCase):
    def setUp(self):
        self.client = PubMedClient()

    def test_search_pubmed_query_match(self):
        pmids = run_sync(self.client.search_pubmed("metformin AMPK gluconeogenesis"))
        self.assertGreater(len(pmids), 0)
        self.assertIn("12558500", pmids)

    def test_get_article_details(self):
        art = run_sync(self.client.get_article_details("11502884"))
        self.assertIsNotNone(art)
        self.assertEqual(art["pmid"], "11502884")
        self.assertIn("Simvastatin", art["abstract"])
        self.assertIn("CYP3A4", art["abstract"])
        self.assertIn("Rhabdomyolysis", art["mesh_terms"])
        self.assertEqual(art["journal"], "Clinical Pharmacokinetics")
        self.assertGreater(art["citation_count"], 100)

    def test_search_and_fetch(self):
        articles = run_sync(self.client.search_and_fetch("warfarin bleeding", max_results=2))
        self.assertGreater(len(articles), 0)
        first = articles[0]
        self.assertIn("pmid", first)
        self.assertIn("title", first)
        self.assertIn("abstract", first)

