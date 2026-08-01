"""Unit tests for the AFRP observability platform.

Tests all collectors, the scoring engine, and dashboard renderers
without running slow subprocess-based checks.
"""

from __future__ import annotations

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
