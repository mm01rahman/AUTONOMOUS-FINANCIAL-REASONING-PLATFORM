"""Regression framework for Phase B (WP-B9)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.verification.math_checks import verify_mathematics
from tools.verification.performance import benchmark_performance
from tools.verification.scenarios import load_scenarios
from tools.verification.statistical import evaluate_statistics
from tools.verification.stress import run_stress_suite
from tools.verification.verifier import verify_runtime


@dataclass(frozen=True)
class RegressionReport:
    scenario_count: int
    runtime_failures: tuple[str, ...]
    math_failures: tuple[str, ...]
    stress_failures: tuple[str, ...]
    performance_passed: bool
    deterministic_passed: bool
    statistical_snapshot: dict[str, float]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_regression_suite(report_path: Path | None = None) -> RegressionReport:
    """Run replay/math/stress/performance/statistical checks."""
    scenarios = load_scenarios()
    runtime = verify_runtime()
    math_report = verify_mathematics()
    stress = run_stress_suite()
    performance = benchmark_performance()
    stats = evaluate_statistics()

    report = RegressionReport(
        scenario_count=len(scenarios),
        runtime_failures=runtime.failures,
        math_failures=math_report.failures,
        stress_failures=stress.failures,
        performance_passed=performance.passed,
        deterministic_passed=runtime.deterministic,
        statistical_snapshot={
            "sharpe_ratio": stats.sharpe_ratio,
            "sortino_ratio": stats.sortino_ratio,
            "max_drawdown": stats.max_drawdown,
            "brier_score": stats.brier_score,
        },
        passed=not runtime.failures
        and not math_report.failures
        and not stress.failures
        and performance.passed,
    )
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
