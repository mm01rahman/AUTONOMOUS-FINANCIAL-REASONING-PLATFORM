"""IKROS Knowledge Graph package."""

from __future__ import annotations

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
from tools.ikros.graph.persistence import KnowledgeGraphRepository, YAMLGraphRepository
from tools.ikros.graph.validation import (
    GraphValidationError,
    assert_graph_valid,
    find_isolated_nodes,
    find_missing_evidence,
    validate_edge,
    validate_graph,
    validate_node,
)

__all__ = [
    "CONTRADICTION_EDGES",
    "LINEAGE_EDGES",
    "RESEARCH_CHAIN_EDGES",
    "VALID_EDGE_TYPES",
    "VALID_NODE_TYPES",
    "ConfidencePropagator",
    "EdgeType",
    "GraphEdge",
    "GraphError",
    "GraphNode",
    "GraphValidationError",
    "KnowledgeGraph",
    "KnowledgeGraphRepository",
    "LineageEngine",
    "NodeType",
    "YAMLGraphRepository",
    "assert_graph_valid",
    "find_isolated_nodes",
    "find_missing_evidence",
    "validate_edge",
    "validate_graph",
    "validate_node",
]
