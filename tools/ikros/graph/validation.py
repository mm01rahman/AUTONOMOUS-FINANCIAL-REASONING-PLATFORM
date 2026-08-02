"""IKROS Knowledge Graph validation — structural and semantic integrity checks."""

from __future__ import annotations

from tools.ikros.graph.core import KnowledgeGraph
from tools.ikros.graph.models import (
    CONTRADICTION_EDGES,
    VALID_EDGE_TYPES,
    VALID_NODE_TYPES,
    GraphEdge,
    GraphNode,
)


class GraphValidationError(ValueError):
    """Raised when the graph fails validation."""


def validate_node(node: GraphNode) -> list[str]:
    """Validate a single node. Returns list of error strings (empty = valid)."""
    errors: list[str] = []
    if not node.node_id:
        errors.append("node_id is required")
    if not node.node_type:
        errors.append("node_type is required")
    elif node.node_type not in VALID_NODE_TYPES:
        errors.append(f"node_type '{node.node_type}' is not a valid NodeType")
    if not node.ikros_id:
        errors.append("ikros_id is required")
    if not (0.0 <= node.confidence <= 1.0):
        errors.append(f"confidence {node.confidence} must be in [0.0, 1.0]")
    if node.valid_from is not None and node.valid_to is not None:
        if node.valid_from >= node.valid_to:
            errors.append(
                "temporal inconsistency: "
                f"valid_from '{node.valid_from}' >= valid_to '{node.valid_to}'"
            )
    return errors


def validate_edge(edge: GraphEdge, graph: KnowledgeGraph) -> list[str]:
    """Validate a single edge against its graph context."""
    errors: list[str] = []
    if not edge.edge_id:
        errors.append("edge_id is required")
    if not edge.edge_type:
        errors.append("edge_type is required")
    elif edge.edge_type not in VALID_EDGE_TYPES:
        errors.append(f"edge_type '{edge.edge_type}' is not a valid EdgeType")
    if not edge.source_id:
        errors.append("source_id is required")
    elif not graph.has_node(edge.source_id):
        errors.append(f"source node '{edge.source_id}' not found in graph")
    if not edge.target_id:
        errors.append("target_id is required")
    elif not graph.has_node(edge.target_id):
        errors.append(f"target node '{edge.target_id}' not found in graph")
    if not (0.0 <= edge.confidence <= 1.0):
        errors.append(f"edge confidence {edge.confidence} must be in [0.0, 1.0]")
    if edge.edge_type in CONTRADICTION_EDGES and not edge.evidence_ref:
        errors.append(
            f"contradiction edge '{edge.edge_id}' ({edge.edge_type}) "
            "requires evidence_ref (SPEC-060 §6)"
        )
    return errors


def validate_graph(graph: KnowledgeGraph) -> list[str]:
    """Validate the entire graph. Returns list of error strings (empty = valid)."""
    errors: list[str] = []

    # Validate all nodes
    for node in graph.nodes():
        node_errors = validate_node(node)
        for err in node_errors:
            errors.append(f"[node:{node.node_id}] {err}")

    # Validate all edges
    for edge in graph.edges():
        edge_errors = validate_edge(edge, graph)
        for err in edge_errors:
            errors.append(f"[edge:{edge.edge_id}] {err}")

    # Check for dangling adjacency (edges in adj that aren't in _edges)
    for node_id, eids in graph._out_adj.items():  # noqa: SLF001
        for eid in eids:
            if not graph.has_edge(eid):
                errors.append(
                    f"[adjacency] out-edge '{eid}' for node '{node_id}' "
                    "missing from edge store"
                )

    return errors


def assert_graph_valid(graph: KnowledgeGraph) -> None:
    """Validate and raise GraphValidationError if any errors found."""
    errors = validate_graph(graph)
    if errors:
        raise GraphValidationError(
            f"Knowledge Graph validation failed ({len(errors)} errors):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def find_isolated_nodes(graph: KnowledgeGraph) -> list[str]:
    """Return node IDs that have no edges (neither in nor out)."""
    return [
        node.node_id
        for node in graph.nodes()
        if not graph.get_out_edges(node.node_id) and not graph.get_in_edges(node.node_id)
    ]


def find_missing_evidence(graph: KnowledgeGraph) -> list[str]:
    """Return edge IDs of contradiction edges that lack evidence_ref."""
    return [
        edge.edge_id
        for edge in graph.edges()
        if edge.is_contradiction and not edge.evidence_ref
    ]


def check_referential_integrity(graph: KnowledgeGraph) -> list[str]:
    """Return a list of referential integrity violation descriptions."""
    violations: list[str] = []
    for edge in graph.edges():
        if not graph.has_node(edge.source_id):
            violations.append(f"Edge '{edge.edge_id}': source '{edge.source_id}' missing")
        if not graph.has_node(edge.target_id):
            violations.append(f"Edge '{edge.edge_id}': target '{edge.target_id}' missing")
    return violations
