"""IKROS Knowledge Graph models — node types, edge types, GraphNode, GraphEdge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Node types
# ---------------------------------------------------------------------------


class NodeType(StrEnum):
    """First-class node types in the Institutional Knowledge Graph (27 types)."""

    RESEARCH_QUESTION = "RESEARCH_QUESTION"
    ECONOMIC_THESIS = "ECONOMIC_THESIS"
    LITERATURE = "LITERATURE"
    DATASET = "DATASET"
    DATASET_VERSION = "DATASET_VERSION"
    FEATURE = "FEATURE"
    FEATURE_FAMILY = "FEATURE_FAMILY"
    FACTOR = "FACTOR"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT = "EXPERIMENT"
    VALIDATION = "VALIDATION"
    MODEL = "MODEL"
    WORLD_MODEL = "WORLD_MODEL"
    BACKTEST = "BACKTEST"
    WALK_FORWARD_STUDY = "WALK_FORWARD_STUDY"
    STRESS_TEST = "STRESS_TEST"
    MONTE_CARLO_STUDY = "MONTE_CARLO_STUDY"
    MARKET_EVENT = "MARKET_EVENT"
    REGIME = "REGIME"
    DECISION = "DECISION"
    POLICY = "POLICY"
    ALPHA_CANDIDATE = "ALPHA_CANDIDATE"
    ALPHA = "ALPHA"
    FAILURE = "FAILURE"
    EVIDENCE = "EVIDENCE"
    RESEARCH_CONCLUSION = "RESEARCH_CONCLUSION"
    KNOWLEDGE_OBJECT = "KNOWLEDGE_OBJECT"


# ---------------------------------------------------------------------------
# Edge types
# ---------------------------------------------------------------------------


class EdgeType(StrEnum):
    """Directed relationship types in the Institutional Knowledge Graph (20 types)."""

    USES_DATASET = "USES_DATASET"
    GENERATED_FEATURE = "GENERATED_FEATURE"
    SUPPORTED_BY = "SUPPORTED_BY"
    TESTED_IN = "TESTED_IN"
    VALIDATED_BY = "VALIDATED_BY"
    GENERATED_ALPHA = "GENERATED_ALPHA"
    REJECTED_BY = "REJECTED_BY"
    CONTRADICTED_BY = "CONTRADICTED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    SUPERSEDES = "SUPERSEDES"
    DEPENDS_ON = "DEPENDS_ON"
    RELATED_TO = "RELATED_TO"
    PRODUCED = "PRODUCED"
    EVALUATED = "EVALUATED"
    OBSERVED_DURING = "OBSERVED_DURING"
    EXPLAINS = "EXPLAINS"
    CAUSES = "CAUSES"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    IMPLEMENTS = "IMPLEMENTS"
    REFUTES = "REFUTES"


# Edge sets for traversal logic
CONTRADICTION_EDGES: frozenset[str] = frozenset({
    EdgeType.CONTRADICTED_BY,
    EdgeType.REJECTED_BY,
    EdgeType.REFUTES,
})

LINEAGE_EDGES: frozenset[str] = frozenset({
    EdgeType.DERIVED_FROM,
    EdgeType.DEPENDS_ON,
    EdgeType.USES_DATASET,
    EdgeType.GENERATED_FEATURE,
    EdgeType.TESTED_IN,
    EdgeType.VALIDATED_BY,
    EdgeType.GENERATED_ALPHA,
    EdgeType.IMPLEMENTS,
    EdgeType.PRODUCED,
})

RESEARCH_CHAIN_EDGES: frozenset[str] = frozenset({
    EdgeType.DEPENDS_ON,
    EdgeType.TESTED_IN,
    EdgeType.VALIDATED_BY,
    EdgeType.GENERATED_ALPHA,
    EdgeType.PRODUCED,
})

VALID_NODE_TYPES: frozenset[str] = frozenset(nt.value for nt in NodeType)
VALID_EDGE_TYPES: frozenset[str] = frozenset(et.value for et in EdgeType)


# ---------------------------------------------------------------------------
# GraphNode
# ---------------------------------------------------------------------------


@dataclass
class GraphNode:
    """A typed node in the Institutional Knowledge Graph."""

    node_id: str        # Reuses the IKROS entity ID as the stable node identifier
    node_type: str      # One of NodeType enum values
    ikros_id: str       # Canonical IKROS entity ID (equals node_id for IKROS entities)
    label: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    valid_from: str | None = None   # ISO 8601 — when this node first becomes valid
    valid_to: str | None = None     # ISO 8601 — when this node expires; None = open
    spec_refs: list[str] = field(default_factory=list)
    wp_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def is_temporally_valid(self, at: str | None = None) -> bool:
        """Return True if this node is valid at the given ISO 8601 timestamp."""
        t = at or _now_iso()
        if self.valid_from is not None and t < self.valid_from:
            return False
        if self.valid_to is not None and t > self.valid_to:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": str(self.node_type),
            "ikros_id": self.ikros_id,
            "label": self.label,
            "attributes": self.attributes,
            "confidence": self.confidence,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "spec_refs": self.spec_refs,
            "wp_refs": self.wp_refs,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GraphNode:
        return cls(
            node_id=str(d["node_id"]),
            node_type=str(d["node_type"]),
            ikros_id=str(d["ikros_id"]),
            label=str(d.get("label", "")),
            attributes=dict(d.get("attributes", {})),
            confidence=float(d.get("confidence", 0.0)),
            valid_from=d.get("valid_from"),
            valid_to=d.get("valid_to"),
            spec_refs=list(d.get("spec_refs", [])),
            wp_refs=list(d.get("wp_refs", [])),
            created_at=str(d.get("created_at", _now_iso())),
        )


# ---------------------------------------------------------------------------
# GraphEdge
# ---------------------------------------------------------------------------


@dataclass
class GraphEdge:
    """A typed directed relationship in the Institutional Knowledge Graph."""

    edge_id: str        # Canonical ID: IKROS-EDGE-{YYYYMMDD}-{SEQ}
    source_id: str      # Source node ID
    target_id: str      # Target node ID
    edge_type: str      # One of EdgeType enum values
    version: str = "1.0"
    timestamp: str = field(default_factory=_now_iso)
    confidence: float = 1.0
    evidence_ref: str = ""
    spec_ref: str = ""
    wp_ref: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def is_contradiction(self) -> bool:
        """Return True if this edge represents a contradiction relationship."""
        return self.edge_type in CONTRADICTION_EDGES

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": str(self.edge_type),
            "version": self.version,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "evidence_ref": self.evidence_ref,
            "spec_ref": self.spec_ref,
            "wp_ref": self.wp_ref,
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GraphEdge:
        return cls(
            edge_id=str(d["edge_id"]),
            source_id=str(d["source_id"]),
            target_id=str(d["target_id"]),
            edge_type=str(d["edge_type"]),
            version=str(d.get("version", "1.0")),
            timestamp=str(d.get("timestamp", _now_iso())),
            confidence=float(d.get("confidence", 1.0)),
            evidence_ref=str(d.get("evidence_ref", "")),
            spec_ref=str(d.get("spec_ref", "")),
            wp_ref=str(d.get("wp_ref", "")),
            attributes=dict(d.get("attributes", {})),
        )
