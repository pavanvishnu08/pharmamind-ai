"""
PharmaMind AI - Node2Vec Graph Embedding Engine
Generates dense topology-aware node representations via biased random walks and matrix factorization.
"""

from typing import Dict, List, Tuple, Optional
import math
import logging
import numpy as np
import networkx as nx

logger = logging.getLogger("pharmamind.services.graph_ml")


class Node2VecEmbedder:
    """
    Node2Vec Graph Embedding Algorithm.
    Computes biased random walks (governed by return parameter p and in-out parameter q)
    and derives dense node embeddings via transition PMI matrix factorization.
    """

    def __init__(
        self,
        dimension: int = 64,
        walk_length: int = 15,
        num_walks: int = 10,
        p: float = 1.0,
        q: float = 0.5,
        random_seed: int = 42
    ):
        self.dimension = dimension
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.random_seed = random_seed
        self.rng = np.random.RandomState(random_seed)
        self.embeddings: Dict[str, np.ndarray] = {}

    def _get_transition_probabilities(self, G: nx.Graph, t: str, v: str) -> Tuple[List[str], np.ndarray]:
        """
        Compute 2nd-order Markov transition probabilities for moving from v given previous node t.
        p parameter: Controls likelihood of returning to t (1/p).
        q parameter: Controls likelihood of moving to nodes not connected to t (1/q).
        """
        neighbors = list(G.neighbors(v))
        if not neighbors:
            return [], np.array([])

        unnormalized_probs = []
        for x in neighbors:
            if x == t:
                prob = 1.0 / self.p
            elif G.has_edge(x, t):
                prob = 1.0
            else:
                prob = 1.0 / self.q
            unnormalized_probs.append(prob)

        probs_arr = np.array(unnormalized_probs, dtype=np.float32)
        total = probs_arr.sum()
        if total > 0:
            probs_arr /= total
        else:
            probs_arr = np.ones(len(neighbors)) / len(neighbors)

        return neighbors, probs_arr

    def generate_random_walks(self, G: nx.Graph) -> List[List[str]]:
        """Generate biased random walks for all nodes in the graph."""
        nodes = list(G.nodes())
        walks = []

        for _ in range(self.num_walks):
            self.rng.shuffle(nodes)
            for node in nodes:
                walk = [node]
                while len(walk) < self.walk_length:
                    curr = walk[-1]
                    neighbors = list(G.neighbors(curr))
                    if not neighbors:
                        break

                    if len(walk) == 1:
                        # 1st-order random step
                        next_node = self.rng.choice(neighbors)
                    else:
                        prev = walk[-2]
                        cand_nodes, probs = self._get_transition_probabilities(G, prev, curr)
                        if len(cand_nodes) == 0:
                            break
                        next_node = self.rng.choice(cand_nodes, p=probs)

                    walk.append(next_node)
                walks.append(walk)

        return walks

    def fit(self, G: nx.Graph) -> Dict[str, np.ndarray]:
        """
        Compute dense node embeddings from graph topology using transition co-occurrence SVD.
        Produces L2-normalized vectors of shape (dimension,).
        """
        nodes = list(G.nodes())
        node_to_idx = {n: i for i, n in enumerate(nodes)}
        N = len(nodes)

        if N == 0:
            return {}

        # 1. Generate biased random walks
        walks = self.generate_random_walks(G)

        # 2. Compute co-occurrence matrix within sliding window of size 5
        window_size = 5
        cooccur = np.zeros((N, N), dtype=np.float32)

        for walk in walks:
            for i, center_node in enumerate(walk):
                center_idx = node_to_idx[center_node]
                start = max(0, i - window_size)
                end = min(len(walk), i + window_size + 1)
                for j in range(start, end):
                    if i != j:
                        ctx_idx = node_to_idx[walk[j]]
                        cooccur[center_idx, ctx_idx] += 1.0

        # 3. Compute Shifted Positive Pointwise Mutual Information (SPPMI)
        total_pairs = cooccur.sum()
        if total_pairs == 0:
            # Fallback to Laplacian spectral embeddings
            adj = nx.to_numpy_array(G, nodelist=nodes)
            U, S, _ = np.linalg.svd(adj)
            dim_actual = min(self.dimension, N)
            emb_matrix = U[:, :dim_actual]
            if dim_actual < self.dimension:
                pad = np.zeros((N, self.dimension - dim_actual), dtype=np.float32)
                emb_matrix = np.hstack([emb_matrix, pad])
        else:
            row_sums = cooccur.sum(axis=1, keepdims=True)
            col_sums = cooccur.sum(axis=0, keepdims=True)
            row_sums[row_sums == 0] = 1.0
            col_sums[col_sums == 0] = 1.0

            # Expected under independence: E[i, j] = (row_sum * col_sum) / total_pairs
            expected = (row_sums @ col_sums) / total_pairs
            expected[expected == 0] = 1e-9

            pmi = np.log(np.maximum(cooccur, 1e-9) / expected)
            sppmi = np.maximum(pmi - math.log(1.0), 0.0)

            # Truncated SVD for low-rank representation
            U, S, _ = np.linalg.svd(sppmi)
            dim_actual = min(self.dimension, N)
            emb_matrix = U[:, :dim_actual] * np.sqrt(S[:dim_actual])

            if dim_actual < self.dimension:
                pad = np.zeros((N, self.dimension - dim_actual), dtype=np.float32)
                emb_matrix = np.hstack([emb_matrix, pad])

        # 4. L2 Normalization and dictionary mapping
        self.embeddings = {}
        for i, node in enumerate(nodes):
            vec = emb_matrix[i].astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            else:
                vec[0] = 1.0
            self.embeddings[node] = vec

        return self.embeddings

    def get_embedding(self, node: str) -> Optional[np.ndarray]:
        return self.embeddings.get(node)

