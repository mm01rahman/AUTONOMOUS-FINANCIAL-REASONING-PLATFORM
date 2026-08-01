from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.verification.dashboard import build_bundle, render_json, render_markdown
from tools.verification.math_checks import verify_mathematics
from tools.verification.performance import benchmark_performance
from tools.verification.regression import run_regression_suite
from tools.verification.scenarios import REQUIRED_SCENARIO_IDS, load_scenarios
from tools.verification.statistical import evaluate_statistics
from tools.verification.stress import run_stress_suite
from tools.verification.verifier import verify_runtime


@pytest.fixture(autouse=True)
def _audit_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRP_AUDIT_HMAC_KEY", "phaseb-test-key")


def test_scenario_library_contains_required_ids() -> None:
    scenarios = load_scenarios()
    found = {scenario.scenario_id for scenario in scenarios}
    for required in REQUIRED_SCENARIO_IDS:
        assert required in found
    assert len(scenarios) >= len(REQUIRED_SCENARIO_IDS)


def test_runtime_verification_is_deterministic() -> None:
    report = verify_runtime()
    assert report.deterministic
    assert report.replay_checksum == report.expected_checksum
    assert report.failures == ()


def test_math_verification_has_no_failures() -> None:
    report = verify_mathematics()
    assert report.failures == ()
    assert len(report.checks) >= 5


def test_statistical_report_shape() -> None:
    report = evaluate_statistics()
    assert report.max_drawdown >= 0.0
    assert 0.0 <= report.win_rate <= 1.0


def test_stress_suite_passes() -> None:
    report = run_stress_suite()
    assert report.failures == ()
    assert len(report.cases) >= 4


def test_performance_report_meets_budget() -> None:
    report = benchmark_performance()
    assert report.passed
    assert report.decision_p99_ms <= 50.0


def test_regression_suite_passes() -> None:
    report = run_regression_suite()
    assert report.passed
    assert report.scenario_count >= len(REQUIRED_SCENARIO_IDS)


def test_dashboard_renderers() -> None:
    runtime = verify_runtime()
    math = verify_mathematics()
    stress = run_stress_suite()
    perf = benchmark_performance()
    stats = evaluate_statistics()
    reg = run_regression_suite()
    bundle = build_bundle(runtime, math, stress, perf, stats, reg)
    rendered_json = render_json(bundle)
    rendered_md = render_markdown(bundle)
    parsed = json.loads(rendered_json)
    assert "runtime" in parsed
    assert "statistics" in parsed
    assert "AFRP Phase B Validation Dashboard" in rendered_md


def test_report_file_outputs(tmp_path: Path) -> None:
    runtime = verify_runtime(tmp_path / "runtime.json")
    math = verify_mathematics(tmp_path / "math.json")
    stress = run_stress_suite(tmp_path / "stress.json")
    perf = benchmark_performance(tmp_path / "perf.json")
    stats = evaluate_statistics(tmp_path / "stats.json")
    reg = run_regression_suite(tmp_path / "reg.json")
    assert runtime.replay_checksum
    assert math.failures == ()
    assert stress.failures == ()
    assert perf.passed
    assert stats.sharpe_ratio == stats.sharpe_ratio
    assert reg.passed
    for name in ("runtime.json", "math.json", "stress.json", "perf.json", "stats.json", "reg.json"):
        assert (tmp_path / name).exists()
