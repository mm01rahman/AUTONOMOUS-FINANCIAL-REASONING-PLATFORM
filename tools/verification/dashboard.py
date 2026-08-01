"""Validation dashboard renderers (WP-B10)."""

from __future__ import annotations

import html
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.verification.math_checks import MathVerificationReport
from tools.verification.performance import PerformanceReport
from tools.verification.regression import RegressionReport
from tools.verification.statistical import StatisticalReport
from tools.verification.stress import StressSuiteReport
from tools.verification.verifier import RuntimeVerificationReport


@dataclass(frozen=True)
class ValidationBundle:
    generated_at: str
    runtime: RuntimeVerificationReport
    mathematics: MathVerificationReport
    stress: StressSuiteReport
    performance: PerformanceReport
    statistics: StatisticalReport
    regression: RegressionReport

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def render_json(bundle: ValidationBundle) -> str:
    return json.dumps(bundle.to_dict(), indent=2)


def render_markdown(bundle: ValidationBundle) -> str:
    runtime_pass = "PASS" if not bundle.runtime.failures else "FAIL"
    math_pass = "PASS" if not bundle.mathematics.failures else "FAIL"
    stress_pass = "PASS" if not bundle.stress.failures else "FAIL"
    perf_pass = "PASS" if bundle.performance.passed else "FAIL"
    reg_pass = "PASS" if bundle.regression.passed else "FAIL"
    lines = [
        "# AFRP Phase B Validation Dashboard",
        "",
        f"Generated at: `{bundle.generated_at}`",
        "",
        "| Component | Result | Key Detail |",
        "|---|---|---|",
        (
            f"| Runtime Verification | {runtime_pass} | "
            f"checksum `{bundle.runtime.replay_checksum[:12]}` |"
        ),
        f"| Mathematical Verification | {math_pass} | checks={len(bundle.mathematics.checks)} |",
        f"| Stress Suite | {stress_pass} | cases={len(bundle.stress.cases)} |",
        f"| Performance Suite | {perf_pass} | p99={bundle.performance.decision_p99_ms:.4f}ms |",
        f"| Regression Suite | {reg_pass} | scenarios={bundle.regression.scenario_count} |",
        "",
        "## Statistical Evaluation",
        "",
        f"- Sharpe: `{bundle.statistics.sharpe_ratio:.6f}`",
        f"- Sortino: `{bundle.statistics.sortino_ratio:.6f}`",
        f"- Calmar: `{bundle.statistics.calmar_ratio:.6f}`",
        f"- Max Drawdown: `{bundle.statistics.max_drawdown:.6f}`",
        f"- Win Rate: `{bundle.statistics.win_rate:.6f}`",
        f"- Brier Score: `{bundle.statistics.brier_score:.6f}`",
    ]
    return "\n".join(lines) + "\n"


def render_html(bundle: ValidationBundle) -> str:
    md = render_markdown(bundle)
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>AFRP Phase B Dashboard</title></head>"
        "<body><pre>"
        + html.escape(md)
        + "</pre></body></html>"
    )


def publish_github_summary(markdown: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not path:
        return
    Path(path).write_text(markdown, encoding="utf-8")


def build_bundle(
    runtime: RuntimeVerificationReport,
    mathematics: MathVerificationReport,
    stress: StressSuiteReport,
    performance: PerformanceReport,
    statistics: StatisticalReport,
    regression: RegressionReport,
) -> ValidationBundle:
    return ValidationBundle(
        generated_at=datetime.now(tz=UTC).isoformat(),
        runtime=runtime,
        mathematics=mathematics,
        stress=stress,
        performance=performance,
        statistics=statistics,
        regression=regression,
    )
