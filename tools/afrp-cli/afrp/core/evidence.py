"""Boundary audit and ERS-1.0 evidence engine (WP-IMP-0006, FIT-005).

* :func:`audit_boundaries` — FIT-005 comparison of modified files against a
  Work Package's ``bounded_files``.
* :func:`modified_files` — modified + untracked files from git.
* :func:`write_evidence` — schema-validated ERS-1.0 record emission.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from afrp.core.exceptions import ContractReferenceError, ManifestValidationError

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


def write_evidence(record: dict[str, Any], repo_root: Path, target: Path) -> Path:
    """Validate then write an ERS-1.0 record as YAML; refuse invalid records."""
    validate_evidence(record, repo_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(record, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
        newline="\n",
    )
    return target
