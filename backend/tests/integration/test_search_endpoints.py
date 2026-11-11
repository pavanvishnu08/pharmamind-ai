"""
Integration tests for Semantic & Hybrid Search Endpoints
"""

import unittest
from app.main import app
from app.api.v1.endpoints.search import (
    semantic_search,
    hybrid_search,
    generate_embedding,
    list_model_cards
)
from app.schemas.search import (
    SemanticSearchRequest,
    HybridSearchRequest,
    EmbeddingRequest
)
from tests.test_utils import run_sync


class TestSearchEndpoints(unittest.TestCase):
    def test_routes_registered_in_fastapi(self):
        routes = [route.path for route in app.routes]
        self.assertIn("/api/v1/search/semantic", routes)
        self.assertIn("/api/v1/search/hybrid", routes)
        self.assertIn("/api/v1/search/embed", routes)
        self.assertIn("/api/v1/search/models", routes)

    def test_semantic_search_retrieves_metformin(self):
        req = SemanticSearchRequest(query="type 2 diabetes glucose lowering AMPK", top_k=3)
        resp = run_sync(semantic_search(req))
        self.assertEqual(resp.search_type, "dense_semantic")
        self.assertGreater(resp.total_results, 0)

        top_hit = resp.results[0]
        self.assertIn("metformin", top_hit.title.lower())
        self.assertGreater(top_hit.similarity_score, 0.4)

    def test_hybrid_search_fused_scoring(self):
        req = HybridSearchRequest(
            query="statin CYP3A4 rhabdomyolysis myopathy",
            top_k=3,
            dense_weight=0.65
        )
        resp = run_sync(hybrid_search(req))
        self.assertEqual(resp.search_type, "hybrid_fused")
        self.assertGreater(resp.total_results, 0)

        # Top hit should be statin related
        top_hit = resp.results[0]
        self.assertTrue("statin" in top_hit.title.lower() or "simvastatin" in top_hit.title.lower())
        self.assertIsNotNone(top_hit.dense_score)
        self.assertIsNotNone(top_hit.sparse_score)
        self.assertIsNotNone(top_hit.hybrid_score)

    def test_hybrid_search_metadata_filtering(self):
        req = HybridSearchRequest(
            query="warfarin bleeding",
            top_k=5,
            filters={"doc_type": "literature"}
        )
        resp = run_sync(hybrid_search(req))
        self.assertGreater(resp.total_results, 0)
        for r in resp.results:
            self.assertEqual(r.doc_type, "literature")

    def test_embed_endpoint(self):
        req = EmbeddingRequest(text="Warfarin sodium anticoagulant")
        resp = run_sync(generate_embedding(req))
        self.assertEqual(resp.dimension, 384)
        self.assertEqual(len(resp.vector_preview), 8)
        self.assertAlmostEqual(resp.l2_norm, 1.0, places=3)

    def test_list_model_cards_endpoint(self):
        cards = run_sync(list_model_cards())
        self.assertEqual(len(cards), 3)
        names = [c.model_name for c in cards]
        self.assertIn("PubMedBERT", names)
        self.assertIn("BioBERT", names)
        self.assertIn("ClinicalBERT", names)

