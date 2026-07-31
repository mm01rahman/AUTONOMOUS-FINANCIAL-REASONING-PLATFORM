"""Tests for EOS-BOOT workspace setup and public entry point."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from afrp.core import workspace as workspace_module
from afrp.core.workspace import (
    CARGO_TEMPLATE,
    MILESTONE_TAG,
    PYPROJECT_TEMPLATE,
    WORKSPACE_DIRECTORIES,
    ToolchainError,
    ToolState,
    WorkspaceBootstrapError,
    bootstrap_workspace,
    load_waived_tools,
    main,
    verify_toolchain,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class FakeProbe:
    """Deterministic ToolProbe fixture."""

    versions: dict[str, str | None]

    def version(self, name: str) -> str | None:
        return self.versions.get(name)


@dataclass
class FakeGit:
    """Deterministic GitPort fixture."""

    repository: bool = True
    tags: set[str] = field(default_factory=set)
    created: list[str] = field(default_factory=list)
    preflight_error: str | None = None
    create_error: str | None = None

    def is_repository(self) -> bool:
        return self.repository

    def tag_exists(self, tag: str) -> bool:
        return tag in self.tags

    def preflight_tag(self, tag: str) -> None:
        del tag
        if self.preflight_error is not None:
            raise WorkspaceBootstrapError(self.preflight_error)

    def create_tag(self, tag: str) -> None:
        if self.create_error is not None:
            raise WorkspaceBootstrapError(self.create_error)
        self.tags.add(tag)
        self.created.append(tag)


def healthy_probe() -> FakeProbe:
    return FakeProbe(
        {
            "git": "git version 2.50",
            "python": "3.11.0",
            "cargo": "cargo 1.80",
            "buf": "1.50.0",
            "uv": "uv 0.12.0",
        }
    )


class TestToolchain:
    def test_all_tools_found(self, tmp_path: Path) -> None:
        checks = verify_toolchain(tmp_path, healthy_probe())
        assert [check.name for check in checks] == [
            "git",
            "python",
            "cargo",
            "buf",
            "uv",
        ]
        assert all(check.state is ToolState.FOUND for check in checks)

    def test_adr_waivers_are_honored(self, tmp_path: Path) -> None:
        profile = tmp_path / "03-engineering" / "BUILD_PROFILE.yaml"
        profile.parent.mkdir(parents=True)
        profile.write_text(
            "toolchain_waivers:\n"
            '  - id: "W-001"\n'
            '    tool: "buf"\n'
            '    approved_by: "ADR-0002"\n'
            '  - id: "W-002"\n'
            '    tool: "cargo"\n'
            '    approved_by: "ADR-0002"\n',
            encoding="utf-8",
        )
        probe = healthy_probe()
        probe.versions["cargo"] = None
        probe.versions["buf"] = None
        checks = verify_toolchain(tmp_path, probe)
        states = {check.name: check.state for check in checks}
        assert states["cargo"] is ToolState.WAIVED
        assert states["buf"] is ToolState.WAIVED

    def test_unwaived_missing_tool_fails_before_writes(self, tmp_path: Path) -> None:
        probe = healthy_probe()
        probe.versions["uv"] = None
        with pytest.raises(ToolchainError):
            bootstrap_workspace(
                tmp_path,
                probe=probe,
                git=FakeGit(),
            )
        assert list(tmp_path.iterdir()) == []

    def test_old_python_is_rejected(self, tmp_path: Path) -> None:
        probe = healthy_probe()
        probe.versions["python"] = "3.10.9"
        checks = verify_toolchain(tmp_path, probe)
        python = next(check for check in checks if check.name == "python")
        assert python.state is ToolState.MISSING
        assert "requires >=3.11" in python.detail

    def test_waiver_parser_is_standard_library_only(self, tmp_path: Path) -> None:
        profile = tmp_path / "BUILD_PROFILE.yaml"
        profile.write_text(
            "toolchain_waivers:\n"
            '  - id: "W-001"\n'
            '    tool: "buf"\n'
            '    approved_by: "ADR-0002"\n'
            '  - id: "W-002"\n'
            '    tool: "cargo"\n'
            '    approved_by: "ADR-0002"\n',
            encoding="utf-8",
        )
        assert load_waived_tools(profile) == frozenset({"buf", "cargo"})

    def test_unapproved_waiver_records_are_rejected(self, tmp_path: Path) -> None:
        profile = tmp_path / "BUILD_PROFILE.yaml"
        profile.write_text(
            "toolchain_waivers:\n"
            '  - id: "W-999"\n'
            '    tool: "uv"\n'
            '    approved_by: "NOT-ADR-0002"\n'
            '  - id: "W-002"\n'
            '    tool: "cargo"\n'
            '    approved_by: "NOT-ADR-0002"\n',
            encoding="utf-8",
        )
        assert load_waived_tools(profile) == frozenset()


class TestWorkspaceCreation:
    def test_creates_approved_skeleton_configs_and_tag(self, tmp_path: Path) -> None:
        git = FakeGit()
        result = bootstrap_workspace(
            tmp_path,
            probe=healthy_probe(),
            git=git,
        )
        assert result.healthy
        for relative in WORKSPACE_DIRECTORIES:
            assert (tmp_path / relative).is_dir()
        assert set(WORKSPACE_DIRECTORIES) <= set(result.directories_created)
        assert set(result.files_created) == {"pyproject.toml", "Cargo.toml"}
        assert (tmp_path / "pyproject.toml").read_text() == PYPROJECT_TEMPLATE
        assert (tmp_path / "Cargo.toml").read_text() == CARGO_TEMPLATE
        assert git.created == [MILESTONE_TAG]
        assert result.tag_created

    def test_idempotent_run_preserves_configs_and_tag(self, tmp_path: Path) -> None:
        git = FakeGit()
        bootstrap_workspace(tmp_path, probe=healthy_probe(), git=git)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("custom = true\n", encoding="utf-8")
        second = bootstrap_workspace(tmp_path, probe=healthy_probe(), git=git)
        assert second.directories_created == ()
        assert second.files_created == ()
        assert set(second.files_preserved) == {"pyproject.toml", "Cargo.toml"}
        assert pyproject.read_text() == "custom = true\n"
        assert git.created == [MILESTONE_TAG]
        assert not second.tag_created

    def test_check_only_is_zero_write(self, tmp_path: Path) -> None:
        result = bootstrap_workspace(
            tmp_path,
            probe=healthy_probe(),
            git=FakeGit(repository=True),
            check_only=True,
        )
        assert result.healthy
        assert result.check_only
        assert list(tmp_path.iterdir()) == []
        assert result.metrics["directories_created"] == 0

    def test_non_repository_fails_before_workspace_writes(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(WorkspaceBootstrapError, match="not a Git work tree"):
            bootstrap_workspace(
                tmp_path,
                probe=healthy_probe(),
                git=FakeGit(repository=False),
            )
        assert list(tmp_path.iterdir()) == []

    def test_tag_preflight_failure_is_zero_write(self, tmp_path: Path) -> None:
        with pytest.raises(WorkspaceBootstrapError, match="identity unavailable"):
            bootstrap_workspace(
                tmp_path,
                probe=healthy_probe(),
                git=FakeGit(preflight_error="identity unavailable"),
            )
        assert list(tmp_path.iterdir()) == []

    def test_tag_creation_failure_rolls_back_created_workspace(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(WorkspaceBootstrapError, match="tag write denied"):
            bootstrap_workspace(
                tmp_path,
                probe=healthy_probe(),
                git=FakeGit(create_error="tag write denied"),
            )
        assert list(tmp_path.iterdir()) == []

    def test_partial_config_write_is_removed_on_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fail_after_partial_write(target: Path, content: str) -> None:
            del content
            target.write_text("partial", encoding="utf-8")
            raise OSError("disk full")

        monkeypatch.setattr(
            workspace_module,
            "_create_file_exclusive",
            fail_after_partial_write,
        )
        with pytest.raises(WorkspaceBootstrapError, match="workspace write failed"):
            bootstrap_workspace(
                tmp_path,
                probe=healthy_probe(),
                git=FakeGit(),
            )
        assert list(tmp_path.iterdir()) == []

    def test_no_tag_mode_allows_non_repository(self, tmp_path: Path) -> None:
        result = bootstrap_workspace(
            tmp_path,
            probe=healthy_probe(),
            git=FakeGit(repository=False),
            create_tag=False,
        )
        assert result.healthy
        assert not result.tag_created


class TestHooksAndEntryPoint:
    def test_health_metrics_and_evidence_hook(self, tmp_path: Path) -> None:
        result = bootstrap_workspace(
            tmp_path,
            probe=healthy_probe(),
            git=FakeGit(),
        )
        assert result.metrics == {
            "tools_found": 5,
            "tools_waived": 0,
            "tools_missing": 0,
            "directories_created": len(result.directories_created),
            "files_created": 2,
            "files_preserved": 0,
            "tag_created": 1,
        }
        payload = result.evidence_payload()
        assert payload["capability_id"] == "EOS-BOOT"
        assert payload["healthy"] is True

    def test_injected_logger_receives_toolchain_and_completion_events(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        logger = logging.getLogger("test.eos.boot")
        with caplog.at_level(logging.INFO, logger=logger.name):
            bootstrap_workspace(
                tmp_path,
                probe=healthy_probe(),
                git=FakeGit(),
                logger=logger,
            )
        assert [record.message for record in caplog.records] == [
            "eos_boot_toolchain_verified",
            "eos_boot_complete",
        ]

    def test_public_check_only_entry_point_on_repository(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main(
            ["--root", str(REPO_ROOT), "--check-only", "--no-tag"]
        )
        output = json.loads(capsys.readouterr().out)
        assert exit_code == 0
        assert output["capability"] == "EOS-BOOT"
        assert output["healthy"] is True
        assert output["check_only"] is True

    def test_public_entry_point_reports_failure_as_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("PATH", "")
        exit_code = main(["--root", str(tmp_path), "--check-only", "--no-tag"])
        output = json.loads(capsys.readouterr().out)
        assert exit_code == 5
        assert output["capability"] == "EOS-BOOT"
        assert output["healthy"] is False

    def test_shell_entrypoint_checks_candidate_python_versions(self) -> None:
        script = (REPO_ROOT / "bootstrap_m1.sh").read_text(encoding="utf-8")
        assert "for candidate in python3 python" in script
        assert '"${candidate}" -B -c' in script
        assert "sys.version_info < (3, 11)" in script
        assert 'exec "${PYTHON}" -B -m afrp.core.workspace' in script
