"""EOS-BOOT workspace bootstrap support."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

BOOTSTRAP_TAG = "m1.1-start"
DIRECTORIES: tuple[str, ...] = (
    "00-governance",
    "01-vision",
    "02-architecture/specs",
    "03-engineering",
    "04-ai-framework",
    "05-work-packages/WP-IMP-0003/evidence",
    "06-runtime/afrp_runtime",
    "07-research/afrp_research",
    "08-operations",
    "09-validation/schemas",
    "10-release",
    "proto/afrp/v1",
    "tests/unit",
    "tools/afrp-cli/afrp/commands",
    "tools/afrp-cli/afrp/core",
)
HOOK_DIRECTORIES: tuple[str, ...] = (
    ".afrp/logs",
    ".afrp/metrics",
    ".afrp/health",
    ".afrp/evidence",
)

PYPROJECT_TEMPLATE = """[project]
name = "afrp-platform"
version = "1.0.0"
description = "Autonomous Financial Reasoning Platform"
requires-python = ">=3.11,<3.13"
dependencies = ["click>=8.1.0", "pydantic>=2.0.0", "pyyaml>=6.0.0"]

[project.scripts]
afrp = "afrp.cli:main"

[dependency-groups]
dev = [
    "ruff>=0.6.0",
    "mypy>=1.11.0",
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "jsonschema>=4.21.0",
    "types-pyyaml>=6.0.0",
    "types-jsonschema>=4.21.0",
    "types-protobuf>=4.25.0",
    "grpcio-tools>=1.62.0",
    "protobuf>=4.25.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = [
    "tools/afrp-cli/afrp",
    "06-runtime/afrp_runtime",
    "07-research/afrp_research",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "ANN"]

[tool.mypy]
strict = true
python_version = "3.11"
mypy_path = ["tools/afrp-cli", "06-runtime", "07-research"]
explicit_package_bases = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
"""

CARGO_TEMPLATE = """[workspace]
resolver = "2"
members = []

