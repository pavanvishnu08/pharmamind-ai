"""
Unit tests for Vector Storage Engines (Numpy & FAISS)
"""

import unittest
import numpy as np
from app.services.semantic_search.vector_store import (
    NumpyVectorStore,
    create_vector_store
)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.dim = 64
        self.store = NumpyVectorStore(dimension=self.dim)

        self.docs = [
            {"id": "doc1", "title": "Metformin Monograph", "doc_type": "monograph"},
            {"id": "doc2", "title": "Warfarin Monograph", "doc_type": "monograph"},
            {"id": "doc3", "title": "Statin Literature Review", "doc_type": "literature"},
        ]

        # Deterministic normalized vectors
        rng = np.random.RandomState(42)
        raw_vecs = rng.randn(3, self.dim).astype(np.float32)
        norms = np.linalg.norm(raw_vecs, axis=1, keepdims=True)
        self.embeddings = raw_vecs / norms

    def test_add_and_search_top_k(self):
        self.store.add_documents(self.docs, self.embeddings)
        self.assertEqual(self.store.total_documents, 3)

        # Query vector exactly equal to doc1
        query_vec = self.embeddings[0]
        results = self.store.search(query_vec, top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "doc1")
        self.assertAlmostEqual(results[0]["similarity_score"], 1.0, places=3)

    def test_metadata_filtering(self):
        self.store.add_documents(self.docs, self.embeddings)

        query_vec = self.embeddings[2]  # Closest to doc3 (literature)
        # Filter for monographs only
        results = self.store.search(query_vec, top_k=5, filters={"doc_type": "monograph"})

        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r["doc_type"], "monograph")
            self.assertIn(r["id"], ["doc1", "doc2"])

    def test_dimension_mismatch_raises_error(self):
        invalid_embs = np.random.randn(2, 32).astype(np.float32)
        with self.assertRaises(ValueError):
            self.store.add_documents(self.docs[:2], invalid_embs)

    def test_clear_index(self):
        self.store.add_documents(self.docs, self.embeddings)
        self.assertEqual(self.store.total_documents, 3)
        self.store.clear()
        self.assertEqual(self.store.total_documents, 0)
        self.assertEqual(self.store.search(self.embeddings[0]), [])

    def test_factory_creation(self):
        store = create_vector_store(dimension=128)
        self.assertIsNotNone(store)
        self.assertEqual(store.dimension, 128)

