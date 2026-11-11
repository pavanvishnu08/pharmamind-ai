"""
PharmaMind AI - Hybrid Search Engine (Dense Semantic + Sparse BM25 Keyword)
Combines dense embedding similarity with Okapi BM25 sparse keyword scoring.
"""

from typing import List, Dict, Any, Optional
import math
import re
import numpy as np

from app.services.embeddings.biomedical_embedder import BiomedicalEmbeddingService
from app.services.semantic_search.vector_store import BaseVectorStore, create_vector_store


class BM25Index:
    """
    Lightweight, high-speed pure-Python Okapi BM25 implementation for biomedical corpora.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_count = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: List[int] = []
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs: List[Dict[str, int]] = []
        self.docs: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9-]{2,}\b", text.lower())

    def index_documents(self, documents: List[Dict[str, Any]], text_field: str = "content") -> None:
        """Build BM25 index from a collection of document dicts."""
        self.docs = documents
        self.doc_count = len(documents)
        if self.doc_count == 0:
            return

        total_len = 0
        self.doc_lengths = []
        self.term_freqs = []
        self.doc_freqs = {}

        for doc in documents:
            text = f"{doc.get('title', '')} {doc.get(text_field, '')} {doc.get('description', '')} {' '.join(doc.get('mesh_terms', []))}"
            tokens = self._tokenize(text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf: Dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.term_freqs.append(tf)

            for token in set(tokens):
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_len / float(self.doc_count) if self.doc_count > 0 else 1.0

    def score(self, query: str) -> List[float]:
        """Compute BM25 score for all indexed documents given a query."""
        if self.doc_count == 0:
            return []

        q_tokens = self._tokenize(query)
        scores = [0.0] * self.doc_count

        for token in q_tokens:
            if token not in self.doc_freqs:
                continue

            df = self.doc_freqs[token]
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)
            idf = max(idf, 0.01)

            for i in range(self.doc_count):
                tf = self.term_freqs[i].get(token, 0)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf * (numerator / denominator)

        # Normalize BM25 scores to [0.0, 1.0] range
        max_score = max(scores) if scores else 0.0
        if max_score > 0:
            scores = [round(s / max_score, 4) for s in scores]

        return scores


class HybridSearchEngine:
    """
    Production-grade Biomedical Hybrid Search Engine.
    Executes dense semantic retrieval + sparse BM25 scoring with reciprocal rank / linear fusion.
    """

    def __init__(
        self,
        embedder: Optional[BiomedicalEmbeddingService] = None,
        vector_store: Optional[BaseVectorStore] = None,
        dense_weight: float = 0.65
    ):
        self.embedder = embedder or BiomedicalEmbeddingService()
        self.vector_store = vector_store or create_vector_store(dimension=self.embedder.dimension)
        self.dense_weight = dense_weight
        self.bm25_index = BM25Index()
        self._indexed_docs: List[Dict[str, Any]] = []

    def index_documents(self, documents: List[Dict[str, Any]], text_field: str = "content") -> None:
        """
        Embed and index documents into both dense vector store and sparse BM25 index.
        """
        if not documents:
            return

        self._indexed_docs = documents

        # Prepare text representations for embedding
        corpus = [
            f"{d.get('title', '')} {d.get(text_field, '')} {d.get('description', '')}".strip()
            for d in documents
        ]

        embeddings = self.embedder.embed_batch(corpus)
        self.vector_store.add_documents(documents, embeddings)
        self.bm25_index.index_documents(documents, text_field=text_field)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute fused hybrid search.
        Score = dense_weight * cosine_sim + (1 - dense_weight) * bm25_score.
        """
        if self.vector_store.total_documents == 0:
            return []

        # 1. Dense Semantic Search
        q_vec = self.embedder.embed_text(query)
        dense_results = self.vector_store.search(q_vec, top_k=self.vector_store.total_documents, filters=filters)
        dense_scores_map = {doc.get("id", str(idx)): doc.get("similarity_score", 0.0) for idx, doc in enumerate(dense_results)}

        # 2. Sparse BM25 Search
        bm25_scores = self.bm25_index.score(query)

        # 3. Score Fusion & Candidate Selection
        fused_candidates = []
        for idx, doc in enumerate(self._indexed_docs):
            doc_id = doc.get("id", str(idx))

            # Apply filters
            if filters:
                if not all(doc.get(k) == v for k, v in filters.items()):
                    continue

            dense_score = dense_scores_map.get(doc_id, 0.0)
            sparse_score = bm25_scores[idx] if idx < len(bm25_scores) else 0.0

            # Linear hybrid fusion
            hybrid_score = round(
                (self.dense_weight * dense_score) + ((1.0 - self.dense_weight) * sparse_score),
                4
            )

            result_item = dict(doc)
            result_item["dense_score"] = float(round(dense_score, 4))
            result_item["sparse_score"] = float(round(sparse_score, 4))
            result_item["hybrid_score"] = float(hybrid_score)
            fused_candidates.append(result_item)

        # 4. Rank by hybrid_score descending
        fused_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return fused_candidates[:top_k]

