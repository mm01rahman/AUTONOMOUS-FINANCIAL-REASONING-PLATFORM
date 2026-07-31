"""Unit tests for WP-IMP-0007: afrp health and the traceability analyzer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml
from afrp.cli import cli
from afrp.commands.health import collect_coverage, read_line_coverage
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


def write_full_health_contracts(repo_root: Path) -> None:
    engineering = repo_root / "03-engineering"
    engineering.mkdir(parents=True, exist_ok=True)
    write_matrix(
        engineering / "TRACEABILITY_MATRIX.yaml",
        matrix_doc(
            [
                req(
                    "R-1",
                    "implemented",
                    ["src/a.py"],
                    ["tests/test_a.py"],
                )
            ]
        ),
    )
    (engineering / "CAPABILITY_REGISTRY.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "registry_id": "TCR-HEALTH",
                "capabilities": [
                    {
                        "id": "TEST-CAP",
                        "version": "1.0.0",
                        "title": "Test Capability",
                        "owner": "qa",
                        "status": "COMPLETE",
                        "depends_on": [],
                        "work_package": None,
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


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

    def test_malformed_totals_raise_typed_error(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text(json.dumps({"totals": {}}), encoding="utf-8")
        with pytest.raises(ManifestValidationError, match="percent_covered"):
            read_line_coverage(cov)

    def test_malformed_json_raises_typed_error(self, tmp_path: Path) -> None:
        cov = tmp_path / "coverage.json"
        cov.write_text("{not-json", encoding="utf-8")
        with pytest.raises(ManifestValidationError, match="malformed"):
            read_line_coverage(cov)

    def test_collector_uses_exact_argv_without_shell(self, tmp_path: Path) -> None:
        captured: dict[str, object] = {}

        def runner(
            argv: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            captured["argv"] = argv
            captured.update(kwargs)
            (tmp_path / "coverage.json").write_text(
                json.dumps({"totals": {"percent_covered": 88.0}}),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(argv, 0, "", "")

        assert collect_coverage(tmp_path, runner) == 88.0
        assert captured["argv"] == [
            "uv",
            "run",
            "pytest",
            "tests",
            "--cov",
            "--cov-report=json",
            "-q",
        ]
        assert "shell" not in captured


class TestHealthCommand:
    def test_health_reports_on_real_repository(self) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["health", "--repo-root", str(REPO_ROOT)])
        assert outcome.exit_code == 0, outcome.output
        assert "traceability:" in outcome.output
        assert "capabilities:" in outcome.output
        assert "fit_007:" in outcome.output

    def test_assert_full_uses_fresh_collection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_full_health_contracts(tmp_path)
        calls: list[Path] = []

        def fake_collect(root: Path) -> float:
            calls.append(root)
            return 87.5

        monkeypatch.setattr("afrp.commands.health.collect_coverage", fake_collect)
        runner = CliRunner()
        outcome = runner.invoke(
            cli, ["health", "--repo-root", str(tmp_path), "--assert-full"]
        )
        assert outcome.exit_code == 0, outcome.output
        assert calls == [tmp_path.resolve()]
        assert "test_coverage: 87.5%" in outcome.output

    def test_health_halts_without_matrix(self, tmp_path: Path) -> None:
        runner = CliRunner()
        outcome = runner.invoke(cli, ["health", "--repo-root", str(tmp_path)])
        assert outcome.exit_code == 2
        assert "HALTED" in outcome.output

    def test_absent_coverage_is_collected_in_normal_cli(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_full_health_contracts(tmp_path)
        calls: list[Path] = []

        def fake_collect(root: Path) -> float:
            calls.append(root)
            (root / "coverage.json").write_text(
                json.dumps({"totals": {"percent_covered": 91.25}}),
                encoding="utf-8",
            )
            return 91.25

        monkeypatch.setattr("afrp.commands.health._running_under_pytest", lambda: False)
        monkeypatch.setattr("afrp.commands.health.collect_coverage", fake_collect)
        outcome = CliRunner().invoke(
            cli, ["health", "--repo-root", str(tmp_path), "--assert-full"]
        )
        assert outcome.exit_code == 0, outcome.output
        assert calls == [tmp_path.resolve()]
        assert "test_coverage: 91.2%" in outcome.output

    def test_assert_full_rejects_failed_fresh_collection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        engineering = tmp_path / "03-engineering"
        engineering.mkdir()
        for name in ("TRACEABILITY_MATRIX.yaml", "CAPABILITY_REGISTRY.yaml"):
            (engineering / name).write_text(
                (REPO_ROOT / "03-engineering" / name).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        def fail_collection(root: Path) -> float:
            raise InvariantError("EOS-HEALTH", f"fresh collection failed in {root}")

        monkeypatch.setattr("afrp.commands.health.collect_coverage", fail_collection)
        outcome = CliRunner().invoke(
            cli, ["health", "--repo-root", str(tmp_path), "--assert-full"]
        )
        assert outcome.exit_code == 3
        assert "fresh collection failed" in outcome.output

    def test_assert_full_does_not_reuse_stale_artifact(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        engineering = tmp_path / "03-engineering"
        engineering.mkdir()
        for name in ("TRACEABILITY_MATRIX.yaml", "CAPABILITY_REGISTRY.yaml"):
            (engineering / name).write_text(
                (REPO_ROOT / "03-engineering" / name).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        (tmp_path / "coverage.json").write_text(
            json.dumps({"totals": {"percent_covered": 100.0}}),
            encoding="utf-8",
        )

        def fail_collection(root: Path) -> float:
            raise InvariantError("EOS-HEALTH", f"collector unavailable in {root}")

        monkeypatch.setattr("afrp.commands.health.collect_coverage", fail_collection)
        outcome = CliRunner().invoke(
            cli, ["health", "--repo-root", str(tmp_path), "--assert-full"]
        )
        assert outcome.exit_code == 3
        assert "collector unavailable" in outcome.output
