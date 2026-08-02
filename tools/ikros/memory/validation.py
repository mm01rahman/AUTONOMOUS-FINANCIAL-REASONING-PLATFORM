"""IKROS memory validation — tier, lifecycle, lineage, and archive integrity."""

from __future__ import annotations

from tools.ikros.graph import KnowledgeGraph
from tools.ikros.memory.models import (
    MemoryLifecycleState,
    MemoryRecord,
    MemoryTier,
    is_valid_memory_id,
)


class MemoryValidationError(ValueError):
    """Raised when a memory object fails validation."""


_VALID_TIERS = {tier.value for tier in MemoryTier}
_VALID_STATES = {state.value for state in MemoryLifecycleState}


def validate_memory_record(
    record: MemoryRecord,
    existing_records: dict[str, MemoryRecord] | None = None,
    graph: KnowledgeGraph | None = None,
) -> list[str]:
    """Validate a single memory record."""
    errors: list[str] = []
    if not record.memory_id:
        errors.append("memory_id is required")
    elif not is_valid_memory_id(record.memory_id):
        errors.append(
            f"memory_id '{record.memory_id}' does not match canonical pattern"
        )
    if record.tier not in _VALID_TIERS:
        errors.append(f"tier '{record.tier}' is not a valid MemoryTier")
    if not record.entity_type:
        errors.append("entity_type is required")
    if not record.title:
        errors.append("title is required")
    if not (0.0 <= record.confidence <= 1.0):
        errors.append("confidence must be in [0.0, 1.0]")
    if record.lifecycle_state not in _VALID_STATES:
        errors.append(
            f"lifecycle_state '{record.lifecycle_state}' is not a valid MemoryLifecycleState"
        )
    if record.valid_from is not None and record.valid_to is not None:
        if record.valid_from >= record.valid_to:
            errors.append(
                "temporal inconsistency: "
                f"valid_from '{record.valid_from}' >= valid_to '{record.valid_to}'"
            )
    if (
        record.tier != MemoryTier.WORKING.value
        and not record.source_ids
        and not record.graph_node_ids
    ):
        errors.append("non-working memory must have source_ids or graph_node_ids")
    if (
        record.lifecycle_state == MemoryLifecycleState.RETIRED.value
        and record.retired_at is None
    ):
        errors.append("retired records must set retired_at")
    if (
        record.tier == MemoryTier.ARCHIVE.value
        or record.lifecycle_state == MemoryLifecycleState.ARCHIVED.value
    ) and record.archived_at is None:
        errors.append("archived records must set archived_at")
    if len(record.lineage_ids) != len(set(record.lineage_ids)):
        errors.append("lineage_ids must be unique")
    if len(record.source_ids) != len(set(record.source_ids)):
        errors.append("source_ids must be unique")
    if len(record.graph_node_ids) != len(set(record.graph_node_ids)):
        errors.append("graph_node_ids must be unique")
    if graph is not None:
        for node_id in record.graph_node_ids:
            if not graph.has_node(node_id):
                errors.append(f"graph node '{node_id}' not found")
    if existing_records is not None:
        for lineage_id in record.lineage_ids:
            if lineage_id not in existing_records:
                errors.append(f"lineage memory '{lineage_id}' not found")
        for dep_id in record.dependency_ids:
            if dep_id not in existing_records and not _is_graph_node(dep_id, graph):
                errors.append(f"dependency reference '{dep_id}' not found")
    return errors


def validate_memory_store(
    records: dict[str, MemoryRecord],
    graph: KnowledgeGraph | None = None,
) -> list[str]:
    """Validate the entire memory store."""
    errors: list[str] = []
    fingerprints: dict[str, str] = {}
    for record in sorted(records.values(), key=lambda item: item.memory_id):
        record_errors = validate_memory_record(record, records, graph)
        for error in record_errors:
            errors.append(f"[record:{record.memory_id}] {error}")
        fingerprint = record.fingerprint()
        existing_id = fingerprints.get(fingerprint)
        if existing_id is not None:
            errors.append(
                f"[duplicate] memory '{record.memory_id}' duplicates '{existing_id}'"
            )
        else:
            fingerprints[fingerprint] = record.memory_id
    return errors


def assert_memory_valid(
    records: dict[str, MemoryRecord],
    graph: KnowledgeGraph | None = None,
) -> None:
    """Validate the store and raise on any failure."""
    errors = validate_memory_store(records, graph)
    if errors:
        raise MemoryValidationError(
            f"IKROS memory validation failed ({len(errors)} errors):\n"
            + "\n".join(f"  - {error}" for error in errors)
        )


def find_archive_integrity_issues(records: dict[str, MemoryRecord]) -> list[str]:
    """Return archived records missing archive metadata."""
    issues: list[str] = []
    for record in sorted(records.values(), key=lambda item: item.memory_id):
        if record.tier == MemoryTier.ARCHIVE.value and record.archived_at is None:
            issues.append(record.memory_id)
    return issues


def find_broken_lineage(records: dict[str, MemoryRecord]) -> list[str]:
    """Return record IDs with unresolved lineage references."""
    issues: list[str] = []
    for record in sorted(records.values(), key=lambda item: item.memory_id):
        if any(lineage_id not in records for lineage_id in record.lineage_ids):
            issues.append(record.memory_id)
    return issues


def _is_graph_node(
    ref: str,
    graph: KnowledgeGraph | None,
) -> bool:
    if graph is None:
        return False
    return graph.has_node(ref)
