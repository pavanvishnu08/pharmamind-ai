"""
Unit Tests for Database Engine and Model Schemas
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import unittest
from sqlalchemy import create_engine, text
from app.database.base import Base
import app.models

class TestDatabase(unittest.TestCase):
    def test_database_initialization_and_table_creation(self):
        # Synchronous test engine avoids Windows IOCP/asyncio socket restrictions
        engine = create_engine("sqlite:///./pharmamind_test.db", echo=False)
        Base.metadata.create_all(engine)
        
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1"))
            row = res.scalar()
            self.assertEqual(row, 1)
        engine.dispose()
        if os.path.exists("./pharmamind_test.db"):
            try:
                os.remove("./pharmamind_test.db")
            except Exception:
                pass

    def test_all_models_registered_in_metadata(self):
        tables = Base.metadata.tables.keys()
        expected = [
            "users", "drugs", "ingredients", "drug_ingredients",
            "drug_synonyms", "diseases", "adverse_effects",
            "drug_relationships", "publications", "source_records",
            "conversations", "messages", "embedding_records",
            "model_experiments", "evaluation_results"
        ]
        for t in expected:
            self.assertIn(t, tables, f"Table '{t}' missing from SQLAlchemy Base metadata.")


if __name__ == "__main__":
    unittest.main()
