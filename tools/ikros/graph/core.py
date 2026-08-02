"""IKROS Knowledge Graph — in-memory directed property graph."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from typing import Any

from tools.ikros.graph.models import CONTRADICTION_EDGES, GraphEdge, GraphNode


class GraphError(RuntimeError):
    """Raised for Knowledge Graph integrity violations."""


class KnowledgeGraph:
    """In-memory directed property graph for institutional research knowledge.

    Nodes and edges are stored with full adjacency indexing for O(1) lookups.
    Node and edge identifiers are immutable once added.
    Thread safety: not guaranteed (single-process use).
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._out_adj: dict[str, list[str]] = {}   # node_id → [edge_ids]
        self._in_adj: dict[str, list[str]] = {}    # node_id → [edge_ids]
        self._edge_seq: int = 0

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> None:
        """Add a node. Raises GraphError on duplicate node_id."""
        if node.node_id in self._nodes:
            raise GraphError(f"Duplicate node '{node.node_id}'")
        self._nodes[node.node_id] = node
        self._out_adj.setdefault(node.node_id, [])
        self._in_adj.setdefault(node.node_id, [])

    def get_node(self, node_id: str) -> GraphNode:
        """Return node by ID. Raises KeyError if not found."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found")
        return self._nodes[node_id]

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def update_node(self, node_id: str, delta: dict[str, Any]) -> GraphNode:
        """Apply attribute delta to a node. Immutable fields (node_id, node_type) are ignored."""
        node = self.get_node(node_id)
        d = node.to_dict()
        for key in (
            "label", "confidence", "valid_from", "valid_to",
            "attributes", "spec_refs", "wp_refs",
        ):
            if key in delta:
                d[key] = delta[key]
        updated = GraphNode.from_dict(d)
        self._nodes[node_id] = updated
        return updated

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its incident edges."""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found")
        incident = {
            eid for eid, e in self._edges.items()
            if e.source_id == node_id or e.target_id == node_id
        }
        for eid in incident:
            edge = self._edges.pop(eid)
            self._out_adj[edge.source_id] = [
                x for x in self._out_adj.get(edge.source_id, []) if x != eid
            ]
            self._in_adj[edge.target_id] = [
                x for x in self._in_adj.get(edge.target_id, []) if x != eid
            ]
        del self._nodes[node_id]
        self._out_adj.pop(node_id, None)
        self._in_adj.pop(node_id, None)

    def nodes(self) -> list[GraphNode]:
        """Return all nodes in deterministic insertion order."""
        return list(self._nodes.values())

    def nodes_by_type(self, node_type: str) -> list[GraphNode]:
        """Return all nodes of the given type."""
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def node_count(self) -> int:
        return len(self._nodes)

    def node_ids(self) -> list[str]:
        """Return all node IDs in deterministic insertion order."""
        return list(self._nodes.keys())

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def next_edge_id(self) -> str:
        """Generate the next sequential canonical edge ID."""
        self._edge_seq += 1
        d = datetime.now(UTC).strftime("%Y%m%d")
        return f"IKROS-EDGE-{d}-{self._edge_seq:04d}"

    def add_edge(self, edge: GraphEdge) -> None:
        """Add a directed edge with referential integrity enforcement."""
        if edge.edge_id in self._edges:
            raise GraphError(f"Duplicate edge '{edge.edge_id}'")
        if edge.source_id not in self._nodes:
            raise GraphError(
                f"Referential integrity violation: source node '{edge.source_id}' not in graph"
            )
        if edge.target_id not in self._nodes:
            raise GraphError(
                f"Referential integrity violation: target node '{edge.target_id}' not in graph"
            )
        self._edges[edge.edge_id] = edge
        self._out_adj.setdefault(edge.source_id, []).append(edge.edge_id)
        self._in_adj.setdefault(edge.target_id, []).append(edge.edge_id)

    def get_edge(self, edge_id: str) -> GraphEdge:
        if edge_id not in self._edges:
            raise KeyError(f"Edge '{edge_id}' not found")
        return self._edges[edge_id]

    def has_edge(self, edge_id: str) -> bool:
        return edge_id in self._edges

    def get_out_edges(self, node_id: str, edge_type: str | None = None) -> list[GraphEdge]:
        """Return edges going out of node_id, optionally filtered by type."""
        eids = self._out_adj.get(node_id, [])
        result = [self._edges[e] for e in eids if e in self._edges]
        if edge_type is not None:
            result = [e for e in result if e.edge_type == edge_type]
        return result

    def get_in_edges(self, node_id: str, edge_type: str | None = None) -> list[GraphEdge]:
        """Return edges coming into node_id, optionally filtered by type."""
        eids = self._in_adj.get(node_id, [])
        result = [self._edges[e] for e in eids if e in self._edges]
        if edge_type is not None:
            result = [e for e in result if e.edge_type == edge_type]
        return result

    def edges(self) -> list[GraphEdge]:
        """Return all edges in deterministic insertion order."""
        return list(self._edges.values())

    def edge_count(self) -> int:
        return len(self._edges)

    def get_contradictions(self, node_id: str) -> list[GraphEdge]:
        """Return all contradiction edges incident to node_id (in or out)."""
        all_edges = self.get_out_edges(node_id) + self.get_in_edges(node_id)
        # Deduplicate (an edge can appear in both if self-loop, which is unusual)
        seen: set[str] = set()
        result = []
        for e in all_edges:
            if e.is_contradiction and e.edge_id not in seen:
                seen.add(e.edge_id)
                result.append(e)
        return result

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def bfs(
        self,
        start_id: str,
        direction: str = "out",
        edge_types: frozenset[str] | None = None,
        max_depth: int | None = None,
    ) -> list[str]:
        """Breadth-first traversal starting from start_id.

        Returns node IDs in BFS order (start_id excluded).
        direction: 'out' follows out-edges; 'in' follows in-edges.
        """
        if start_id not in self._nodes:
            raise KeyError(f"Node '{start_id}' not found")
        visited: set[str] = {start_id}
        queue: deque[tuple[str, int]] = deque([(start_id, 0)])
        result: list[str] = []
        while queue:
            nid, depth = queue.popleft()
            if max_depth is not None and depth >= max_depth:
                continue
            adj_edges = self.get_out_edges(nid) if direction == "out" else self.get_in_edges(nid)
            for edge in adj_edges:
                if edge_types is not None and edge.edge_type not in edge_types:
                    continue
                neighbor = edge.target_id if direction == "out" else edge.source_id
                if neighbor not in visited:
                    visited.add(neighbor)
                    result.append(neighbor)
                    queue.append((neighbor, depth + 1))
        return result

    def dfs(
        self,
        start_id: str,
        direction: str = "out",
        edge_types: frozenset[str] | None = None,
        max_depth: int | None = None,
    ) -> list[str]:
        """Depth-first traversal starting from start_id.

        Returns node IDs in DFS order (start_id excluded).
        """
        if start_id not in self._nodes:
            raise KeyError(f"Node '{start_id}' not found")
        visited: set[str] = {start_id}
        result: list[str] = []
        self._dfs_impl(start_id, direction, edge_types, max_depth, 0, visited, result)
        return result

    def _dfs_impl(
        self,
        nid: str,
        direction: str,
        edge_types: frozenset[str] | None,
        max_depth: int | None,
        depth: int,
        visited: set[str],
        result: list[str],
    ) -> None:
        if max_depth is not None and depth >= max_depth:
            return
        adj_edges = self.get_out_edges(nid) if direction == "out" else self.get_in_edges(nid)
        for edge in adj_edges:
            if edge_types is not None and edge.edge_type not in edge_types:
                continue
            neighbor = edge.target_id if direction == "out" else edge.source_id
            if neighbor not in visited:
                visited.add(neighbor)
                result.append(neighbor)
                self._dfs_impl(
                    neighbor, direction, edge_types, max_depth, depth + 1, visited, result,
                )

    def find_path(
        self,
        source_id: str,
        target_id: str,
        edge_types: frozenset[str] | None = None,
    ) -> list[str]:
        """Return the shortest directed path from source to target (BFS).

        Returns the list of node IDs including start and end, or [] if no path exists.
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return []
        if source_id == target_id:
            return [source_id]
        visited: set[str] = {source_id}
        queue: deque[list[str]] = deque([[source_id]])
        while queue:
            path = queue.popleft()
            nid = path[-1]
            for edge in self.get_out_edges(nid):
                if edge_types is not None and edge.edge_type not in edge_types:
                    continue
                neighbor = edge.target_id
                if neighbor == target_id:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return []

    def temporally_valid_nodes(self, at: str | None = None) -> list[GraphNode]:
        """Return all nodes valid at the given timestamp (or now)."""
        return [n for n in self._nodes.values() if n.is_temporally_valid(at)]

    # ------------------------------------------------------------------
    # Statistics & sync
    # ------------------------------------------------------------------

    def sync_edge_seq(self) -> None:
        """Sync internal edge sequence counter past loaded edge IDs (call after load)."""
        for eid in self._edges:
            parts = eid.split("-")
            if len(parts) >= 4 and parts[0] == "IKROS" and parts[1] == "EDGE":
                try:
                    seq = int(parts[-1])
                    self._edge_seq = max(self._edge_seq, seq)
                except ValueError:
                    pass

    def summary(self) -> dict[str, Any]:
        """Return a deterministic graph statistics summary."""
        node_type_counts: dict[str, int] = {}
        for n in self._nodes.values():
            node_type_counts[n.node_type] = node_type_counts.get(n.node_type, 0) + 1
        edge_type_counts: dict[str, int] = {}
        contradiction_count = 0
        for e in self._edges.values():
            edge_type_counts[e.edge_type] = edge_type_counts.get(e.edge_type, 0) + 1
            if e.edge_type in CONTRADICTION_EDGES:
                contradiction_count += 1
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "node_type_counts": dict(sorted(node_type_counts.items())),
            "edge_type_counts": dict(sorted(edge_type_counts.items())),
            "contradiction_count": contradiction_count,
        }
