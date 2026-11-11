"""
Unit tests for PharmaMind AI Empirical Evaluation Service
"""

import unittest
from app.services.evaluation.evaluator import PharmaMindEvaluator


class TestEvaluationService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = PharmaMindEvaluator()

    def test_evaluate_biomedical_nlp(self):
        nlp = self.evaluator.evaluate_biomedical_nlp()
        self.assertIsNotNone(nlp)
        self.assertGreaterEqual(nlp["precision"], 0.70)
        self.assertGreaterEqual(nlp["recall"], 0.70)
        self.assertGreaterEqual(nlp["f1_score"], 0.70)
        self.assertEqual(nlp["sample_size"], 5)

    def test_evaluate_semantic_search(self):
        search = self.evaluator.evaluate_semantic_search()
        self.assertIsNotNone(search)
        self.assertEqual(search["recall_at_5"], 1.0)
        self.assertGreaterEqual(search["mrr"], 0.70)
        self.assertGreaterEqual(search["ndcg_at_10"], 0.70)
        self.assertEqual(search["sample_size"], 5)

    def test_evaluate_graph_ml(self):
        graph = self.evaluator.evaluate_graph_ml()
        self.assertIsNotNone(graph)
        self.assertGreaterEqual(graph["auroc"], 0.70)
        self.assertGreaterEqual(graph["auprc"], 0.70)
        self.assertLessEqual(graph["brier_score_calibration"], 0.40)
        self.assertTrue(graph["leakage_prevention_verified"])

    def test_evaluate_rag_pipeline(self):
        rag = self.evaluator.evaluate_rag_pipeline()
        self.assertIsNotNone(rag)
        self.assertGreaterEqual(rag["faithfulness"], 0.80)
        self.assertGreaterEqual(rag["answer_relevance"], 0.80)
        self.assertGreaterEqual(rag["citation_accuracy"], 0.80)
        self.assertEqual(rag["sample_size"], 3)

    def test_run_all_evaluations(self):
        full_report = self.evaluator.run_all_evaluations()
        self.assertIn("nlp", full_report)
        self.assertIn("retrieval", full_report)
        self.assertIn("graph_ml", full_report)
        self.assertIn("rag", full_report)
        self.assertGreater(full_report["benchmark_execution_time_ms"], 0.0)

