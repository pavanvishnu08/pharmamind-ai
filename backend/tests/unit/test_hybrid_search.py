"""
Unit tests for Hybrid Search Engine & Okapi BM25 Index
"""

import unittest
from app.services.semantic_search.hybrid_search import BM25Index, HybridSearchEngine
from app.services.embeddings.biomedical_embedder import BiomedicalEmbeddingService
from app.services.semantic_search.vector_store import NumpyVectorStore


class TestHybridSearch(unittest.TestCase):
    def setUp(self):
        self.corpus = [
            {
                "id": "metformin_doc",
                "title": "Metformin Hydrochloride Monograph",
                "content": "First-line biguanide oral agent indicated for type 2 diabetes mellitus. Activates AMPK and reduces hepatic gluconeogenesis.",
                "doc_type": "monograph"
            },
            {
                "id": "warfarin_doc",
                "title": "Warfarin Sodium Anticoagulant",
                "content": "Vitamin K antagonist oral anticoagulant indicated for deep vein thrombosis and pulmonary embolism. Inhibits VKORC1.",
                "doc_type": "monograph"
            },
            {
                "id": "simvastatin_doc",
                "title": "Simvastatin Statin Therapy",
                "content": "HMG-CoA reductase inhibitor for hyperlipidemia. Metabolized by CYP3A4, risk of myopathy and rhabdomyolysis.",
                "doc_type": "literature"
            }
        ]

        self.bm25 = BM25Index()
        self.bm25.index_documents(self.corpus, text_field="content")

        self.embedder = BiomedicalEmbeddingService(dimension=64)
        self.vector_store = NumpyVectorStore(dimension=64)
        self.hybrid_engine = HybridSearchEngine(
            embedder=self.embedder,
            vector_store=self.vector_store,
            dense_weight=0.60
        )
        self.hybrid_engine.index_documents(self.corpus, text_field="content")

    def test_bm25_scoring(self):
        scores = self.bm25.score("diabetes gluconeogenesis AMPK")
        self.assertEqual(len(scores), 3)
        # First document should have highest BM25 score
        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[0], scores[2])
        self.assertAlmostEqual(scores[0], 1.0, places=3)

    def test_hybrid_fused_search(self):
        results = self.hybrid_engine.search("type 2 diabetes glycemic control", top_k=3)
        self.assertEqual(len(results), 3)

        top_hit = results[0]
        self.assertEqual(top_hit["id"], "metformin_doc")
        self.assertIn("dense_score", top_hit)
        self.assertIn("sparse_score", top_hit)
        self.assertIn("hybrid_score", top_hit)

        # Verify linear fusion formula
        expected_hybrid = round(
            (0.60 * top_hit["dense_score"]) + (0.40 * top_hit["sparse_score"]),
            4
        )
        self.assertAlmostEqual(top_hit["hybrid_score"], expected_hybrid, places=3)

    def test_hybrid_search_with_metadata_filter(self):
        results = self.hybrid_engine.search(
            "statin rhabdomyolysis",
            top_k=5,
            filters={"doc_type": "literature"}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "simvastatin_doc")
        self.assertEqual(results[0]["doc_type"], "literature")

