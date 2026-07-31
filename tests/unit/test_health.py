"""Unit tests for WP-IMP-0007: afrp health and the traceability analyzer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from afrp.cli import cli
from afrp.commands.health import read_line_coverage
from afrp.core.exceptions import (
    ContractReferenceError,
    InvariantError,
    ManifestValidationError,
)
from afrp.core.traceability import assert_full_coverage, load_matrix
from click.testing import CliRunner

REPO_ROOT = Path(__file__).resolve().parents[2]


def req(
    rid: str,
    status: str = "planned",
    artifacts: list[str] | None = None,
    verified: list[str] | None = None,
) -> dict[str, object]:
    return {
        "id": rid,
        "title": f"requirement {rid}",
        "source": "02-architecture/100_SYSTEM_ARCHITECTURE.md#2",
        "capability": "TEST-CAP",
        "status": status,
        "artifacts": artifacts or [],
        "verified_by": verified or [],
    }


def matrix_doc(reqs: list[dict[str, object]]) -> dict[str, object]:
    return {"schema_version": "1.0", "matrix_id": "TVM-001", "requirements": reqs}


def write_matrix(path: Path, doc: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


class TestMatrixParser:
    def test_parses_real_matrix(self) -> None:
        matrix = load_matrix(REPO_ROOT / "03-engineering" / "TRACEABILITY_MATRIX.yaml")
        ids = {r.id for r in matrix.requirements}
        assert {"FR-001", "NFR-001", "FIT-007", "EDR-002"} <= ids
        assert 0.0 < matrix.coverage_ratio <= 1.0

    def test_missing_matrix_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ContractReferenceError):
            load_matrix(tmp_path / "absent.yaml")

    def test_duplicate_requirement_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(target, matrix_doc([req("R-1"), req("R-1")]))
        with pytest.raises(ManifestValidationError, match="duplicate"):
            load_matrix(target)

    def test_unknown_status_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(target, matrix_doc([req("R-1", status="wishful")]))
        with pytest.raises(ManifestValidationError):
            load_matrix(target)

    def test_drift_guard_implemented_without_evidence(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(target, matrix_doc([req("R-1", status="implemented")]))
        with pytest.raises(ManifestValidationError, match="drift"):
            load_matrix(target)


class TestFit007Coverage:
    def test_full_coverage_passes(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(
            target,
            matrix_doc(
                [req("R-1", "implemented", ["src/a.py"], ["tests/test_a.py"])]
            ),
        )
        matrix = load_matrix(target)
        assert matrix.coverage_ratio == 1.0
        assert_full_coverage(matrix)  # must not raise

    def test_partial_coverage_ratio(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(
            target,
            matrix_doc(
                [
                    req("R-1", "implemented", ["src/a.py"], ["tests/test_a.py"]),
                    req("R-2"),
                    req("R-3"),
                    req("R-4"),
                ]
            ),
        )
        matrix = load_matrix(target)
        assert matrix.coverage_ratio == 0.25

    def test_assert_full_coverage_names_gaps(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(
            target,
            matrix_doc(
                [
                    req("R-1", "implemented", ["src/a.py"], ["tests/test_a.py"]),
                    req("R-GAP"),
                ]
            ),
        )
        with pytest.raises(InvariantError) as excinfo:
            assert_full_coverage(load_matrix(target))
        assert excinfo.value.invariant == "FIT-007"
        assert "R-GAP" in excinfo.value.detail

    def test_artifact_without_verification_uncovered(self, tmp_path: Path) -> None:
        target = tmp_path / "tvm.yaml"
        write_matrix(target, matrix_doc([req("R-1", "planned", ["src/a.py"], [])]))
        matrix = load_matrix(target)
        assert matrix.coverage_ratio == 0.0


class TestLineCoverage:
    def test_reads_pytest_cov_totals(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"totals": {"percent_covered": 93.4}}), encoding="utf-8")
        assert read_line_coverage(cov) == pytest.approx(93.4)

    def test_missing_file_yields_none(self, tmp_path: Path) -> None:
        assert read_line_coverage(tmp_path / "coverage.json") is None

    def test_malformed_totals_yield_none(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"totals": {}}), encoding="utf-8")
        assert read_line_coverage(cov) is None


class TestHealthCommand:
    def test_health_reports_on_real_repository(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["health", "--repo-root", str(REPO_ROOT)])
        assert outcome.exit_code == 0, outcome.output
        assert "traceability:" in outcome.output
        assert "capabilities:" in outcome.output
        assert "fit_007:" in outcome.output

    def test_assert_full_fails_while_build_incomplete(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(
            cli, ["health", "--repo-root", str(REPO_ROOT), "--assert-full"]
        )
        # During the build TVM is intentionally not yet 100%; flag must gate.
        matrix = load_matrix(REPO_ROOT / "03-engineering" / "TRACEABILITY_MATRIX.yaml")
        if matrix.coverage_ratio == 1.0:
            assert outcome.exit_code == 0
        else:
            assert outcome.exit_code == 3
            assert "FIT-007" in outcome.output

    def test_health_halts_without_matrix(self, tmp_path: Path) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["health", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 2
        assert "HALTED" in outcome.output
