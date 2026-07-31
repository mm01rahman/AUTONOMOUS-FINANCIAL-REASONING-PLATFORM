"""Repository manifest parser (WP-IMP-0003, FR-001).

Parses ``REPOSITORY_MANIFEST.yaml`` into the strongly typed
:class:`RepositoryManifest` Pydantic model and enforces
``schema_version == "1.0"``.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from afrp.core.exceptions import ContractReferenceError, ManifestValidationError
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

SUPPORTED_SCHEMA_VERSION = "1.0"


class BaselineInfo(BaseModel):
    """Baseline identity block of the repository manifest."""

    model_config = ConfigDict(frozen=True)

    suite_id: str
    baseline_tag: str
    genesis_commit_tag: str
    governance_protocol: str
    repository_os: str
    effective_date: str
    authority: str


class ProductEntry(BaseModel):
    """One of the three AFRP products (ARCH-002)."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    paths: tuple[str, ...]


class TopologyEntry(BaseModel):
    """A monorepo top-level directory and its declared purpose (IMP-001)."""

    model_config = ConfigDict(frozen=True)

    path: str
    purpose: str


class IntegrityInfo(BaseModel):
    """Integrity ledger binding (EGP-2.0)."""

    model_config = ConfigDict(frozen=True)

    fingerprint_ledger: str
    hash_algorithm: str


class RepositoryManifest(BaseModel):
    """Top-level repository topology manifest (`REPOSITORY_MANIFEST.yaml`)."""

    model_config = ConfigDict(frozen=True)

    schema_version: str
    manifest_id: str
    baseline: BaselineInfo
    products: tuple[ProductEntry, ...]
    topology: tuple[TopologyEntry, ...]
    document_index: dict[str, str]
    integrity: IntegrityInfo

    @field_validator("schema_version")
    @classmethod
    def _schema_version_supported(cls, value: str) -> str:
        if value != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {value!r}; expected {SUPPORTED_SCHEMA_VERSION!r}"
            )
        return value

    def resolve_document(self, name: str) -> str:
        """Resolve a bare governed document name to its canonical repository path."""
        try:
            return self.document_index[name]
        except KeyError as exc:
            raise ManifestValidationError(f"document {name!r} not in document_index") from exc


def load_manifest(path: Path) -> RepositoryManifest:
    """Load and validate the repository manifest at ``path``.

    Raises:
        ContractReferenceError: the manifest file does not exist.
        ManifestValidationError: YAML is malformed or the model rejects it.
    """
    if not path.is_file():
        raise ContractReferenceError(str(path))
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestValidationError(f"YAML parse failure: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestValidationError("manifest root must be a mapping")
    try:
        return RepositoryManifest.model_validate(raw)
    except ValidationError as exc:
        raise ManifestValidationError(str(exc)) from exc
