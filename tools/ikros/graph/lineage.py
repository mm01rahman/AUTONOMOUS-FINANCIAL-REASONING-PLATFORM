"""IKROS Knowledge Graph lineage traversal engine."""

from __future__ import annotations

from tools.ikros.graph.core import KnowledgeGraph
from tools.ikros.graph.models import LINEAGE_EDGES, RESEARCH_CHAIN_EDGES, EdgeType


class LineageEngine:
    """Forward and reverse lineage traversal for IKROS research objects.

    The research dependency chain follows:
        ResearchQuestion → Hypothesis → Experiment → (Validation | AlphaCandidate) → Alpha
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    def get_upstream(self, node_id: str, max_depth: int = 10) -> list[str]:
        """Return all ancestors via lineage edges (following in-edges of LINEAGE_EDGES).

        Returns node IDs in BFS order, closest ancestors first.
        """
        return self._graph.bfs(
            node_id,
            direction="in",
            edge_types=LINEAGE_EDGES,
            max_depth=max_depth,
        )

    def get_downstream(self, node_id: str, max_depth: int = 10) -> list[str]:
        """Return all descendants via lineage edges (following out-edges of LINEAGE_EDGES).

        Returns node IDs in BFS order, closest descendants first.
        """
        return self._graph.bfs(
            node_id,
            direction="out",
            edge_types=LINEAGE_EDGES,
            max_depth=max_depth,
        )

    def get_full_lineage(self, node_id: str, max_depth: int = 10) -> dict[str, list[str]]:
        """Return both upstream and downstream lineage for a node."""
        return {
            "upstream": self.get_upstream(node_id, max_depth),
            "downstream": self.get_downstream(node_id, max_depth),
        }

    def get_research_chain(self, node_id: str) -> list[str]:
        """Return the complete research chain path through RESEARCH_CHAIN_EDGES.

        Traverses downstream along the canonical research chain:
            ResearchQuestion → Hypothesis → Experiment → AlphaCandidate → Alpha
        """
        return self._graph.bfs(
            node_id,
            direction="out",
            edge_types=RESEARCH_CHAIN_EDGES,
        )

    def find_lineage_path(self, source_id: str, target_id: str) -> list[str]:
        """Return the shortest lineage path from source to target.

        Returns empty list if no path exists through LINEAGE_EDGES.
        """
        return self._graph.find_path(source_id, target_id, edge_types=LINEAGE_EDGES)

    def get_all_supporting_evidence(self, node_id: str) -> list[str]:
        """Return all evidence node IDs supporting this node (transitively upstream)."""
        from tools.ikros.graph.models import NodeType
        upstream = self.get_upstream(node_id)
        evidence_nodes = []
        for nid in upstream:
            try:
                node = self._graph.get_node(nid)
                if node.node_type == NodeType.EVIDENCE:
                    evidence_nodes.append(nid)
            except KeyError:
                pass
        return evidence_nodes

    def get_dependent_experiments(self, node_id: str) -> list[str]:
        """Return all experiment node IDs that tested or depend on this node."""
        from tools.ikros.graph.models import NodeType
        downstream = self.get_downstream(node_id)
        return [
            nid for nid in downstream
            if self._graph.has_node(nid)
            and self._graph.get_node(nid).node_type == NodeType.EXPERIMENT
        ]

    def get_alpha_chain(self, rq_node_id: str) -> list[list[str]]:
        """Return all complete paths from a ResearchQuestion to Alpha nodes.

        Each path represents a successful research lineage chain.
        """
        paths: list[list[str]] = []
        self._find_alpha_paths(rq_node_id, [rq_node_id], paths)
        return paths

    def _find_alpha_paths(
        self,
        current_id: str,
        current_path: list[str],
        all_paths: list[list[str]],
        max_depth: int = 10,
    ) -> None:
        if len(current_path) > max_depth:
            return
        try:
            node = self._graph.get_node(current_id)
        except KeyError:
            return
        from tools.ikros.graph.models import NodeType
        if node.node_type == NodeType.ALPHA:
            all_paths.append(list(current_path))
            return
        for edge in self._graph.get_out_edges(current_id):
            if edge.edge_type in RESEARCH_CHAIN_EDGES and edge.target_id not in current_path:
                self._find_alpha_paths(
                    edge.target_id,
                    current_path + [edge.target_id],
                    all_paths,
                    max_depth,
                )

    def get_contradicting_nodes(self, node_id: str) -> list[str]:
        """Return all node IDs involved in contradiction relationships with this node."""
        contradictions = self._graph.get_contradictions(node_id)
        result = set()
        for edge in contradictions:
            if edge.source_id != node_id:
                result.add(edge.source_id)
            if edge.target_id != node_id:
                result.add(edge.target_id)
        return list(result)

    def get_validated_by(self, hypothesis_id: str) -> list[str]:
        """Return all validation node IDs that directly validate a hypothesis."""
        return [
            e.target_id
            for e in self._graph.get_out_edges(hypothesis_id, EdgeType.VALIDATED_BY)
        ]
