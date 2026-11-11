"""
Unit tests for Node2Vec Graph Embedding Engine
"""

import unittest
import numpy as np
import networkx as nx
from app.services.graph_ml.node2vec import Node2VecEmbedder


class TestNode2VecEmbedder(unittest.TestCase):
    def setUp(self):
        # Create a small benchmark graph (Karate Club or synthetic clique)
        self.G = nx.karate_club_graph()
        self.embedder = Node2VecEmbedder(
            dimension=32,
            walk_length=10,
            num_walks=5,
            p=1.0,
            q=0.5,
            random_seed=42
        )

    def test_random_walk_generation(self):
        walks = self.embedder.generate_random_walks(self.G)
        self.assertGreater(len(walks), 0)
        # Check first walk
        first_walk = walks[0]
        self.assertEqual(len(first_walk), 10)
        # Every adjacent step must be an edge in G
        for i in range(len(first_walk) - 1):
            u, v = first_walk[i], first_walk[i + 1]
            self.assertTrue(self.G.has_edge(u, v) or u == v)

    def test_node2vec_embedding_properties(self):
        embeddings = self.embedder.fit(self.G)
        self.assertEqual(len(embeddings), self.G.number_of_nodes())

        for node, vec in embeddings.items():
            self.assertIsInstance(vec, np.ndarray)
            self.assertEqual(vec.shape, (32,))
            self.assertEqual(vec.dtype, np.float32)
            # L2 normalization test
            norm = float(np.linalg.norm(vec))
            self.assertAlmostEqual(norm, 1.0, places=4)

    def test_deterministic_reproducibility(self):
        emb1 = Node2VecEmbedder(dimension=16, random_seed=99).fit(self.G)
        emb2 = Node2VecEmbedder(dimension=16, random_seed=99).fit(self.G)

        first_node = list(self.G.nodes())[0]
        np.testing.assert_array_almost_equal(emb1[first_node], emb2[first_node], decimal=4)

