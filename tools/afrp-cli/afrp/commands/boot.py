"""``afrp boot`` — EGP-2.0 zero-write handshake (WP-IMP-0003, FR-001).

Reads the KERNEL bootloader, ingests the repository manifest, verifies the
SHA256 baseline fingerprint ledger, and emits the ``repository_state``
diagnostic block, terminating in ``BASELINE_VERIFIED``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import click
import yaml
from afrp.core.exceptions import (
    AfrpError,
    BaselineIntegrityError,
    ContractReferenceError,
)
from afrp.core.kernel import KernelDocument, load_kernel
from afrp.core.manifest import RepositoryManifest, load_manifest

_AGENT_IDENTITY = {
    "role": "AEF-02 (Software Engineer)",
    "agent_vendor": "Vendor-Neutral",
    "agent_name": "AFRP Engineering OS",
}


@dataclass(frozen=True)
class BootResult:
    """Outcome of a successful zero-write handshake."""

    manifest: RepositoryManifest
    kernel: KernelDocument
    verified_artifacts: int


def verify_baseline(repo_root: Path, ledger_path: Path) -> int:
    """Verify every ledger entry's SHA256 digest; return the count verified.

    Raises:
        ContractReferenceError: ledger or a listed artifact is missing.
        BaselineIntegrityError: one or more digests mismatch.
    """
    if not ledger_path.is_file():
        raise ContractReferenceError(str(ledger_path))
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    entries = ledger.get("artifacts", []) if isinstance(ledger, dict) else []
    mismatches: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or "path" not in entry or "sha256" not in entry:
            raise BaselineIntegrityError([f"malformed ledger entry: {entry!r}"])
        rel = str(entry["path"])
        expected = str(entry["sha256"])
        target = repo_root / rel
        if not target.is_file():
            raise ContractReferenceError(rel)
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            mismatches.append(rel)
    if mismatches:
        raise BaselineIntegrityError(mismatches)
    return len(entries)


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
