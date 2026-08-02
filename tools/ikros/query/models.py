"""IKROS query models — parsed queries, plans, results, and audit entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class QuerySource(StrEnum):
    ENTITY = "ENTITY"
    REGISTRY = "REGISTRY"
    GRAPH = "GRAPH"
    MEMORY = "MEMORY"


class GraphOperation(StrEnum):
    DESCENDANTS = "DESCENDANTS"
    ANCESTORS = "ANCESTORS"
    SUCCESSORS = "SUCCESSORS"
    PREDECESSORS = "PREDECESSORS"
    SUPPORTING_EXPERIMENTS = "SUPPORTING_EXPERIMENTS"
    CONTRADICTIONS = "CONTRADICTIONS"
    FEATURES_FROM_DATASET = "FEATURES_FROM_DATASET"
    SHORTEST_PATH = "SHORTEST_PATH"
    DEPENDENCY_CHAIN = "DEPENDENCY_CHAIN"
    CONTRADICTION_CHAIN = "CONTRADICTION_CHAIN"


@dataclass
class ParsedQuery:
    """Deterministic parsed query representation."""

    raw: str
    source: str
    target: str = ""
    filters: dict[str, str] = field(default_factory=dict)
    include_archive: bool = False
    graph_operation: str | None = None
    source_id: str | None = None
    target_id: str | None = None
    direction: str = "out"
    max_depth: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "source": str(self.source),
            "target": self.target,
            "filters": dict(sorted(self.filters.items())),
            "include_archive": self.include_archive,
            "graph_operation": (
                str(self.graph_operation) if self.graph_operation is not None else None
            ),
            "source_id": self.source_id,
            "target_id": self.target_id,
            "direction": self.direction,
            "max_depth": self.max_depth,
        }


@dataclass
class QueryPlanStep:
    """A single query planning step."""

    name: str
    source: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "source": self.source,
            "detail": self.detail,
        }


@dataclass
class QueryPlan:
    """Deterministic execution plan for a parsed query."""

    query: ParsedQuery
    steps: list[QueryPlanStep]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass
class QueryResultItem:
    """Normalized query result."""

    object: dict[str, Any]
    identifier: str
    type: str
    confidence: float
    lineage: dict[str, Any]
    evidence_refs: list[str]
    specification_refs: list[str]
    work_package_refs: list[str]
    temporal_metadata: dict[str, Any]
    version: str
    source: str
    rank: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "object": self.object,
            "identifier": self.identifier,
            "type": self.type,
            "confidence": self.confidence,
            "lineage": self.lineage,
            "evidence_refs": self.evidence_refs,
            "specification_refs": self.specification_refs,
            "work_package_refs": self.work_package_refs,
            "temporal_metadata": self.temporal_metadata,
            "version": self.version,
            "source": self.source,
            "rank": self.rank,
        }


@dataclass
class QueryAuditEntry:
    """Audit trail for a single query execution."""

    audit_id: str
    executed_at: str
    raw_query: str
    parsed_query: dict[str, Any]
    plan: dict[str, Any]
    result_ids: list[str]
    result_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "executed_at": self.executed_at,
            "raw_query": self.raw_query,
            "parsed_query": self.parsed_query,
            "plan": self.plan,
            "result_ids": self.result_ids,
            "result_count": self.result_count,
        }


@dataclass
class QueryResponse:
    """Structured query response."""

    parsed_query: ParsedQuery
    plan: QueryPlan
    results: list[QueryResultItem]
    audit_id: str
    executed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "parsed_query": self.parsed_query.to_dict(),
            "plan": self.plan.to_dict(),
            "results": [result.to_dict() for result in self.results],
            "audit_id": self.audit_id,
            "executed_at": self.executed_at,
        }
