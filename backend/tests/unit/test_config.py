"""
Unit Tests for PharmaMind AI Configuration
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import unittest
from app.core.config import settings

class TestConfig(unittest.TestCase):
    def test_project_name_and_version(self):
        self.assertEqual(settings.PROJECT_NAME, "PharmaMind AI")
        self.assertIsNotNone(settings.VERSION)

    def test_hardware_constraints(self):
        self.assertEqual(settings.ML_DEVICE, "cpu")
        self.assertEqual(settings.TORCH_NUM_THREADS, 4)
        self.assertTrue(settings.ENABLE_LAZY_MODEL_LOADING)
        self.assertLessEqual(settings.MAX_BATCH_SIZE, 16)
        self.assertGreaterEqual(settings.MEMORY_SAFETY_THRESHOLD_MB, 512)

    def test_database_settings(self):
        self.assertTrue(settings.DATABASE_FALLBACK_SQLITE)
        self.assertIn("sqlite", settings.SQLITE_URL)
        self.assertIn("5432", settings.DATABASE_URL)

    def test_cors_origins_configured(self):
        self.assertTrue(len(settings.CORS_ORIGINS) > 0)
        self.assertTrue(any("5173" in url for url in settings.CORS_ORIGINS))


if __name__ == "__main__":
    unittest.main()
