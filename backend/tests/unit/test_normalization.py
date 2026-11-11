"""
Unit tests for Biomedical Drug Normalization Service
"""

import unittest
from app.services.drug_normalization.normalizer import (
    DrugNormalizer,
    compute_levenshtein_distance,
    compute_similarity_ratio
)


class TestDrugNormalization(unittest.TestCase):
    def setUp(self):
        self.normalizer = DrugNormalizer()

    def test_levenshtein_distance_and_similarity(self):
        self.assertEqual(compute_levenshtein_distance("metformin", "metformin"), 0)
        self.assertEqual(compute_levenshtein_distance("metformn", "metformin"), 1)
        sim = compute_similarity_ratio("metformn", "metformin")
        self.assertGreater(sim, 0.85)

    def test_salt_stripping(self):
        base, salt = self.normalizer.strip_salts("metformin hydrochloride")
        self.assertEqual(base, "metformin")
        self.assertEqual(salt, "hydrochloride")

        base_na, salt_na = self.normalizer.strip_salts("warfarin sodium")
        self.assertEqual(base_na, "warfarin")
        self.assertEqual(salt_na, "sodium")

        base_hyd, salt_hyd = self.normalizer.strip_salts("lisinopril dihydrate")
        self.assertEqual(base_hyd, "lisinopril")
        self.assertEqual(salt_hyd, "dihydrate")

    def test_normalize_exact_generic(self):
        res = self.normalizer.normalize("Metformin")
        self.assertEqual(res.canonical_name, "metformin")
        self.assertEqual(res.display_name, "Metformin")
        self.assertEqual(res.rxcui, "6809")
        self.assertEqual(res.atc_code, "A10BA02")
        self.assertEqual(res.match_type, "EXACT")
        self.assertEqual(res.confidence_score, 1.0)

    def test_normalize_brand_to_generic(self):
        res = self.normalizer.normalize("Coumadin")
        self.assertEqual(res.canonical_name, "warfarin")
        self.assertEqual(res.display_name, "Warfarin")
        self.assertEqual(res.rxcui, "11289")
        self.assertEqual(res.match_type, "BRAND_MAPPING")
        self.assertEqual(res.original_brand, "Coumadin")

        res_gluc = self.normalizer.normalize("Glucophage")
        self.assertEqual(res_gluc.canonical_name, "metformin")
        self.assertEqual(res_gluc.rxcui, "6809")

        res_lipitor = self.normalizer.normalize("Lipitor")
        self.assertEqual(res_lipitor.canonical_name, "atorvastatin")
        self.assertEqual(res_lipitor.rxcui, "83367")

    def test_normalize_salt_formulation(self):
        res = self.normalizer.normalize("Metformin HCl")
        self.assertEqual(res.canonical_name, "metformin")
        self.assertEqual(res.rxcui, "6809")
        self.assertEqual(res.match_type, "SALT_STRIPPED")
        self.assertEqual(res.salt_removed.lower(), "hcl")

    def test_normalize_typo_fuzzy_matching(self):
        res = self.normalizer.normalize("Metformn")
        self.assertEqual(res.canonical_name, "metformin")
        self.assertEqual(res.match_type, "FUZZY_CORRECTION")
        self.assertGreaterEqual(res.confidence_score, 0.8)

        res_warf = self.normalizer.normalize("Warfrin")
        self.assertEqual(res_warf.canonical_name, "warfarin")
        self.assertEqual(res_warf.match_type, "FUZZY_CORRECTION")

        res_lis = self.normalizer.normalize("Lisinoprl")
        self.assertEqual(res_lis.canonical_name, "lisinopril")

    def test_unknown_entity_handling(self):
        res = self.normalizer.normalize("TotallyUnknownSyntheticSubstance999")
        self.assertEqual(res.match_type, "UNKNOWN")
        self.assertIsNone(res.rxcui)
        self.assertLess(res.confidence_score, 0.5)

