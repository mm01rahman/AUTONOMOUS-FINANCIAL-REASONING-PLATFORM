"""IKROS memory core — six-tier governed storage, consolidation, and lifecycle."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from tools.ikros.graph import KnowledgeGraph
from tools.ikros.memory.models import (
    MemoryLifecycleState,
    MemoryRecord,
    MemoryTier,
    MemoryVersion,
    WorkingMemorySnapshot,
    make_memory_id,
)
from tools.ikros.memory.persistence import MemoryRepository
from tools.ikros.memory.retrieval import MemoryQuery, MemoryRetriever
from tools.ikros.memory.validation import assert_memory_valid, validate_memory_record


class MemoryError(RuntimeError):
    """Raised for IKROS memory integrity or lifecycle violations."""


_ALLOWED_TIER_TRANSITIONS: dict[str, set[str]] = {
    MemoryTier.WORKING: {
        MemoryTier.EPISODIC,
        MemoryTier.INSTITUTIONAL,
        MemoryTier.ARCHIVE,
    },
    MemoryTier.EPISODIC: {
        MemoryTier.SEMANTIC,
        MemoryTier.PROCEDURAL,
        MemoryTier.INSTITUTIONAL,
        MemoryTier.ARCHIVE,
    },
    MemoryTier.SEMANTIC: {
        MemoryTier.INSTITUTIONAL,
        MemoryTier.ARCHIVE,
    },
    MemoryTier.PROCEDURAL: {
        MemoryTier.INSTITUTIONAL,
        MemoryTier.ARCHIVE,
    },
    MemoryTier.INSTITUTIONAL: {MemoryTier.ARCHIVE},
    MemoryTier.ARCHIVE: {
        MemoryTier.EPISODIC,
        MemoryTier.SEMANTIC,
        MemoryTier.PROCEDURAL,
        MemoryTier.INSTITUTIONAL,
    },
}


class ResearchMemoryManager:
    """Deterministic in-memory controller for the IKROS memory subsystem."""

    def __init__(
        self,
        repository: MemoryRepository | None = None,
        graph: KnowledgeGraph | None = None,
    ) -> None:
        self._repository = repository
        self._graph = graph
        self._records: dict[str, MemoryRecord] = {}
        if repository is not None:
            for record in repository.load():
                self._records[record.memory_id] = record

    def store(self, record: MemoryRecord) -> str:
        """Validate and store a memory record."""
        if record.memory_id in self._records:
            raise MemoryError(f"Duplicate memory '{record.memory_id}'")
        errors = validate_memory_record(record, self._records, self._graph)
        if errors:
            raise MemoryError("; ".join(errors))
        if self._is_duplicate_fingerprint(record):
            raise MemoryError(f"Duplicate memory content detected for '{record.memory_id}'")
        self._records[record.memory_id] = record
        self._persist(record)
        return record.memory_id

    def store_working_memory(self, snapshot: WorkingMemorySnapshot) -> str:
        """Store a T0 working-memory snapshot."""
        memory_id = self.next_id(MemoryTier.WORKING)
        return self.store(snapshot.to_record(memory_id))

    def get(self, memory_id: str) -> MemoryRecord:
        if memory_id not in self._records:
            raise KeyError(f"Memory '{memory_id}' not found")
        return self._records[memory_id]

    def exists(self, memory_id: str) -> bool:
        return memory_id in self._records

    def list_all(self) -> list[MemoryRecord]:
        return [self._records[key] for key in sorted(self._records)]

    def list_by_tier(self, tier: str) -> list[MemoryRecord]:
        return [
            record
            for record in self.list_all()
            if record.tier == tier
        ]

    def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        return MemoryRetriever(self._records).retrieve(query)

    def next_id(self, tier: str, date: datetime | None = None) -> str:
        seq = 1
        while True:
            candidate = make_memory_id(tier, date=date, seq=seq)
            if candidate not in self._records:
                return candidate
            seq += 1

    def promote(
        self,
        memory_id: str,
        target_tier: str,
        note: str = "",
    ) -> MemoryRecord:
        """Promote a record to a higher tier."""
        return self._move_to_tier(
            memory_id,
            target_tier,
            MemoryLifecycleState.PROMOTED.value,
            note or f"Promoted to {target_tier}",
        )

    def consolidate(
        self,
        memory_id: str,
        target_tier: str | None = None,
        note: str = "",
    ) -> MemoryRecord:
        """Consolidate a record according to deterministic tier rules."""
        record = self.get(memory_id)
        resolved_tier = target_tier or self._default_consolidation_target(record)
        return self._move_to_tier(
            memory_id,
            resolved_tier,
            MemoryLifecycleState.CONSOLIDATED.value,
            note or f"Consolidated to {resolved_tier}",
        )

    def merge(
        self,
        memory_ids: list[str],
        target_tier: str,
        title: str,
        summary: str = "",
    ) -> MemoryRecord:
        """Merge multiple records into a deterministic consolidated record."""
        if not memory_ids:
            raise MemoryError("merge requires at least one memory ID")
        source_records = [self.get(memory_id) for memory_id in sorted(memory_ids)]
        merged = MemoryRecord(
            memory_id=self.next_id(target_tier),
            tier=target_tier,
            entity_type="MergedMemory",
            title=title,
            summary=summary,
            source_ids=_sorted_unique(
                ref
                for record in source_records
                for ref in record.source_ids
            ),
            evidence_refs=_sorted_unique(
                ref
                for record in source_records
                for ref in record.evidence_refs
            ),
            spec_refs=_sorted_unique(
                ref
                for record in source_records
                for ref in record.spec_refs
            ),
            capability_refs=_sorted_unique(
                ref
                for record in source_records
                for ref in record.capability_refs
            ),
            work_package_refs=_sorted_unique(
                ref
                for record in source_records
                for ref in record.work_package_refs
            ),
            graph_node_ids=_sorted_unique(
                ref
                for record in source_records
                for ref in record.graph_node_ids
            ),
            lineage_ids=[record.memory_id for record in source_records],
            dependency_ids=_sorted_unique(
                ref
                for record in source_records
                for ref in record.dependency_ids
            ),
            tags=_sorted_unique(
                tag
                for record in source_records
                for tag in record.tags
            ),
            payload={
                "merged_records": [record.memory_id for record in source_records],
                "source_payloads": {
                    record.memory_id: record.payload
                    for record in source_records
                },
            },
            confidence=max(record.confidence for record in source_records),
            lifecycle_state=MemoryLifecycleState.MERGED.value,
        )
        self.store(merged)
        return merged

    def retire(self, memory_id: str, reason: str) -> MemoryRecord:
        """Retire a record without deleting it."""
        return self._update_record(
            memory_id,
            {
                "lifecycle_state": MemoryLifecycleState.RETIRED.value,
                "retired_at": _now_iso(),
                "valid_to": _now_iso(),
                "summary": f"{self.get(memory_id).summary} | RETIRED: {reason}".strip(),
            },
            f"Retired: {reason}",
        )

    def archive(self, memory_id: str, reason: str) -> MemoryRecord:
        """Archive a record while keeping it searchable."""
        return self._move_to_tier(
            memory_id,
            MemoryTier.ARCHIVE,
            MemoryLifecycleState.ARCHIVED.value,
            f"Archived: {reason}",
        )

    def restore(
        self,
        memory_id: str,
        target_tier: str,
        note: str = "",
    ) -> MemoryRecord:
        """Restore a record from archive into an active tier."""
        record = self.get(memory_id)
        if record.tier != MemoryTier.ARCHIVE.value:
            raise MemoryError("only archived memory can be restored")
        return self._move_to_tier(
            memory_id,
            target_tier,
            MemoryLifecycleState.RESTORED.value,
            note or f"Restored to {target_tier}",
        )

    def validate(self) -> None:
        """Validate the full store."""
        assert_memory_valid(self._records, self._graph)

    def summary(self) -> dict[str, Any]:
        """Return deterministic memory subsystem statistics."""
        tier_counts: dict[str, int] = {}
        for tier in MemoryTier:
            tier_counts[tier.value] = len(self.list_by_tier(tier.value))
        archived = len(self.list_by_tier(MemoryTier.ARCHIVE.value))
        institutional = len(self.list_by_tier(MemoryTier.INSTITUTIONAL.value))
        graph_nodes = 0 if self._graph is None else self._graph.node_count()
        return {
            "record_count": len(self._records),
            "tier_counts": tier_counts,
            "working_memory_age_hours": self._working_age_hours(),
            "institutional_memory_objects": institutional,
            "archived_objects": archived,
            "graph_nodes": graph_nodes,
        }

    def _move_to_tier(
        self,
        memory_id: str,
        target_tier: str,
        lifecycle_state: str,
        change_summary: str,
    ) -> MemoryRecord:
        record = self.get(memory_id)
        allowed = _ALLOWED_TIER_TRANSITIONS.get(record.tier, set())
        if target_tier not in allowed:
            raise MemoryError(
                f"tier transition '{record.tier}' -> '{target_tier}' is not allowed"
            )
        delta: dict[str, Any] = {
            "tier": target_tier,
            "lifecycle_state": lifecycle_state,
        }
        if target_tier == MemoryTier.ARCHIVE.value:
            delta["archived_at"] = _now_iso()
            delta["valid_to"] = _now_iso()
        else:
            delta["archived_at"] = None
            delta["valid_to"] = None
        if lifecycle_state == MemoryLifecycleState.RESTORED.value:
            delta["valid_from"] = _now_iso()
        return self._update_record(memory_id, delta, change_summary)

    def _update_record(
        self,
        memory_id: str,
        delta: dict[str, Any],
        change_summary: str,
    ) -> MemoryRecord:
        record = self.get(memory_id)
        data = record.to_dict()
        data.update(delta)
        data["updated_at"] = _now_iso()
        history = list(data.get("version_history", []))
        history.append(
            MemoryVersion(
                version=record.version,
                changed_at=_now_iso(),
                change_summary=change_summary,
            ).to_dict()
        )
        data["version_history"] = history
        updated = MemoryRecord.from_dict(data)
        remaining = {
            key: value
            for key, value in self._records.items()
            if key != memory_id
        }
        errors = validate_memory_record(updated, remaining, self._graph)
        if errors:
            raise MemoryError("; ".join(errors))
        self._records[memory_id] = updated
        self._persist(updated)
        return updated

    def _default_consolidation_target(self, record: MemoryRecord) -> str:
        if record.tier == MemoryTier.WORKING.value:
            return MemoryTier.EPISODIC
        if (
            record.tier == MemoryTier.EPISODIC.value
            and record.entity_type == "Failure"
        ):
            return MemoryTier.INSTITUTIONAL
        if record.tier == MemoryTier.EPISODIC.value and record.confidence >= 0.75:
            return MemoryTier.SEMANTIC
        if record.tier == MemoryTier.EPISODIC.value:
            return MemoryTier.INSTITUTIONAL
        if record.lifecycle_state in {
            MemoryLifecycleState.RETIRED.value,
            MemoryLifecycleState.ARCHIVED.value,
        }:
            return MemoryTier.ARCHIVE
        return MemoryTier.INSTITUTIONAL

    def _working_age_hours(self) -> float:
        working = self.list_by_tier(MemoryTier.WORKING.value)
        if not working:
            return 0.0
        oldest = min(record.created_at for record in working)
        delta = datetime.now(UTC) - datetime.fromisoformat(oldest)
        return round(delta.total_seconds() / 3600.0, 4)

    def _is_duplicate_fingerprint(self, candidate: MemoryRecord) -> bool:
        fingerprint = candidate.fingerprint()
        return any(
            existing.fingerprint() == fingerprint
            for existing in self._records.values()
        )

    def _persist(self, record: MemoryRecord) -> None:
        if self._repository is not None:
            self._repository.save_record(record)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sorted_unique(values: Iterable[object]) -> list[str]:
    return sorted(set(str(value) for value in values))
