"""
Integration and Functional Tests for PharmaMind AI FastAPI Endpoints
Tests handlers, schemas, validation rules, and medical advice guardrails.
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.chat import ChatMessageRequest
from app.schemas.interaction import InteractionCheckRequest
from app.api.v1.endpoints.assistant import _check_safety_guardrails
from app.core.exceptions import MedicalAdviceProhibitedException
from app.api.v1.endpoints.evaluation import get_evaluation_dashboard
from app.api.v1.endpoints.literature import search_literature

def run_coro_sync(coro):
    """Drive a simple coroutine without starting an OS socket event loop."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value

class TestAPIEndpoints(unittest.TestCase):
    def test_root_endpoint_metadata(self):
        # Direct route resolution
        routes = [route.path for route in app.routes]
        self.assertIn("/", routes)
        self.assertIn("/api/v1/health", routes)
        self.assertIn("/api/v1/drugs", routes)
        self.assertIn("/api/v1/interactions/check", routes)
        self.assertIn("/api/v1/graph", routes)
        self.assertIn("/api/v1/literature", routes)
        self.assertIn("/api/v1/assistant", routes)
        self.assertIn("/api/v1/evaluation", routes)
        self.assertIn("/api/v1/auth/register", routes)
        self.assertIn("/api/v1/auth/login", routes)

    def test_safety_guardrail_refusal_for_prescribing(self):
        # Ensure queries requesting medical prescribing or diagnosis are strictly refused
        prohibited_queries = [
            "What dosage for me should I take?",
            "Can you diagnose me with diabetes?",
            "How much should I take of this drug?",
            "Stop taking my medication immediately"
        ]
        for q in prohibited_queries:
            with self.assertRaises(MedicalAdviceProhibitedException):
                _check_safety_guardrails(q)

    def test_safety_guardrail_allows_educational_queries(self):
        educational_queries = [
            "What is the mechanism of action of Metformin?",
            "Are there documented interactions between Warfarin and Aspirin?",
            "Explain the pharmacokinetics of Simvastatin"
        ]
        for q in educational_queries:
            # Should pass without exception
            _check_safety_guardrails(q)

    def test_research_literature_search(self):
        results = run_coro_sync(search_literature(q="Metformin", limit=5))
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("Metformin", results[0].title)
        self.assertIn("AMPK", results[0].mesh_terms)
        self.assertEqual(results[0].pmid, "11502884")

    def test_evaluation_dashboard_logic_and_transparency(self):
        resp = run_coro_sync(get_evaluation_dashboard())
        self.assertIsNotNone(resp.system_metrics)
        self.assertGreater(len(resp.nlp_metrics), 0)
        self.assertGreater(len(resp.retrieval_metrics), 0)
        self.assertGreater(len(resp.graph_ml_metrics), 0)
        self.assertGreater(len(resp.rag_metrics), 0)
        # Verify honest reporting of untested components
        untested = [m for m in resp.nlp_metrics if not m.is_tested]
        self.assertTrue(len(untested) > 0)
        self.assertEqual(untested[0].benchmark_status, "UNTESTED")


if __name__ == "__main__":
    unittest.main()
