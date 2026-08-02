"""IKROS memory retrieval — deterministic structured filtering."""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.ikros.memory.models import MemoryRecord


@dataclass
class MemoryQuery:
    """Structured deterministic retrieval request."""

    identifier: str | None = None
    tier: str | None = None
    entity_type: str | None = None
    specification: str | None = None
    capability: str | None = None
    work_package: str | None = None
    evidence: str | None = None
    feature: str | None = None
    hypothesis: str | None = None
    experiment: str | None = None
    alpha: str | None = None
    lineage: str | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
    start_time: str | None = None
    end_time: str | None = None
    lifecycle_state: str | None = None
    tags: list[str] = field(default_factory=list)


class MemoryRetriever:
    """Deterministic retrieval engine over memory records."""

    def __init__(self, records: dict[str, MemoryRecord]) -> None:
        self._records = records

    def get(self, identifier: str) -> MemoryRecord | None:
        return self._records.get(identifier)

    def retrieve(self, query: MemoryQuery) -> list[MemoryRecord]:
        """Return all records matching every populated query field."""
        records = sorted(self._records.values(), key=lambda record: record.memory_id)
        return [record for record in records if self._matches(record, query)]

    def by_identifier(self, identifier: str) -> MemoryRecord | None:
        return self.get(identifier)

    def by_entity_type(self, entity_type: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(entity_type=entity_type))

    def by_specification(self, spec_ref: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(specification=spec_ref))

    def by_capability(self, capability_ref: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(capability=capability_ref))

    def by_work_package(self, work_package_ref: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(work_package=work_package_ref))

    def by_evidence(self, evidence_ref: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(evidence=evidence_ref))

    def by_feature(self, feature_id: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(feature=feature_id))

    def by_hypothesis(self, hypothesis_id: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(hypothesis=hypothesis_id))

    def by_experiment(self, experiment_id: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(experiment=experiment_id))

    def by_alpha(self, alpha_id: str) -> list[MemoryRecord]:
        return self.retrieve(MemoryQuery(alpha=alpha_id))

    def _matches(self, record: MemoryRecord, query: MemoryQuery) -> bool:
        if query.identifier is not None and record.memory_id != query.identifier:
            return False
        if query.tier is not None and record.tier != query.tier:
            return False
        if query.entity_type is not None and record.entity_type != query.entity_type:
            return False
        if (
            query.specification is not None
            and query.specification not in record.spec_refs
        ):
            return False
        if query.capability is not None and query.capability not in record.capability_refs:
            return False
        if (
            query.work_package is not None
            and query.work_package not in record.work_package_refs
        ):
            return False
        if query.evidence is not None and query.evidence not in record.evidence_refs:
            return False
        if query.feature is not None and not self._matches_ref(record, query.feature):
            return False
        if (
            query.hypothesis is not None
            and not self._matches_ref(record, query.hypothesis)
        ):
            return False
        if (
            query.experiment is not None
            and not self._matches_ref(record, query.experiment)
        ):
            return False
        if query.alpha is not None and not self._matches_ref(record, query.alpha):
            return False
        if query.lineage is not None and query.lineage not in record.lineage_ids:
            return False
        if (
            query.min_confidence is not None
            and record.confidence < query.min_confidence
        ):
            return False
        if (
            query.max_confidence is not None
            and record.confidence > query.max_confidence
        ):
            return False
        if (
            query.lifecycle_state is not None
            and record.lifecycle_state != query.lifecycle_state
        ):
            return False
        if query.start_time is not None and record.created_at < query.start_time:
            return False
        if query.end_time is not None and record.created_at > query.end_time:
            return False
        if query.tags and not all(tag in record.tags for tag in query.tags):
            return False
        return True

    def _matches_ref(self, record: MemoryRecord, ref: str) -> bool:
        return (
            ref in record.source_ids
            or ref in record.dependency_ids
            or ref in record.graph_node_ids
            or ref in record.lineage_ids
        )
