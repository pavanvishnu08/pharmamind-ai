"""
Unit tests for Biomedical Transformer Benchmark & Management
"""

import unittest
import torch
from app.services.biomedical_nlp.transformer_benchmark import (
    BiomedicalTransformerManager,
    BIOMEDICAL_MODEL_CARDS
)
from app.core.config import settings


class TestBiomedicalTransformerBenchmark(unittest.TestCase):
    def setUp(self):
        self.manager = BiomedicalTransformerManager(default_model="PubMedBERT")

    def test_cpu_thread_capping_enforced(self):
        # Verify PyTorch thread cap is respected
        current_threads = torch.get_num_threads()
        self.assertEqual(current_threads, settings.TORCH_NUM_THREADS)

    def test_model_cards_presence_and_structure(self):
        cards = self.manager.get_benchmark_cards()
        self.assertEqual(len(cards), 3)

        model_names = {c["model_name"] for c in cards}
        self.assertIn("PubMedBERT", model_names)
        self.assertIn("BioBERT", model_names)
        self.assertIn("ClinicalBERT", model_names)

        # PubMedBERT should be the primary choice for literature and pharmacological search
        pubmed_card = next(c for c in cards if c["model_name"] == "PubMedBERT")
        self.assertTrue(pubmed_card["is_primary_choice"])
        self.assertIn("BLURB", pubmed_card["justification"])
        self.assertEqual(pubmed_card["parameters"], "110M")
        self.assertGreater(pubmed_card["checkpoint_size_mb"], 400.0)

    def test_clinicalbert_justification_boundary(self):
        cards = self.manager.get_benchmark_cards()
        clinical_card = next(c for c in cards if c["model_name"] == "ClinicalBERT")
        self.assertFalse(clinical_card["is_primary_choice"])
        self.assertIn("MIMIC", clinical_card["pretraining_corpus"])
        self.assertIn("clinical notes", clinical_card["justification"].lower())

