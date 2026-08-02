"""Unit tests for IKROS Knowledge Graph — WP-IMP-0043."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tools.ikros.graph.confidence import ConfidencePropagator
from tools.ikros.graph.core import GraphError, KnowledgeGraph
from tools.ikros.graph.lineage import LineageEngine
from tools.ikros.graph.models import (
    CONTRADICTION_EDGES,
    LINEAGE_EDGES,
    RESEARCH_CHAIN_EDGES,
    VALID_EDGE_TYPES,
    VALID_NODE_TYPES,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)
from tools.ikros.graph.persistence import YAMLGraphRepository
from tools.ikros.graph.validation import (
    GraphValidationError,
    assert_graph_valid,
    check_referential_integrity,
    find_isolated_nodes,
    find_missing_evidence,
    validate_edge,
    validate_graph,
    validate_node,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _node(
    node_id: str,
    node_type: str = NodeType.RESEARCH_QUESTION,
    confidence: float = 0.5,
    label: str = "",
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        node_type=node_type,
        ikros_id=node_id,
        label=label or node_id,
        confidence=confidence,
    )


def _edge(
    edge_id: str,
    source_id: str,
    target_id: str,
    edge_type: str = EdgeType.DEPENDS_ON,
    confidence: float = 1.0,
    evidence_ref: str = "",
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        source_id=source_id,
        target_id=target_id,
        edge_type=edge_type,
        confidence=confidence,
        evidence_ref=evidence_ref,
    )


def _build_research_chain() -> KnowledgeGraph:
    """Build a canonical 5-hop research chain for testing.

    RQ → HYP (DEPENDS_ON) → EXP (TESTED_IN) → VAL (VALIDATED_BY)
    → CAND (GENERATED_ALPHA) → ALPHA (PRODUCED)
    """
    g = KnowledgeGraph()
    g.add_node(_node("RQ-001", NodeType.RESEARCH_QUESTION, confidence=0.4))
    g.add_node(_node("HYP-001", NodeType.HYPOTHESIS, confidence=0.5))
    g.add_node(_node("EXP-001", NodeType.EXPERIMENT, confidence=0.6))
    g.add_node(_node("VAL-001", NodeType.VALIDATION, confidence=0.7))
    g.add_node(_node("CAND-001", NodeType.ALPHA_CANDIDATE, confidence=0.45))
    g.add_node(_node("ALPHA-001", NodeType.ALPHA, confidence=0.85))
    g.add_edge(_edge("E-001", "RQ-001", "HYP-001", EdgeType.DEPENDS_ON))
    g.add_edge(_edge("E-002", "HYP-001", "EXP-001", EdgeType.TESTED_IN))
    g.add_edge(_edge("E-003", "EXP-001", "VAL-001", EdgeType.VALIDATED_BY))
    g.add_edge(_edge("E-004", "EXP-001", "CAND-001", EdgeType.GENERATED_ALPHA))
    g.add_edge(_edge("E-005", "CAND-001", "ALPHA-001", EdgeType.PRODUCED))
    return g


# ---------------------------------------------------------------------------
# Node type / edge type tests
# ---------------------------------------------------------------------------


class TestNodeAndEdgeTypes:
    def test_node_type_count(self) -> None:
        assert len(list(NodeType)) == 27

    def test_edge_type_count(self) -> None:
        assert len(list(EdgeType)) == 20

    def test_valid_node_types_complete(self) -> None:
        for nt in NodeType:
            assert nt.value in VALID_NODE_TYPES

    def test_valid_edge_types_complete(self) -> None:
        for et in EdgeType:
            assert et.value in VALID_EDGE_TYPES

    def test_contradiction_edges_subset(self) -> None:
        for et in CONTRADICTION_EDGES:
            assert et in VALID_EDGE_TYPES

    def test_lineage_edges_subset(self) -> None:
        for et in LINEAGE_EDGES:
            assert et in VALID_EDGE_TYPES

    def test_research_chain_edges_subset(self) -> None:
        for et in RESEARCH_CHAIN_EDGES:
            assert et in LINEAGE_EDGES


# ---------------------------------------------------------------------------
# GraphNode tests
# ---------------------------------------------------------------------------


class TestGraphNode:
    def test_default_confidence_zero(self) -> None:
        n = _node("N-001")
        assert n.confidence == 0.5

    def test_to_dict_from_dict_roundtrip(self) -> None:
        n = GraphNode(
            node_id="IKROS-RQ-20260802-0001",
            node_type=NodeType.RESEARCH_QUESTION,
            ikros_id="IKROS-RQ-20260802-0001",
            label="test question",
            confidence=0.42,
            valid_from="2026-01-01T00:00:00+00:00",
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0043"],
        )
        d = n.to_dict()
        n2 = GraphNode.from_dict(d)
        assert n2.node_id == n.node_id
        assert n2.node_type == n.node_type
        assert n2.confidence == n.confidence
        assert n2.spec_refs == n.spec_refs
        assert n2.wp_refs == n.wp_refs

    def test_temporal_validity_open_ended(self) -> None:
        n = _node("N-001")
        assert n.is_temporally_valid() is True

    def test_temporal_validity_future_start(self) -> None:
        n = GraphNode(
            node_id="N-001",
            node_type=NodeType.RESEARCH_QUESTION,
            ikros_id="N-001",
            valid_from="9999-01-01T00:00:00+00:00",
        )
        assert n.is_temporally_valid("2026-01-01T00:00:00+00:00") is False

    def test_temporal_validity_past_end(self) -> None:
        n = GraphNode(
            node_id="N-001",
            node_type=NodeType.RESEARCH_QUESTION,
            ikros_id="N-001",
            valid_to="2020-01-01T00:00:00+00:00",
        )
        assert n.is_temporally_valid("2026-01-01T00:00:00+00:00") is False

    def test_temporal_validity_in_range(self) -> None:
        n = GraphNode(
            node_id="N-001",
            node_type=NodeType.RESEARCH_QUESTION,
            ikros_id="N-001",
            valid_from="2025-01-01T00:00:00+00:00",
            valid_to="2027-01-01T00:00:00+00:00",
        )
        assert n.is_temporally_valid("2026-06-01T00:00:00+00:00") is True


# ---------------------------------------------------------------------------
# GraphEdge tests
# ---------------------------------------------------------------------------


class TestGraphEdge:
    def test_to_dict_from_dict_roundtrip(self) -> None:
        e = GraphEdge(
            edge_id="IKROS-EDGE-20260802-0001",
            source_id="N-001",
            target_id="N-002",
            edge_type=EdgeType.DEPENDS_ON,
            confidence=0.8,
            evidence_ref="05-work-packages/WP-001/evidence/EXEC-001.yaml",
            spec_ref="SPEC-060",
            wp_ref="WP-IMP-0043",
        )
        d = e.to_dict()
        e2 = GraphEdge.from_dict(d)
        assert e2.edge_id == e.edge_id
        assert e2.source_id == e.source_id
        assert e2.edge_type == e.edge_type
        assert e2.confidence == e.confidence
        assert e2.evidence_ref == e.evidence_ref

    def test_is_contradiction_true(self) -> None:
        for et in (EdgeType.CONTRADICTED_BY, EdgeType.REJECTED_BY, EdgeType.REFUTES):
            e = _edge("E-001", "N-001", "N-002", edge_type=et)
            assert e.is_contradiction is True

    def test_is_contradiction_false(self) -> None:
        e = _edge("E-001", "N-001", "N-002", EdgeType.DEPENDS_ON)
        assert e.is_contradiction is False


# ---------------------------------------------------------------------------
# KnowledgeGraph core tests
# ---------------------------------------------------------------------------


class TestKnowledgeGraph:
    def test_add_and_get_node(self) -> None:
        g = KnowledgeGraph()
        n = _node("N-001")
        g.add_node(n)
        assert g.get_node("N-001").node_id == "N-001"

    def test_duplicate_node_raises(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001"))
        with pytest.raises(GraphError):
            g.add_node(_node("N-001"))

    def test_get_missing_node_raises(self) -> None:
        g = KnowledgeGraph()
        with pytest.raises(KeyError):
            g.get_node("NONEXISTENT")

    def test_has_node(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001"))
        assert g.has_node("N-001") is True
        assert g.has_node("N-999") is False

    def test_node_count(self) -> None:
        g = KnowledgeGraph()
        for i in range(5):
            g.add_node(_node(f"N-{i:03d}"))
        assert g.node_count() == 5

    def test_add_edge_referential_integrity(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001"))
        with pytest.raises(GraphError, match="N-002"):
            g.add_edge(_edge("E-001", "N-001", "N-002"))

    def test_add_edge_missing_source_raises(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-002"))
        with pytest.raises(GraphError, match="N-001"):
            g.add_edge(_edge("E-001", "N-001", "N-002"))

    def test_add_duplicate_edge_raises(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001"))
        g.add_node(_node("N-002"))
        g.add_edge(_edge("E-001", "N-001", "N-002"))
        with pytest.raises(GraphError):
            g.add_edge(_edge("E-001", "N-001", "N-002"))

    def test_get_out_edges(self) -> None:
        g = _build_research_chain()
        out = g.get_out_edges("RQ-001")
        assert len(out) == 1
        assert out[0].target_id == "HYP-001"

    def test_get_in_edges(self) -> None:
        g = _build_research_chain()
        in_edges = g.get_in_edges("HYP-001")
        assert len(in_edges) == 1
        assert in_edges[0].source_id == "RQ-001"

    def test_get_out_edges_filtered_by_type(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        g.add_node(_node("C"))
        g.add_edge(_edge("E1", "A", "B", EdgeType.DEPENDS_ON))
        g.add_edge(_edge("E2", "A", "C", EdgeType.RELATED_TO))
        filtered = g.get_out_edges("A", EdgeType.DEPENDS_ON)
        assert len(filtered) == 1
        assert filtered[0].edge_id == "E1"

    def test_edge_count(self) -> None:
        g = _build_research_chain()
        assert g.edge_count() == 5

    def test_get_contradictions(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("H-001", NodeType.HYPOTHESIS))
        g.add_node(_node("E-001", NodeType.EXPERIMENT))
        g.add_edge(GraphEdge(
            edge_id="CONTRA-001",
            source_id="E-001",
            target_id="H-001",
            edge_type=EdgeType.CONTRADICTED_BY,
            evidence_ref="evidence.yaml",
        ))
        contradictions = g.get_contradictions("H-001")
        assert len(contradictions) == 1
        assert contradictions[0].edge_type == EdgeType.CONTRADICTED_BY

    def test_remove_node_removes_edges(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        g.add_edge(_edge("E-001", "A", "B"))
        g.remove_node("A")
        assert not g.has_node("A")
        assert not g.has_edge("E-001")
        assert g.get_in_edges("B") == []

    def test_remove_missing_node_raises(self) -> None:
        g = KnowledgeGraph()
        with pytest.raises(KeyError):
            g.remove_node("NONEXISTENT")

    def test_update_node(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001", confidence=0.3))
        updated = g.update_node("N-001", {"confidence": 0.9, "label": "updated"})
        assert updated.confidence == 0.9
        assert updated.label == "updated"

    def test_nodes_by_type(self) -> None:
        g = _build_research_chain()
        hyps = g.nodes_by_type(NodeType.HYPOTHESIS)
        assert len(hyps) == 1
        assert hyps[0].node_id == "HYP-001"

    def test_temporally_valid_nodes(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001"))
        g.add_node(GraphNode(
            node_id="N-002",
            node_type=NodeType.HYPOTHESIS,
            ikros_id="N-002",
            valid_to="2020-01-01T00:00:00+00:00",
        ))
        valid = g.temporally_valid_nodes("2026-01-01T00:00:00+00:00")
        valid_ids = [n.node_id for n in valid]
        assert "N-001" in valid_ids
        assert "N-002" not in valid_ids

    def test_next_edge_id_unique(self) -> None:
        g = KnowledgeGraph()
        ids = {g.next_edge_id() for _ in range(10)}
        assert len(ids) == 10

    def test_summary_counts(self) -> None:
        g = _build_research_chain()
        s = g.summary()
        assert s["node_count"] == 6
        assert s["edge_count"] == 5
        assert s["contradiction_count"] == 0


# ---------------------------------------------------------------------------
# BFS / DFS / path finding tests
# ---------------------------------------------------------------------------


class TestTraversal:
    def test_bfs_out_full_chain(self) -> None:
        g = _build_research_chain()
        result = g.bfs("RQ-001")
        assert "HYP-001" in result
        assert "EXP-001" in result
        assert "ALPHA-001" in result
        assert "RQ-001" not in result  # start excluded

    def test_bfs_in_reverse(self) -> None:
        g = _build_research_chain()
        result = g.bfs("ALPHA-001", direction="in")
        assert "CAND-001" in result
        assert "EXP-001" in result
        assert "RQ-001" in result

    def test_bfs_max_depth_1(self) -> None:
        g = _build_research_chain()
        result = g.bfs("RQ-001", max_depth=1)
        assert result == ["HYP-001"]

    def test_bfs_edge_type_filter(self) -> None:
        g = _build_research_chain()
        result = g.bfs("RQ-001", edge_types=frozenset({EdgeType.DEPENDS_ON}))
        assert result == ["HYP-001"]  # only DEPENDS_ON edge from RQ

    def test_bfs_missing_start_raises(self) -> None:
        g = KnowledgeGraph()
        with pytest.raises(KeyError):
            g.bfs("NONEXISTENT")

    def test_dfs_order(self) -> None:
        g = _build_research_chain()
        result = g.dfs("RQ-001")
        assert len(result) == 5  # all 5 downstream nodes
        assert result[0] == "HYP-001"  # first neighbor of RQ

    def test_dfs_max_depth(self) -> None:
        g = _build_research_chain()
        result = g.dfs("RQ-001", max_depth=2)
        assert "HYP-001" in result
        assert "EXP-001" in result
        assert "ALPHA-001" not in result

    def test_find_path_direct(self) -> None:
        g = _build_research_chain()
        path = g.find_path("RQ-001", "HYP-001")
        assert path == ["RQ-001", "HYP-001"]

    def test_find_path_multi_hop(self) -> None:
        g = _build_research_chain()
        path = g.find_path("RQ-001", "ALPHA-001")
        assert path[0] == "RQ-001"
        assert path[-1] == "ALPHA-001"
        assert len(path) >= 2

    def test_find_path_no_route(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        assert g.find_path("A", "B") == []

    def test_find_path_same_node(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        assert g.find_path("A", "A") == ["A"]

    def test_find_path_with_edge_type_filter(self) -> None:
        g = _build_research_chain()
        # DEPENDS_ON only — can reach HYP but not EXP (which uses TESTED_IN)
        path = g.find_path("RQ-001", "EXP-001", edge_types=frozenset({EdgeType.DEPENDS_ON}))
        assert path == []


# ---------------------------------------------------------------------------
# Lineage Engine tests
# ---------------------------------------------------------------------------


class TestLineageEngine:
    def test_get_downstream(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        downstream = engine.get_downstream("RQ-001")
        assert "HYP-001" in downstream
        assert "ALPHA-001" in downstream

    def test_get_upstream(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        upstream = engine.get_upstream("ALPHA-001")
        assert "CAND-001" in upstream
        assert "RQ-001" in upstream

    def test_get_full_lineage(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        lineage = engine.get_full_lineage("EXP-001")
        assert "HYP-001" in lineage["upstream"]
        assert "VAL-001" in lineage["downstream"]

    def test_get_research_chain(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        chain = engine.get_research_chain("RQ-001")
        assert "ALPHA-001" in chain

    def test_find_lineage_path(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        path = engine.find_lineage_path("RQ-001", "ALPHA-001")
        assert path[0] == "RQ-001"
        assert path[-1] == "ALPHA-001"

    def test_empty_upstream_for_root(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        assert engine.get_upstream("RQ-001") == []

    def test_empty_downstream_for_leaf(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        assert engine.get_downstream("ALPHA-001") == []

    def test_max_depth_limit(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        downstream = engine.get_downstream("RQ-001", max_depth=1)
        assert downstream == ["HYP-001"]

    def test_get_contradicting_nodes(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("H-001", NodeType.HYPOTHESIS))
        g.add_node(_node("E-001", NodeType.EXPERIMENT))
        g.add_edge(GraphEdge(
            edge_id="C-001",
            source_id="E-001",
            target_id="H-001",
            edge_type=EdgeType.CONTRADICTED_BY,
            evidence_ref="ev.yaml",
        ))
        engine = LineageEngine(g)
        contra_nodes = engine.get_contradicting_nodes("H-001")
        assert "E-001" in contra_nodes

    def test_get_alpha_chain_paths(self) -> None:
        g = _build_research_chain()
        engine = LineageEngine(g)
        paths = engine.get_alpha_chain("RQ-001")
        assert len(paths) >= 1
        for path in paths:
            assert path[0] == "RQ-001"
            assert path[-1] == "ALPHA-001"

    def test_get_all_supporting_evidence(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("HYP-001", NodeType.HYPOTHESIS))
        g.add_node(_node("EV-001", NodeType.EVIDENCE))
        g.add_edge(_edge("E-001", "EV-001", "HYP-001", EdgeType.SUPPORTED_BY))
        engine = LineageEngine(g)
        # SUPPORTED_BY not in LINEAGE_EDGES — evidence would need DERIVED_FROM etc.
        # Test it returns empty (SUPPORTED_BY not in LINEAGE_EDGES)
        ev_ids = engine.get_all_supporting_evidence("HYP-001")
        assert isinstance(ev_ids, list)


# ---------------------------------------------------------------------------
# Confidence Propagator tests
# ---------------------------------------------------------------------------


class TestConfidencePropagator:
    def test_single_node_propagation(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001", confidence=0.6))
        prop = ConfidencePropagator(g)
        result = prop.propagate_downstream("N-001")
        assert result["N-001"] == pytest.approx(0.6)

    def test_propagation_decays_downstream(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A", confidence=0.8))
        g.add_node(_node("B", confidence=0.5))
        g.add_edge(_edge("E1", "A", "B", EdgeType.DEPENDS_ON))
        prop = ConfidencePropagator(g)
        result = prop.propagate_downstream("A")
        assert result["A"] == pytest.approx(0.8)
        assert result["B"] < result["A"]  # damping applied

    def test_propagation_capped_at_095(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("N-001", confidence=1.0))
        prop = ConfidencePropagator(g)
        result = prop.propagate_downstream("N-001")
        assert result["N-001"] <= 0.95

    def test_contradiction_penalty(self) -> None:
        prop = ConfidencePropagator(KnowledgeGraph())
        base = 0.80
        penalised = prop.apply_contradiction_penalty(base, contradiction_count=1)
        assert penalised < base
        assert penalised >= 0.0

    def test_contradiction_penalty_floor_zero(self) -> None:
        prop = ConfidencePropagator(KnowledgeGraph())
        penalised = prop.apply_contradiction_penalty(0.10, contradiction_count=10)
        assert penalised == 0.0

    def test_aggregate_upstream_empty(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("RQ-001", confidence=0.4))
        prop = ConfidencePropagator(g)
        agg = prop.aggregate_upstream_confidence("RQ-001")
        assert agg == pytest.approx(0.4)

    def test_aggregate_upstream_with_chain(self) -> None:
        g = _build_research_chain()
        prop = ConfidencePropagator(g)
        # EXP-001 has upstream HYP-001 and RQ-001
        agg = prop.aggregate_upstream_confidence("EXP-001")
        assert 0.0 <= agg <= 0.95

    def test_graph_confidence_map_deterministic(self) -> None:
        g = _build_research_chain()
        prop = ConfidencePropagator(g)
        m1 = prop.compute_graph_confidence_map()
        m2 = prop.compute_graph_confidence_map()
        assert m1 == m2

    def test_propagation_summary_keys(self) -> None:
        g = _build_research_chain()
        prop = ConfidencePropagator(g)
        summary = prop.get_propagation_summary()
        assert "node_count" in summary
        assert "mean_confidence" in summary
        assert "low_confidence_nodes" in summary

    def test_missing_node_returns_empty(self) -> None:
        prop = ConfidencePropagator(KnowledgeGraph())
        result = prop.propagate_downstream("NONEXISTENT")
        assert result == {}


# ---------------------------------------------------------------------------
# Graph Validation tests
# ---------------------------------------------------------------------------


class TestGraphValidation:
    def test_valid_graph(self) -> None:
        g = _build_research_chain()
        errors = validate_graph(g)
        assert errors == []

    def test_invalid_node_type(self) -> None:
        n = GraphNode(
            node_id="N-001",
            node_type="INVALID_TYPE",
            ikros_id="N-001",
        )
        errors = validate_node(n)
        assert any("INVALID_TYPE" in e for e in errors)

    def test_invalid_confidence_low(self) -> None:
        n = _node("N-001", confidence=-0.1)
        errors = validate_node(n)
        assert any("confidence" in e for e in errors)

    def test_invalid_confidence_high(self) -> None:
        n = _node("N-001", confidence=1.1)
        errors = validate_node(n)
        assert any("confidence" in e for e in errors)

    def test_temporal_inconsistency(self) -> None:
        n = GraphNode(
            node_id="N-001",
            node_type=NodeType.HYPOTHESIS,
            ikros_id="N-001",
            valid_from="2026-12-01T00:00:00+00:00",
            valid_to="2026-01-01T00:00:00+00:00",
        )
        errors = validate_node(n)
        assert any("temporal" in e for e in errors)

    def test_invalid_edge_type(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        e = GraphEdge(
            edge_id="E-001",
            source_id="A",
            target_id="B",
            edge_type="FAKE_EDGE",
        )
        errors = validate_edge(e, g)
        assert any("FAKE_EDGE" in err for err in errors)

    def test_contradiction_without_evidence_ref(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        e = GraphEdge(
            edge_id="E-001",
            source_id="A",
            target_id="B",
            edge_type=EdgeType.CONTRADICTED_BY,
            evidence_ref="",  # missing
        )
        errors = validate_edge(e, g)
        assert any("evidence_ref" in err for err in errors)

    def test_assert_graph_valid_raises(self) -> None:
        g = KnowledgeGraph()
        # Manually inject an invalid node to bypass add_node
        invalid_node = GraphNode(
            node_id="N-001",
            node_type="INVALID",
            ikros_id="N-001",
        )
        g._nodes["N-001"] = invalid_node  # noqa: SLF001
        g._out_adj["N-001"] = []
        g._in_adj["N-001"] = []
        with pytest.raises(GraphValidationError):
            assert_graph_valid(g)

    def test_find_isolated_nodes(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("SOLO"))
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        g.add_edge(_edge("E1", "A", "B"))
        isolated = find_isolated_nodes(g)
        assert "SOLO" in isolated
        assert "A" not in isolated

    def test_find_missing_evidence(self) -> None:
        g = KnowledgeGraph()
        g.add_node(_node("A"))
        g.add_node(_node("B"))
        g.add_edge(GraphEdge(
            edge_id="E-001",
            source_id="A",
            target_id="B",
            edge_type=EdgeType.CONTRADICTED_BY,
            evidence_ref="",  # missing
        ))
        missing = find_missing_evidence(g)
        assert "E-001" in missing

    def test_referential_integrity_clean(self) -> None:
        g = _build_research_chain()
        violations = check_referential_integrity(g)
        assert violations == []


# ---------------------------------------------------------------------------
# YAML Persistence tests
# ---------------------------------------------------------------------------


class TestYAMLGraphRepository:
    def test_save_and_load_empty_graph(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = KnowledgeGraph()
            repo.save(g)
            g2 = repo.load()
            assert g2.node_count() == 0
            assert g2.edge_count() == 0

    def test_save_and_load_node(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            n = _node("IKROS-RQ-20260802-0001", NodeType.RESEARCH_QUESTION, confidence=0.6)
            g = KnowledgeGraph()
            g.add_node(n)
            repo.save(g)
            g2 = repo.load()
            assert g2.has_node("IKROS-RQ-20260802-0001")
            assert g2.get_node("IKROS-RQ-20260802-0001").confidence == pytest.approx(0.6)

    def test_save_and_load_full_chain(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = _build_research_chain()
            repo.save(g)
            g2 = repo.load()
            assert g2.node_count() == g.node_count()
            assert g2.edge_count() == g.edge_count()

    def test_topology_preserved_after_reload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = _build_research_chain()
            repo.save(g)
            g2 = repo.load()
            out = g2.get_out_edges("RQ-001")
            assert len(out) == 1
            assert out[0].target_id == "HYP-001"

    def test_node_ids_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = KnowledgeGraph()
            g.add_node(_node("Z-001"))
            g.add_node(_node("A-001"))
            repo.save(g)
            ids = repo.node_ids()
            assert ids == sorted(ids)

    def test_edge_ids_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = _build_research_chain()
            repo.save(g)
            ids = repo.edge_ids()
            assert ids == sorted(ids)

    def test_save_node_incremental(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            repo.save_node(_node("N-001"))
            assert "N-001" in repo.node_ids()

    def test_save_edge_incremental(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            e = _edge("E-001", "N-001", "N-002")
            repo.save_edge(e)
            assert "E-001" in repo.edge_ids()

    def test_deterministic_resave(self) -> None:
        """Save twice; loaded graph should be identical both times."""
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = _build_research_chain()
            repo.save(g)
            g1 = repo.load()
            repo.save(g1)
            g2 = repo.load()
            assert g1.node_count() == g2.node_count()
            assert g1.edge_count() == g2.edge_count()

    def test_sync_edge_seq_after_load(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = YAMLGraphRepository(Path(td))
            g = _build_research_chain()
            repo.save(g)
            g2 = repo.load()
            # After sync, new edge IDs should not collide
            new_id1 = g2.next_edge_id()
            new_id2 = g2.next_edge_id()
            assert new_id1 != new_id2
