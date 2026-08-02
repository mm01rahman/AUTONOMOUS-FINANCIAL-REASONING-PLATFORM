"""IKROS memory models — six-tier institutional research memory objects."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class MemoryTier(StrEnum):
    """Approved six-tier IKROS memory model."""

    WORKING = "T0_WORKING"
    EPISODIC = "T1_EPISODIC"
    SEMANTIC = "T2_SEMANTIC"
    PROCEDURAL = "T3_PROCEDURAL"
    INSTITUTIONAL = "T4_INSTITUTIONAL"
    ARCHIVE = "T5_ARCHIVE"


class MemoryLifecycleState(StrEnum):
    """Lifecycle states for governed memory records."""

    ACTIVE = "ACTIVE"
    CONSOLIDATED = "CONSOLIDATED"
    PROMOTED = "PROMOTED"
    MERGED = "MERGED"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"
    RESTORED = "RESTORED"


_TIER_CODES: dict[str, str] = {
    MemoryTier.WORKING: "T0",
    MemoryTier.EPISODIC: "T1",
    MemoryTier.SEMANTIC: "T2",
    MemoryTier.PROCEDURAL: "T3",
    MemoryTier.INSTITUTIONAL: "T4",
    MemoryTier.ARCHIVE: "T5",
}

_MEMORY_ID_PATTERN = re.compile(r"^IKMEM-T[0-5]-\d{8}-\d{4}$")


def make_memory_id(
    tier: str,
    date: datetime | None = None,
    seq: int = 1,
) -> str:
    """Return a canonical deterministic memory ID."""
    code = _TIER_CODES.get(tier, tier)
    d = date or datetime.now(UTC)
    return f"IKMEM-{code}-{d.strftime('%Y%m%d')}-{seq:04d}"


def is_valid_memory_id(memory_id: str) -> bool:
    """Return True if the memory ID matches the canonical pattern."""
    return bool(_MEMORY_ID_PATTERN.match(memory_id))


@dataclass
class MemoryVersion:
    """Version history entry for a memory record."""

    version: str
    changed_at: str
    change_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "changed_at": self.changed_at,
            "change_summary": self.change_summary,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MemoryVersion:
        return cls(
            version=str(d["version"]),
            changed_at=str(d["changed_at"]),
            change_summary=str(d["change_summary"]),
        )


@dataclass
class MemoryRecord:
    """Generic governed memory object across all six IKROS tiers."""

    memory_id: str
    tier: str
    entity_type: str
    title: str
    summary: str = ""
    source_ids: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    spec_refs: list[str] = field(default_factory=list)
    capability_refs: list[str] = field(default_factory=list)
    work_package_refs: list[str] = field(default_factory=list)
    graph_node_ids: list[str] = field(default_factory=list)
    lineage_ids: list[str] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    lifecycle_state: str = MemoryLifecycleState.ACTIVE.value
    version: str = "1.0.0"
    version_history: list[MemoryVersion] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    valid_from: str | None = None
    valid_to: str | None = None
    retired_at: str | None = None
    archived_at: str | None = None

    def fingerprint(self) -> str:
        """Return a deterministic fingerprint for duplicate detection."""
        data = {
            "tier": self.tier,
            "entity_type": self.entity_type,
            "title": self.title,
            "summary": self.summary,
            "source_ids": sorted(self.source_ids),
            "graph_node_ids": sorted(self.graph_node_ids),
            "payload": self.payload,
        }
        return json.dumps(data, sort_keys=True, default=str)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "tier": str(self.tier),
            "entity_type": self.entity_type,
            "title": self.title,
            "summary": self.summary,
            "source_ids": self.source_ids,
            "evidence_refs": self.evidence_refs,
            "spec_refs": self.spec_refs,
            "capability_refs": self.capability_refs,
            "work_package_refs": self.work_package_refs,
            "graph_node_ids": self.graph_node_ids,
            "lineage_ids": self.lineage_ids,
            "dependency_ids": self.dependency_ids,
            "tags": self.tags,
            "payload": self.payload,
            "confidence": self.confidence,
            "lifecycle_state": str(self.lifecycle_state),
            "version": self.version,
            "version_history": [entry.to_dict() for entry in self.version_history],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "retired_at": self.retired_at,
            "archived_at": self.archived_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MemoryRecord:
        return cls(
            memory_id=str(d["memory_id"]),
            tier=str(d["tier"]),
            entity_type=str(d["entity_type"]),
            title=str(d["title"]),
            summary=str(d.get("summary", "")),
            source_ids=list(d.get("source_ids", [])),
            evidence_refs=list(d.get("evidence_refs", [])),
            spec_refs=list(d.get("spec_refs", [])),
            capability_refs=list(d.get("capability_refs", [])),
            work_package_refs=list(d.get("work_package_refs", [])),
            graph_node_ids=list(d.get("graph_node_ids", [])),
            lineage_ids=list(d.get("lineage_ids", [])),
            dependency_ids=list(d.get("dependency_ids", [])),
            tags=list(d.get("tags", [])),
            payload=dict(d.get("payload", {})),
            confidence=float(d.get("confidence", 0.0)),
            lifecycle_state=str(
                d.get("lifecycle_state", MemoryLifecycleState.ACTIVE.value)
            ),
            version=str(d.get("version", "1.0.0")),
            version_history=[
                MemoryVersion.from_dict(entry)
                for entry in d.get("version_history", [])
                if isinstance(entry, dict)
            ],
            created_at=str(d.get("created_at", _now_iso())),
            updated_at=str(d.get("updated_at", _now_iso())),
            valid_from=str(d["valid_from"]) if d.get("valid_from") else None,
            valid_to=str(d["valid_to"]) if d.get("valid_to") else None,
            retired_at=str(d["retired_at"]) if d.get("retired_at") else None,
            archived_at=str(d["archived_at"]) if d.get("archived_at") else None,
        )


@dataclass
class WorkingMemorySnapshot:
    """Session-scoped T0 working memory snapshot."""

    session_id: str
    active_research_question: str | None = None
    active_experiment: str | None = None
    active_hypotheses: list[str] = field(default_factory=list)
    active_features: list[str] = field(default_factory=list)
    active_dataset_version: str | None = None
    current_results: dict[str, Any] = field(default_factory=dict)
    current_confidence: float = 0.0
    flags: dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_record(self, memory_id: str, title: str = "Working memory snapshot") -> MemoryRecord:
        """Convert the snapshot into a governed T0 memory record."""
        source_ids = [
            ref
            for ref in [
                self.active_research_question,
                self.active_experiment,
                self.active_dataset_version,
            ]
            if ref is not None
        ]
        source_ids.extend(self.active_hypotheses)
        source_ids.extend(self.active_features)
        return MemoryRecord(
            memory_id=memory_id,
            tier=MemoryTier.WORKING,
            entity_type="WorkingMemory",
            title=title,
            summary=f"Session {self.session_id} working context",
            source_ids=sorted(set(source_ids)),
            payload={
                "session_id": self.session_id,
                "active_research_question": self.active_research_question,
                "active_experiment": self.active_experiment,
                "active_hypotheses": self.active_hypotheses,
                "active_features": self.active_features,
                "active_dataset_version": self.active_dataset_version,
                "current_results": self.current_results,
                "flags": self.flags,
                "started_at": self.started_at,
            },
            confidence=self.current_confidence,
            updated_at=self.updated_at,
        )
