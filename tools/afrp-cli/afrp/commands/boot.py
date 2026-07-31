"""``afrp boot`` — EGP-2.0 zero-write handshake (WP-IMP-0003, FR-001).

Reads the KERNEL bootloader, ingests the repository manifest, verifies the
SHA256 baseline fingerprint ledger, and emits the ``repository_state``
diagnostic block, terminating in ``BASELINE_VERIFIED``.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

import click
import yaml
from afrp.core.exceptions import (
    AfrpError,
    BaselineIntegrityError,
    ContractReferenceError,
    ManifestValidationError,
)
from afrp.core.kernel import KernelDocument, load_kernel
from afrp.core.manifest import RepositoryManifest, load_manifest

_AGENT_IDENTITY = {
    "role": "AEF-02 (Software Engineer)",
    "agent_vendor": "Vendor-Neutral",
    "agent_name": "AFRP Engineering OS",
}
_LEDGER_SCHEMA_VERSION = "1.0"
_LEDGER_ID = "BASELINE_FINGERPRINT"
_BASELINE_ID = "AFRP-BASELINE-1.0.0"
_HASH_ALGORITHM = "sha256"
_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
_LEDGER_KEYS = frozenset(
    {
        "schema_version",
        "ledger_id",
        "baseline_id",
        "hash_algorithm",
        "generated_at",
        "artifacts",
    }
)
_ARTIFACT_KEYS = frozenset({"path", "sha256"})


@dataclass(frozen=True)
class FingerprintArtifact:
    """One validated genesis-ledger artifact."""

    path: str
    sha256: str


@dataclass(frozen=True)
class FingerprintLedger:
    """Strictly validated genesis fingerprint ledger."""

    schema_version: str
    ledger_id: str
    baseline_id: str
    hash_algorithm: str
    artifacts: tuple[FingerprintArtifact, ...]


@dataclass(frozen=True)
class BootResult:
    """Outcome of a successful zero-write handshake."""

    manifest: RepositoryManifest
    kernel: KernelDocument
    verified_artifacts: int


def _ledger_error(reason: str) -> ManifestValidationError:
    return ManifestValidationError(f"fingerprint ledger invalid: {reason}")


def _safe_artifact_path(repo_root: Path, raw_path: object) -> str:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise _ledger_error("artifact path must be a non-empty string")
    rel = raw_path.strip()
    posix = PurePosixPath(rel)
    windows = PureWindowsPath(rel)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise _ledger_error(f"artifact path must be repository-relative: {rel!r}")
    if ".." in posix.parts or ".." in windows.parts:
        raise _ledger_error(f"artifact path contains traversal: {rel!r}")
    root = repo_root.resolve()
    target = (root / Path(*posix.parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise _ledger_error(f"artifact path escapes repository: {rel!r}") from exc
    return posix.as_posix()


def _load_fingerprint_ledger(repo_root: Path, ledger_path: Path) -> FingerprintLedger:
    try:
        loaded = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise _ledger_error(f"YAML parse failure: {exc}") from exc
    if not isinstance(loaded, dict):
        raise _ledger_error("root must be a mapping")
    if not all(isinstance(key, str) for key in loaded):
        raise _ledger_error("all top-level keys must be strings")
    unknown_keys = set(loaded) - _LEDGER_KEYS
    missing_keys = _LEDGER_KEYS - set(loaded)
    if unknown_keys or missing_keys:
        detail: list[str] = []
        if missing_keys:
            detail.append(f"missing keys: {', '.join(sorted(missing_keys))}")
        if unknown_keys:
            detail.append(f"unknown keys: {', '.join(sorted(unknown_keys))}")
        raise _ledger_error("; ".join(detail))

    identities = {
        "schema_version": _LEDGER_SCHEMA_VERSION,
        "ledger_id": _LEDGER_ID,
        "baseline_id": _BASELINE_ID,
        "hash_algorithm": _HASH_ALGORITHM,
    }
    for field, expected in identities.items():
        if loaded.get(field) != expected:
            raise _ledger_error(f"{field} must be {expected!r}")
    generated_at = loaded["generated_at"]
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise _ledger_error("generated_at must be a non-empty ISO datetime string")
    try:
        parsed_generated_at = datetime.fromisoformat(
            generated_at.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise _ledger_error("generated_at must be an ISO datetime string") from exc
    if parsed_generated_at.tzinfo is None:
        raise _ledger_error("generated_at must include a timezone")

    raw_artifacts = loaded.get("artifacts")
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise _ledger_error("artifacts must be a non-empty list")
    artifacts: list[FingerprintArtifact] = []
    seen: set[str] = set()
    for index, entry in enumerate(raw_artifacts):
        if not isinstance(entry, dict):
            raise _ledger_error(f"artifact {index} must be a mapping")
        if not all(isinstance(key, str) for key in entry):
            raise _ledger_error(f"artifact {index} keys must be strings")
        if set(entry) != _ARTIFACT_KEYS:
            unknown = set(entry) - _ARTIFACT_KEYS
            missing = _ARTIFACT_KEYS - set(entry)
            detail = []
            if missing:
                detail.append(f"missing keys: {', '.join(sorted(missing))}")
            if unknown:
                detail.append(f"unknown keys: {', '.join(sorted(unknown))}")
            raise _ledger_error(f"artifact {index} {'; '.join(detail)}")
        rel = _safe_artifact_path(repo_root, entry.get("path"))
        if rel in seen:
            raise _ledger_error(f"duplicate artifact path: {rel}")
        seen.add(rel)
        digest = entry.get("sha256")
        if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
            raise _ledger_error(f"artifact {rel!r} has invalid SHA256")
        artifacts.append(FingerprintArtifact(rel, digest.lower()))
    return FingerprintLedger(
        schema_version=_LEDGER_SCHEMA_VERSION,
        ledger_id=_LEDGER_ID,
        baseline_id=_BASELINE_ID,
        hash_algorithm=_HASH_ALGORITHM,
        artifacts=tuple(artifacts),
    )


def verify_baseline(repo_root: Path, ledger_path: Path) -> int:
    """Verify every ledger entry's SHA256 digest; return the count verified.

    Raises:
        ContractReferenceError: ledger or a listed artifact is missing.
        BaselineIntegrityError: one or more digests mismatch.
    """
    if not ledger_path.is_file():
        raise ContractReferenceError(str(ledger_path))
    root = repo_root.resolve()
    ledger = _load_fingerprint_ledger(root, ledger_path)
    mismatches: list[str] = []
    for entry in ledger.artifacts:
        target = root / entry.path
        if not target.is_file():
            raise ContractReferenceError(entry.path)
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != entry.sha256:
            mismatches.append(entry.path)
    if mismatches:
        raise BaselineIntegrityError(mismatches)
    return len(ledger.artifacts)


def run_boot(repo_root: Path) -> BootResult:
    """Execute the EGP-2.0 handshake against ``repo_root``."""
    manifest = load_manifest(repo_root / "REPOSITORY_MANIFEST.yaml")
    kernel_rel = manifest.resolve_document("KERNEL.md")
    kernel = load_kernel(repo_root / kernel_rel)
    ledger_rel = manifest.integrity.fingerprint_ledger
    verified = verify_baseline(repo_root, repo_root / ledger_rel)
    return BootResult(manifest=manifest, kernel=kernel, verified_artifacts=verified)


def render_repository_state(result: BootResult) -> str:
    """Render the EGP-2.0 ``repository_state`` diagnostic block as YAML."""
    block = {
        "repository_state": {
            "protocol_version": result.manifest.baseline.governance_protocol,
            "lifecycle_state": "BASELINE_VERIFIED",
            "verification": {
                "baseline_verified": True,
                "governance_verified": True,
                "manifest_verified": True,
            },
            "authorization": {
                "execution_authorized": False,
                "reason": "Work package contract not loaded. Write access locked.",
            },
            "agent_identity": dict(_AGENT_IDENTITY),
            "integrity": {
                "fingerprint_ledger": result.manifest.integrity.fingerprint_ledger,
                "status": "PASS",
                "artifacts_verified": result.verified_artifacts,
            },
            "kernel": {
                "title": result.kernel.title,
                "word_count": result.kernel.word_count,
                "budget": 400,
            },
            "termination": {
                "state": "BASELINE_VERIFIED",
                "reason": "Zero-write environment handshake complete. Awaiting WP assignment.",
                "next_action": "LOAD_WORK_PACKAGE",
            },
        }
    }
    return yaml.safe_dump(block, sort_keys=False, default_flow_style=False)


@click.command(name="boot")
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Repository root containing REPOSITORY_MANIFEST.yaml.",
)
def boot_command(repo_root: Path) -> None:
    """Perform the EGP-2.0 zero-write handshake and emit repository_state."""
    try:
        result = run_boot(repo_root.resolve())
    except AfrpError as exc:
        click.echo(f"HALTED: {exc}", err=True)
        raise SystemExit(exc.exit_code) from exc
    click.echo(render_repository_state(result), nl=False)