[workspace.package]
version = "1.0.0"
edition = "2021"
"""

CLI_TEMPLATE = '''"""Bootstrap placeholder CLI for EOS-BOOT workspaces."""

from __future__ import annotations


def main() -> None:
    """Emit a deterministic placeholder message for fresh workspaces."""
    print("AFRP workspace bootstrap complete.")
'''

PACKAGE_TEMPLATE = '''"""Bootstrap placeholder package for AFRP."""
'''

CommandRunner = Callable[
    [Sequence[str], Path | None, Mapping[str, str] | None], subprocess.CompletedProcess[str]
]
WhichFunction = Callable[[str], str | None]


@dataclass(frozen=True)
class BootstrapResult:
    """Result of bootstrapping an AFRP workspace."""

    workspace: Path
    created_tag: bool
    waived_tools: tuple[str, ...]


class BootstrapError(RuntimeError):
    """Raised when EOS-BOOT cannot materialize a governed workspace."""


def _run_command(
    command: Sequence[str],
    cwd: Path | None,
    env: Mapping[str, str] | None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=None if env is None else dict(env),
        capture_output=True,
        text=True,
        check=False,
    )


def _write_file(path: Path, content: str) -> None:
    normalized = content.rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == normalized:
            return
        raise BootstrapError(f"Refusing to overwrite non-bootstrap file: {path}")
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(normalized)
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _replace_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _git(
    repo_root: Path,
    *args: str,
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> subprocess.CompletedProcess[str]:
    return run_command(("git", *args), repo_root, env)


def _require_success(result: subprocess.CompletedProcess[str], context: str) -> str:
    if result.returncode == 0:
        return result.stdout.strip()
    detail = (result.stderr or result.stdout).strip()
    raise BootstrapError(f"{context}: {detail or 'command failed'}")


def _ensure_toolchain(which: WhichFunction) -> tuple[str, ...]:
    if sys.version_info < (3, 11):
        raise BootstrapError("python3.11+ is required for EOS-BOOT")
    missing = [name for name in ("git", "uv") if which(name) is None]
    if missing:
        joined = ", ".join(missing)
        raise BootstrapError(f"Missing required toolchain dependency: {joined}")
    waived = tuple(name for name in ("buf", "cargo") if which(name) is None)
    return waived


def _ensure_git_repository(
    repo_root: Path,
    *,
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> None:
    probe = _git(repo_root, "rev-parse", "--is-inside-work-tree", run_command=run_command, env=env)
    if probe.returncode == 0:
        return
    _require_success(_git(repo_root, "init", "-q", run_command=run_command, env=env), "git init")


def _head_commit(
    repo_root: Path,
    *,
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> str | None:
    result = _git(repo_root, "rev-parse", "--verify", "HEAD", run_command=run_command, env=env)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _tag_target(
    repo_root: Path,
    *,
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> str | None:
    result = _git(
        repo_root,
        "rev-parse",
        "--verify",
        f"refs/tags/{BOOTSTRAP_TAG}",
        run_command=run_command,
        env=env,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _commit_if_needed(
    repo_root: Path,
    *,
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> bool:
    tracked = _tracked_paths()
    _require_success(_git(repo_root, "add", *tracked, run_command=run_command, env=env), "git add")
    status = _tracked_status(repo_root, tracked=tracked, run_command=run_command, env=env)
    head = _head_commit(repo_root, run_command=run_command, env=env)
    if status or head is None:
        commit_env = dict(os.environ if env is None else env)
        commit_env.setdefault("GIT_AUTHOR_NAME", "AFRP Bootstrap")
        commit_env.setdefault("GIT_AUTHOR_EMAIL", "bootstrap@afrp.local")
        commit_env.setdefault("GIT_COMMITTER_NAME", commit_env["GIT_AUTHOR_NAME"])
        commit_env.setdefault("GIT_COMMITTER_EMAIL", commit_env["GIT_AUTHOR_EMAIL"])
        _require_success(
            _git(
                repo_root,
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "Initialize AFRP workspace (m1.1-start)",
                run_command=run_command,
                env=commit_env,
            ),
            "git commit",
        )
        return True
    return False


def _tracked_paths() -> tuple[str, ...]:
    return (
        "pyproject.toml",
        "Cargo.toml",
        "tools/afrp-cli/afrp/__init__.py",
        "tools/afrp-cli/afrp/cli.py",
        "tools/afrp-cli/afrp/commands/__init__.py",
        "tools/afrp-cli/afrp/core/__init__.py",
        "06-runtime/afrp_runtime/__init__.py",
        "07-research/afrp_research/__init__.py",
    )


def _tracked_status(
    repo_root: Path,
    *,
    tracked: Sequence[str],
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> str:
    status = _git(repo_root, "status", "--porcelain", "--", *tracked, run_command=run_command, env=env)
    return status.stdout.strip()


def _write_hooks(
    repo_root: Path,
    *,
    waived_tools: tuple[str, ...],
    run_command: CommandRunner,
    env: Mapping[str, str] | None,
) -> None:
    commit = _require_success(
        _git(repo_root, "rev-parse", "HEAD", run_command=run_command, env=env),
        "git rev-parse HEAD",
    )
    for rel in HOOK_DIRECTORIES:
        (repo_root / rel).mkdir(parents=True, exist_ok=True)
    (repo_root / ".afrp" / "logs" / "bootstrap_m1.log").write_text(
        "status=PASS\n"
        f"workspace={repo_root}\n"
        f"tag={BOOTSTRAP_TAG}\n"
        f"waived_tools={','.join(waived_tools) or 'none'}\n",
        encoding="utf-8",
    )
    _replace_json(
        repo_root / ".afrp" / "metrics" / "bootstrap_m1.json",
        {
            "directories_declared": len(DIRECTORIES),
            "tag": BOOTSTRAP_TAG,
            "uv_sync": "PASS",
            "waived_tools": list(waived_tools),
        },
    )
    _replace_json(
        repo_root / ".afrp" / "health" / "bootstrap_m1.json",
        {
            "commit": commit,
            "python": ".".join(str(part) for part in sys.version_info[:3]),
            "status": "PASS",
        },
    )
    _replace_json(
        repo_root / ".afrp" / "evidence" / "bootstrap_m1.json",
        {
            "commit": commit,
            "tag": BOOTSTRAP_TAG,
            "workspace": str(repo_root),
        },
    )


def bootstrap_workspace(
    target_root: Path,
    *,
    run_command: CommandRunner = _run_command,
    which: WhichFunction = shutil.which,
    env: Mapping[str, str] | None = None,
) -> BootstrapResult:
    """Create the governed AFRP workspace skeleton in ``target_root``."""
    repo_root = target_root.resolve()
    repo_root.mkdir(parents=True, exist_ok=True)
    waived_tools = _ensure_toolchain(which)
    for rel in DIRECTORIES:
        (repo_root / rel).mkdir(parents=True, exist_ok=True)
    _write_file(repo_root / "pyproject.toml", PYPROJECT_TEMPLATE)
    _write_file(repo_root / "Cargo.toml", CARGO_TEMPLATE)
    _write_file(repo_root / "tools/afrp-cli/afrp/__init__.py", PACKAGE_TEMPLATE)
    _write_file(repo_root / "tools/afrp-cli/afrp/cli.py", CLI_TEMPLATE)
    _write_file(repo_root / "tools/afrp-cli/afrp/commands/__init__.py", PACKAGE_TEMPLATE)
    _write_file(repo_root / "tools/afrp-cli/afrp/core/__init__.py", PACKAGE_TEMPLATE)
    _write_file(repo_root / "06-runtime/afrp_runtime/__init__.py", PACKAGE_TEMPLATE)
    _write_file(repo_root / "07-research/afrp_research/__init__.py", PACKAGE_TEMPLATE)

    _ensure_git_repository(repo_root, run_command=run_command, env=env)
    head_before = _head_commit(repo_root, run_command=run_command, env=env)
    tag_before = _tag_target(repo_root, run_command=run_command, env=env)
    if tag_before is not None and tag_before != head_before:
        raise BootstrapError(f"Existing tag {BOOTSTRAP_TAG} does not point at HEAD")
    tracked = _tracked_paths()
    _require_success(_git(repo_root, "add", *tracked, run_command=run_command, env=env), "git add")
    if tag_before is not None and _tracked_status(
        repo_root, tracked=tracked, run_command=run_command, env=env
    ):
        raise BootstrapError(f"Existing tag {BOOTSTRAP_TAG} would be moved by bootstrap")

    _commit_if_needed(repo_root, run_command=run_command, env=env)

    created_tag = False
    try:
        if tag_before is None:
            _require_success(
                _git(repo_root, "tag", BOOTSTRAP_TAG, run_command=run_command, env=env),
                "git tag",
            )
            created_tag = True
        sync = run_command(("uv", "sync", "--group", "dev"), repo_root, env)
        _require_success(sync, "uv sync --group dev")
        _write_hooks(repo_root, waived_tools=waived_tools, run_command=run_command, env=env)
    except BootstrapError:
        if created_tag:
            _git(repo_root, "tag", "-d", BOOTSTRAP_TAG, run_command=run_command, env=env)
        raise

    return BootstrapResult(workspace=repo_root, created_tag=created_tag, waived_tools=waived_tools)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point used by ``bootstrap_m1.sh``."""
    parser = argparse.ArgumentParser(description="Bootstrap an AFRP EOS-BOOT workspace.")
    parser.add_argument("workspace", nargs="?", default=".", help="Target workspace directory.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = bootstrap_workspace(Path(args.workspace))
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    waived = ", ".join(result.waived_tools) or "none"
    print(f"Initialized AFRP workspace at {result.workspace} with tag {BOOTSTRAP_TAG}")
    print(f"ADR-0002 waivers applied: {waived}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
