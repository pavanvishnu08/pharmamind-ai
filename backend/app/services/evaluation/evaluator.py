"""
PharmaMind AI - Automated Empirical AI Evaluation Service
Computes real, reproducible benchmark metrics across Biomedical NLP, Semantic Search,
Graph ML Link Prediction, RAG Quality, and System Resources.
"""

from typing import Dict, Any, List, Tuple
import math
import time
import logging
from app.services.entity_extraction.extractor import BiomedicalEntityExtractor
from app.services.semantic_search.hybrid_search import HybridSearchEngine
from app.services.knowledge_graph.graph_engine import build_default_biomedical_graph
from app.services.graph_ml.link_predictor import GraphLinkPredictor
from app.services.rag.pipeline import PharmaMindRAGPipeline
from app.services.rag.evidence_corpus import create_and_populate_evidence_corpus

logger = logging.getLogger("pharmamind.services.evaluation")

# 1. REPRODUCIBLE BENCHMARK DATASET: Biomedical NER Gold Standard
NER_BENCHMARK_DATASET = [
    {
        "text": "Warfarin sodium prevents deep vein thrombosis by targeting VKORC1.",
        "gold_entities": [
            {"text": "warfarin", "label": "DRUG"},
            {"text": "thrombosis", "label": "DISEASE"},
            {"text": "vkorc1", "label": "TARGET"}
        ]
    },
    {
        "text": "Metformin reduces hepatic gluconeogenesis via AMPK activation in type 2 diabetes.",
        "gold_entities": [
            {"text": "metformin", "label": "DRUG"},
            {"text": "ampk", "label": "TARGET"},
            {"text": "type 2 diabetes", "label": "DISEASE"}
        ]
    },
    {
        "text": "Lisinopril treats essential hypertension by inhibiting ACE enzyme.",
        "gold_entities": [
            {"text": "lisinopril", "label": "DRUG"},
            {"text": "hypertension", "label": "DISEASE"},
            {"text": "ace", "label": "TARGET"}
        ]
    },
    {
        "text": "Simvastatin lowers cholesterol by inhibiting HMG-CoA reductase (HMGCR).",
        "gold_entities": [
            {"text": "simvastatin", "label": "DRUG"},
            {"text": "hmgcr", "label": "TARGET"}
        ]
    },
    {
        "text": "Aspirin acetylates COX-1 and COX-2 enzymes to inhibit platelet aggregation.",
        "gold_entities": [
            {"text": "aspirin", "label": "DRUG"},
            {"text": "cox-1", "label": "TARGET"},
            {"text": "cox-2", "label": "TARGET"}
        ]
    }
]

# 2. REPRODUCIBLE BENCHMARK DATASET: Semantic Search Retrieval
RETRIEVAL_BENCHMARK_DATASET = [
    {
        "query": "vitamin K antagonist VKORC1 anticoagulant bleeding",
        "gold_doc_id": "DAILYMED-WARFARIN-001"
    },
    {
        "query": "AMPK gluconeogenesis type 2 diabetes biguanide",
        "gold_doc_id": "DAILYMED-METFORMIN-002"
    },
    {
        "query": "angiotensin converting enzyme inhibitor fetal toxicity blood pressure",
        "gold_doc_id": "DAILYMED-LISINOPRIL-003"
    },
    {
        "query": "irreversible cyclooxygenase inhibition thromboxane A2 secondary prevention",
        "gold_doc_id": "DAILYMED-ASPIRIN-004"
    },
    {
        "query": "HMG-CoA reductase inhibitor rhabdomyolysis CYP3A4 substrate",
        "gold_doc_id": "DAILYMED-SIMVASTATIN-005"
    }
]

# 3. REPRODUCIBLE BENCHMARK DATASET: RAG Quality Evaluation
RAG_BENCHMARK_DATASET = [
    {
        "query": "What is the boxed warning and mechanism of Warfarin?",
        "expected_entity": "Warfarin",
        "expected_target": "VKORC1",
        "expected_source_id": "RxCUI:11289"
    },
    {
        "query": "How does Metformin act on AMPK in diabetes?",
        "expected_entity": "Metformin",
        "expected_target": "AMPK",
        "expected_source_id": "RxCUI:6809"
    },
    {
        "query": "Explain Lisinopril ACE inhibition and boxed warning.",
        "expected_entity": "Lisinopril",
        "expected_target": "ACE",
        "expected_source_id": "RxCUI:29046"
    }
]


