"""
Unit Tests for Data Models and Provenance Tracking
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import unittest
from datetime import datetime, timezone
from app.models.drug import Drug, DrugSynonym
from app.models.graph import DrugRelationship
from app.models.user import User
from app.core.security import hash_password, verify_password

class TestModels(unittest.TestCase):
    def test_user_password_hashing(self):
        plain = "SecureBiomedicalPassword123!"
        hashed = hash_password(plain)
        self.assertNotEqual(plain, hashed)
        self.assertTrue(verify_password(plain, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_drug_relationship_provenance(self):
        rel = DrugRelationship(
            source_id="Warfarin",
            source_type="DRUG",
            target_id="Aspirin",
            target_type="DRUG",
            relationship_type="INTERACTS_WITH",
            clinical_effect="Additive bleeding risk",
            evidence_level="VERIFIED_AUTHORITATIVE",
            provenance_source="FDA DailyMed",
            provenance_id="SetID-12345",
            confidence_score=0.99,
            retrieved_date=datetime.now(timezone.utc)
        )
        self.assertEqual(rel.evidence_level, "VERIFIED_AUTHORITATIVE")
        self.assertEqual(rel.provenance_source, "FDA DailyMed")
        self.assertGreaterEqual(rel.confidence_score, 0.9)


if __name__ == "__main__":
    unittest.main()
