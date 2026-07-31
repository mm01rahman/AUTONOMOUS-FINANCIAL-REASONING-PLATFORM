"""Focused tests for the EOS-BOOT bootstrap script."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from afrp.core.bootstrap import BOOTSTRAP_TAG, BootstrapError, bootstrap_workspace

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "bootstrap_m1.sh"


def install_fake_uv(root: Path, *, exit_code: int = 0) -> Path:
    """Install a synthetic uv executable for deterministic bootstrap tests."""
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True)
    if os.name == "nt":
        uv_path = bin_dir / "uv.cmd"
        uv_path.write_text(
            "@echo off\n"
            "setlocal\n"
            "set args=%*\n"
            "(echo %args%) > .uv-invocation\n"
            "if /I \"%~1\"==\"sync\" (\n"
            "  (echo ok) > .uv-sync-complete\n"
            ")\n"
            f"exit /b {exit_code}\n",
            encoding="utf-8",
        )
    else:
        uv_path = bin_dir / "uv"
        uv_path.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "printf '%s\\n' \"$*\" > .uv-invocation\n"
            "if [[ ${1:-} == sync ]]; then\n"
            "  printf 'ok\\n' > .uv-sync-complete\n"
            "fi\n"
            f"exit {exit_code}\n",
            encoding="utf-8",
        )
        uv_path.chmod(0o755)
    return bin_dir


def tag_points_at_head(repo_root: Path) -> bool:
    """Return whether the bootstrap tag resolves to HEAD."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tag = subprocess.run(
        ["git", "rev-parse", BOOTSTRAP_TAG],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return head == tag


def bootstrap_script_command(workspace: Path) -> list[str]:
    """Invoke the bootstrap wrapper across host platforms."""
    if os.name != "nt":
        return [str(SCRIPT_PATH), str(workspace)]
    return [sys.executable, "-B", "-m", "afrp.core.bootstrap", str(workspace)]


class TestBootstrapWorkspace:
    def test_bootstrap_workspace_is_idempotent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_bin = install_fake_uv(tmp_path / "tools")
        monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")

        workspace = tmp_path / "workspace"
        first = bootstrap_workspace(workspace)
        second = bootstrap_workspace(workspace)

        assert first.created_tag is True
        assert second.created_tag is False
        assert (workspace / "pyproject.toml").is_file()
        assert (workspace / "Cargo.toml").is_file()
        assert (workspace / "tools/afrp-cli/afrp/cli.py").is_file()
        assert (workspace / ".afrp/health/bootstrap_m1.json").is_file()
        assert tag_points_at_head(workspace)
        assert "buf" in first.waived_tools

    def test_script_wrapper_runs_end_to_end(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_bin = install_fake_uv(tmp_path / "tools")
        monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")

        workspace = tmp_path / "workspace"
        outcome = subprocess.run(
            bootstrap_script_command(workspace),
            check=False,
            capture_output=True,
            text=True,
        )

        if os.name != "nt":
            assert SCRIPT_PATH.stat().st_mode & 0o111
        assert outcome.returncode == 0, outcome.stderr
        assert BOOTSTRAP_TAG in outcome.stdout
        assert tag_points_at_head(workspace)

    def test_failed_sync_rolls_back_created_tag(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_bin = install_fake_uv(tmp_path / "tools", exit_code=7)
        monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ['PATH']}")

        workspace = tmp_path / "workspace"
        outcome: subprocess.CompletedProcess[str]
        if os.name == "nt":
            def run_command(
                command: Sequence[str],
                cwd: Path | None,
                env: Mapping[str, str] | None,
            ) -> subprocess.CompletedProcess[str]:
                if list(command[:1]) == ["uv"]:
                    return subprocess.CompletedProcess(
                        args=list(command),
                        returncode=7,
                        stdout="",
                        stderr="simulated sync failure",
                    )
                return subprocess.run(
                    list(command),
                    cwd=cwd,
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                )

            with pytest.raises(BootstrapError, match="uv sync --group dev"):
                bootstrap_workspace(workspace, run_command=run_command)
            outcome = subprocess.CompletedProcess(args=["bootstrap"], returncode=1)
        else:
            outcome = subprocess.run(
                bootstrap_script_command(workspace),
                check=False,
                capture_output=True,
                text=True,
            )

        tag_check = subprocess.run(
            ["git", "rev-parse", BOOTSTRAP_TAG],
            cwd=workspace,
            check=False,
            capture_output=True,
            text=True,
        )
        assert outcome.returncode == 1
        if os.name != "nt":
            assert "uv sync --group dev" in outcome.stderr
        assert tag_check.returncode != 0
