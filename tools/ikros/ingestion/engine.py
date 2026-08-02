"""IKROS Institutional Research Ingestion Engine."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from tools.ikros.graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    KnowledgeGraphRepository,
    NodeType,
    YAMLGraphRepository,
)
from tools.ikros.identifiers import make_ikros_id
from tools.ikros.ingestion.loaders import SourceLoader
from tools.ikros.ingestion.models import (
    ExtractedKnowledgeObject,
    IngestionReport,
    IngestionResult,
    IngestionStatus,
    KnowledgeObjectType,
    ObjectRelationship,
    SourceDocument,
    SourceKind,
)
from tools.ikros.ingestion.persistence import IngestionRepository, YAMLIngestionRepository
from tools.ikros.ingestion.validation import (
    IngestionValidationError,
    validate_extracted_objects,
    validate_source_document,
)
from tools.ikros.memory import (
    MemoryRecord,
    MemoryTier,
    ResearchMemoryManager,
    YAMLMemoryRepository,
)
from tools.ikros.models import (
    Alpha,
    AlphaCandidate,
    AlphaPaperStatus,
    ConfidenceVector,
    Experiment,
    Feature,
    FeatureFamily,
    Hypothesis,
    IKROSEntity,
    LineageDependencies,
    LineageEvidence,
    LineageExperiments,
    LineageOrigin,
    LineageRecord,
    ResearchQuestion,
)
from tools.ikros.query import QueryEngine
from tools.ikros.query.audit import QueryAuditLog
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import BaseRegistry
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.feature import FeatureRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry

_REGISTRY_TYPES: set[str] = {
    "ResearchQuestion",
    "Hypothesis",
    "Experiment",
    "Feature",
    "FeatureFamily",
    "AlphaCandidate",
    "Alpha",
}

_NODE_TYPE_MAP: dict[str, str] = {
    "ResearchQuestion": NodeType.RESEARCH_QUESTION,
    "EconomicThesis": NodeType.ECONOMIC_THESIS,
    "Hypothesis": NodeType.HYPOTHESIS,
    "Feature": NodeType.FEATURE,
    "FeatureFamily": NodeType.FEATURE_FAMILY,
    "Dataset": NodeType.DATASET,
    "DatasetVersion": NodeType.DATASET_VERSION,
    "Experiment": NodeType.EXPERIMENT,
    "Validation": NodeType.VALIDATION,
    "MarketEvent": NodeType.MARKET_EVENT,
    "Regime": NodeType.REGIME,
    "AlphaCandidate": NodeType.ALPHA_CANDIDATE,
    "Alpha": NodeType.ALPHA,
    "ResearchConclusion": NodeType.RESEARCH_CONCLUSION,
    "Evidence": NodeType.EVIDENCE,
    "ContradictoryEvidence": NodeType.EVIDENCE,
    "KnowledgeObject": NodeType.KNOWLEDGE_OBJECT,
}


class ResearchIngestionEngine:
    """Deterministic document-to-IKROS ingestion pipeline."""

    def __init__(
        self,
        registries: dict[str, BaseRegistry[IKROSEntity]] | None = None,
        graph: KnowledgeGraph | None = None,
        graph_repository: KnowledgeGraphRepository | None = None,
        memory: ResearchMemoryManager | None = None,
        ingestion_repository: IngestionRepository | None = None,
        loader: SourceLoader | None = None,
        base_dir: Path | None = None,
    ) -> None:
        resolved_base = base_dir or Path("data") / "ikros"
        self._base_dir = resolved_base
        self._registries = registries or self._default_registries(resolved_base / "registries")
        self._graph_repository = graph_repository or YAMLGraphRepository(resolved_base / "graph")
        self._graph = graph or self._graph_repository.load()
        memory_repository = YAMLMemoryRepository(resolved_base / "memory")
        self._memory = memory or ResearchMemoryManager(memory_repository, self._graph)
        self._ingestion_repository = ingestion_repository or YAMLIngestionRepository(
            resolved_base / "ingestion"
        )
        self._loader = loader or SourceLoader()

    def ingest_path(self, path: Path | str) -> IngestionResult:
        document = self._loader.load_path(Path(path))
        return self.ingest_document(document)

    def ingest_document(self, document: SourceDocument) -> IngestionResult:
        validate_source_document(document)
        existing = self._ingestion_repository.find_by_source(
            document.source_ref,
            document.content_hash,
        )
        if existing is not None:
            return IngestionResult(
                status=IngestionStatus.SKIPPED_DUPLICATE,
                report=existing,
                objects=[],
            )

        objects = self._normalize_objects(document)
        validate_extracted_objects(
            objects,
            self._existing_identifiers(),
            self._ingestion_repository.known_fingerprints(),
        )

        object_ids: list[str] = []
        memory_ids: list[str] = []
        graph_node_ids: list[str] = []

        for obj in objects:
            entity = self._register_entity_if_supported(obj)
            self._ensure_graph_node(obj, entity)
            object_ids.append(obj.identifier)
            graph_node_ids.append(obj.identifier)

        for obj in objects:
            for edge in self._build_edges(obj):
                self._graph.add_edge(edge)

        self._graph_repository.save(self._graph)

        for obj in objects:
            memory = self._build_memory_record(obj)
            self._memory.store(memory)
            memory_ids.append(memory.memory_id)

        report = IngestionReport(
            ingestion_id=self._ingestion_repository.next_ingestion_id(),
            source_ref=document.source_ref,
            source_kind=document.source_kind,
            source_format=document.source_format,
            source_hash=document.content_hash,
            source_version=document.version,
            status=IngestionStatus.INGESTED,
            object_ids=object_ids,
            memory_ids=memory_ids,
            graph_node_ids=graph_node_ids,
            object_fingerprints=[obj.fingerprint() for obj in objects],
        )
        self._ingestion_repository.save_report(report)
        return IngestionResult(
            status=IngestionStatus.INGESTED,
            report=report,
            objects=objects,
        )

    def build_query_engine(self) -> QueryEngine:
        return QueryEngine(
            registries=self._registries,
            graph=self._graph,
            memory=self._memory,
            audit_log=QueryAuditLog(self._base_dir / "ingestion" / "query-audit"),
        )

    def _normalize_objects(self, document: SourceDocument) -> list[ExtractedKnowledgeObject]:
        raw_objects = self._extract_objects(document)
        if not raw_objects:
            raise IngestionValidationError(
                f"{document.source_ref}: no deterministic IKROS objects found"
            )
        reserved_ids = self._existing_identifiers()
        normalized: list[ExtractedKnowledgeObject] = []
        for index, raw in enumerate(raw_objects, start=1):
            object_type = str(
                raw.get("type") or raw.get("object_type") or KnowledgeObjectType.KNOWLEDGE_OBJECT
            )
            identifier = str(raw.get("identifier") or raw.get("ikros_id") or "")
            if not identifier:
                identifier = self._next_identifier(object_type, reserved_ids)
            reserved_ids.add(identifier)
            created_at = str(
                raw.get("created_at")
                or raw.get("origin_created_at")
                or document.metadata.get("created_at")
                or document.metadata.get("effective_date")
                or datetime.now(UTC).isoformat()
            )
            normalized.append(
                ExtractedKnowledgeObject(
                    identifier=identifier,
                    object_type=object_type,
                    title=str(raw.get("title") or f"{object_type} {index}"),
                    summary=str(raw.get("summary", "")),
                    lifecycle_state=str(
                        raw.get(
                            "lifecycle_state",
                            self._default_lifecycle(object_type),
                        )
                    ),
                    confidence=float(
                        raw.get(
                            "confidence",
                            self._default_confidence(document.source_kind),
                        )
                    ),
                    version=str(raw.get("version", document.version)),
                    source_reference=document.source_ref,
                    source_kind=document.source_kind,
                    source_format=document.source_format,
                    specification_refs=_sorted_unique(
                        raw.get("specification_refs")
                        or raw.get("spec_refs")
                        or self._default_spec_refs(document)
                    ),
                    capability_refs=_sorted_unique(raw.get("capability_refs", [])),
                    work_package_refs=_sorted_unique(
                        raw.get("work_package_refs")
                        or raw.get("wp_refs")
                        or self._default_work_package_refs(document)
                    ),
                    evidence_refs=_sorted_unique(
                        raw.get("evidence_refs")
                        or raw.get("evidence")
                        or self._default_evidence_refs(document)
                    ),
                    source_ids=_sorted_unique(raw.get("source_ids", [])),
                    dependency_ids=_sorted_unique(raw.get("dependency_ids", [])),
                    relationships=[
                        ObjectRelationship.from_dict(item)
                        for item in raw.get("relationships", [])
                        if isinstance(item, dict)
                    ],
                    attributes=dict(raw.get("attributes", {})),
                    memory_tier=raw.get("memory_tier"),
                    created_at=created_at,
                )
            )
        return normalized

    def _extract_objects(self, document: SourceDocument) -> list[dict[str, Any]]:
        if document.object_specs:
            return document.object_specs
        if document.payload.get("schema_version") == "ERS-1.0":
            return self._extract_evidence_record(document)
        if document.source_kind in {SourceKind.SPECIFICATION, SourceKind.ADR, SourceKind.MARKDOWN}:
            return [self._extract_document_knowledge_object(document)]
        if document.source_kind in {SourceKind.JSON, SourceKind.YAML}:
            return [self._extract_document_knowledge_object(document)]
        return []

    def _extract_evidence_record(self, document: SourceDocument) -> list[dict[str, Any]]:
        payload = document.payload
        evidence_id = str(payload.get("evidence_id", Path(document.source_ref).stem))
        work_package_id = str(payload.get("work_package_id", ""))
        gates = payload.get("quality_gates", [])
        summary = f"ERS evidence import for {work_package_id}".strip()
        gate_results = [
            dict(item)
            for item in gates
            if isinstance(item, dict)
        ]
        validation_verdict = "COMPLETE" if all(
            str(item.get("result", "FAIL")) == "PASS" for item in gate_results
        ) else "INVALIDATED"
        return [
            {
                "type": KnowledgeObjectType.EVIDENCE,
                "title": f"Evidence {evidence_id}",
                "summary": summary,
                "lifecycle_state": "ACTIVE",
                "confidence": 1.0 if validation_verdict == "COMPLETE" else 0.6,
                "specification_refs": self._default_spec_refs(document),
                "work_package_refs": [work_package_id] if work_package_id else [],
                "evidence_refs": [document.source_ref],
                "attributes": {
                    "evidence_id": evidence_id,
                    "quality_gates": gate_results,
                    "boundary_compliance": payload.get("boundary_compliance", {}),
                    "verdict": payload.get("verdict", {}),
                },
            },
            {
                "type": KnowledgeObjectType.VALIDATION,
                "title": f"Validation {evidence_id}",
                "summary": f"Quality-gate validation extracted from {evidence_id}",
                "lifecycle_state": validation_verdict,
                "confidence": 1.0 if validation_verdict == "COMPLETE" else 0.5,
                "specification_refs": self._default_spec_refs(document),
                "work_package_refs": [work_package_id] if work_package_id else [],
                "evidence_refs": [document.source_ref],
                "source_ids": [],
                "dependency_ids": [],
                "attributes": {
                    "evidence_id": evidence_id,
                    "capability": payload.get("capability", {}),
                    "quality_gates": gate_results,
                    "all_gates_passed": bool(
                        payload.get("verdict", {}).get("all_gates_passed", False)
                    ),
                },
            },
        ]

    def _extract_document_knowledge_object(self, document: SourceDocument) -> dict[str, Any]:
        ordered_sections = sorted(document.sections)
        summary = (
            document.sections.get("Overview")
            or document.sections.get("Mission")
            or document.sections.get("Summary")
            or f"{document.source_kind} imported from {document.source_ref}"
        )
        return {
            "type": KnowledgeObjectType.KNOWLEDGE_OBJECT,
            "title": document.title,
            "summary": summary[:400],
            "lifecycle_state": "ACTIVE",
            "confidence": self._default_confidence(document.source_kind),
            "specification_refs": self._default_spec_refs(document),
            "work_package_refs": self._default_work_package_refs(document),
            "evidence_refs": self._default_evidence_refs(document),
            "attributes": {
                "document_metadata": dict(sorted(document.metadata.items())),
                "section_names": ordered_sections,
            },
        }

    def _register_entity_if_supported(
        self,
        obj: ExtractedKnowledgeObject,
    ) -> IKROSEntity | None:
        if obj.object_type not in _REGISTRY_TYPES:
            return None
        entity = self._materialize_entity(obj)
        if obj.object_type == "FeatureFamily":
            registry = self._feature_registry()
            if not isinstance(entity, FeatureFamily):
                raise IngestionValidationError(
                    "FeatureFamily ingestion materialized invalid entity"
                )
            registry.register_family(entity)
            return entity
        if obj.object_type == "Alpha":
            alpha_registry = self._alpha_registry()
            if not isinstance(entity, Alpha):
                raise IngestionValidationError("Alpha ingestion materialized invalid entity")
            if not entity.promoted_from:
                raise IngestionValidationError("Alpha ingestion requires promoted_from")
            alpha_registry.promote(entity.promoted_from, entity)
            return entity
        self._registry_for_type(obj.object_type).register(entity)
        return entity

    def _materialize_entity(self, obj: ExtractedKnowledgeObject) -> IKROSEntity:
        common: dict[str, Any] = {
            "ikros_id": obj.identifier,
            "entity_type": obj.object_type,
            "version": obj.version,
            "lifecycle_state": obj.lifecycle_state,
            "confidence": self._confidence_vector(obj.confidence),
            "lineage": self._build_lineage(obj),
            "spec_refs": list(obj.specification_refs),
            "capability_refs": list(obj.capability_refs),
            "work_package_refs": list(obj.work_package_refs),
        }
        fields = dict(obj.attributes)
        if obj.object_type == "ResearchQuestion":
            return ResearchQuestion(
                title=obj.title,
                motivation=str(fields.get("motivation", obj.summary)),
                scope=str(fields.get("scope", "MACRO")),
                instrument=str(fields.get("instrument", "")),
                time_horizon=str(fields.get("time_horizon", "")),
                campaign_tag=str(fields.get("campaign_tag", "")),
                linked_hypotheses=list(fields.get("linked_hypotheses", [])),
                linked_conclusions=list(fields.get("linked_conclusions", [])),
                **common,
            )
        if obj.object_type == "Hypothesis":
            return Hypothesis(
                statement=str(fields.get("statement", obj.title)),
                null_hypothesis=str(fields.get("null_hypothesis", "H0")),
                alternative_hypothesis=str(
                    fields.get("alternative_hypothesis", obj.summary or "H1")
                ),
                significance_level=float(fields.get("significance_level", 0.05)),
                power=float(fields.get("power", 0.80)),
                prior_confidence=float(fields.get("prior_confidence", obj.confidence)),
                posterior_confidence=float(fields.get("posterior_confidence", obj.confidence)),
                source_rq=str(fields.get("source_rq", "")),
                motivating_theses=list(fields.get("motivating_theses", [])),
                experiments=list(fields.get("experiments", [])),
                validations=list(fields.get("validations", [])),
                contradictions=list(fields.get("contradictions", [])),
                **common,
            )
        if obj.object_type == "Experiment":
            return Experiment(
                title=obj.title,
                hypotheses=list(fields.get("hypotheses", [])),
                protocol=str(fields.get("protocol", obj.summary)),
                dataset_versions=list(fields.get("dataset_versions", [])),
                feature_versions=list(fields.get("feature_versions", [])),
                parameters=dict(fields.get("parameters", {})),
                random_seed=int(fields.get("random_seed", 42)),
                in_sample_start=str(fields.get("in_sample_start", "")),
                in_sample_end=str(fields.get("in_sample_end", "")),
                out_of_sample_start=str(fields.get("out_of_sample_start", "")),
                out_of_sample_end=str(fields.get("out_of_sample_end", "")),
                reproducibility_hash=str(fields.get("reproducibility_hash", "")),
                git_commit=str(fields.get("git_commit", "")),
                completed_at=fields.get("completed_at"),
                validations_produced=list(fields.get("validations_produced", [])),
                failures_produced=list(fields.get("failures_produced", [])),
                **common,
            )
        if obj.object_type == "FeatureFamily":
            return FeatureFamily(
                name=str(fields.get("name", obj.title)),
                description=str(fields.get("description", obj.summary)),
                member_features=list(fields.get("member_features", [])),
                **common,
            )
        if obj.object_type == "Feature":
            return Feature(
                name=str(fields.get("name", obj.title)),
                family_id=str(fields.get("family_id", "")),
                computation=str(fields.get("computation", obj.summary)),
                inputs=list(fields.get("inputs", [])),
                lookback=str(fields.get("lookback", "")),
                normalization=str(fields.get("normalization", "")),
                stationarity=str(fields.get("stationarity", "UNKNOWN")),
                information_content=float(fields.get("information_content", obj.confidence)),
                stability_score=float(fields.get("stability_score", obj.confidence)),
                used_in_experiments=list(fields.get("used_in_experiments", [])),
                superseded_by=fields.get("superseded_by"),
                **common,
            )
        if obj.object_type == "AlphaCandidate":
            return AlphaCandidate(
                name=str(fields.get("name", obj.title)),
                strategy_type=str(fields.get("strategy_type", "HYBRID")),
                sharpe_oos=float(fields.get("sharpe_oos", 0.0)),
                max_drawdown=float(fields.get("max_drawdown", 0.0)),
                direction_accuracy=float(fields.get("direction_accuracy", 0.0)),
                win_rate=float(fields.get("win_rate", 0.0)),
                promotion_score=float(fields.get("promotion_score", obj.confidence)),
                promotion_status=str(fields.get("promotion_status", obj.lifecycle_state)),
                rejection_reasons=list(fields.get("rejection_reasons", [])),
                backtests=list(fields.get("backtests", [])),
                walk_forwards=list(fields.get("walk_forwards", [])),
                monte_carlos=list(fields.get("monte_carlos", [])),
                implements_hypotheses=list(fields.get("implements_hypotheses", [])),
                **common,
            )
        if obj.object_type == "Alpha":
            return Alpha(
                promoted_from=str(fields.get("promoted_from", "")),
                promotion_date=str(fields.get("promotion_date", obj.created_at or "")),
                promotion_evidence=str(
                    fields.get(
                        "promotion_evidence",
                        obj.evidence_refs[0] if obj.evidence_refs else "",
                    )
                ),
                paper_trading_status=str(
                    fields.get("paper_trading_status", AlphaPaperStatus.NOT_STARTED.value)
                ),
                live_eligible=bool(fields.get("live_eligible", False)),
                **common,
            )
        raise IngestionValidationError(f"unsupported registry object type '{obj.object_type}'")

    def _build_lineage(self, obj: ExtractedKnowledgeObject) -> LineageRecord:
        fields = obj.attributes
        origin = LineageOrigin(
            created_by=str(fields.get("created_by", "ikros-ingestion-engine")),
            created_at=str(obj.created_at or datetime.now(UTC).isoformat()),
            creation_context=obj.source_kind,
            motivation=str(fields.get("motivation", f"Ingested from {obj.source_reference}")),
        )
        experiments = LineageExperiments(
            tested_in=list(fields.get("tested_in", fields.get("experiments", []))),
            validated_by=list(fields.get("validated_by", fields.get("validations", []))),
        )
        return LineageRecord(
            origin=origin,
            dependencies=LineageDependencies(
                inputs=list(obj.source_ids),
                datasets=list(fields.get("datasets", fields.get("dataset_versions", []))),
                features=list(fields.get("features", fields.get("feature_versions", []))),
                external_refs=[obj.source_reference],
            ),
            experiments=experiments,
            evidence=LineageEvidence(ers_records=list(obj.evidence_refs)),
        )

    def _ensure_graph_node(
        self,
        obj: ExtractedKnowledgeObject,
        entity: IKROSEntity | None,
    ) -> None:
        if self._graph.has_node(obj.identifier):
            raise IngestionValidationError(f"graph node '{obj.identifier}' already exists")
        attributes = entity.to_dict() if entity is not None else {
            "summary": obj.summary,
            **obj.attributes,
            "source_reference": obj.source_reference,
            "source_kind": obj.source_kind,
        }
        self._graph.add_node(
            GraphNode(
                node_id=obj.identifier,
                ikros_id=obj.identifier,
                node_type=_NODE_TYPE_MAP.get(obj.object_type, NodeType.KNOWLEDGE_OBJECT),
                label=obj.title,
                attributes=attributes,
                confidence=obj.confidence,
                valid_from=obj.created_at,
                spec_refs=list(obj.specification_refs),
                wp_refs=list(obj.work_package_refs),
                created_at=str(obj.created_at or datetime.now(UTC).isoformat()),
            )
        )

    def _build_edges(self, obj: ExtractedKnowledgeObject) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        seen: set[tuple[str, str, str]] = set()
        for target_id in _sorted_unique(obj.source_ids + obj.dependency_ids):
            self._ensure_reference_node(target_id)
            edge_key: tuple[str, str, str] = (
                obj.identifier,
                target_id,
                EdgeType.DEPENDS_ON,
            )
            if edge_key not in seen:
                edges.append(self._make_edge(obj.identifier, target_id, EdgeType.DEPENDS_ON, obj))
                seen.add(edge_key)
        for relationship in obj.relationships:
            self._ensure_reference_node(relationship.target_id)
            if relationship.direction == "out":
                source_id, target_id = obj.identifier, relationship.target_id
            else:
                source_id, target_id = relationship.target_id, obj.identifier
            edge_key = (source_id, target_id, relationship.edge_type)
            if edge_key not in seen:
                edges.append(
                    self._make_edge(
                        source_id,
                        target_id,
                        relationship.edge_type,
                        obj,
                        confidence=relationship.confidence,
                        evidence_ref=relationship.evidence_ref,
                        spec_ref=relationship.spec_ref,
                        wp_ref=relationship.work_package_ref,
                        attributes=relationship.attributes,
                    )
                )
                seen.add(edge_key)
        for source_id, target_id, edge_type in self._automatic_relationships(obj):
            self._ensure_reference_node(source_id)
            self._ensure_reference_node(target_id)
            edge_key = (source_id, target_id, edge_type)
            if edge_key not in seen:
                edges.append(self._make_edge(source_id, target_id, edge_type, obj))
                seen.add(edge_key)
        return edges

    def _automatic_relationships(
        self,
        obj: ExtractedKnowledgeObject,
    ) -> list[tuple[str, str, str]]:
        fields = obj.attributes
        relationships: list[tuple[str, str, str]] = []
        if obj.object_type == "Hypothesis":
            source_rq = str(fields.get("source_rq", ""))
            if source_rq:
                relationships.append((obj.identifier, source_rq, EdgeType.DEPENDS_ON))
            for validation in fields.get("validations", []):
                if isinstance(validation, str) and validation:
                    relationships.append((obj.identifier, validation, EdgeType.VALIDATED_BY))
        if obj.object_type == "Experiment":
            for hypothesis in fields.get("hypotheses", []):
                if isinstance(hypothesis, str) and hypothesis:
                    relationships.append((hypothesis, obj.identifier, EdgeType.TESTED_IN))
            for dataset in fields.get("dataset_versions", []):
                if isinstance(dataset, str) and dataset:
                    relationships.append((obj.identifier, dataset, EdgeType.USES_DATASET))
        if obj.object_type == "Feature":
            for source_id in obj.source_ids:
                if source_id.startswith("IKROS-DS") or source_id.startswith("IKROS-DSV"):
                    relationships.append((obj.identifier, source_id, EdgeType.DERIVED_FROM))
        if obj.object_type == "AlphaCandidate":
            for hypothesis in fields.get("implements_hypotheses", []):
                if isinstance(hypothesis, str) and hypothesis:
                    relationships.append((obj.identifier, hypothesis, EdgeType.IMPLEMENTS))
        if obj.object_type == "ContradictoryEvidence":
            for target in fields.get("contradicts", []):
                if isinstance(target, str) and target:
                    relationships.append((obj.identifier, target, EdgeType.CONTRADICTED_BY))
        return relationships

    def _make_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        obj: ExtractedKnowledgeObject,
        *,
        confidence: float | None = None,
        evidence_ref: str = "",
        spec_ref: str = "",
        wp_ref: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> GraphEdge:
        return GraphEdge(
            edge_id=self._graph.next_edge_id(),
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            confidence=obj.confidence if confidence is None else confidence,
            evidence_ref=evidence_ref or (obj.evidence_refs[0] if obj.evidence_refs else ""),
            spec_ref=spec_ref or (obj.specification_refs[0] if obj.specification_refs else ""),
            wp_ref=wp_ref or (obj.work_package_refs[0] if obj.work_package_refs else ""),
            attributes=attributes or {},
        )

    def _build_memory_record(self, obj: ExtractedKnowledgeObject) -> MemoryRecord:
        tier = obj.memory_tier or self._default_memory_tier(obj)
        created_at = str(obj.created_at or datetime.now(UTC).isoformat())
        archived_at = created_at if tier == MemoryTier.ARCHIVE.value else None
        valid_to = created_at if tier == MemoryTier.ARCHIVE.value else None
        lifecycle_state = "ARCHIVED" if tier == MemoryTier.ARCHIVE.value else "ACTIVE"
        return MemoryRecord(
            memory_id=self._memory.next_id(tier),
            tier=tier,
            entity_type=obj.object_type,
            title=obj.title,
            summary=obj.summary,
            source_ids=[obj.identifier, *obj.source_ids],
            evidence_refs=list(obj.evidence_refs),
            spec_refs=list(obj.specification_refs),
            capability_refs=list(obj.capability_refs),
            work_package_refs=list(obj.work_package_refs),
            graph_node_ids=[obj.identifier],
            dependency_ids=list(obj.dependency_ids),
            tags=[
                obj.object_type.lower(),
                obj.source_kind.lower(),
                "ingested",
            ],
            payload={
                "source_reference": obj.source_reference,
                "source_kind": obj.source_kind,
                "source_format": obj.source_format,
                "version": obj.version,
                "lifecycle_state": obj.lifecycle_state,
                "attributes": obj.attributes,
            },
            confidence=obj.confidence,
            lifecycle_state=lifecycle_state,
            created_at=created_at,
            updated_at=created_at,
            valid_from=created_at,
            valid_to=valid_to,
            archived_at=archived_at,
        )

    def _default_memory_tier(self, obj: ExtractedKnowledgeObject) -> str:
        if obj.lifecycle_state == "ARCHIVED":
            return MemoryTier.ARCHIVE.value
        if obj.object_type in {"Evidence", "Validation", "Experiment", "MarketEvent"}:
            return MemoryTier.EPISODIC.value
        if obj.object_type in {"ResearchConclusion", "EconomicThesis", "Alpha", "AlphaCandidate"}:
            return MemoryTier.INSTITUTIONAL.value
        if obj.object_type == "KnowledgeObject" and obj.source_kind in {
            SourceKind.SPECIFICATION,
            SourceKind.ADR,
        }:
            return MemoryTier.PROCEDURAL.value
        return MemoryTier.SEMANTIC.value

    def _ensure_reference_node(self, identifier: str) -> None:
        if self._graph.has_node(identifier):
            return
        entity = self._find_entity(identifier)
        if entity is None:
            raise IngestionValidationError(f"graph reference '{identifier}' does not exist")
        placeholder = ExtractedKnowledgeObject(
            identifier=identifier,
            object_type=entity.entity_type,
            title=getattr(entity, "title", getattr(entity, "name", identifier)),
            summary="",
            lifecycle_state=entity.lifecycle_state,
            confidence=entity.confidence.overall(),
            version=entity.version,
            source_reference="existing-registry-entity",
            source_kind="JSON",
            source_format="JSON",
            specification_refs=list(entity.spec_refs),
            capability_refs=list(entity.capability_refs),
            work_package_refs=list(entity.work_package_refs),
        )
        self._ensure_graph_node(placeholder, entity)

    def _existing_identifiers(self) -> set[str]:
        identifiers = set(self._graph.node_ids())
        identifiers.update(self._collect_registry_ids())
        return identifiers

    def _collect_registry_ids(self) -> set[str]:
        identifiers: set[str] = set()
        for registry in self._registries.values():
            identifiers.update(entity.ikros_id for entity in registry.list_all())
            if isinstance(registry, FeatureRegistry):
                identifiers.update(entity.ikros_id for entity in registry.list_families())
            if isinstance(registry, AlphaRegistry):
                identifiers.update(entity.ikros_id for entity in registry.list_alphas())
        return identifiers

    def _find_entity(self, identifier: str) -> IKROSEntity | None:
        for registry in self._registries.values():
            if registry.exists(identifier):
                return registry.get(identifier)
            if isinstance(registry, FeatureRegistry):
                try:
                    return registry.get_family(identifier)
                except KeyError:
                    pass
            if isinstance(registry, AlphaRegistry):
                try:
                    return registry.get_alpha(identifier)
                except KeyError:
                    pass
        return None

    def _registry_for_type(self, object_type: str) -> BaseRegistry[IKROSEntity]:
        if object_type == "ResearchQuestion":
            return self._registries["ResearchQuestion"]
        if object_type == "Hypothesis":
            return self._registries["Hypothesis"]
        if object_type == "Experiment":
            return self._registries["Experiment"]
        if object_type == "Feature":
            return self._registries["Feature"]
        if object_type in {"FeatureFamily", "AlphaCandidate", "Alpha"}:
            if object_type == "FeatureFamily":
                return self._registries["Feature"]
            return self._registries["AlphaCandidate"]
        raise IngestionValidationError(f"no registry configured for '{object_type}'")

    def _feature_registry(self) -> FeatureRegistry:
        registry = self._registries["Feature"]
        if not isinstance(registry, FeatureRegistry):
            raise IngestionValidationError("Feature registry is not configured correctly")
        return registry

    def _alpha_registry(self) -> AlphaRegistry:
        registry = self._registries["AlphaCandidate"]
        if not isinstance(registry, AlphaRegistry):
            raise IngestionValidationError("Alpha registry is not configured correctly")
        return registry

    def _next_identifier(self, object_type: str, reserved_ids: set[str]) -> str:
        sequence = 1
        while True:
            candidate = make_ikros_id(object_type, seq=sequence)
            if candidate not in reserved_ids:
                return candidate
            sequence += 1

    def _default_spec_refs(self, document: SourceDocument) -> list[str]:
        refs: list[str] = []
        for key in ("specification_refs", "spec_refs"):
            value = document.metadata.get(key)
            if isinstance(value, list):
                refs.extend(str(item) for item in value)
        for key in ("specification_id", "specification_authority"):
            value = document.metadata.get(key)
            if value:
                refs.append(str(value))
        if not refs:
            refs.append("SPEC-060")
        return _sorted_unique(refs)

    def _default_work_package_refs(self, document: SourceDocument) -> list[str]:
        work_package = document.metadata.get("work_package_id")
        if work_package:
            return [str(work_package)]
        return []

    def _default_evidence_refs(self, document: SourceDocument) -> list[str]:
        if document.source_kind == SourceKind.EVIDENCE_RECORD:
            return [document.source_ref]
        return []

    def _default_lifecycle(self, object_type: str) -> str:
        if object_type == "ResearchQuestion":
            return "OPEN"
        if object_type == "Hypothesis":
            return "PROPOSED"
        if object_type == "Experiment":
            return "DESIGNED"
        if object_type == "Feature":
            return "DRAFT"
        if object_type == "FeatureFamily":
            return "ACTIVE"
        if object_type == "AlphaCandidate":
            return "CANDIDATE"
        if object_type == "Alpha":
            return "PROMOTED"
        if object_type == "Validation":
            return "PENDING"
        if object_type == "ResearchConclusion":
            return "DRAFT"
        return "ACTIVE"

    def _default_confidence(self, source_kind: str) -> float:
        if source_kind == SourceKind.EVIDENCE_RECORD:
            return 0.95
        if source_kind in {SourceKind.SPECIFICATION, SourceKind.ADR}:
            return 0.85
        if source_kind in {
            SourceKind.EXPERIMENT_REPORT,
            SourceKind.VALIDATION_REPORT,
            SourceKind.BACKTEST_REPORT,
            SourceKind.STATISTICAL_REPORT,
        }:
            return 0.75
        return 0.60

    def _confidence_vector(self, level: float) -> ConfidenceVector:
        return ConfidenceVector(
            prior=level,
            statistical=level,
            economic=level,
            data=level,
            validation=level,
            replication=level,
        )

    def _default_registries(
        self,
        base_dir: Path,
    ) -> dict[str, BaseRegistry[IKROSEntity]]:
        return {
            "ResearchQuestion": cast(BaseRegistry[IKROSEntity], ResearchRegistry(base_dir)),
            "Hypothesis": cast(BaseRegistry[IKROSEntity], HypothesisRegistry(base_dir)),
            "Experiment": cast(BaseRegistry[IKROSEntity], ExperimentRegistry(base_dir)),
            "Feature": cast(BaseRegistry[IKROSEntity], FeatureRegistry(base_dir)),
            "AlphaCandidate": cast(BaseRegistry[IKROSEntity], AlphaRegistry(base_dir)),
        }


def _sorted_unique(values: Iterable[object]) -> list[str]:
    return sorted({str(value) for value in values if value})
