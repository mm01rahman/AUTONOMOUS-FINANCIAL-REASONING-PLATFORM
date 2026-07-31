"""Traceability Verification Matrix parser and FIT-007 analyzer (WP-IMP-0007).

Article IV: every artifact must trace back to a requirement. FIT-007 asserts
100% requirement coverage in ``03-engineering/TRACEABILITY_MATRIX.yaml``.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from afrp.core.exceptions import (
    ContractReferenceError,
    InvariantError,
    ManifestValidationError,
)
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

SUPPORTED_SCHEMA_VERSION = "1.0"


class RequirementStatus(StrEnum):
    """Lifecycle status of a tracked requirement."""

    PLANNED = "planned"
    IMPLEMENTED = "implemented"


class Requirement(BaseModel):
    """One TVM requirement row."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    source: str
    capability: str
    status: RequirementStatus
    artifacts: tuple[str, ...]
    verified_by: tuple[str, ...]

    @property
    def covered(self) -> bool:
        """Covered iff at least one artifact and one verification exist."""
        return bool(self.artifacts) and bool(self.verified_by)


class TraceabilityMatrix(BaseModel):
    """The parsed TVM ledger."""

    model_config = ConfigDict(frozen=True)

    schema_version: str
    matrix_id: str
    requirements: tuple[Requirement, ...]

    @field_validator("schema_version")
    @classmethod
    def _schema_version_supported(cls, value: str) -> str:
        if value != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {value!r}; expected {SUPPORTED_SCHEMA_VERSION!r}"
            )
        return value

    @property
    def covered(self) -> tuple[Requirement, ...]:
        """Requirements satisfying the coverage predicate."""
        return tuple(r for r in self.requirements if r.covered)

    @property
    def coverage_ratio(self) -> float:
        """Fraction of requirements covered (1.0 when the matrix is empty)."""
        if not self.requirements:
            return 1.0
        return len(self.covered) / len(self.requirements)


def load_matrix(path: Path) -> TraceabilityMatrix:
    """Load and validate the TVM at ``path``.

    Raises:
        ContractReferenceError: the matrix file is missing.
        ManifestValidationError: YAML malformed, model invalid, duplicate ids,
            or drift (implemented without artifacts/verification).
    """
    if not path.is_file():
        raise ContractReferenceError(str(path))
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestValidationError(f"YAML parse failure: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestValidationError("matrix root must be a mapping")
    try:
        matrix = TraceabilityMatrix.model_validate(raw)
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc

    seen: set[str] = set()
    for req in matrix.requirements:
        if req.id in seen:
            raise ManifestValidationError(f"duplicate requirement id {req.id!r}")
        seen.add(req.id)
        if req.status is RequirementStatus.IMPLEMENTED and not req.covered:
            raise ManifestValidationError(
                f"requirement {req.id!r} marked implemented without artifacts "
                f"and verification (documentation drift)"
            )
    return matrix


def assert_full_coverage(matrix: TraceabilityMatrix) -> None:
    """FIT-007: raise unless every requirement is covered.

    Raises:
        InvariantError: at least one requirement lacks coverage.
    """
    uncovered = [r.id for r in matrix.requirements if not r.covered]
    if uncovered:
        raise InvariantError(
            "FIT-007",
            f"{len(uncovered)} requirement(s) lack coverage: {', '.join(uncovered)}",
        )
