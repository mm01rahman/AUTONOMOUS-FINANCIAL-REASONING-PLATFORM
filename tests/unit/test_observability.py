"""Unit tests for the AFRP observability platform.

Tests all collectors, the scoring engine, and dashboard renderers
without running slow subprocess-based checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).parent.parent.parent


# ── Repository collector ───────────────────────────────────────────────────


class TestRepositoryCollector:
    def test_collect_capabilities_real_registry(self) -> None:
        from tools.observability.collectors.repository import collect_capabilities

        m = collect_capabilities(_REPO_ROOT)
        assert m.total >= 30, f"Expected >=30 capabilities, got {m.total}"
        assert m.complete >= 20, f"Expected >=20 complete, got {m.complete}"
        assert 0 <= m.completion_pct <= 100
        assert m.eos_total > 0
        assert m.eos_complete > 0
        assert m.eos_completion_pct > 0

    def test_collect_capabilities_missing_file(self, tmp_path: Path) -> None:
        from tools.observability.collectors.repository import collect_capabilities

        m = collect_capabilities(tmp_path)
        assert m.total == 0
        assert m.completion_pct == 0.0

    def test_collect_capabilities_layer_breakdown(self) -> None:
        from tools.observability.collectors.repository import collect_capabilities

        m = collect_capabilities(_REPO_ROOT)
        # Runtime layers should appear in layer breakdown
        assert len(m.layers) >= 1

    def test_collect_work_packages(self) -> None:
        from tools.observability.collectors.repository import collect_work_packages

        m = collect_work_packages(_REPO_ROOT)
        assert m.total >= 30
        assert m.completed >= 20
        assert 0 <= m.burn_pct <= 100

    def test_collect_work_packages_missing_dir(self, tmp_path: Path) -> None:
        from tools.observability.collectors.repository import collect_work_packages

        m = collect_work_packages(tmp_path)
        assert m.total == 0
        assert m.burn_pct == 0.0

    def test_to_dict_shape(self) -> None:
        from tools.observability.collectors.repository import collect_capabilities

        d = collect_capabilities(_REPO_ROOT).to_dict()
        assert "total" in d
        assert "complete" in d
        assert "completion_pct" in d
        assert "eos" in d
        assert "runtime" in d


# ── Quality collector ──────────────────────────────────────────────────────


class TestQualityCollector:
    def test_collect_coverage_from_file(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_coverage

        cov_data = {
            "totals": {
                "percent_covered": 87.5,
                "covered_lines": 3537,
                "num_statements": 4042,
                "covered_branches": 883,
                "num_branches": 1132,
            },
            "files": {"a.py": {}, "b.py": {}},
        }
        import json

        (tmp_path / "coverage.json").write_text(json.dumps(cov_data))
        m = collect_coverage(tmp_path)
        assert m.available
        assert m.line_pct == 87.5
        assert m.lines_covered == 3537
        assert m.files_measured == 2

    def test_collect_coverage_missing(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_coverage

        m = collect_coverage(tmp_path)
        assert not m.available
        assert m.line_pct == 0.0

    def test_ruff_metrics_pass(self) -> None:
        from tools.observability.collectors.quality import RuffMetrics

        m = RuffMetrics(status="PASS", violations=0)
        d = m.to_dict()
        assert d["status"] == "PASS"
        assert d["violations"] == 0

    def test_mypy_metrics_structure(self) -> None:
        from tools.observability.collectors.quality import MypyMetrics

        m = MypyMetrics(status="PASS", errors=0, files_checked=99)
        d = m.to_dict()
        assert d["status"] == "PASS"
        assert d["files_checked"] == 99

    def test_test_metrics_pass_rate(self) -> None:
        from tools.observability.collectors.quality import TestMetrics

        m = TestMetrics(status="PASS", collected=460, passed=460)
        assert m.pass_rate == 100.0

    def test_test_metrics_zero_collected(self) -> None:
        from tools.observability.collectors.quality import TestMetrics

        m = TestMetrics()
        assert m.pass_rate == 0.0

    def test_coverage_to_dict(self, tmp_path: Path) -> None:
        import json

        from tools.observability.collectors.quality import collect_coverage

        cov_data = {
            "totals": {
                "percent_covered": 87.2,
                "covered_lines": 3537,
                "num_statements": 3937,
                "covered_branches": 883,
                "num_branches": 1132,
            },
            "files": {},
        }
        (tmp_path / "coverage.json").write_text(json.dumps(cov_data))
        m = collect_coverage(tmp_path)
        d = m.to_dict()
        assert d["available"] is True
        assert d["line_pct"] == 87.2


# ── Governance collector ───────────────────────────────────────────────────


class TestGovernanceCollector:
    def test_collect_governance_real_repo(self) -> None:
        from tools.observability.collectors.governance import collect_governance

        m = collect_governance(_REPO_ROOT)
        assert m.wps_total >= 30
        assert m.wps_completed >= 20
        assert m.tvm_requirements_total >= 40
        assert m.tvm_requirements_implemented >= 40
        assert m.tvm_coverage_pct >= 90.0
        assert m.ers_total >= 20
        assert m.ers_approved >= 20

    def test_governance_to_dict_shape(self) -> None:
        from tools.observability.collectors.governance import collect_governance

        d = collect_governance(_REPO_ROOT).to_dict()
        assert "work_packages" in d
        assert "evidence_records" in d
        assert "traceability" in d
        assert "adrs" in d

    def test_governance_empty_repo(self, tmp_path: Path) -> None:
        from tools.observability.collectors.governance import collect_governance

        m = collect_governance(tmp_path)
        assert m.wps_total == 0
        assert m.tvm_requirements_total == 0


# ── Security collector ─────────────────────────────────────────────────────


class TestSecurityCollector:
    def test_security_detects_precommit(self) -> None:
        from tools.observability.collectors.security import collect_security

        m = collect_security(_REPO_ROOT)
        assert m.secret_scan_status in ("CONFIGURED", "PARTIAL", "NOT_CONFIGURED")

    def test_security_detects_codeql(self) -> None:
        from tools.observability.collectors.security import collect_security

        m = collect_security(_REPO_ROOT)
        assert m.codeql_status in ("CONFIGURED", "NOT_CONFIGURED")

    def test_security_to_dict(self) -> None:
        from tools.observability.collectors.security import collect_security

        d = collect_security(_REPO_ROOT).to_dict()
        assert "bandit" in d
        assert "dependencies" in d
        assert "secret_scan" in d
        assert "codeql" in d

    def test_bandit_report_parsing(self, tmp_path: Path) -> None:
        import json

        from tools.observability.collectors.security import _load_bandit_report

        report = {
            "results": [
                {"issue_severity": "HIGH", "issue_text": "test"},
                {"issue_severity": "MEDIUM", "issue_text": "test"},
                {"issue_severity": "LOW", "issue_text": "test"},
            ]
        }
        p = tmp_path / "bandit.json"
        p.write_text(json.dumps(report))
        m = _load_bandit_report(p)
        assert m.available
        assert m.high_severity == 1
        assert m.medium_severity == 1
        assert m.low_severity == 1
        assert m.status == "FAIL"

    def test_bandit_pass_no_high(self, tmp_path: Path) -> None:
        import json

        from tools.observability.collectors.security import _load_bandit_report

        report = {"results": [{"issue_severity": "LOW", "issue_text": "test"}]}
        p = tmp_path / "bandit.json"
        p.write_text(json.dumps(report))
        m = _load_bandit_report(p)
        assert m.status == "PASS"
        assert m.high_severity == 0


# ── Release collector ──────────────────────────────────────────────────────


class TestReleaseCollector:
    def test_collect_release_real_repo(self) -> None:
        from tools.observability.collectors.release import collect_release

        m = collect_release(_REPO_ROOT)
        assert m.completion_reports >= 1
        assert m.evidence_records >= 1
        assert 0 <= m.readiness_score <= 100

    def test_release_to_dict_shape(self) -> None:
        from tools.observability.collectors.release import collect_release

        d = collect_release(_REPO_ROOT).to_dict()
        assert "tags" in d
        assert "evidence" in d
        assert "readiness" in d


# ── Git collector ──────────────────────────────────────────────────────────


class TestGitCollector:
    def test_collect_git_real_repo(self) -> None:
        from tools.observability.collectors.git_metrics import collect_git

        m = collect_git(_REPO_ROOT)
        assert m.total_commits > 0
        assert m.tracked_files > 0
        assert m.python_files > 0
        assert m.current_branch != ""

    def test_git_to_dict_shape(self) -> None:
        from tools.observability.collectors.git_metrics import collect_git

        d = collect_git(_REPO_ROOT).to_dict()
        assert "commits" in d
        assert "branch" in d
        assert "files" in d


# ── Snapshot ──────────────────────────────────────────────────────────────


class TestMetricsSnapshot:
    def test_collect_all_fast_mode(self) -> None:
        from tools.observability.snapshot import collect_all

        snap = collect_all(
            _REPO_ROOT,
            skip_quality_checks=True,
            skip_architecture_checks=True,
        )
        assert snap.generated_at != ""
        assert snap.repository.total > 0
        assert snap.governance.tvm_requirements_total > 0
        assert snap.quality.ruff.status == "SKIPPED"
        assert snap.quality.mypy.status == "SKIPPED"
        assert snap.quality.tests.status == "SKIPPED"

    def test_snapshot_to_dict_schema(self) -> None:
        from tools.observability.snapshot import collect_all

        snap = collect_all(
            _REPO_ROOT,
            skip_quality_checks=True,
            skip_architecture_checks=True,
        )
        d = snap.to_dict()
        assert d["schema_version"] == "2.0"
        assert "metrics" in d
        assert "repository" in d["metrics"]
        assert "quality" in d["metrics"]
        assert "governance" in d["metrics"]


# ── Scoring engine ─────────────────────────────────────────────────────────


class TestHealthScoring:
    def test_grade_from_score(self) -> None:
        from tools.observability.scoring import HealthGrade

        assert HealthGrade.from_score(0.97) == HealthGrade.A_PLUS
        assert HealthGrade.from_score(0.87) == HealthGrade.A
        assert HealthGrade.from_score(0.72) == HealthGrade.B
        assert HealthGrade.from_score(0.57) == HealthGrade.C
        assert HealthGrade.from_score(0.40) == HealthGrade.D

    def test_compute_health_score_fast(self) -> None:
        from tools.observability.scoring import compute_health_score
        from tools.observability.snapshot import collect_all

        snap = collect_all(
            _REPO_ROOT,
            skip_quality_checks=True,
            skip_architecture_checks=True,
        )
        score = compute_health_score(snap)
        assert 0.0 <= score.total <= 1.0
        assert score.grade.value in ("A+", "A", "B", "C", "D")
        assert len(score.dimensions) > 0

    def test_score_to_dict(self) -> None:
        from tools.observability.scoring import compute_health_score
        from tools.observability.snapshot import collect_all

        snap = collect_all(
            _REPO_ROOT,
            skip_quality_checks=True,
            skip_architecture_checks=True,
        )
        d = compute_health_score(snap).to_dict()
        assert "score" in d
        assert "grade" in d
        assert "dimensions" in d

    def test_dimension_weights_sum_to_one(self) -> None:
        from tools.observability.scoring import compute_health_score
        from tools.observability.snapshot import collect_all

        snap = collect_all(
            _REPO_ROOT,
            skip_quality_checks=True,
            skip_architecture_checks=True,
        )
        score = compute_health_score(snap)
        total_weight = sum(d.weight for d in score.dimensions)
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight:.3f}"


# ── Dashboard renderers ────────────────────────────────────────────────────


class TestDashboardRenderers:
    def _make_snap_and_score(self) -> tuple[object, object]:
        from tools.observability.scoring import compute_health_score
        from tools.observability.snapshot import collect_all

        snap = collect_all(
            _REPO_ROOT,
            skip_quality_checks=True,
            skip_architecture_checks=True,
        )
        score = compute_health_score(snap)
        return snap, score

    def test_render_markdown_has_sections(self) -> None:
        from tools.observability.dashboard import render_markdown

        snap, score = self._make_snap_and_score()
        md = render_markdown(snap, score)  # type: ignore[arg-type]
        assert "Repository Dashboard" in md
        assert "Repository Progress" in md
        assert "Code Quality" in md
        assert "Architecture" in md
        assert "Governance" in md
        assert "Security" in md
        assert "Release" in md
        assert "Git Metrics" in md

    def test_render_github_summary_is_concise(self) -> None:
        from tools.observability.dashboard import render_github_summary

        snap, score = self._make_snap_and_score()
        summary = render_github_summary(snap, score)  # type: ignore[arg-type]
        assert "AFRP Repository Health" in summary
        assert len(summary) < 5000  # must be concise

    def test_render_html_is_valid(self) -> None:
        from tools.observability.dashboard import render_html

        snap, score = self._make_snap_and_score()
        htm = render_html(snap, score)  # type: ignore[arg-type]
        assert "<!DOCTYPE html>" in htm
        assert "AFRP Engineering Dashboard" in htm
        assert "</html>" in htm

    def test_publish_to_github_summary_noop_without_env(self) -> None:
        from tools.observability.dashboard import publish_to_github_summary

        # Should not raise when GITHUB_STEP_SUMMARY is not set
        publish_to_github_summary("test content")

    def test_publish_to_github_summary_writes_file(self, tmp_path: Path) -> None:
        from tools.observability.dashboard import publish_to_github_summary

        summary_file = tmp_path / "step_summary.md"
        with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            publish_to_github_summary("## Test")
        assert summary_file.read_text() == "## Test\n"


# ── Quality collector (subprocess paths) ──────────────────────────────────


class TestQualityCollectorSubprocess:
    def test_collect_ruff_pass(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_ruff

        with patch(
            "tools.observability.collectors.quality._run", return_value=(0, "")
        ):
            m = collect_ruff(tmp_path)
        assert m.status == "PASS"
        assert m.violations == 0

    def test_collect_ruff_fail_with_json(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_ruff

        findings = [
            {"code": "E501", "fix": None},
            {"code": "F401", "fix": {"message": "Remove import"}},
        ]
        with patch(
            "tools.observability.collectors.quality._run",
            return_value=(1, json.dumps(findings)),
        ):
            m = collect_ruff(tmp_path)
        assert m.status == "FAIL"
        assert m.violations == 2
        assert m.fixable == 1
        assert len(m.error_types) > 0

    def test_collect_ruff_fail_non_json(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_ruff

        # Output starts with "[" so JSON parse is attempted, but is malformed
        # → triggers the regex fallback line-counter
        out = (
            "[\nnot valid json\n"
            "tools/foo.py:10:1: E501 line too long\n"
            "tools/bar.py:5:1: F401 unused"
        )
        with patch(
            "tools.observability.collectors.quality._run", return_value=(1, out)
        ):
            m = collect_ruff(tmp_path)
        assert m.status == "FAIL"
        assert m.violations == 2

    def test_collect_mypy_pass(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_mypy

        out = "Success: no issues found in 42 source files"
        with patch(
            "tools.observability.collectors.quality._run", return_value=(0, out)
        ):
            m = collect_mypy(tmp_path)
        assert m.status == "PASS"
        assert m.files_checked == 42

    def test_collect_mypy_fail(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_mypy

        out = (
            "tools/foo.py:1: error: oops\n"
            "tools/foo.py:2: warning: note\n"
            "tools/foo.py:3: note: suggestion\n"
            "Found 1 error in 1 file (checked 10 source files)\n"
        )
        with patch(
            "tools.observability.collectors.quality._run", return_value=(1, out)
        ):
            m = collect_mypy(tmp_path)
        assert m.status == "FAIL"
        assert m.errors == 1
        assert m.warnings == 1
        assert m.notes == 1
        assert m.files_checked == 1  # regex captures file count from "in 1 file"

    def test_collect_coverage_invalid_json(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_coverage

        (tmp_path / "coverage.json").write_text("{invalid}")
        m = collect_coverage(tmp_path)
        assert not m.available

    def test_collect_coverage_branch_pct(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_coverage

        data = {
            "totals": {
                "percent_covered": 82.0,
                "covered_lines": 820,
                "num_statements": 1000,
                "covered_branches": 200,
                "num_branches": 250,
            },
            "files": {"a.py": {}, "b.py": {}},
        }
        (tmp_path / "coverage.json").write_text(json.dumps(data))
        m = collect_coverage(tmp_path)
        assert m.available
        assert m.branch_pct == 80.0

    def test_collect_tests_pass(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_tests

        out = "462 passed, 1 failed, 3 skipped in 8.21s"
        with patch(
            "tools.observability.collectors.quality._run", return_value=(0, out)
        ):
            m = collect_tests(tmp_path)
        assert m.status == "PASS"
        assert m.passed == 462
        assert m.failed == 1
        assert m.skipped == 3
        assert m.collected == 466

    def test_collect_tests_with_errors(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import collect_tests

        out = "10 passed, 2 errors in 1.23s"
        with patch(
            "tools.observability.collectors.quality._run", return_value=(1, out)
        ):
            m = collect_tests(tmp_path)
        assert m.status == "FAIL"
        assert m.errors == 2

    def test_run_oserror(self, tmp_path: Path) -> None:
        from tools.observability.collectors.quality import _run

        with patch("subprocess.run", side_effect=OSError("no such file")):
            rc, out = _run(["nonexistent-command"], tmp_path)
        assert rc == 1
        assert "no such file" in out


# ── Security collector (extended paths) ──────────────────────────────────


class TestSecurityCollectorExtended:
    def test_load_pip_audit_no_vulns(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import _load_pip_audit_report

        data = [{"name": "requests", "version": "2.28.0", "vulns": []}]
        p = tmp_path / "pip-audit.json"
        p.write_text(json.dumps(data))
        m = _load_pip_audit_report(p)
        assert m.available
        assert m.status == "PASS"
        assert m.total_vulnerabilities == 0

    def test_load_pip_audit_with_vulns(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import _load_pip_audit_report

        data = [
            {
                "name": "vulnerable-pkg",
                "version": "1.0.0",
                "vulns": [{"id": "CVE-2024-0001"}, {"id": "CVE-2024-0002"}],
            }
        ]
        p = tmp_path / "pip-audit.json"
        p.write_text(json.dumps(data))
        m = _load_pip_audit_report(p)
        assert m.status == "FAIL"
        assert m.total_vulnerabilities == 2
        assert "vulnerable-pkg" in m.affected_packages

    def test_load_pip_audit_dict_format(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import _load_pip_audit_report

        data = {
            "dependencies": [
                {"name": "pkg-a", "version": "0.1", "vulns": []},
            ]
        }
        p = tmp_path / "pip-audit.json"
        p.write_text(json.dumps(data))
        m = _load_pip_audit_report(p)
        assert m.status == "PASS"

    def test_load_pip_audit_invalid(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import _load_pip_audit_report

        p = tmp_path / "pip-audit.json"
        p.write_text("{invalid json}")
        m = _load_pip_audit_report(p)
        assert not m.available
        assert m.status == "UNAVAILABLE"

    def test_collect_security_with_bandit_file(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import collect_security

        (tmp_path / "bandit-report.json").write_text(json.dumps({"results": []}))
        m = collect_security(tmp_path)
        assert m.bandit.status == "PASS"

    def test_collect_security_with_audit_file(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import collect_security

        (tmp_path / "pip-audit-report.json").write_text(json.dumps([]))
        m = collect_security(tmp_path)
        assert m.dependencies.status == "PASS"

    def test_collect_security_partial_precommit(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import collect_security

        (tmp_path / ".pre-commit-config.yaml").write_text("repos: []")
        m = collect_security(tmp_path)
        assert m.secret_scan_status == "PARTIAL"

    def test_collect_security_configured_codeql(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import collect_security

        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "security.yml").write_text("name: security")
        codeql_dir = tmp_path / ".github" / "codeql"
        codeql_dir.mkdir()
        (codeql_dir / "codeql-config.yml").write_text("name: codeql")
        m = collect_security(tmp_path)
        assert m.codeql_status == "CONFIGURED"

    def test_collect_security_overall_fail(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import collect_security

        report = {
            "results": [{"issue_severity": "HIGH", "issue_text": "bad"}]
        }
        (tmp_path / "bandit-report.json").write_text(json.dumps(report))
        m = collect_security(tmp_path)
        assert m.overall_status == "FAIL"

    def test_collect_security_overall_pass(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import collect_security

        (tmp_path / "bandit-report.json").write_text(json.dumps({"results": []}))
        m = collect_security(tmp_path)
        assert m.overall_status == "PASS"

    def test_load_bandit_error_handling(self, tmp_path: Path) -> None:
        from tools.observability.collectors.security import _load_bandit_report

        p = tmp_path / "bandit.json"
        p.write_text("{not valid}")
        m = _load_bandit_report(p)
        assert not m.available
        assert m.status == "UNAVAILABLE"


# ── Architecture collector ─────────────────────────────────────────────────


class TestArchitectureCollector:
    def test_parse_fit_result_pass(self) -> None:
        from tools.observability.collectors.architecture import _parse_fit_result

        result = _parse_fit_result("FIT-002 PASS: no violations found", "FIT-002")
        assert result.status == "PASS"

    def test_parse_fit_result_fail(self) -> None:
        from tools.observability.collectors.architecture import _parse_fit_result

        result = _parse_fit_result("FIT-002 FAIL: 3 violations", "FIT-002")
        assert result.status == "FAIL"

    def test_parse_fit_result_unknown(self) -> None:
        from tools.observability.collectors.architecture import _parse_fit_result

        result = _parse_fit_result("no relevant output", "FIT-002")
        assert result.status == "UNKNOWN"

    def test_collect_architecture_all_pass(self, tmp_path: Path) -> None:
        from tools.observability.collectors.architecture import collect_architecture

        outputs = [
            (0, "FIT-002 PASS\nFIT-004 PASS\nFIT-006 PASS"),
            (0, ""),
            (0, "FIT-003 PASS"),
            (0, "violations: 0"),
            (0, "FIT-001 PASS dag ok"),
        ]
        with patch(
            "tools.observability.collectors.architecture._run", side_effect=outputs
        ):
            m = collect_architecture(tmp_path)
        assert m.baseline_gate_status == "PASS"
        assert m.ops_gate_status == "PASS"
        assert m.proto_gate_status == "PASS"
        assert m.validate_status == "PASS"
        assert m.plan_status == "PASS"
        assert m.dag_acyclic is True
        assert m.violations == 0
        assert m.fit_pass >= 4

    def test_collect_architecture_failures(self, tmp_path: Path) -> None:
        from tools.observability.collectors.architecture import collect_architecture

        outputs = [
            (1, "FIT-002 FAIL: import cycle\nFIT-004 PASS\nFIT-006 FAIL"),
            (1, "ops gate failed"),
            (1, "FIT-003 FAIL"),
            (1, "found 2 violations in layer boundary"),
            (1, "FIT-001 FAIL: cycle detected"),
        ]
        with patch(
            "tools.observability.collectors.architecture._run", side_effect=outputs
        ):
            m = collect_architecture(tmp_path)
        assert m.baseline_gate_status == "FAIL"
        assert m.plan_status == "FAIL"
        assert m.dag_acyclic is False
        assert m.fit_fail >= 3
        assert m.violations >= 1

    def test_collect_architecture_violation_count(self, tmp_path: Path) -> None:
        from tools.observability.collectors.architecture import collect_architecture

        outputs = [
            (0, "FIT-002 PASS\nFIT-004 PASS\nFIT-006 PASS"),
            (0, ""),
            (0, "FIT-003 PASS"),
            (0, "found 5 violations in boundary check"),
            (0, "FIT-001 PASS"),
        ]
        with patch(
            "tools.observability.collectors.architecture._run", side_effect=outputs
        ):
            m = collect_architecture(tmp_path)
        assert m.layer_violations == 5

    def test_architecture_run_oserror(self, tmp_path: Path) -> None:
        from tools.observability.collectors.architecture import _run

        with patch("subprocess.run", side_effect=OSError("not found")):
            rc, out = _run(["bad-cmd"], tmp_path)
        assert rc == 1
        assert "not found" in out

    def test_architecture_metrics_overall_status(self) -> None:
        from tools.observability.collectors.architecture import ArchitectureMetrics

        m = ArchitectureMetrics(fit_pass=3, fit_fail=0, violations=0)
        assert m.overall_status == "PASS"
        m2 = ArchitectureMetrics(fit_pass=0, fit_fail=1, violations=1)
        assert m2.overall_status == "FAIL"
        m3 = ArchitectureMetrics()
        assert m3.overall_status == "UNKNOWN"


# ── Dashboard CLI ──────────────────────────────────────────────────────────


class TestDashboardCLI:
    def test_cli_help(self) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "dashboard" in result.output.lower() or "format" in result.output.lower()

    def test_cli_fast_markdown_stdout(self) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "markdown",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
            ],
        )
        assert result.exit_code == 0
        assert "Repository" in result.output or "Health" in result.output

    def test_cli_fast_json_stdout(self) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "json",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
            ],
        )
        assert result.exit_code == 0
        # Verify JSON content is present in output
        assert '"metrics"' in result.output
        assert '"health"' in result.output

    def test_cli_fast_summary_stdout(self) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "summary",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
            ],
        )
        assert result.exit_code == 0

    def test_cli_fast_html_stdout(self) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "html",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
            ],
        )
        assert result.exit_code == 0
        assert "<!DOCTYPE html>" in result.output

    def test_cli_fast_all_output_dir(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "all",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
                "--output-dir",
                str(tmp_path / "reports"),
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "reports" / "dashboard.md").exists()
        assert (tmp_path / "reports" / "metrics.json").exists()

    def test_cli_threshold_pass(self) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "json",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
                "--threshold",
                "0.0",
            ],
        )
        assert result.exit_code == 0

    def test_cli_github_summary_flag(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        summary_file = tmp_path / "summary.md"
        runner = CliRunner(env={"GITHUB_STEP_SUMMARY": str(summary_file)})
        result = runner.invoke(
            main,
            [
                "--format",
                "json",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
                "--github-summary",
            ],
        )
        assert result.exit_code == 0
        assert summary_file.exists()

    def test_cli_markdown_to_file(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        out_file = tmp_path / "dashboard.md"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "markdown",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()

    def test_cli_html_to_file(self, tmp_path: Path) -> None:
        from click.testing import CliRunner

        from tools.dashboard import main

        out_file = tmp_path / "dashboard.html"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--format",
                "html",
                "--fast",
                "--repo-root",
                str(_REPO_ROOT),
                "--output",
                str(out_file),
            ],
        )
        assert result.exit_code == 0
        assert out_file.exists()
