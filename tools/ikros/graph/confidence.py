"""IKROS Knowledge Graph confidence propagation engine.

Implements deterministic confidence propagation per SPEC-060 §5.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from tools.ikros.graph.core import KnowledgeGraph
from tools.ikros.graph.models import LINEAGE_EDGES

# Propagation parameters
_DAMPING_FACTOR: float = 0.85       # Confidence decays with each hop
_MAX_PROPAGATION_DEPTH: int = 5
_CONTRADICTION_PENALTY: float = 0.20  # Subtract 20% per contradicting edge


class ConfidencePropagator:
    """Deterministic confidence propagation through the Knowledge Graph.

    Propagation rules (per SPEC-060 §5):
    - P-1: Start with node's own confidence as the base.
    - P-2: Propagate downstream, decaying by _DAMPING_FACTOR per hop.
    - P-3: Evidence nodes boost confidence of their dependents.
    - P-6: Contradiction relationships apply a penalty to the source node's confidence.
    - P-7: Maximum confidence is capped at 0.95.
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    def propagate_downstream(
        self,
        node_id: str,
        max_depth: int = _MAX_PROPAGATION_DEPTH,
    ) -> dict[str, float]:
        """Propagate confidence outward from node_id through lineage edges.

        Returns a dict mapping node_id → propagated confidence score.
        The start node is included with its own confidence.
        """
        result: dict[str, float] = {}
        visited: set[str] = set()
        # Queue: (node_id, weight, depth)
        queue: deque[tuple[str, float, int]] = deque()
        try:
            start_conf = self._graph.get_node(node_id).confidence
        except KeyError:
            return result
        queue.append((node_id, start_conf, 0))
        while queue:
            nid, weight, depth = queue.popleft()
            if nid in visited or depth > max_depth:
                continue
            visited.add(nid)
            result[nid] = min(weight, 0.95)
            if depth < max_depth:
                for edge in self._graph.get_out_edges(nid):
                    if edge.edge_type in LINEAGE_EDGES and edge.target_id not in visited:
                        propagated = weight * _DAMPING_FACTOR * edge.confidence
                        queue.append((edge.target_id, propagated, depth + 1))
        return result

    def aggregate_upstream_confidence(
        self,
        node_id: str,
        max_depth: int = _MAX_PROPAGATION_DEPTH,
    ) -> float:
        """Compute effective confidence for node_id by aggregating upstream evidence.

        Returns a float in [0.0, 0.95]. Uses geometric mean of upstream node
        confidences weighted by edge confidence, with contradiction penalty.
        """
        base = 0.0
        try:
            base = self._graph.get_node(node_id).confidence
        except KeyError:
            return 0.0

        # Gather upstream confidences
        upstream_weights: list[float] = []
        visited: set[str] = {node_id}
        queue: deque[tuple[str, float, int]] = deque()
        queue.append((node_id, 1.0, 0))
        while queue:
            nid, weight, depth = queue.popleft()
            if depth > max_depth:
                continue
            for edge in self._graph.get_in_edges(nid):
                if edge.edge_type in LINEAGE_EDGES and edge.source_id not in visited:
                    visited.add(edge.source_id)
                    try:
                        src_conf = self._graph.get_node(edge.source_id).confidence
                    except KeyError:
                        continue
                    contribution = src_conf * weight * edge.confidence
                    upstream_weights.append(contribution)
                    queue.append((edge.source_id, weight * _DAMPING_FACTOR, depth + 1))

        # Aggregate
        if upstream_weights:
            avg = sum(upstream_weights) / len(upstream_weights)
            aggregated = (base + avg) / 2.0
        else:
            aggregated = base

        # Apply contradiction penalty
        contradictions = self._graph.get_contradictions(node_id)
        penalty = len(contradictions) * _CONTRADICTION_PENALTY
        effective = max(0.0, aggregated - penalty)
        return float(min(effective, 0.95))

    def apply_contradiction_penalty(
        self, base_confidence: float, contradiction_count: int
    ) -> float:
        """Return base_confidence reduced by contradiction_count × penalty."""
        penalty = contradiction_count * _CONTRADICTION_PENALTY
        return float(max(0.0, min(base_confidence - penalty, 0.95)))

    def compute_graph_confidence_map(self) -> dict[str, float]:
        """Compute effective confidence for every node in the graph.

        Returns a deterministic dict sorted by node_id for reproducibility.
        """
        all_node_ids = sorted(self._graph.node_ids())
        result: dict[str, float] = {}
        for nid in all_node_ids:
            result[nid] = self.aggregate_upstream_confidence(nid)
        return result

    def get_propagation_summary(self) -> dict[str, Any]:
        """Return a summary of confidence propagation across the graph."""
        conf_map = self.compute_graph_confidence_map()
        if not conf_map:
            return {"node_count": 0, "mean_confidence": 0.0, "low_confidence_nodes": []}
        values = list(conf_map.values())
        mean_conf = sum(values) / len(values)
        low_conf = [nid for nid, c in sorted(conf_map.items()) if c < 0.20]
        return {
            "node_count": len(conf_map),
            "mean_confidence": round(mean_conf, 4),
            "min_confidence": round(min(values), 4),
            "max_confidence": round(max(values), 4),
            "low_confidence_nodes": low_conf,
        }
