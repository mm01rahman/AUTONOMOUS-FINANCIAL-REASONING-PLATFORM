"""IKROS ingestion validation — source, object, duplicate, and reference checks."""

from __future__ import annotations

from tools.ikros.graph import VALID_EDGE_TYPES
from tools.ikros.identifiers import is_valid_ikros_id
from tools.ikros.ingestion.models import ExtractedKnowledgeObject, SourceDocument

_NON_REGISTRY_LIFECYCLES: dict[str, set[str]] = {
    "EconomicThesis": {"DRAFT", "VALIDATED", "RETIRED"},
    "Dataset": {"ACTIVE", "DEPRECATED", "ARCHIVED"},
    "DatasetVersion": {"VALIDATED", "ARCHIVED"},
    "Validation": {"PENDING", "COMPLETE", "INVALIDATED", "ARCHIVED"},
    "MarketEvent": {"RECORDED", "ARCHIVED"},
    "Regime": {"ACTIVE", "SUPERSEDED", "ARCHIVED"},
    "ResearchConclusion": {"DRAFT", "PUBLISHED", "ARCHIVED"},
    "Evidence": {"ACTIVE", "ARCHIVED"},
    "ContradictoryEvidence": {"ACTIVE", "RESOLVED", "ARCHIVED"},
    "KnowledgeObject": {"ACTIVE", "ARCHIVED"},
}

_SUPPORTED_TYPES: set[str] = {
    "ResearchQuestion",
    "Hypothesis",
    "Experiment",
    "Feature",
    "FeatureFamily",
    "AlphaCandidate",
    "Alpha",
    *list(_NON_REGISTRY_LIFECYCLES),
}


class IngestionValidationError(ValueError):
    """Raised when a source or extracted object violates ingestion constraints."""


def validate_source_document(document: SourceDocument) -> None:
    if not document.source_ref:
        raise IngestionValidationError("source_ref is required")
    if not document.title:
        raise IngestionValidationError("source title is required")
    if not document.source_kind:
        raise IngestionValidationError("source_kind is required")
    if not document.source_format:
        raise IngestionValidationError("source_format is required")
    if not document.content_hash:
        raise IngestionValidationError("content_hash is required")


def validate_extracted_objects(
    objects: list[ExtractedKnowledgeObject],
    existing_ids: set[str],
    known_fingerprints: set[str],
) -> None:
    seen_ids: set[str] = set()
    seen_fingerprints: set[str] = set()
    batch_ids = {obj.identifier for obj in objects}
    for obj in objects:
        if obj.object_type not in _SUPPORTED_TYPES:
            raise IngestionValidationError(f"unsupported object type '{obj.object_type}'")
        if not obj.identifier or not is_valid_ikros_id(obj.identifier):
            raise IngestionValidationError(
                f"{obj.object_type}: invalid identifier '{obj.identifier}'"
            )
        if obj.identifier in existing_ids:
            raise IngestionValidationError(
                f"{obj.object_type} '{obj.identifier}' already exists"
            )
        if obj.identifier in seen_ids:
            raise IngestionValidationError(f"duplicate object identifier '{obj.identifier}'")
        seen_ids.add(obj.identifier)
        if not obj.title:
            raise IngestionValidationError(f"{obj.identifier}: title is required")
        if not obj.source_reference:
            raise IngestionValidationError(f"{obj.identifier}: source_reference is required")
        if not obj.specification_refs:
            raise IngestionValidationError(
                f"{obj.identifier}: at least one specification reference is required"
            )
        if not (0.0 <= obj.confidence <= 1.0):
            raise IngestionValidationError(
                f"{obj.identifier}: confidence must be in [0, 1]"
            )
        if obj.object_type in _NON_REGISTRY_LIFECYCLES:
            allowed = _NON_REGISTRY_LIFECYCLES[obj.object_type]
            if obj.lifecycle_state not in allowed:
                raise IngestionValidationError(
                    f"{obj.identifier}: lifecycle_state '{obj.lifecycle_state}' "
                    f"is not allowed for {obj.object_type}"
                )
        fingerprint = obj.fingerprint()
        if fingerprint in seen_fingerprints:
            raise IngestionValidationError(
                f"{obj.identifier}: duplicate extracted object content detected"
            )
        if fingerprint in known_fingerprints:
            raise IngestionValidationError(
                f"{obj.identifier}: object content already ingested"
            )
        seen_fingerprints.add(fingerprint)
        _validate_references(obj, existing_ids, batch_ids)


def _validate_references(
    obj: ExtractedKnowledgeObject,
    existing_ids: set[str],
    batch_ids: set[str],
) -> None:
    known_ids = existing_ids | batch_ids
    for reference in set(obj.source_ids + obj.dependency_ids):
        if reference not in known_ids:
            raise IngestionValidationError(
                f"{obj.identifier}: reference '{reference}' does not exist"
            )
    for relationship in obj.relationships:
        if relationship.edge_type not in VALID_EDGE_TYPES:
            raise IngestionValidationError(
                f"{obj.identifier}: invalid edge type '{relationship.edge_type}'"
            )
        if relationship.direction not in {"in", "out"}:
            raise IngestionValidationError(
                f"{obj.identifier}: invalid relationship direction '{relationship.direction}'"
            )
        if relationship.target_id not in known_ids:
            raise IngestionValidationError(
                f"{obj.identifier}: relationship target '{relationship.target_id}' does not exist"
            )
        if not (0.0 <= relationship.confidence <= 1.0):
            raise IngestionValidationError(
                f"{obj.identifier}: relationship confidence must be in [0, 1]"
            )

