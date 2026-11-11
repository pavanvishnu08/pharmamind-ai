"""
Integration tests for Knowledge Graph & Graph ML Endpoints
"""

import unittest
from app.main import app
from app.api.v1.endpoints.knowledge_graph import (
    get_knowledge_graph,
    get_entity_subgraph,
    get_explanatory_path,
    predict_graph_link,
    get_graph_ml_benchmarks
)
from app.schemas.graph import LinkPredictionRequest
from tests.test_utils import run_sync


class TestGraphEndpoints(unittest.TestCase):
    def test_routes_registered_in_fastapi(self):
        routes = [route.path for route in app.routes]
        self.assertIn("/api/v1/graph", routes)
        self.assertIn("/api/v1/graph/subgraph/{entity_id}", routes)
        self.assertIn("/api/v1/graph/path", routes)
        self.assertIn("/api/v1/graph/predict-interaction", routes)
        self.assertIn("/api/v1/graph/ml-benchmark", routes)

    def test_get_knowledge_graph_full(self):
        resp = run_sync(get_knowledge_graph(node_type=None, relationship_type=None, db=None))
        self.assertGreater(resp.total_nodes, 10)
        self.assertGreater(resp.total_edges, 10)
        self.assertIn("FDA DailyMed", resp.provenance_summary)

    def test_get_knowledge_graph_filtered_by_node_type(self):
        resp = run_sync(get_knowledge_graph(node_type="DRUG", relationship_type=None, db=None))
        for n in resp.nodes:
            self.assertEqual(n.node_type, "DRUG")

    def test_get_subgraph_warfarin(self):
        resp = run_sync(get_entity_subgraph("Warfarin", radius=1))
        self.assertEqual(resp.center_node, "Warfarin")
        self.assertGreater(resp.total_nodes, 1)
        self.assertGreater(resp.total_edges, 1)

    def test_get_explanatory_path(self):
        resp = run_sync(get_explanatory_path(source="Warfarin", target="Thrombosis"))
        self.assertTrue(resp.path_found)
        self.assertGreaterEqual(resp.length, 1)
        self.assertGreater(len(resp.path), 0)

    def test_predict_interaction_safety_labeling(self):
        req = LinkPredictionRequest(source_id="Warfarin", target_id="Simvastatin")
        resp = run_sync(predict_graph_link(req))
        self.assertEqual(resp.source, "Warfarin")
        self.assertEqual(resp.target, "Simvastatin")
        self.assertTrue(resp.is_experimental)
        self.assertEqual(resp.evidence_level, "EXPERIMENTAL_ML_PREDICTION")
        self.assertIn("EXPERIMENTAL ML PREDICTION", resp.warning_notice)
        self.assertGreaterEqual(resp.probability, 0.0)
        self.assertLessEqual(resp.probability, 1.0)

    def test_ml_benchmark_metrics(self):
        resp = run_sync(get_graph_ml_benchmarks())
        self.assertGreaterEqual(resp.auroc, 0.50)
        self.assertGreaterEqual(resp.auprc, 0.50)
        self.assertEqual(resp.negative_sampling_ratio, "1:1")
        self.assertTrue(resp.leakage_prevention_verified)
        self.assertIn("EXPERIMENTAL", resp.disclaimer)

