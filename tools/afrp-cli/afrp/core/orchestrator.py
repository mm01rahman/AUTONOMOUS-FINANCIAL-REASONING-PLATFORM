"""EOS orchestrator engine (WP-IMP-0008, EOS-003).

Drives a Work Package through the RSM-1.0 lifecycle under EGP-2.0 controls:
baseline verification, contract load, precondition evaluation, gate
execution, boundary audit, and rollback on failure.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from afrp.commands.boot import verify_baseline
from afrp.core.evidence import audit_boundaries, modified_files
from afrp.core.exceptions import AfrpError, InvariantError
from afrp.core.lifecycle import LifecycleMachine, LifecycleState
from afrp.core.registry import CapabilityStatus, load_registry
from afrp.core.workpackage import WorkPackage, load_work_package

LEDGER_RELPATH = Path("00-governance") / "BASELINE_FINGERPRINT.yaml"
REGISTRY_RELPATH = Path("03-engineering") / "CAPABILITY_REGISTRY.yaml"

_TAG_PREDICATE = re.compile(r"^git\.tag\s*==\s*'([^']+)'$")
_FILE_PREDICATE = re.compile(r"^file\.exists\('([^']+)'\)$")
_CAP_PREDICATE = re.compile(r"^capability\.complete\('([^']+)'\)$")


@dataclass(frozen=True)
class PreconditionResult:
    """Outcome of one precondition predicate."""

    predicate: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class GateResult:
    """Outcome of one quality gate execution."""

    gate: str
    command: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class RunReport:
    """Full orchestrator run outcome."""

    work_package_id: str
    final_state: LifecycleState
    transitions: tuple[tuple[str, str], ...]
    preconditions: tuple[PreconditionResult, ...]
    gates: tuple[GateResult, ...]
    boundary_violations: tuple[str, ...]
    halted_reason: str | None


def _git_tag_exists(repo_root: Path, tag: str) -> bool:
    result = subprocess.run(
        ["git", "tag", "--list", tag],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return tag in result.stdout.split()


def evaluate_precondition(repo_root: Path, predicate: str) -> PreconditionResult:
    """Evaluate one WPS-1.0 precondition predicate.

    Raises:
        InvariantError: the predicate grammar is not recognized.
    """
    if match := _TAG_PREDICATE.match(predicate):
        tag = match.group(1)
        ok = _git_tag_exists(repo_root, tag)
        return PreconditionResult(predicate, ok, f"tag {tag} {'found' if ok else 'missing'}")
    if match := _FILE_PREDICATE.match(predicate):
        rel = match.group(1)
        ok = (repo_root / rel).exists()
        return PreconditionResult(predicate, ok, f"{rel} {'exists' if ok else 'missing'}")
    if match := _CAP_PREDICATE.match(predicate):
        cap_id = match.group(1)
        registry = load_registry(repo_root / REGISTRY_RELPATH)
        cap = registry.by_id().get(cap_id)
        ok = cap is not None and cap.status is CapabilityStatus.COMPLETE
        return PreconditionResult(
            predicate, ok, f"capability {cap_id} {'complete' if ok else 'not complete'}"
        )
    raise InvariantError("WPS-1.0", f"unrecognized precondition grammar: {predicate!r}")


def run_gate(repo_root: Path, gate: str, command: str) -> GateResult:
    """Execute one quality gate command via the shell."""
    try:
        proc = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            shell=True,
            check=False,
        )
    except OSError as exc:
        return GateResult(gate, command, False, f"spawn failure: {exc}")
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or [""]
    return GateResult(gate, command, proc.returncode == 0, tail[0])


def rollback_bounded_files(repo_root: Path, bounded: tuple[str, ...], ref: str) -> None:
    """Restore bounded files to ``ref`` (WPS rollback strategy)."""
    tracked = [b for b in bounded if not b.endswith("/")]
    if tracked:
        subprocess.run(
            ["git", "checkout", ref, "--", *tracked],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )


def orchestrate(
    repo_root: Path,
    wp_id: str,
    *,
    dry_run: bool = False,
    skip_gates: bool = False,
    base_ref: str = "HEAD",
) -> RunReport:
    """Drive ``wp_id`` through the RSM-1.0 lifecycle.

    ``dry_run`` evaluates baseline, contract, and preconditions but executes
    no gates and never rolls back. ``skip_gates`` (used when gates already ran
    externally) records gates as skipped-pass.
    """
    machine = LifecycleMachine()
    preconditions: list[PreconditionResult] = []
    gates: list[GateResult] = []
    violations: tuple[str, ...] = ()
    halted_reason: str | None = None
    wp: WorkPackage | None = None

    try:
        verify_baseline(repo_root, repo_root / LEDGER_RELPATH)
        machine.advance(LifecycleState.BASELINE_VERIFIED, "SHA256 ledger PASS")

        wp = load_work_package(repo_root, wp_id)
        machine.advance(LifecycleState.WORK_PACKAGE_LOADED, wp.title)

        for raw in wp.raw.get("preconditions", []):
            pre_outcome = evaluate_precondition(repo_root, str(raw["predicate"]))
            preconditions.append(pre_outcome)
        failed = [p for p in preconditions if not p.passed]
        if failed:
            machine.halt(f"precondition failed: {failed[0].predicate}")
            return _report(wp_id, machine, preconditions, gates, violations,
                           machine.history[-1][1])
        machine.advance(LifecycleState.PRECONDITIONS_VERIFIED,
                        f"{len(preconditions)} predicate(s) PASS")

        machine.advance(LifecycleState.EXECUTION_AUTHORIZED,
                        f"write lock: {len(wp.bounded_files)} bounded file(s)")
        if dry_run:
            machine.halt("dry-run complete (no execution attempted)")
            return _report(wp_id, machine, preconditions, gates, violations,
                           "dry-run complete (no execution attempted)")

        machine.advance(LifecycleState.EXECUTING, "delegated to AEF-02 engineer")
        machine.advance(LifecycleState.VALIDATING, "running quality gates")

        if skip_gates:
            gates.extend(
                GateResult(g, cmd, True, "recorded as externally executed")
                for g, cmd, _req in wp.quality_gates
            )
        else:
            for gate, command, required in wp.quality_gates:
                gate_outcome = run_gate(repo_root, gate, command)
                gates.append(gate_outcome)
                if required and not gate_outcome.passed:
                    rollback_bounded_files(repo_root, wp.bounded_files, base_ref)
                    machine.halt(f"gate {gate} failed; bounded files rolled back")
                    return _report(wp_id, machine, preconditions, gates, violations,
                                   machine.history[-1][1])

        audit = audit_boundaries(wp.bounded_files, modified_files(repo_root, base_ref))
        violations = audit.violations
        if not audit.compliant:
            machine.halt(f"FIT-005 violation: {len(violations)} file(s) out of bounds")
            return _report(wp_id, machine, preconditions, gates, violations,
                           machine.history[-1][1])

        machine.advance(LifecycleState.EVIDENCE_GENERATED, "evidence composition delegated")
        machine.advance(LifecycleState.REVIEW_PENDING, "awaiting ARB disposition")
    except AfrpError as exc:
        if not machine.terminal:
            machine.halt(str(exc))
        halted_reason = str(exc)

    return _report(wp_id, machine, preconditions, gates, violations, halted_reason)


def _report(
    wp_id: str,
    machine: LifecycleMachine,
    preconditions: list[PreconditionResult],
    gates: list[GateResult],
    violations: tuple[str, ...],
    halted_reason: str | None,
) -> RunReport:
    return RunReport(
        work_package_id=wp_id,
        final_state=machine.state,
        transitions=tuple((s.value, note) for s, note in machine.history),
        preconditions=tuple(preconditions),
        gates=tuple(gates),
        boundary_violations=violations,
        halted_reason=halted_reason,
    )
