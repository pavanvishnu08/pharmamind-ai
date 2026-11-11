"""
Unit tests for Biomedical Embedding Service
"""

import unittest
import numpy as np
from app.services.embeddings.biomedical_embedder import BiomedicalEmbeddingService


class TestBiomedicalEmbeddingService(unittest.TestCase):
    def setUp(self):
        self.embedder = BiomedicalEmbeddingService(dimension=384)

    def test_embedding_dimension_and_dtype(self):
        text = "Metformin is a biguanide antidiabetic agent used to improve glycemic control."
        emb = self.embedder.embed_text(text)
        self.assertIsInstance(emb, np.ndarray)
        self.assertEqual(emb.shape, (384,))
        self.assertEqual(emb.dtype, np.float32)

    def test_l2_normalization(self):
        text = "Warfarin competitively inhibits the VKORC1 enzyme in the coagulation cascade."
        emb = self.embedder.embed_text(text)
        norm = float(np.linalg.norm(emb))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_semantic_relatedness_contrast(self):
        # Diabetes-related queries should exhibit higher cosine similarity to each other
        emb_metformin = self.embedder.embed_text("metformin type 2 diabetes mellitus glycemic control")
        emb_glucophage = self.embedder.embed_text("glucophage antidiabetic biguanide lowering glucose")
        emb_warfarin = self.embedder.embed_text("warfarin anticoagulant bleeding risk vkorc1 thrombosis")

        sim_related = float(np.dot(emb_metformin, emb_glucophage))
        sim_unrelated = float(np.dot(emb_metformin, emb_warfarin))

        self.assertGreater(sim_related, sim_unrelated, f"Related sim {sim_related} should exceed unrelated {sim_unrelated}")

    def test_batch_embedding_shape(self):
        texts = [
            "Aspirin irreversibly inhibits cyclooxygenase-1 (COX-1).",
            "Simvastatin reduces cholesterol synthesis via HMG-CoA reductase.",
            "Lisinopril inhibits angiotensin-converting enzyme to lower blood pressure."
        ]
        embs = self.embedder.embed_batch(texts)
        self.assertEqual(embs.shape, (3, 384))
        self.assertEqual(embs.dtype, np.float32)

        for i in range(3):
            norm = float(np.linalg.norm(embs[i]))
            self.assertAlmostEqual(norm, 1.0, places=4)

    def test_empty_string_handling(self):
        emb = self.embedder.embed_text("")
        self.assertEqual(emb.shape, (384,))
        norm = float(np.linalg.norm(emb))
        self.assertAlmostEqual(norm, 1.0, places=4)

