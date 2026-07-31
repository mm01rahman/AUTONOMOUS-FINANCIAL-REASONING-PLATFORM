"""EOS-BOOT workspace setup (EOS-002).

The module is intentionally Python-standard-library only so it can execute before
the project environment is synchronized. Tool and Git access are injected through
Protocols; the production adapters use subprocess without a shell.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from afrp.core.exceptions import AfrpError

MILESTONE_TAG = "m1.1-start"
MINIMUM_PYTHON = (3, 11)

WORKSPACE_DIRECTORIES: tuple[str, ...] = (
    "00-governance",
    "01-vision",
    "02-architecture/specs",
    "03-engineering",
    "04-ai-framework",
    "05-work-packages/WP-IMP-0003/evidence",
    "06-runtime",
    "07-research",
    "08-operations",
    "09-validation/schemas",
    "10-release",
    "proto/afrp/v1",
    "tests/unit",
    "tools/afrp-cli/afrp/commands",
    "tools/afrp-cli/afrp/core",
)

PYPROJECT_TEMPLATE = """[project]
name = "afrp-platform"
version = "0.1.0"
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
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tools/afrp-cli/afrp"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "ANN"]

[tool.mypy]
strict = true
python_version = "3.11"
mypy_path = ["tools/afrp-cli"]
explicit_package_bases = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.coverage.run]
source = ["tools/afrp-cli/afrp"]
"""

CARGO_TEMPLATE = """[workspace]
resolver = "2"
members = []

