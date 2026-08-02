"""IKROS Knowledge Graph persistence — storage-independent repository abstraction.

Architecture (per SPEC-060 §7):

    KnowledgeGraphRepository  (abstract — port)
            ↓
    YAMLGraphRepository       (concrete — YAML file adapter)

Future adapters may implement SQLite, NetworkX, Neo4j, or Memgraph backends
without changing the KnowledgeGraph API.
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Any

import yaml

from tools.ikros.graph.core import KnowledgeGraph
from tools.ikros.graph.models import GraphEdge, GraphNode

# ---------------------------------------------------------------------------
# Port (abstract repository)
# ---------------------------------------------------------------------------


class KnowledgeGraphRepository(abc.ABC):
    """Abstract port for Knowledge Graph persistence.

    Implementations must be deterministic: save then load must produce
    an identical graph (same nodes, same edges, same topology).
    """

    @abc.abstractmethod
    def save(self, graph: KnowledgeGraph) -> None:
        """Persist the complete graph to the backing store."""

    @abc.abstractmethod
    def load(self) -> KnowledgeGraph:
        """Load and return the full graph from the backing store."""

    @abc.abstractmethod
    def save_node(self, node: GraphNode) -> None:
        """Upsert a single node in the backing store."""

    @abc.abstractmethod
    def save_edge(self, edge: GraphEdge) -> None:
        """Upsert a single edge in the backing store."""

    @abc.abstractmethod
    def node_ids(self) -> list[str]:
        """Return all persisted node IDs in deterministic order."""

    @abc.abstractmethod
    def edge_ids(self) -> list[str]:
        """Return all persisted edge IDs in deterministic order."""


# ---------------------------------------------------------------------------
# YAML adapter
# ---------------------------------------------------------------------------


class YAMLGraphRepository(KnowledgeGraphRepository):
    """YAML-backed graph repository.

    Layout::

        {base_dir}/nodes/{node_id}.yaml   — one file per node
        {base_dir}/edges.yaml             — all edges as a sorted YAML list

    Serialisation is deterministic: dicts use sorted keys; lists preserve
    insertion order.  Calling :meth:`save` then :meth:`load` is idempotent.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._nodes_dir = base_dir / "nodes"
        self._edges_file = base_dir / "edges.yaml"

    def save(self, graph: KnowledgeGraph) -> None:
        """Write every node and the full edge list to disk."""
        self._nodes_dir.mkdir(parents=True, exist_ok=True)
        for node in graph.nodes():
            self.save_node(node)
        edges_data = sorted(
            [e.to_dict() for e in graph.edges()],
            key=lambda d: d["edge_id"],
        )
        self._edges_file.parent.mkdir(parents=True, exist_ok=True)
        self._edges_file.write_text(
            yaml.dump(
                edges_data,
                Dumper=yaml.SafeDumper,
                default_flow_style=False,
                sort_keys=True,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    def load(self) -> KnowledgeGraph:
        """Load a graph from disk. Syncs edge sequence counter after load."""
        graph = KnowledgeGraph()
        self._nodes_dir.mkdir(parents=True, exist_ok=True)
        # Load nodes in deterministic (alphabetical) order
        for node_file in sorted(self._nodes_dir.glob("*.yaml")):
            data = self._read_yaml(node_file)
            if data:
                graph.add_node(GraphNode.from_dict(data))
        # Load edges
        if self._edges_file.exists():
            raw = yaml.safe_load(self._edges_file.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                for edge_data in raw:
                    if isinstance(edge_data, dict):
                        graph.add_edge(GraphEdge.from_dict(edge_data))
        graph.sync_edge_seq()
        return graph

    def save_node(self, node: GraphNode) -> None:
        """Write a single node YAML file (creates parent dirs as needed)."""
        self._nodes_dir.mkdir(parents=True, exist_ok=True)
        path = self._nodes_dir / f"{node.node_id}.yaml"
        path.write_text(
            yaml.dump(
                node.to_dict(),
                Dumper=yaml.SafeDumper,
                default_flow_style=False,
                sort_keys=True,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    def save_edge(self, edge: GraphEdge) -> None:
        """Append or update a single edge in edges.yaml (full rewrite)."""
        existing: list[dict[str, Any]] = []
        if self._edges_file.exists():
            raw = yaml.safe_load(self._edges_file.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                existing = [
                    d for d in raw
                    if isinstance(d, dict) and d.get("edge_id") != edge.edge_id
                ]
        existing.append(edge.to_dict())
        existing_sorted = sorted(existing, key=lambda d: d["edge_id"])
        self._edges_file.parent.mkdir(parents=True, exist_ok=True)
        self._edges_file.write_text(
            yaml.dump(
                existing_sorted,
                Dumper=yaml.SafeDumper,
                default_flow_style=False,
                sort_keys=True,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    def node_ids(self) -> list[str]:
        """Return sorted node IDs from disk."""
        if not self._nodes_dir.exists():
            return []
        return sorted(p.stem for p in self._nodes_dir.glob("*.yaml"))

    def edge_ids(self) -> list[str]:
        """Return sorted edge IDs from disk."""
        if not self._edges_file.exists():
            return []
        raw = yaml.safe_load(self._edges_file.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return sorted(str(d["edge_id"]) for d in raw if isinstance(d, dict) and "edge_id" in d)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        return raw
