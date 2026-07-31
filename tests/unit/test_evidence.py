"""Unit tests for WP-IMP-0006: WP loader, FIT-005 boundary audit, ERS engine."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from afrp.cli import cli
from afrp.core.evidence import (
    audit_boundaries,
    modified_files,
    validate_evidence,
    write_evidence,
)
from afrp.core.exceptions import ContractReferenceError, ManifestValidationError
from afrp.core.workpackage import load_work_package
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


def minimal_evidence() -> dict[str, Any]:
    return {
        "schema_version": "ERS-1.0",
        "evidence_id": "EXEC-999",
        "work_package_id": "WP-IMP-9999",
        "capability": {"id": "TEST-CAP", "version": "1.0"},
        "agent_identity": {
            "role": "AEF-02 (Software Engineer)",
            "agent_vendor": "Test",
            "agent_name": "pytest",
        },
        "lifecycle": {
            "protocol_version": "EGP-2.0",
            "started_at": "2026-07-31T00:00:00+06:00",
            "finished_at": "2026-07-31T00:10:00+06:00",
            "final_state": "REVIEW_PENDING",
        },
        "boundary_compliance": {
            "bounded_files": ["a.py"],
            "files_modified": ["a.py"],
            "violations": [],
            "compliant": True,
        },
        "quality_gates": [
            {"gate": "pytest_units", "command": "uv run pytest", "result": "PASS"}
        ],
        "artifacts": {"source_files": ["a.py"]},
        "unlocked_capabilities": [],
        "verdict": {
            "all_gates_passed": True,
            "boundary_compliant": True,
            "review_status": "PENDING_ARB",
        },
    }


class TestWorkPackageLoader:
    @pytest.mark.parametrize(
        "wp_id", ["WP-IMP-0003", "WP-IMP-0004", "WP-IMP-0005", "WP-IMP-0006"]
    )
    def test_loads_real_contracts(self, wp_id: str) -> None:
        wp = load_work_package(REPO_ROOT, wp_id)
        assert wp.work_package_id == wp_id
        assert wp.bounded_files
        assert wp.quality_gates
        assert wp.expected_evidence

    def test_missing_contract_raises(self) -> None:
        with pytest.raises(ContractReferenceError):
            load_work_package(REPO_ROOT, "WP-IMP-9999")

    def test_schema_violation_rejected(self, tmp_path: Path) -> None:
        wpdir = tmp_path / "05-work-packages"
        wpdir.mkdir(parents=True)
        (wpdir / "WP-BAD-0001.yaml").write_text(
            yaml.safe_dump({"schema_version": "WPS-1.0", "work_package_id": "WP-BAD-0001"}),
            encoding="utf-8",
        )
        schemas = tmp_path / "09-validation" / "schemas"
        schemas.mkdir(parents=True)
        real_schema = REPO_ROOT / "09-validation" / "schemas" / "wps-1.0.schema.json"
        (schemas / "wps-1.0.schema.json").write_text(
            real_schema.read_text(encoding="utf-8"), encoding="utf-8"
        )
        with pytest.raises(ManifestValidationError, match="WPS-1.0"):
            load_work_package(tmp_path, "WP-BAD-0001")

    def test_unlocks_and_gates_exposed(self) -> None:
        wp = load_work_package(REPO_ROOT, "WP-IMP-0006")
        assert ("EOS-HEALTH", "1.0") in wp.unlocks
        gate_names = [g[0] for g in wp.quality_gates]
        assert "ruff_lint" in gate_names and "pytest_units" in gate_names


class TestFit005Audit:
    def test_compliant_change_set(self) -> None:
        audit = audit_boundaries(("a.py", "b.py"), ("a.py",))
        assert audit.compliant and audit.violations == ()

    def test_violation_detected(self) -> None:
        audit = audit_boundaries(("a.py",), ("a.py", "sneaky.py"))
        assert not audit.compliant
        assert audit.violations == ("sneaky.py",)

    def test_directory_grant_prefix(self) -> None:
        audit = audit_boundaries(
            ("05-work-packages/WP-IMP-0006/evidence/",),
            ("05-work-packages/WP-IMP-0006/evidence/EXEC-004.yaml",),
        )
        assert audit.compliant

    def test_prefix_does_not_leak_to_siblings(self) -> None:
        audit = audit_boundaries(
            ("05-work-packages/WP-IMP-0006/evidence/",),
            ("05-work-packages/WP-IMP-0007/evidence/EXEC-005.yaml",),
        )
        assert not audit.compliant

    def test_empty_change_set_compliant(self) -> None:
        assert audit_boundaries(("a.py",), ()).compliant


class TestModifiedFiles:
    def test_detects_untracked_file(self, tmp_path: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
             "--allow-empty", "-m", "root"],
            cwd=tmp_path,
            check=True,
        )
        (tmp_path / "new.py").write_text("x = 1\n", encoding="utf-8")
        assert modified_files(tmp_path) == ("new.py",)

    def test_detects_tracked_modification(self, tmp_path: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        (tmp_path / "f.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "c1"],
            cwd=tmp_path,
            check=True,
        )
        (tmp_path / "f.py").write_text("x = 2\n", encoding="utf-8")
        assert modified_files(tmp_path) == ("f.py",)

    def test_git_failure_raises_typed_error(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestValidationError):
            modified_files(tmp_path)  # not a git repository


class TestEvidenceEngine:
    def test_valid_record_written(self, tmp_path: Path) -> None:
        record = minimal_evidence()
        target = tmp_path / "EXEC-999.yaml"
        write_evidence(record, REPO_ROOT, target)
        assert yaml.safe_load(target.read_text(encoding="utf-8")) == record

    def test_invalid_record_refused(self, tmp_path: Path) -> None:
        record = minimal_evidence()
        record["verdict"]["review_status"] = "MAYBE"
        with pytest.raises(ManifestValidationError, match="ERS-1.0"):
            write_evidence(record, REPO_ROOT, tmp_path / "bad.yaml")
        assert not (tmp_path / "bad.yaml").exists()

    def test_missing_required_block_refused(self) -> None:
        record = minimal_evidence()
        del record["boundary_compliance"]
        with pytest.raises(ManifestValidationError):
            validate_evidence(record, REPO_ROOT)

    def test_real_evidence_records_validate(self) -> None:
        for rel in [
            "05-work-packages/WP-IMP-0003/evidence/EXEC-001.yaml",
            "05-work-packages/WP-IMP-0004/evidence/EXEC-002.yaml",
            "05-work-packages/WP-IMP-0005/evidence/EXEC-003.yaml",
        ]:
            record = yaml.safe_load((REPO_ROOT / rel).read_text(encoding="utf-8"))
            validate_evidence(record, REPO_ROOT)


class TestEvidenceCommand:
    def test_missing_wp_halts(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(
            cli, ["evidence", "--wp", "WP-IMP-4242", "--repo-root", str(REPO_ROOT)]
        )
        assert outcome.exit_code == 2
        assert "HALTED" in outcome.output

    def test_audit_runs_against_real_wp(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(
            cli,
            [
                "evidence",
                "--wp",
                "WP-IMP-0003",
                "--base-ref",
                "HEAD",
                "--repo-root",
                str(REPO_ROOT),
            ],
        )
        # Working tree during WP-IMP-0006 contains files outside WP-IMP-0003's
        # bounds, so either verdict is legitimate; the command must not crash.
        assert outcome.exit_code in (0, 3)
        assert "fit_005:" in outcome.output
