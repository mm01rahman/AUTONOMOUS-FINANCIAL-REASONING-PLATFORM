"""IKROS confidence validation — evidence, assessment, history, and audit checks."""

from __future__ import annotations

from collections.abc import Iterable

from tools.ikros.confidence.models import (
    ConfidenceAssessment,
    ConfidenceAuditEntry,
    ConfidenceDimensions,
    ConfidenceEvidence,
    ConfidenceEvidenceType,
    ConfidenceHistoryEntry,
    ContradictionSeverity,
    EvidenceRelation,
)


class ConfidenceValidationError(ValueError):
    """Raised when a confidence assessment or audit artifact is invalid."""


def validate_dimensions(
    dimensions: ConfidenceDimensions,
    *,
    entity_type: str,
) -> list[str]:
    errors: list[str] = []
    values = dimensions.to_dict(entity_type)
    for key in (
        "prior",
        "statistical",
        "economic",
        "data",
        "experimental",
        "validation",
        "replication",
        "operational",
        "overall",
    ):
        value = float(values[key])
        if not (0.0 <= value <= 0.95):
            errors.append(f"{key} must be in [0.0, 0.95], got {value}")
    if not dimensions.last_updated:
        errors.append("last_updated is required")
    return errors


def validate_evidence(evidence: ConfidenceEvidence) -> list[str]:
    errors: list[str] = []
    if not evidence.evidence_id:
        errors.append("evidence_id is required")
    if evidence.evidence_type not in {item.value for item in ConfidenceEvidenceType}:
        errors.append(f"unsupported evidence_type '{evidence.evidence_type}'")
    if evidence.relation not in {item.value for item in EvidenceRelation}:
        errors.append(f"unsupported relation '{evidence.relation}'")
    if not (0.0 <= evidence.confidence_weight <= 1.0):
        errors.append("confidence_weight must be in [0, 1]")
    if evidence.relation == EvidenceRelation.CONTRADICTS and not evidence.contradiction_severity:
        errors.append("contradiction_severity is required for contradicting evidence")
    if evidence.contradiction_severity and evidence.contradiction_severity not in {
        item.value for item in ContradictionSeverity
    }:
        errors.append(f"unsupported contradiction_severity '{evidence.contradiction_severity}'")
    if not evidence.observed_at:
        errors.append("observed_at is required")
    if not evidence.references.all_identifiers():
        errors.append("evidence must carry at least one structured reference")
    return errors


def validate_assessment(
    assessment: ConfidenceAssessment,
    *,
    known_identifiers: set[str],
) -> list[str]:
    errors: list[str] = []
    if not assessment.assessment_id:
        errors.append("assessment_id is required")
    if not assessment.target_id:
        errors.append("target_id is required")
    elif assessment.target_id not in known_identifiers:
        errors.append(f"target_id '{assessment.target_id}' was not found in IKROS state")
    if not assessment.target_type:
        errors.append("target_type is required")
    if not assessment.reason:
        errors.append("reason is required")
    if not assessment.operator:
        errors.append("operator is required")
    if not assessment.references.specification_ids:
        errors.append("at least one specification reference is required")
    if not assessment.evidence:
        errors.append("at least one evidence item is required")
    errors.extend(
        validate_dimensions(assessment.previous_confidence, entity_type=assessment.target_type)
    )
    errors.extend(
        validate_dimensions(assessment.assessed_confidence, entity_type=assessment.target_type)
    )
    for evidence in assessment.evidence:
        errors.extend(validate_evidence(evidence))
    return errors


def validate_history_entry(entry: ConfidenceHistoryEntry) -> list[str]:
    errors: list[str] = []
    if not entry.history_id:
        errors.append("history_id is required")
    if not entry.assessment_id:
        errors.append("assessment_id is required")
    if not entry.target_id:
        errors.append("target_id is required")
    if not entry.timestamp:
        errors.append("timestamp is required")
    if not entry.operator:
        errors.append("operator is required")
    errors.extend(validate_dimensions(entry.previous_confidence, entity_type=entry.target_type))
    errors.extend(validate_dimensions(entry.new_confidence, entity_type=entry.target_type))
    return errors


def validate_audit_entry(entry: ConfidenceAuditEntry) -> list[str]:
    errors: list[str] = []
    if not entry.audit_id:
        errors.append("audit_id is required")
    if not entry.assessment_id:
        errors.append("assessment_id is required")
    if not entry.timestamp:
        errors.append("timestamp is required")
    if not entry.entry_hash:
        errors.append("entry_hash is required")
    errors.extend(validate_dimensions(entry.previous_confidence, entity_type=entry.target_type))
    errors.extend(validate_dimensions(entry.new_confidence, entity_type=entry.target_type))
    return errors


def assert_valid_assessment(
    assessment: ConfidenceAssessment,
    *,
    known_identifiers: set[str],
) -> None:
    errors = validate_assessment(assessment, known_identifiers=known_identifiers)
    if errors:
        raise ConfidenceValidationError("\n".join(errors))


def assert_valid_history(entry: ConfidenceHistoryEntry) -> None:
    errors = validate_history_entry(entry)
    if errors:
        raise ConfidenceValidationError("\n".join(errors))


def assert_valid_audit(entry: ConfidenceAuditEntry) -> None:
    errors = validate_audit_entry(entry)
    if errors:
        raise ConfidenceValidationError("\n".join(errors))


def find_broken_history_chain(entries: Iterable[ConfidenceHistoryEntry]) -> list[str]:
    seen: set[str] = set()
    broken: list[str] = []
    for entry in entries:
        if entry.assessment_id in seen:
            broken.append(entry.history_id)
        seen.add(entry.assessment_id)
    return broken
