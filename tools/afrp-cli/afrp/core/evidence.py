"""Boundary audit and ERS-1.0 evidence engine (WP-IMP-0006, FIT-005).

* :func:`audit_boundaries` — FIT-005 comparison of modified files against a
  Work Package's ``bounded_files``.
* :func:`modified_files` — modified + untracked files from git.
* :func:`write_evidence` — schema-validated ERS-1.0 record emission.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any

import jsonschema
import yaml
from afrp.core.exceptions import ContractReferenceError, ManifestValidationError

if TYPE_CHECKING:
    from afrp.core.workpackage import WorkPackage

ERS_SCHEMA_RELPATH = Path("09-validation") / "schemas" / "ers-1.0.schema.json"


@dataclass(frozen=True)
class BoundaryAudit:
    """Outcome of a FIT-005 boundary confinement verification."""

    bounded_files: tuple[str, ...]
    files_modified: tuple[str, ...]
    violations: tuple[str, ...]

    @property
    def compliant(self) -> bool:
        """True when every modified file lies inside the declared bounds."""
        return not self.violations


def modified_files(repo_root: Path, base_ref: str = "HEAD") -> tuple[str, ...]:
    """Modified (vs ``base_ref``) plus untracked files, as posix relpaths.

    Raises:
        ManifestValidationError: git invocation failed.
    """
    try:
        diff = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise ManifestValidationError(f"git query failed: {exc}") from exc
    names = {
        line.strip()
        for out in (diff.stdout, untracked.stdout)
        for line in out.splitlines()
        if line.strip()
    }
    return tuple(sorted(names))


def audit_boundaries(
    bounded_files: tuple[str, ...],
    changed: tuple[str, ...],
) -> BoundaryAudit:
    """FIT-005: every changed file must be one of the declared bounded files.

    A bounded entry ending in ``/`` grants the whole subtree (used by WP
    evidence directories).
    """
    exact = {b for b in bounded_files if not b.endswith("/")}
    prefixes = tuple(b for b in bounded_files if b.endswith("/"))
    violations = tuple(
        f
        for f in changed
        if f not in exact and not any(f.startswith(p) for p in prefixes)
    )
    return BoundaryAudit(
        bounded_files=bounded_files,
        files_modified=changed,
        violations=violations,
    )


def resolve_evidence_target(
    repo_root: Path,
    bounded_files: tuple[str, ...],
    relative: str,
    *,
    allow_existing_unbounded: bool = False,
) -> Path:
    """Resolve a bounded evidence path and reject traversal or repository escape."""
    posix = PurePosixPath(relative)
    windows = PureWindowsPath(relative)
    if (
        not relative.strip()
        or posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or ".." in posix.parts
        or ".." in windows.parts
    ):
        raise ManifestValidationError(
            f"unsafe expected evidence path: {relative!r}"
        )
    normalized = posix.as_posix()
    root = repo_root.resolve()
    target = (root / Path(*posix.parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ManifestValidationError(
            f"expected evidence path escapes repository: {relative!r}"
        ) from exc
    resolved_relative = target.relative_to(root).as_posix()
    lexical_bounded = audit_boundaries(bounded_files, (normalized,)).compliant
    resolved_bounded = audit_boundaries(
        bounded_files, (resolved_relative,)
    ).compliant
    if not (lexical_bounded and resolved_bounded) and not (
        allow_existing_unbounded and target.is_file()
    ):
        raise ManifestValidationError(
            "evidence target is outside bounded_files "
            f"(possible symlink redirect): {normalized} -> {resolved_relative}"
        )
    return target


def load_ers_schema(repo_root: Path) -> dict[str, Any]:
    """Load the ERS-1.0 JSON Schema."""
    schema_path = repo_root / ERS_SCHEMA_RELPATH
    if not schema_path.is_file():
        raise ContractReferenceError(str(schema_path))
    loaded = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ManifestValidationError("ERS schema root must be an object")
    return loaded


def validate_evidence(record: dict[str, Any], repo_root: Path) -> None:
    """Validate an ERS record; raise on violation.

    Raises:
        ManifestValidationError: the record violates ERS-1.0.
    """
    try:
        jsonschema.validate(record, load_ers_schema(repo_root))
    except jsonschema.ValidationError as exc:
        raise ManifestValidationError(f"evidence violates ERS-1.0: {exc.message}") from exc


def load_evidence(repo_root: Path, target: Path) -> dict[str, Any]:
    """Load and validate one existing ERS record."""
    if not target.is_file():
        raise ContractReferenceError(str(target))
    try:
        loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ManifestValidationError(f"evidence YAML parse failure: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ManifestValidationError("evidence root must be a mapping")
    validate_evidence(loaded, repo_root)
    return loaded


def validate_existing_evidence(
    record: dict[str, Any],
    wp: WorkPackage,
    target: Path,
    audit: BoundaryAudit | None = None,
) -> None:
    """Verify that an existing ERS record belongs to its requested contract."""
    expected_identity = {
        "evidence_id": target.stem,
        "work_package_id": wp.work_package_id,
    }
    for field, expected in expected_identity.items():
        if record.get(field) != expected:
            raise ManifestValidationError(
                f"existing evidence {field} does not match {expected!r}"
            )
    if record.get("capability") != {
        "id": wp.capability_id,
        "version": wp.capability_version,
    }:
        raise ManifestValidationError("existing evidence capability does not match WPS")
    if audit is None or wp.status == "Completed":
        return
    boundary = record.get("boundary_compliance")
    if not isinstance(boundary, dict):
        raise ManifestValidationError("existing evidence has no boundary mapping")
    current_files = [
        path for path in audit.files_modified if path not in wp.expected_evidence
    ]
    expected_boundary = {
        "bounded_files": list(audit.bounded_files),
        "files_modified": current_files,
        "violations": list(audit.violations),
        "compliant": audit.compliant,
    }
    if any(boundary.get(key) != value for key, value in expected_boundary.items()):
        raise ManifestValidationError(
            "existing evidence boundary data is stale for the current change set"
        )


def compose_boundary_evidence(
    wp: WorkPackage,
    audit: BoundaryAudit,
    gates: Sequence[Mapping[str, object]],
    *,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    final_state: str = "REVIEW_PENDING",
    preconditions: Sequence[Mapping[str, object]] = (),
) -> dict[str, Any]:
    """Compose truthful internal ERS data for a boundary-controlled run."""
    started = started_at or datetime.now(UTC)
    finished = finished_at or datetime.now(UTC)
    gate_records = [dict(gate) for gate in gates]
    supplied_gates = {str(gate.get("gate")) for gate in gate_records}
    gate_records.extend(
        [
            {
                "gate": name,
                "command": command,
                "result": "SKIPPED",
                "detail": "gate result was not supplied",
            }
            for name, command, _required in wp.quality_gates
            if name not in supplied_gates
        ]
    )
    if not wp.expected_evidence:
        raise ManifestValidationError(
            f"{wp.work_package_id} declares no expected evidence path"
        )
    target = Path(wp.expected_evidence[0])
    changed_sources = [
        path for path in audit.files_modified if path not in wp.expected_evidence
    ]
    return {
        "schema_version": "ERS-1.0",
        "evidence_id": target.stem,
        "work_package_id": wp.work_package_id,
        "capability": {"id": wp.capability_id, "version": wp.capability_version},
        "agent_identity": {
            "role": "AEF-02 (Software Engineer)",
            "agent_vendor": "GitHub",
            "agent_name": "Copilot CLI",
        },
        "lifecycle": {
            "protocol_version": "EGP-2.0",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "final_state": final_state,
        },
        "preconditions": [dict(precondition) for precondition in preconditions],
        "boundary_compliance": {
            "bounded_files": list(audit.bounded_files),
            "files_modified": list(audit.files_modified),
            "violations": list(audit.violations),
            "compliant": audit.compliant,
        },
        "quality_gates": gate_records,
        "artifacts": {"source_files": changed_sources},
        "unlocked_capabilities": [],
        "verdict": {
            "all_gates_passed": bool(gate_records)
            and all(gate.get("result") == "PASS" for gate in gate_records),
            "boundary_compliant": audit.compliant,
            "review_status": "PENDING_ARB",
        },
    }


def write_evidence(record: dict[str, Any], repo_root: Path, target: Path) -> Path:
    """Atomically publish a new ERS record, refusing every overwrite."""
    validate_evidence(record, repo_root)
    payload = yaml.safe_dump(
        record, sort_keys=False, default_flow_style=False
    ).encode("utf-8")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ManifestValidationError(f"evidence directory creation failed: {exc}") from exc
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise ManifestValidationError(
                f"evidence already exists and will not be overwritten: {target}"
            ) from exc
        except OSError as exc:
            raise ManifestValidationError(f"evidence publication failed: {exc}") from exc
    except OSError as exc:
        raise ManifestValidationError(f"evidence staging failed: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    return target
