"""
Unit tests for Graph ML Link Predictor & Leakage Prevention
"""

import unittest
from app.services.knowledge_graph.graph_engine import build_default_biomedical_graph
from app.services.graph_ml.link_predictor import GraphLinkPredictor, MANDATORY_EXPERIMENTAL_DISCLAIMER


class TestGraphLinkPredictor(unittest.TestCase):
    def setUp(self):
        self.kg = build_default_biomedical_graph()
        self.predictor = GraphLinkPredictor(
            dimension=32,
            walk_length=10,
            num_walks=5,
            edge_operator="hadamard",
            random_seed=42
        )

    def test_train_and_evaluate_metrics(self):
        results = self.predictor.train_and_evaluate(self.kg, test_ratio=0.25)
        self.assertIsNotNone(results)

        # Check required evaluation dimensions
        self.assertIn("auroc", results)
        self.assertIn("auprc", results)
        self.assertIn("precision", results)
        self.assertIn("recall", results)
        self.assertIn("f1_score", results)
        self.assertIn("brier_score_calibration", results)

        # AUROC should be higher than random baseline (0.50)
        self.assertGreaterEqual(results["auroc"], 0.50)
        # Brier calibration score should be reasonable (<= 0.5)
        self.assertLessEqual(results["brier_score_calibration"], 0.40)
        self.assertTrue(results["leakage_prevention_verified"])

    def test_predict_link_enforces_experimental_safety_labeling(self):
        self.predictor.train_and_evaluate(self.kg, test_ratio=0.20)

        pred = self.predictor.predict_link("Warfarin", "Simvastatin")
        self.assertIsNotNone(pred)
        # CRITICAL TEST: Must NEVER represent prediction as clinically confirmed interaction
        self.assertTrue(pred["is_experimental"])
        self.assertEqual(pred["evidence_level"], "EXPERIMENTAL_ML_PREDICTION")
        self.assertIn("EXPERIMENTAL ML PREDICTION", pred["warning_notice"])
        self.assertIn("NOT a verified clinical drug interaction", pred["warning_notice"])
        self.assertGreaterEqual(pred["probability"], 0.0)
        self.assertLessEqual(pred["probability"], 1.0)

    def test_predict_link_unknown_node(self):
        self.predictor.train_and_evaluate(self.kg, test_ratio=0.20)
        pred = self.predictor.predict_link("Warfarin", "UnknownFictionalDrugXYZ")
        self.assertTrue(pred["is_experimental"])
        self.assertEqual(pred["probability"], 0.0)
        self.assertEqual(pred["status"], "NODE_NOT_IN_TRAINING_GRAPH")

