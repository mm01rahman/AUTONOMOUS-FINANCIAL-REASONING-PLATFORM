"""Work Package contract loader (WP-IMP-0006, WPS-1.0).

Loads ``05-work-packages/WP-*.yaml`` contracts and validates them against the
authoritative JSON Schema at ``09-validation/schemas/wps-1.0.schema.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from afrp.core.exceptions import ContractReferenceError, ManifestValidationError

WPS_SCHEMA_RELPATH = Path("09-validation") / "schemas" / "wps-1.0.schema.json"
WP_DIR_RELPATH = Path("05-work-packages")


@dataclass(frozen=True)
class WorkPackage:
    """A validated, immutable Work Package contract."""

    work_package_id: str
    capability_id: str
    capability_version: str
    title: str
    status: str
    bounded_files: tuple[str, ...]
    quality_gates: tuple[tuple[str, str, bool], ...]  # (gate, command, required)
    unlocks: tuple[tuple[str, str], ...]  # (capability id, version)
    expected_evidence: tuple[str, ...]
    raw: dict[str, Any]


def _load_schema(repo_root: Path) -> dict[str, Any]:
    schema_path = repo_root / WPS_SCHEMA_RELPATH
    if not schema_path.is_file():
        raise ContractReferenceError(str(schema_path))
    loaded = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ManifestValidationError("WPS schema root must be an object")
    return loaded


def load_work_package(repo_root: Path, wp_id: str) -> WorkPackage:
    """Load and schema-validate the Work Package ``wp_id``.

    Raises:
        ContractReferenceError: contract or schema file missing.
        ManifestValidationError: YAML malformed or schema validation failed.
    """
    contract_path = repo_root / WP_DIR_RELPATH / f"{wp_id}.yaml"
    if not contract_path.is_file():
        raise ContractReferenceError(str(contract_path))
    try:
        raw = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestValidationError(f"YAML parse failure in {wp_id}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestValidationError(f"{wp_id} root must be a mapping")

    schema = _load_schema(repo_root)
    try:
        jsonschema.validate(raw, schema)
    except jsonschema.ValidationError as exc:
        raise ManifestValidationError(f"{wp_id} violates WPS-1.0: {exc.message}") from exc

    gates = tuple(
        (name, str(spec["command"]), bool(spec["required"]))
        for name, spec in raw["quality_gates"].items()
    )
    unlocks = tuple(
        (str(u["id"]), str(u["version"]))
        for u in raw.get("produces", {}).get("unlocks", [])
    )
    return WorkPackage(
        work_package_id=str(raw["work_package_id"]),
        capability_id=str(raw["capability_id"]["id"]),
        capability_version=str(raw["capability_id"]["version"]),
        title=str(raw["title"]),
        status=str(raw["status"]),
        bounded_files=tuple(str(f) for f in raw["scope"]["bounded_files"]),
        quality_gates=gates,
        unlocks=unlocks,
        expected_evidence=tuple(str(e) for e in raw["outputs"]["expected_evidence"]),
        raw=raw,
    )
