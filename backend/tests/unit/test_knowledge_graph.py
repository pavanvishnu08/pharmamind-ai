"""
Unit tests for Biomedical Knowledge Graph Engine
"""

import unittest
from app.services.knowledge_graph.graph_engine import (
    BiomedicalKnowledgeGraph,
    build_default_biomedical_graph,
    VALID_NODE_TYPES,
    VALID_RELATIONSHIPS
)


class TestKnowledgeGraphEngine(unittest.TestCase):
    def setUp(self):
        self.kg = BiomedicalKnowledgeGraph()

    def test_add_valid_entities_and_relationships(self):
        self.kg.add_entity("Metformin", "Metformin", "DRUG", {"rxnorm": "6809"})
        self.kg.add_entity("Type2Diabetes", "Type 2 Diabetes", "DISEASE", {"mesh": "D003924"})

        edge_id = self.kg.add_relationship(
            source="Metformin",
            target="Type2Diabetes",
            relationship_type="TREATS",
            provenance_source="FDA DailyMed",
            provenance_id="SPL-Metformin",
            confidence_score=0.99
        )

        self.assertEqual(self.kg.total_nodes, 2)
        self.assertEqual(self.kg.total_edges, 1)
        self.assertIn("Metformin_TREATS_Type2Diabetes", edge_id)

    def test_invalid_node_type_raises_error(self):
        with self.assertRaises(ValueError):
            self.kg.add_entity("InvalidNode", "Invalid", "NON_EXISTENT_TYPE")

    def test_invalid_relationship_type_raises_error(self):
        with self.assertRaises(ValueError):
            self.kg.add_relationship("A", "B", "INVALID_RELATIONSHIP")

    def test_default_graph_bootstrap_integrity(self):
        default_kg = build_default_biomedical_graph()
        self.assertGreaterEqual(default_kg.total_nodes, 15)
        self.assertGreaterEqual(default_kg.total_edges, 15)

        exported = default_kg.export_graph()
        self.assertIn("nodes", exported)
        self.assertIn("edges", exported)
        self.assertIn("provenance_summary", exported)
        self.assertIn("FDA DailyMed", exported["provenance_summary"])

    def test_subgraph_neighborhood_extraction(self):
        default_kg = build_default_biomedical_graph()
        hood = default_kg.get_neighborhood("Warfarin", radius=1)

        self.assertEqual(hood["center_node"], "Warfarin")
        self.assertGreater(hood["total_nodes"], 1)
        self.assertGreater(hood["total_edges"], 1)

        node_ids = {n["id"] for n in hood["nodes"]}
        self.assertIn("Warfarin", node_ids)
        # Should connect to VKORC1 (target) and Thrombosis (indication)
        self.assertTrue("VKORC1" in node_ids or "Thrombosis" in node_ids)

    def test_multi_hop_path_traversal(self):
        default_kg = build_default_biomedical_graph()
        # Direct or 1-hop path
        path = default_kg.find_shortest_path("Warfarin", "Thrombosis")
        self.assertIsNotNone(path)
        self.assertGreaterEqual(len(path), 1)

        step1 = path[0]
        self.assertIn("from_node", step1)
        self.assertIn("to_node", step1)
        self.assertIn("relationship", step1)

    def test_disconnected_path_returns_none(self):
        self.kg.add_entity("IsolatedA", "IsolatedA", "DRUG")
        self.kg.add_entity("IsolatedB", "IsolatedB", "DISEASE")
        path = self.kg.find_shortest_path("IsolatedA", "IsolatedB")
        self.assertIsNone(path)