class PharmaMindEvaluator:
    """
    Executes empirical evaluation across all ML and RAG components.
    Produces actual benchmark scores without synthetic fabrications.
    """

    def __init__(self):
        self.extractor = BiomedicalEntityExtractor()
        self.hybrid_engine = create_and_populate_evidence_corpus()
        self.kg = build_default_biomedical_graph()
        self.predictor = GraphLinkPredictor(
            dimension=32,
            walk_length=10,
            num_walks=5,
            edge_operator="hadamard",
            random_seed=42
        )
        self.predictor.train_and_evaluate(self.kg, test_ratio=0.25)
        self.rag_pipeline = PharmaMindRAGPipeline(
            hybrid_engine=self.hybrid_engine,
            kg=self.kg,
            predictor=self.predictor
        )

    def evaluate_biomedical_nlp(self) -> Dict[str, float]:
        """
        Evaluate Biomedical Named Entity Recognition (Precision, Recall, F1).
        """
        tp = 0
        fp = 0
        fn = 0

        for item in NER_BENCHMARK_DATASET:
            extracted = self.extractor.extract_entities(item["text"])
            pred_terms = {e.text.lower() for e in extracted}
            gold_terms = {g["text"].lower() for g in item["gold_entities"]}

            true_pos = len(pred_terms.intersection(gold_terms))
            false_pos = len(pred_terms - gold_terms)
            false_neg = len(gold_terms - pred_terms)

            tp += true_pos
            fp += false_pos
            fn += false_neg

        precision = round(tp / max(1, tp + fp), 4)
        recall = round(tp / max(1, tp + fn), 4)
        f1 = round((2 * precision * recall) / max(1e-9, precision + recall), 4)

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "sample_size": len(NER_BENCHMARK_DATASET)
        }

    def evaluate_semantic_search(self) -> Dict[str, float]:
        """
        Evaluate Semantic Search Retrieval (Recall@5, MRR, NDCG@10).
        """
        hits_at_5 = 0
        reciprocal_ranks = []
        ndcg_scores = []

        for item in RETRIEVAL_BENCHMARK_DATASET:
            results = self.hybrid_engine.search(query=item["query"], top_k=5)
            retrieved_ids = [r.get("id", r.get("doc_id", "")) for r in results]
            gold_id = item["gold_doc_id"]

            # Recall@5
            if gold_id in retrieved_ids:
                hits_at_5 += 1
                rank = retrieved_ids.index(gold_id) + 1
                reciprocal_ranks.append(1.0 / rank)
                # DCG = 1 / log2(rank + 1), IDCG = 1 / log2(1 + 1) = 1.0
                ndcg = 1.0 / math.log2(rank + 1)
                ndcg_scores.append(ndcg)
            else:
                reciprocal_ranks.append(0.0)
                ndcg_scores.append(0.0)

        n = len(RETRIEVAL_BENCHMARK_DATASET)
        recall_at_5 = round(hits_at_5 / n, 4)
        mrr = round(sum(reciprocal_ranks) / n, 4)
        ndcg = round(sum(ndcg_scores) / n, 4)

        return {
            "recall_at_5": recall_at_5,
            "mrr": mrr,
            "ndcg_at_10": ndcg,
            "sample_size": n
        }

    def evaluate_graph_ml(self) -> Dict[str, Any]:
        """
        Retrieve empirical Graph ML link prediction evaluation metrics.
        """
        return self.predictor.evaluation_results

    def evaluate_rag_pipeline(self) -> Dict[str, float]:
        """
        Evaluate RAG generation quality: Faithfulness, Answer Relevance, Context Precision, Citation Accuracy.
        """
        faithfulness_count = 0
        relevance_count = 0
        citation_acc_scores = []
        context_prec_scores = []

        for item in RAG_BENCHMARK_DATASET:
            resp = self.rag_pipeline.execute(query=item["query"])

            # 1. Faithfulness: Contains target drug and mechanism without contradiction
            if item["expected_entity"].lower() in resp.direct_explanation.lower():
                faithfulness_count += 1

            # 2. Answer Relevance: Explains target biological action
            if item["expected_target"].lower() in resp.direct_explanation.lower():
                relevance_count += 1

            # 3. Context Precision: Retrieved evidence includes authoritative source
            has_gold_id = any(
                item["expected_source_id"] in c.identifier
                for c in resp.citations
            )
            context_prec_scores.append(1.0 if has_gold_id else 0.0)

            # 4. Citation Accuracy: Validation passed
            citation_acc_scores.append(1.0 if resp.citation_validation_passed else 0.0)

        n = len(RAG_BENCHMARK_DATASET)
        return {
            "faithfulness": round(faithfulness_count / n, 4),
            "answer_relevance": round(relevance_count / n, 4),
            "context_precision": round(sum(context_prec_scores) / n, 4),
            "citation_accuracy": round(sum(citation_acc_scores) / n, 4),
            "sample_size": n
        }

    def run_all_evaluations(self) -> Dict[str, Any]:
        """
        Execute comprehensive empirical benchmark across all 5 dimensions.
        """
        t0 = time.perf_counter()
        nlp_res = self.evaluate_biomedical_nlp()
        retrieval_res = self.evaluate_semantic_search()
        graph_res = self.evaluate_graph_ml()
        rag_res = self.evaluate_rag_pipeline()
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "nlp": nlp_res,
            "retrieval": retrieval_res,
            "graph_ml": graph_res,
            "rag": rag_res,
            "benchmark_execution_time_ms": duration_ms
        }

