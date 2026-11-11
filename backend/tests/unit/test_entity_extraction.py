"""
Unit tests for Biomedical Named Entity Recognition (NER) Extractor
"""

import unittest
from app.services.entity_extraction.extractor import BiomedicalEntityExtractor


class TestBiomedicalEntityExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = BiomedicalEntityExtractor()

    def test_extract_all_8_categories(self):
        sample_text = (
            "Patients taking Glucophage (metformin) for type 2 diabetes may rarely experience "
            "lactic acidosis. In contrast, Coumadin inhibits VKORC1 in the coagulation cascade "
            "to prevent deep vein thrombosis, though major hemorrhage is a known adverse effect. "
            "Statins inhibit HMG-CoA reductase and may cause myalgia or rhabdomyolysis."
        )

        entities = self.extractor.extract_entities(sample_text)
        self.assertGreater(len(entities), 6)

        labels = {e.label for e in entities}
        self.assertIn("DRUG", labels)
        self.assertIn("INGREDIENT", labels)
        self.assertIn("DISEASE", labels)
        self.assertIn("PROTEIN", labels)
        self.assertIn("PATHWAY", labels)
        self.assertIn("ADVERSE_EFFECT", labels)
        self.assertIn("DRUG_CLASS", labels)
        # Symptoms like myalgia
        self.assertTrue("SYMPTOM" in labels or any("myalgia" in e.text.lower() for e in entities))

    def test_character_offset_accuracy(self):
        text = "Lisinopril is an ACE inhibitor used in hypertension that can cause dry cough or angioedema."
        entities = self.extractor.extract_entities(text)
        self.assertGreater(len(entities), 0)

        for ent in entities:
            # Exact substring match verification
            extracted_substr = text[ent.start_char:ent.end_char]
            self.assertEqual(extracted_substr, ent.text)

    def test_non_overlapping_spans(self):
        text = "Type 2 diabetes mellitus is treated with metformin hydrochloride and lifestyle adjustments."
        entities = self.extractor.extract_entities(text)

        # Ensure no character indices are shared across entities
        covered_indices = set()
        for ent in entities:
            ent_indices = set(range(ent.start_char, ent.end_char))
            self.assertEqual(len(covered_indices & ent_indices), 0, f"Overlap detected for entity '{ent.text}'")
            covered_indices.update(ent_indices)

    def test_ontological_linkage(self):
        text = "Warfarin acts on VKORC1 in atrial fibrillation."
        entities = self.extractor.extract_entities(text)
        ent_dict = {e.text.lower(): e for e in entities}

        self.assertIn("warfarin", ent_dict)
        self.assertEqual(ent_dict["warfarin"].normalized_id, "RxNorm:11289")

        self.assertIn("vkorc1", ent_dict)
        self.assertEqual(ent_dict["vkorc1"].normalized_id, "HGNC:13647")

        self.assertIn("atrial fibrillation", ent_dict)
        self.assertEqual(ent_dict["atrial fibrillation"].normalized_id, "MeSH:D001281")

    def test_empty_and_whitespace_input(self):
        self.assertEqual(self.extractor.extract_entities(""), [])
        self.assertEqual(self.extractor.extract_entities("   \n\t  "), [])

