"""EOS orchestrator engine (WP-IMP-0008, EOS-003)."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

from afrp.commands.boot import verify_baseline
from afrp.core.evidence import (
    audit_boundaries,
    compose_boundary_evidence,
    is_tooling_artifact,
    load_evidence,
    resolve_evidence_target,
    validate_existing_evidence,
    write_evidence,
)
from afrp.core.exceptions import AfrpError, InvariantError, ManifestValidationError
from afrp.core.lifecycle import LifecycleMachine, LifecycleState
from afrp.core.registry import CapabilityStatus, load_registry
from afrp.core.workpackage import WorkPackage, load_work_package

LEDGER_RELPATH = Path("00-governance") / "BASELINE_FINGERPRINT.yaml"
REGISTRY_RELPATH = Path("03-engineering") / "CAPABILITY_REGISTRY.yaml"
_LOCK_NAME = "afrp-orchestrator.lock"
_OUTPUT_LIMIT = 4000

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
    duration_seconds: float = 0.0


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


@dataclass(frozen=True)
class _FileState:
    contents: bytes
    mode: int
    symlink_target: str | None


@dataclass(frozen=True)
class _WorkspaceSnapshot:
    files: dict[str, _FileState | None]

    def changed(self, current: _WorkspaceSnapshot) -> tuple[str, ...]:
        names = set(self.files) | set(current.files)
        return tuple(
            sorted(name for name in names if self.files.get(name) != current.files.get(name))
        )


@dataclass(frozen=True)
class _GitControlSnapshot:
    roots: tuple[Path, ...]
    files: dict[Path, _FileState]
    index_path: Path
    index_state: bytes
    head: str
    symbolic_head: str
    refs: bytes
    status: bytes


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
    """Evaluate one WPS-1.0 precondition predicate."""
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


def _command_argv(command: str | Sequence[str]) -> list[str]:
    if isinstance(command, str):
        try:
            argv = shlex.split(command, posix=True)
        except ValueError as exc:
            raise InvariantError("EGP-2.0", f"invalid command quoting: {exc}") from exc
    elif isinstance(command, Sequence):
        argv = list(command)
        if not all(isinstance(argument, str) for argument in argv):
            raise InvariantError("EGP-2.0", "command argv must contain only strings")
    else:
        raise InvariantError("EGP-2.0", "command must be a string or argv list")
    if not argv or not argv[0]:
        raise InvariantError("EGP-2.0", "command must not be empty")
    return argv


def _bounded_output(stdout: str, stderr: str) -> str:
    combined = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    if not combined:
        return "no output"
    return combined[-_OUTPUT_LIMIT:]


def _execute_command(
    repo_root: Path, command: str | Sequence[str]
) -> tuple[bool, str, float]:
    argv = _command_argv(command)
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=repo_root,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
    except OSError as exc:
        elapsed = time.monotonic() - started
        return False, f"spawn failure: {exc}", elapsed
    elapsed = time.monotonic() - started
    return proc.returncode == 0, _bounded_output(proc.stdout, proc.stderr), elapsed


def run_gate(repo_root: Path, gate: str, command: str) -> GateResult:
    """Execute one quality gate as an argv vector, never through a shell."""
    try:
        passed, detail, elapsed = _execute_command(repo_root, command)
    except InvariantError as exc:
        return GateResult(gate, command, False, str(exc))
    return GateResult(gate, command, passed, detail, elapsed)


def _git_file_names(repo_root: Path) -> set[str]:
    names: set[str] = set()
    for arguments in (
        ["git", "ls-files", "-z"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
    ):
        try:
            result = subprocess.run(
                arguments,
                cwd=repo_root,
                capture_output=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ManifestValidationError(f"git workspace query failed: {exc}") from exc
        for name in result.stdout.decode(
            "utf-8", errors="surrogateescape"
        ).split("\0"):
            if name:
                names.add(name)
    return names


def _read_file_state(path: Path) -> _FileState | None:
    if path.is_symlink():
        return _FileState(b"", stat.S_IMODE(path.lstat().st_mode), os.readlink(path))
    if not path.is_file():
        return None
    return _FileState(path.read_bytes(), stat.S_IMODE(path.stat().st_mode), None)


def _snapshot_workspace(repo_root: Path) -> _WorkspaceSnapshot:
    return _WorkspaceSnapshot(
        {name: _read_file_state(repo_root / name) for name in _git_file_names(repo_root)}
    )


def _git_output(repo_root: Path, arguments: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ManifestValidationError(
            f"git control query failed ({' '.join(arguments)}): {exc}"
        ) from exc
    return result.stdout


def _git_optional_output(repo_root: Path, arguments: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise ManifestValidationError(
            f"git control query failed ({' '.join(arguments)}): {exc}"
        ) from exc
    if result.returncode not in (0, 1):
        raise ManifestValidationError(
            f"git control query failed ({' '.join(arguments)}): "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def _git_path(repo_root: Path, name: str) -> Path:
    raw = _git_output(repo_root, ["rev-parse", "--git-path", name]).decode(
        "utf-8", errors="strict"
    ).strip()
    if not raw:
        raise ManifestValidationError(f"git returned an empty path for {name}")
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _metadata_files(roots: Sequence[Path]) -> dict[Path, _FileState]:
    files: dict[Path, _FileState] = {}
    for root in roots:
        if root.is_symlink() or root.is_file():
            state = _read_file_state(root)
            if state is not None:
                files[root] = state
        elif root.is_dir():
            for path in root.rglob("*"):
                if path.is_symlink() or path.is_file():
                    state = _read_file_state(path)
                    if state is not None:
                        files[path] = state
    return files


def _snapshot_git_control(repo_root: Path) -> _GitControlSnapshot:
    index_path = _git_path(repo_root, "index")
    roots = tuple(
        dict.fromkeys(
            _git_path(repo_root, name)
            for name in (
                "HEAD",
                "index",
                "config",
                "config.worktree",
                "packed-refs",
                "refs",
                "logs/refs",
                "logs/HEAD",
                "hooks",
                "ORIG_HEAD",
                "MERGE_HEAD",
                "CHERRY_PICK_HEAD",
                "REVERT_HEAD",
            )
        )
    )
    head = _git_output(repo_root, ["rev-parse", "HEAD"]).decode().strip()
    symbolic_head = _git_optional_output(
        repo_root, ["symbolic-ref", "-q", "HEAD"]
    ).decode().strip()
    refs = _git_output(
        repo_root,
        ["for-each-ref", "--format=%(refname)%00%(objectname)%00"],
    )
    index_state = _git_output(repo_root, ["ls-files", "--stage", "-z"])
    status = _git_output(
        repo_root,
        [
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
        ],
    )
    return _GitControlSnapshot(
        roots=roots,
        files=_metadata_files(roots),
        index_path=index_path,
        index_state=index_state,
        head=head,
        symbolic_head=symbolic_head,
        refs=refs,
        status=status,
    )


def _git_control_changes(
    repo_root: Path, snapshot: _GitControlSnapshot
) -> tuple[str, ...]:
    current = _snapshot_git_control(repo_root)
    changed: list[str] = []
    if current.head != snapshot.head:
        changed.append("HEAD")
    if current.symbolic_head != snapshot.symbolic_head:
        changed.append("symbolic HEAD")
    if current.refs != snapshot.refs:
        changed.append("refs")
    if current.index_state != snapshot.index_state:
        changed.append("index")
    current_metadata = {
        path: state
        for path, state in current.files.items()
        if path != current.index_path
    }
    original_metadata = {
        path: state
        for path, state in snapshot.files.items()
        if path != snapshot.index_path
    }
    if current_metadata != original_metadata:
        changed.append("config/hooks/ref metadata")
    return tuple(changed)


def _restore_git_control(
    repo_root: Path, snapshot: _GitControlSnapshot
) -> None:
    current = _metadata_files(snapshot.roots)
    for path in sorted(
        set(current) - set(snapshot.files),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        _remove_path(path)
    for path, original in snapshot.files.items():
        if _read_file_state(path) == original:
            continue
        if path.exists() or path.is_symlink():
            _remove_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if original.symlink_target is not None:
            path.symlink_to(original.symlink_target)
        else:
            path.write_bytes(original.contents)
            path.chmod(original.mode)
    for root in sorted(snapshot.roots, key=lambda item: len(item.parts), reverse=True):
        if root.is_dir():
            for directory in sorted(
                (path for path in root.rglob("*") if path.is_dir()),
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                try:
                    directory.rmdir()
                except OSError:
                    pass


def _verify_restored_state(
    repo_root: Path,
    workspace: _WorkspaceSnapshot,
    git_control: _GitControlSnapshot,
) -> None:
    current_workspace = _snapshot_workspace(repo_root)
    workspace_changes = workspace.changed(current_workspace)
    current_git = _snapshot_git_control(repo_root)
    git_changes: list[str] = []
    if current_git.head != git_control.head:
        git_changes.append("HEAD")
    if current_git.symbolic_head != git_control.symbolic_head:
        git_changes.append("symbolic HEAD")
    if current_git.refs != git_control.refs:
        git_changes.append("refs")
    if current_git.index_state != git_control.index_state:
        git_changes.append("index")
    current_metadata = {
        path: state
        for path, state in current_git.files.items()
        if path != current_git.index_path
    }
    original_metadata = {
        path: state
        for path, state in git_control.files.items()
        if path != git_control.index_path
    }
    if current_metadata != original_metadata:
        git_changes.append("config/hooks/ref metadata")
    if current_git.status != git_control.status:
        git_changes.append("index/worktree status")
    if workspace_changes or git_changes:
        detail = [*workspace_changes, *git_changes]
        raise InvariantError(
            "EGP-2.0", f"rollback verification failed: {', '.join(detail)}"
        )


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _restore_workspace(repo_root: Path, snapshot: _WorkspaceSnapshot) -> None:
    current = _snapshot_workspace(repo_root)
    changed_names = set(snapshot.changed(current))
    new_names = changed_names - set(snapshot.files)
    parent_candidates: set[Path] = set()
    for name in sorted(new_names, key=lambda item: len(Path(item).parts), reverse=True):
        target = repo_root / name
        parent_candidates.add(target.parent)
        _remove_path(target)

    for name in changed_names & set(snapshot.files):
        original = snapshot.files[name]
        target = repo_root / name
        if original is None:
            _remove_path(target)
            continue
        if target.exists() or target.is_symlink():
            _remove_path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        if original.symlink_target is not None:
            target.symlink_to(original.symlink_target)
        else:
            target.write_bytes(original.contents)
            target.chmod(original.mode)

    for parent in sorted(parent_candidates, key=lambda item: len(item.parts), reverse=True):
        current_parent = parent
        while current_parent != repo_root:
            try:
                current_parent.rmdir()
            except OSError:
                break
            current_parent = current_parent.parent

    after = _snapshot_workspace(repo_root)
    remaining = snapshot.changed(after)
    if remaining:
        raise InvariantError(
            "EGP-2.0", f"rollback verification failed: {', '.join(remaining)}"
        )


def rollback_bounded_files(repo_root: Path, bounded: tuple[str, ...], ref: str) -> None:
    """Compatibility helper restoring tracked bounded paths without a hard reset."""
    tracked = [path for path in bounded if not path.endswith("/")]
    if not tracked:
        return
    result = subprocess.run(
        ["git", "checkout", ref, "--", *tracked],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise InvariantError("EGP-2.0", f"bounded rollback failed: {result.stderr.strip()}")


@contextmanager
def _workspace_lock(repo_root: Path) -> Iterator[None]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ManifestValidationError(f"cannot resolve workspace lock path: {exc}") from exc
    raw_common_dir = result.stdout.strip()
    if not raw_common_dir:
        raise ManifestValidationError("git returned an empty workspace lock path")
    candidate = Path(raw_common_dir)
    common_dir = candidate if candidate.is_absolute() else repo_root / candidate
    target = common_dir.resolve() / _LOCK_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise InvariantError("EGP-2.0", f"workspace lock is already held: {target}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(f"pid={os.getpid()}\n")
            stream.flush()
            os.fsync(stream.fileno())
        yield
    finally:
        target.unlink(missing_ok=True)


def _safe_evidence_target(repo_root: Path, wp: WorkPackage) -> tuple[str, Path]:
    if not wp.expected_evidence:
        raise ManifestValidationError(f"{wp.work_package_id} has no expected evidence path")
    relative = wp.expected_evidence[0]
    target = resolve_evidence_target(
        repo_root,
        wp.bounded_files,
        relative,
        allow_existing_unbounded=wp.status == "Completed",
    )
    return relative, target


def _validate_expected_outputs(
    repo_root: Path, wp: WorkPackage, changed: tuple[str, ...]
) -> None:
    raw_outputs = wp.raw.get("outputs", {}).get("expected_source_files", [])
    if not isinstance(raw_outputs, list) or not raw_outputs:
        raise InvariantError(
            "WPS-1.0", "outputs.expected_source_files must be non-empty for execution"
        )
    changed_set = set(changed)
    missing: list[str] = []
    unchanged: list[str] = []
    unsafe: list[str] = []
    for raw in raw_outputs:
        if not isinstance(raw, str) or not raw.strip():
            unsafe.append(repr(raw))
            continue
        relative = raw.strip()
        posix = PurePosixPath(relative)
        windows = PureWindowsPath(relative)
        if (
            posix.is_absolute()
            or windows.is_absolute()
            or windows.drive
            or ".." in posix.parts
            or ".." in windows.parts
        ):
            unsafe.append(relative)
            continue
        normalized = posix.as_posix()
        target = (repo_root / Path(*posix.parts)).resolve()
        try:
            target.relative_to(repo_root)
        except ValueError:
            unsafe.append(relative)
            continue
        if not audit_boundaries(wp.bounded_files, (normalized,)).compliant:
            unsafe.append(relative)
        elif not target.is_file():
            missing.append(normalized)
        elif normalized not in changed_set:
            unchanged.append(normalized)
    failures: list[str] = []
    if unsafe:
        failures.append(f"unsafe/out-of-bounds: {', '.join(unsafe)}")
    if missing:
        failures.append(f"missing: {', '.join(missing)}")
    if unchanged:
        failures.append(f"not changed by task: {', '.join(unchanged)}")
    if failures:
        raise InvariantError(
            "WPS-1.0",
            "expected source output validation failed (" + "; ".join(failures) + ")",
        )


def _gate_evidence(gates: Sequence[GateResult]) -> list[dict[str, object]]:
    return [
        {
            "gate": gate.gate,
            "command": gate.command,
            "result": "PASS" if gate.passed else "FAIL",
            "detail": (
                f"{gate.detail} (duration={gate.duration_seconds:.3f}s)"
            )[-_OUTPUT_LIMIT:],
        }
        for gate in gates
    ]


def _precondition_evidence(
    preconditions: Sequence[PreconditionResult],
) -> list[dict[str, object]]:
    return [
        {
            "predicate": precondition.predicate,
            "result": "PASS" if precondition.passed else "FAIL",
        }
        for precondition in preconditions
    ]


def _halt_with_evidence(
    machine: LifecycleMachine,
    repo_root: Path,
    wp: WorkPackage,
    evidence_target: Path,
    snapshot: _WorkspaceSnapshot,
    git_control: _GitControlSnapshot,
    preconditions: Sequence[PreconditionResult],
    gates: Sequence[GateResult],
    started_at: datetime,
    reason: str,
) -> tuple[str, tuple[str, ...]]:
    attempted = snapshot.changed(_snapshot_workspace(repo_root))
    audit = audit_boundaries(wp.bounded_files, attempted)
    _restore_git_control(repo_root, git_control)
    _restore_workspace(repo_root, snapshot)
    _verify_restored_state(repo_root, snapshot, git_control)
    record = compose_boundary_evidence(
        wp,
        audit,
        _gate_evidence(gates),
        started_at=started_at,
        finished_at=datetime.now(UTC),
        final_state="HALTED",
        preconditions=_precondition_evidence(preconditions),
    )
    write_evidence(record, repo_root, evidence_target)
    full_reason = (
        f"{reason}; task-introduced changes rolled back and verified; "
        f"HALTED evidence emitted to {evidence_target.relative_to(repo_root)}"
    )
    machine.halt(full_reason)
    return full_reason, audit.violations


def orchestrate(
    repo_root: Path,
    wp_id: str,
    *,
    dry_run: bool = False,
    skip_gates: bool = False,
    base_ref: str = "HEAD",
) -> RunReport:
    """Drive ``wp_id`` through RSM-1.0 with locked execution and precise rollback."""
    del base_ref  # retained for public API compatibility
    root = repo_root.resolve()
    machine = LifecycleMachine()
    preconditions: list[PreconditionResult] = []
    gates: list[GateResult] = []
    violations: tuple[str, ...] = ()
    halted_reason: str | None = None
    snapshot: _WorkspaceSnapshot | None = None
    git_control: _GitControlSnapshot | None = None

    if skip_gates:
        reason = "skip_gates is prohibited; required gates must execute"
        machine.halt(reason)
        return _report(wp_id, machine, preconditions, gates, violations, reason)

    try:
        verify_baseline(root, root / LEDGER_RELPATH)
        machine.advance(LifecycleState.BASELINE_VERIFIED, "SHA256 ledger PASS")
        wp = load_work_package(root, wp_id)
        machine.advance(LifecycleState.WORK_PACKAGE_LOADED, wp.title)

        for raw in wp.raw.get("preconditions", []):
            outcome = evaluate_precondition(root, str(raw["predicate"]))
            preconditions.append(outcome)
        failed = [result for result in preconditions if not result.passed]
        if failed:
            reason = f"precondition failed: {failed[0].predicate}"
            machine.halt(reason)
            return _report(wp_id, machine, preconditions, gates, violations, reason)
        machine.advance(
            LifecycleState.PRECONDITIONS_VERIFIED,
            f"{len(preconditions)} predicate(s) PASS",
        )
        if dry_run:
            machine.advance(
                LifecycleState.EXECUTION_AUTHORIZED,
                f"dry-run authorization: {len(wp.bounded_files)} bounded file(s)",
            )
            reason = "dry-run complete (no execution attempted)"
            machine.halt(reason)
            return _report(wp_id, machine, preconditions, gates, violations, reason)

        with _workspace_lock(root):
            machine.advance(
                LifecycleState.EXECUTION_AUTHORIZED,
                f"exclusive workspace lock: {len(wp.bounded_files)} bounded file(s)",
            )
            relative_evidence, evidence_target = _safe_evidence_target(root, wp)
            if evidence_target.exists():
                record = load_evidence(root, evidence_target)
                validate_existing_evidence(record, wp, evidence_target)
                reason = (
                    f"validated existing evidence {relative_evidence}; refusing overwrite"
                )
                machine.halt(reason)
                return _report(
                    wp_id, machine, preconditions, gates, violations, reason
                )
            command = wp.raw.get("execution", {}).get("command")
            if command is None:
                reason = "non-dry-run execution requires execution.command"
                machine.halt(reason)
                return _report(wp_id, machine, preconditions, gates, violations, reason)

            snapshot = _snapshot_workspace(root)
            git_control = _snapshot_git_control(root)
            execution_started_at = datetime.now(UTC)
            machine.advance(LifecycleState.EXECUTING, "executing WPS execution.command")
            passed, detail, duration = _execute_command(root, command)
            if not passed:
                reason, violations = _halt_with_evidence(
                    machine,
                    root,
                    wp,
                    evidence_target,
                    snapshot,
                    git_control,
                    preconditions,
                    gates,
                    execution_started_at,
                    f"task command failed after {duration:.3f}s: {detail}",
                )
                return _report(wp_id, machine, preconditions, gates, violations, reason)

            task_changed = snapshot.changed(_snapshot_workspace(root))
            git_changes = _git_control_changes(root, git_control)
            if git_changes:
                reason, violations = _halt_with_evidence(
                    machine,
                    root,
                    wp,
                    evidence_target,
                    snapshot,
                    git_control,
                    preconditions,
                    gates,
                    execution_started_at,
                    "task command mutated prohibited Git state: "
                    + ", ".join(git_changes),
                )
                return _report(wp_id, machine, preconditions, gates, violations, reason)
            task_audit = audit_boundaries(wp.bounded_files, task_changed)
            violations = task_audit.violations
            if not task_audit.compliant:
                reason, violations = _halt_with_evidence(
                    machine,
                    root,
                    wp,
                    evidence_target,
                    snapshot,
                    git_control,
                    preconditions,
                    gates,
                    execution_started_at,
                    f"FIT-005 violation: {len(violations)} file(s) out of bounds",
                )
                return _report(wp_id, machine, preconditions, gates, violations, reason)
            try:
                _validate_expected_outputs(root, wp, task_changed)
            except InvariantError as exc:
                reason, violations = _halt_with_evidence(
                    machine,
                    root,
                    wp,
                    evidence_target,
                    snapshot,
                    git_control,
                    preconditions,
                    gates,
                    execution_started_at,
                    str(exc),
                )
                return _report(wp_id, machine, preconditions, gates, violations, reason)

            post_task_snapshot = _snapshot_workspace(root)
            machine.advance(LifecycleState.VALIDATING, "running required quality gates")
            for gate, gate_command, required in wp.quality_gates:
                gate_outcome = run_gate(root, gate, gate_command)
                gates.append(gate_outcome)
                git_changes = _git_control_changes(root, git_control)
                if git_changes:
                    reason, violations = _halt_with_evidence(
                        machine,
                        root,
                        wp,
                        evidence_target,
                        snapshot,
                        git_control,
                        preconditions,
                        gates,
                        execution_started_at,
                        f"gate {gate} mutated prohibited Git state: "
                        + ", ".join(git_changes),
                    )
                    return _report(
                        wp_id, machine, preconditions, gates, violations, reason
                    )
                if required and not gate_outcome.passed:
                    reason, violations = _halt_with_evidence(
                        machine,
                        root,
                        wp,
                        evidence_target,
                        snapshot,
                        git_control,
                        preconditions,
                        gates,
                        execution_started_at,
                        f"gate {gate} failed",
                    )
                    return _report(
                        wp_id, machine, preconditions, gates, violations, reason
                    )
                current_workspace = _snapshot_workspace(root)
                final_changed = snapshot.changed(current_workspace)
                try:
                    _validate_expected_outputs(root, wp, final_changed)
                except InvariantError as exc:
                    reason, violations = _halt_with_evidence(
                        machine,
                        root,
                        wp,
                        evidence_target,
                        snapshot,
                        git_control,
                        preconditions,
                        gates,
                        execution_started_at,
                        str(exc),
                    )
                    return _report(
                        wp_id, machine, preconditions, gates, violations, reason
                    )
                gate_changes = post_task_snapshot.changed(current_workspace)
                substantive_gate_changes = tuple(
                    path for path in gate_changes if not is_tooling_artifact(path)
                )
                if substantive_gate_changes:
                    reason, violations = _halt_with_evidence(
                        machine,
                        root,
                        wp,
                        evidence_target,
                        snapshot,
                        git_control,
                        preconditions,
                        gates,
                        execution_started_at,
                        f"gate {gate} mutated non-tooling workspace files: "
                        + ", ".join(substantive_gate_changes),
                    )
                    return _report(
                        wp_id, machine, preconditions, gates, violations, reason
                    )
                _restore_workspace(root, post_task_snapshot)

            task_changed = snapshot.changed(_snapshot_workspace(root))
            audit = audit_boundaries(wp.bounded_files, task_changed)
            violations = audit.violations
            if not audit.compliant:
                reason, violations = _halt_with_evidence(
                    machine,
                    root,
                    wp,
                    evidence_target,
                    snapshot,
                    git_control,
                    preconditions,
                    gates,
                    execution_started_at,
                    f"FIT-005 violation: {len(violations)} file(s) out of bounds",
                )
                return _report(wp_id, machine, preconditions, gates, violations, reason)
            try:
                _validate_expected_outputs(root, wp, task_changed)
            except InvariantError as exc:
                reason, violations = _halt_with_evidence(
                    machine,
                    root,
                    wp,
                    evidence_target,
                    snapshot,
                    git_control,
                    preconditions,
                    gates,
                    execution_started_at,
                    str(exc),
                )
                return _report(wp_id, machine, preconditions, gates, violations, reason)

            record = compose_boundary_evidence(
                wp,
                audit,
                _gate_evidence(gates),
                started_at=execution_started_at,
                finished_at=datetime.now(UTC),
                preconditions=_precondition_evidence(preconditions),
            )
            write_evidence(record, root, evidence_target)
            evidence_note = f"atomically emitted {relative_evidence}"
            machine.advance(LifecycleState.EVIDENCE_GENERATED, evidence_note)
            machine.advance(LifecycleState.REVIEW_PENDING, "awaiting ARB disposition")
    except AfrpError as exc:
        halted_reason = str(exc)
        if snapshot is not None and git_control is not None and not machine.terminal:
            try:
                _restore_git_control(root, git_control)
                _restore_workspace(root, snapshot)
                _verify_restored_state(root, snapshot, git_control)
                halted_reason += "; task-introduced changes rolled back and verified"
            except AfrpError as rollback_error:
                halted_reason += f"; rollback failed: {rollback_error}"
        if not machine.terminal:
            machine.halt(halted_reason)

    return _report(
        wp_id, machine, preconditions, gates, violations, halted_reason
    )


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
        transitions=tuple((state.value, note) for state, note in machine.history),
        preconditions=tuple(preconditions),
        gates=tuple(gates),
        boundary_violations=violations,
        halted_reason=halted_reason,
    )