[workspace.package]
version = "0.1.0"
edition = "2021"
"""

_YAML_VALUE = re.compile(r'^"([^"]+)"$')
_APPROVED_WAIVERS = {
    "W-001": "buf",
    "W-002": "cargo",
}


class ToolState(StrEnum):
    """EOS-BOOT tool-health state."""

    FOUND = "FOUND"
    WAIVED = "WAIVED"
    MISSING = "MISSING"


@dataclass(frozen=True)
class ToolCheck:
    """One toolchain probe result."""

    name: str
    state: ToolState
    detail: str


@dataclass(frozen=True)
class WorkspaceBootstrapResult:
    """EOS-BOOT result, health hook, metrics, and evidence hook."""

    root: str
    checks: tuple[ToolCheck, ...]
    directories_created: tuple[str, ...]
    files_created: tuple[str, ...]
    files_preserved: tuple[str, ...]
    tag_created: bool
    check_only: bool

    @property
    def healthy(self) -> bool:
        """True when no unwaived dependency is missing."""
        return all(check.state is not ToolState.MISSING for check in self.checks)

    @property
    def metrics(self) -> dict[str, int]:
        """Stable EOS-BOOT health metrics."""
        return {
            "tools_found": sum(
                check.state is ToolState.FOUND for check in self.checks
            ),
            "tools_waived": sum(
                check.state is ToolState.WAIVED for check in self.checks
            ),
            "tools_missing": sum(
                check.state is ToolState.MISSING for check in self.checks
            ),
            "directories_created": len(self.directories_created),
            "files_created": len(self.files_created),
            "files_preserved": len(self.files_preserved),
            "tag_created": int(self.tag_created),
        }

    def evidence_payload(self) -> dict[str, object]:
        """Return an ERS-ready deterministic summary hook."""
        return {
            "capability_id": "EOS-BOOT",
            "healthy": self.healthy,
            "check_only": self.check_only,
            "toolchain": [asdict(check) for check in self.checks],
            "metrics": self.metrics,
            "root": self.root,
        }

    def as_dict(self) -> dict[str, object]:
        """JSON-safe public result representation."""
        return {
            "capability": "EOS-BOOT",
            "root": self.root,
            "healthy": self.healthy,
            "checks": [asdict(check) for check in self.checks],
            "directories_created": list(self.directories_created),
            "files_created": list(self.files_created),
            "files_preserved": list(self.files_preserved),
            "tag_created": self.tag_created,
            "check_only": self.check_only,
            "metrics": self.metrics,
        }


class ToolProbe(Protocol):
    """Dependency-injected toolchain probe."""

    def version(self, name: str) -> str | None:
        """Return version text, or None when unavailable/unsupported."""


class GitPort(Protocol):
    """Dependency-injected Git operations required by EOS-BOOT."""

    def is_repository(self) -> bool:
        """Return whether the target is inside a Git work tree."""

    def tag_exists(self, tag: str) -> bool:
        """Return whether ``tag`` exists."""

    def preflight_tag(self, tag: str) -> None:
        """Verify tag prerequisites without writing."""

    def create_tag(self, tag: str) -> None:
        """Create an annotated milestone tag."""


class SystemToolProbe:
    """Production probe using the current process and PATH."""

    _EXECUTABLES: dict[str, tuple[str, ...]] = {
        "git": ("git",),
        "uv": ("uv",),
        "cargo": ("cargo",),
        "buf": ("buf",),
    }

    def version(self, name: str) -> str | None:
        if name == "python":
            return ".".join(str(part) for part in sys.version_info[:3])
        candidates = self._EXECUTABLES.get(name)
        if candidates is None:
            return None
        executable = next(
            (candidate for candidate in candidates if shutil.which(candidate)),
            None,
        )
        if executable is None:
            return None
        completed = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        return (completed.stdout or completed.stderr).strip()


@dataclass(frozen=True)
class SubprocessGitPort:
    """Production Git port scoped to a workspace root."""

    root: Path

    def _run(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        if not self.root.is_dir():
            return subprocess.CompletedProcess(
                ["git", *arguments],
                returncode=1,
                stdout="",
                stderr=f"workspace root does not exist: {self.root}",
            )
        return subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def is_repository(self) -> bool:
        result = self._run(["rev-parse", "--is-inside-work-tree"])
        return result.returncode == 0 and result.stdout.strip() == "true"

    def tag_exists(self, tag: str) -> bool:
        result = self._run(["tag", "--list", tag])
        return result.returncode == 0 and tag in result.stdout.splitlines()

    def preflight_tag(self, tag: str) -> None:
        if self.tag_exists(tag):
            return
        head = self._run(["rev-parse", "--verify", "HEAD"])
        if head.returncode != 0:
            raise WorkspaceBootstrapError(
                f"cannot create {tag!r}: repository has no commit at HEAD"
            )
        identity = self._run(["var", "GIT_COMMITTER_IDENT"])
        if identity.returncode != 0:
            raise WorkspaceBootstrapError(
                f"cannot create {tag!r}: Git committer identity is unavailable"
            )

    def create_tag(self, tag: str) -> None:
        result = self._run(["tag", "-a", tag, "-m", "AFRP M1.1 workspace initialized"])
        if result.returncode != 0:
            raise WorkspaceBootstrapError(
                f"unable to create tag {tag!r}: {result.stderr.strip()}"
            )


class WorkspaceBootstrapError(AfrpError):
    """EOS-BOOT workspace setup failure."""

    exit_code = 5


class ToolchainError(WorkspaceBootstrapError):
    """One or more unwaived EOS-BOOT dependencies are unavailable."""

    def __init__(self, checks: tuple[ToolCheck, ...]) -> None:
        self.checks = checks
        missing = ", ".join(
            check.name for check in checks if check.state is ToolState.MISSING
        )
        super().__init__(f"unwaived toolchain dependencies missing: {missing}")


def load_waived_tools(build_profile: Path) -> frozenset[str]:
    """Read only ADR-0002-approved W-001/buf and W-002/cargo waivers."""
    if not build_profile.is_file():
        return frozenset()
    inside = False
    current: dict[str, str] = {}
    waived: set[str] = set()

    def commit_record() -> None:
        waiver_id = current.get("id")
        tool = current.get("tool")
        approved_by = current.get("approved_by")
        if (
            waiver_id in _APPROVED_WAIVERS
            and tool == _APPROVED_WAIVERS[waiver_id]
            and approved_by == "ADR-0002"
        ):
            waived.add(tool)
        current.clear()

    for raw_line in build_profile.read_text(encoding="utf-8").splitlines():
        if raw_line == "toolchain_waivers:":
            inside = True
            continue
        if inside and raw_line and not raw_line[0].isspace():
            commit_record()
            break
        if not inside:
            continue
        stripped = raw_line.strip()
        if stripped.startswith("- id:"):
            commit_record()
            key, value = stripped[2:].split(":", maxsplit=1)
        elif ":" in stripped:
            key, value = stripped.split(":", maxsplit=1)
        else:
            continue
        match = _YAML_VALUE.match(value.strip())
        if match is not None:
            current[key] = match.group(1)
    if inside:
        commit_record()
    return frozenset(waived)


def _missing_directories(root: Path, target: Path) -> list[Path]:
    """Return absent target/parent directories from root outward."""
    missing: list[Path] = []
    cursor = target
    while cursor != root and not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    return list(reversed(missing))


def _rollback_created(
    root: Path,
    files_created: list[str],
    directories_created: list[str],
) -> None:
    """Remove only artifacts created by the current failed bootstrap."""
    for relative in reversed(files_created):
        target = root / relative
        if target.is_file():
            target.unlink()
    for relative in sorted(
        directories_created,
        key=lambda value: len(Path(value).parts),
        reverse=True,
    ):
        target = root / relative
        if target.is_dir():
            try:
                target.rmdir()
            except OSError:
                # A non-empty directory contains something not created by this
                # operation and must be preserved.
                continue


def _create_file_exclusive(target: Path, content: str) -> None:
    """Create and durably flush a new file without overwriting an existing one."""
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def verify_toolchain(
    root: Path, probe: ToolProbe | None = None
) -> tuple[ToolCheck, ...]:
    """Probe EOS-002 tools, applying only ADR-backed BUILD_PROFILE waivers."""
    active_probe = probe or SystemToolProbe()
    waived = load_waived_tools(root / "03-engineering" / "BUILD_PROFILE.yaml")
    checks: list[ToolCheck] = []
    for name in ("git", "python", "cargo", "buf", "uv"):
        version = active_probe.version(name)
        if version is not None:
            if name == "python":
                parts = tuple(int(part) for part in version.split(".")[:2])
                if parts < MINIMUM_PYTHON:
                    checks.append(
                        ToolCheck(
                            name,
                            ToolState.MISSING,
                            f"{version}; requires >=3.11",
                        )
                    )
                    continue
            checks.append(ToolCheck(name, ToolState.FOUND, version))
        elif name in waived:
            checks.append(
                ToolCheck(name, ToolState.WAIVED, "waived by BUILD_PROFILE/ADR")
            )
        else:
            checks.append(ToolCheck(name, ToolState.MISSING, "not found"))
    return tuple(checks)


def bootstrap_workspace(
    root: Path,
    *,
    probe: ToolProbe | None = None,
    git: GitPort | None = None,
    logger: logging.Logger | None = None,
    check_only: bool = False,
    create_tag: bool = True,
) -> WorkspaceBootstrapResult:
    """Verify and initialize the approved AFRP M1.1 workspace.

    The operation is idempotent: existing configuration files and tags are
    preserved. Toolchain and Git preconditions are evaluated before any write.
    """
    resolved = root.resolve()
    checks = verify_toolchain(resolved, probe)
    if any(check.state is ToolState.MISSING for check in checks):
        raise ToolchainError(checks)

    git_port = git or SubprocessGitPort(resolved)
    if create_tag and not git_port.is_repository():
        raise WorkspaceBootstrapError(f"{resolved} is not a Git work tree")
    needs_tag = create_tag and not git_port.tag_exists(MILESTONE_TAG)
    if needs_tag:
        git_port.preflight_tag(MILESTONE_TAG)

    if logger is not None:
        logger.info(
            "eos_boot_toolchain_verified",
            extra={"checks": [asdict(check) for check in checks]},
        )

    if check_only:
        return WorkspaceBootstrapResult(
            root=str(resolved),
            checks=checks,
            directories_created=(),
            files_created=(),
            files_preserved=(),
            tag_created=False,
            check_only=True,
        )

    directories_created: list[str] = []
    files_created: list[str] = []
    files_preserved: list[str] = []
    try:
        resolved.mkdir(parents=True, exist_ok=True)
        for relative in WORKSPACE_DIRECTORIES:
            target = resolved / relative
            missing = _missing_directories(resolved, target)
            target.mkdir(parents=True, exist_ok=True)
            directories_created.extend(
                str(path.relative_to(resolved)).replace("\\", "/")
                for path in missing
            )

        for relative, content in (
            ("pyproject.toml", PYPROJECT_TEMPLATE),
            ("Cargo.toml", CARGO_TEMPLATE),
        ):
            target = resolved / relative
            if target.exists():
                files_preserved.append(relative)
            else:
                files_created.append(relative)
                try:
                    _create_file_exclusive(target, content)
                except FileExistsError:
                    # Another bootstrap process won the exclusive-create race.
                    files_created.remove(relative)
                    files_preserved.append(relative)

        tag_created = False
        if needs_tag:
            git_port.create_tag(MILESTONE_TAG)
            tag_created = True
    except WorkspaceBootstrapError:
        _rollback_created(resolved, files_created, directories_created)
        raise
    except OSError as exc:
        _rollback_created(resolved, files_created, directories_created)
        raise WorkspaceBootstrapError(f"workspace write failed: {exc}") from exc

    result = WorkspaceBootstrapResult(
        root=str(resolved),
        checks=checks,
        directories_created=tuple(directories_created),
        files_created=tuple(files_created),
        files_preserved=tuple(files_preserved),
        tag_created=tag_created,
        check_only=False,
    )
    if logger is not None:
        logger.info("eos_boot_complete", extra={"metrics": result.metrics})
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify and initialize the AFRP EOS M1.1 workspace."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root (default: current directory).",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Verify prerequisites without writing.",
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Do not create the m1.1-start tag.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """EOS-BOOT public command entry point."""
    arguments = _parser().parse_args(argv)
    logger = logging.getLogger("afrp.eos.boot")
    try:
        result = bootstrap_workspace(
            arguments.root,
            logger=logger,
            check_only=arguments.check_only,
            create_tag=not arguments.no_tag,
        )
    except AfrpError as exc:
        print(
            json.dumps(
                {
                    "capability": "EOS-BOOT",
                    "healthy": False,
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        return exc.exit_code
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
