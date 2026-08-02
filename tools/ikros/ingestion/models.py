"""IKROS ingestion models — structured sources, extracted objects, and reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class SourceFormat(StrEnum):
    MARKDOWN = "MARKDOWN"
    YAML = "YAML"
    JSON = "JSON"


class SourceKind(StrEnum):
    SPECIFICATION = "SPECIFICATION"
    INTERNAL_RESEARCH_REPORT = "INTERNAL_RESEARCH_REPORT"
    EXPERIMENT_REPORT = "EXPERIMENT_REPORT"
    VALIDATION_REPORT = "VALIDATION_REPORT"
    BACKTEST_REPORT = "BACKTEST_REPORT"
    STATISTICAL_REPORT = "STATISTICAL_REPORT"
    EVIDENCE_RECORD = "EVIDENCE_RECORD"
    ADR = "ADR"
    MARKDOWN = "MARKDOWN"
    YAML = "YAML"
    JSON = "JSON"


class KnowledgeObjectType(StrEnum):
    RESEARCH_QUESTION = "ResearchQuestion"
    ECONOMIC_THESIS = "EconomicThesis"
    HYPOTHESIS = "Hypothesis"
    FEATURE = "Feature"
    FEATURE_FAMILY = "FeatureFamily"
    DATASET = "Dataset"
    DATASET_VERSION = "DatasetVersion"
    EXPERIMENT = "Experiment"
    VALIDATION = "Validation"
    MARKET_EVENT = "MarketEvent"
    REGIME = "Regime"
    ALPHA_CANDIDATE = "AlphaCandidate"
    ALPHA = "Alpha"
    RESEARCH_CONCLUSION = "ResearchConclusion"
    EVIDENCE = "Evidence"
    CONTRADICTORY_EVIDENCE = "ContradictoryEvidence"
    KNOWLEDGE_OBJECT = "KnowledgeObject"


class IngestionStatus(StrEnum):
    INGESTED = "INGESTED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"


@dataclass
class ObjectRelationship:
    edge_type: str
    target_id: str
    direction: str = "out"
    confidence: float = 1.0
    evidence_ref: str = ""
    spec_ref: str = ""
    work_package_ref: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_type": self.edge_type,
            "target_id": self.target_id,
            "direction": self.direction,
            "confidence": self.confidence,
            "evidence_ref": self.evidence_ref,
            "spec_ref": self.spec_ref,
            "work_package_ref": self.work_package_ref,
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObjectRelationship:
        return cls(
            edge_type=str(data["edge_type"]),
            target_id=str(data["target_id"]),
            direction=str(data.get("direction", "out")).lower(),
            confidence=float(data.get("confidence", 1.0)),
            evidence_ref=str(data.get("evidence_ref", "")),
            spec_ref=str(data.get("spec_ref", "")),
            work_package_ref=str(data.get("work_package_ref", "")),
            attributes=dict(data.get("attributes", {})),
        )


@dataclass
class SourceDocument:
    source_ref: str
    source_kind: str
    source_format: str
    title: str
    content_hash: str
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)
    object_specs: list[dict[str, Any]] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedKnowledgeObject:
    identifier: str
    object_type: str
    title: str
    summary: str
    lifecycle_state: str
    confidence: float
    version: str
    source_reference: str
    source_kind: str
    source_format: str
    specification_refs: list[str] = field(default_factory=list)
    capability_refs: list[str] = field(default_factory=list)
    work_package_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    dependency_ids: list[str] = field(default_factory=list)
    relationships: list[ObjectRelationship] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    memory_tier: str | None = None
    created_at: str | None = None

    def fingerprint(self) -> str:
        return json.dumps(
            {
                "identifier": self.identifier,
                "object_type": self.object_type,
                "title": self.title,
                "summary": self.summary,
                "lifecycle_state": self.lifecycle_state,
                "confidence": self.confidence,
                "version": self.version,
                "source_reference": self.source_reference,
                "source_kind": self.source_kind,
                "source_format": self.source_format,
                "specification_refs": sorted(self.specification_refs),
                "capability_refs": sorted(self.capability_refs),
                "work_package_refs": sorted(self.work_package_refs),
                "evidence_refs": sorted(self.evidence_refs),
                "source_ids": sorted(self.source_ids),
                "dependency_ids": sorted(self.dependency_ids),
                "relationships": [
                    relationship.to_dict()
                    for relationship in sorted(
                        self.relationships,
                        key=lambda item: (
                            item.edge_type,
                            item.direction,
                            item.target_id,
                        ),
                    )
                ],
                "attributes": self.attributes,
                "memory_tier": self.memory_tier,
                "created_at": self.created_at,
            },
            sort_keys=True,
            default=str,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "object_type": self.object_type,
            "title": self.title,
            "summary": self.summary,
            "lifecycle_state": self.lifecycle_state,
            "confidence": self.confidence,
            "version": self.version,
            "source_reference": self.source_reference,
            "source_kind": self.source_kind,
            "source_format": self.source_format,
            "specification_refs": self.specification_refs,
            "capability_refs": self.capability_refs,
            "work_package_refs": self.work_package_refs,
            "evidence_refs": self.evidence_refs,
            "source_ids": self.source_ids,
            "dependency_ids": self.dependency_ids,
            "relationships": [item.to_dict() for item in self.relationships],
            "attributes": self.attributes,
            "memory_tier": self.memory_tier,
            "created_at": self.created_at,
        }


@dataclass
class IngestionReport:
    ingestion_id: str
    source_ref: str
    source_kind: str
    source_format: str
    source_hash: str
    source_version: str
    status: str
    ingested_at: str = field(default_factory=_now_iso)
    object_ids: list[str] = field(default_factory=list)
    memory_ids: list[str] = field(default_factory=list)
    graph_node_ids: list[str] = field(default_factory=list)
    object_fingerprints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ingestion_id": self.ingestion_id,
            "source_ref": self.source_ref,
            "source_kind": str(self.source_kind),
            "source_format": str(self.source_format),
            "source_hash": self.source_hash,
            "source_version": self.source_version,
            "status": str(self.status),
            "ingested_at": self.ingested_at,
            "object_ids": self.object_ids,
            "memory_ids": self.memory_ids,
            "graph_node_ids": self.graph_node_ids,
            "object_fingerprints": self.object_fingerprints,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IngestionReport:
        return cls(
            ingestion_id=str(data["ingestion_id"]),
            source_ref=str(data["source_ref"]),
            source_kind=str(data["source_kind"]),
            source_format=str(data["source_format"]),
            source_hash=str(data["source_hash"]),
            source_version=str(data.get("source_version", "1.0.0")),
            status=str(data.get("status", IngestionStatus.INGESTED.value)),
            ingested_at=str(data.get("ingested_at", _now_iso())),
            object_ids=list(data.get("object_ids", [])),
            memory_ids=list(data.get("memory_ids", [])),
            graph_node_ids=list(data.get("graph_node_ids", [])),
            object_fingerprints=list(data.get("object_fingerprints", [])),
            warnings=list(data.get("warnings", [])),
        )


@dataclass
class IngestionResult:
    status: str
    report: IngestionReport
    objects: list[ExtractedKnowledgeObject] = field(default_factory=list)

