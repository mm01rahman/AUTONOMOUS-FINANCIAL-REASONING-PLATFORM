"""Statistical evaluation framework (WP-B6)."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools import system_gate


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def _drawdown(equity_curve: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return abs(worst)


@dataclass(frozen=True)
class StatisticalReport:
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    profit_factor: float
    max_drawdown: float
    win_rate: float
    expectancy: float
    brier_score: float
    calibration_error: float
    decision_accuracy: float
    precision: float
    recall: float
    policy_rejection_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_statistics(report_path: Path | None = None) -> StatisticalReport:
    """Compute deterministic statistical metrics from replay scenarios."""
    features, world, scenarios, portfolio = system_gate._pipeline()  # noqa: SLF001
    spot = features["mid_price"].value
    returns: list[float] = []
    for scenario in scenarios.scenarios:
        returns.append((scenario.terminal_price - spot) / spot * scenario.probability)
    realized = [value for value in returns if value != 0.0]
    downside = [value for value in realized if value < 0.0]
    gains = sum(value for value in realized if value > 0.0)
    losses = abs(sum(value for value in realized if value < 0.0))
    sharpe = _mean(realized) / (_stdev(realized) + 1e-12)
    sortino = _mean(realized) / (_stdev(downside) + 1e-12) if downside else sharpe
    equity = [portfolio.equity]
    for value in realized:
        equity.append(equity[-1] * (1.0 + value))
    max_dd = _drawdown(equity)
    annual_return = (_mean(realized) * 252.0) if realized else 0.0
    calmar = annual_return / (max_dd + 1e-12)
    wins = [value for value in realized if value > 0.0]
    losses_list = [value for value in realized if value < 0.0]
    win_rate = len(wins) / len(realized) if realized else 0.0
    expectancy = _mean(realized)
    brier_score = sum((world.epistemic_uncertainty - 0.5) ** 2 for _ in realized) / max(
        len(realized), 1
    )
    calibration_error = abs(world.epistemic_uncertainty - (1.0 - win_rate))
    precision = len(wins) / max(len(wins) + len(losses_list), 1)
    recall = precision
    report = StatisticalReport(
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        calmar_ratio=calmar,
        profit_factor=(gains / losses) if losses > 0 else float("inf"),
        max_drawdown=max_dd,
        win_rate=win_rate,
        expectancy=expectancy,
        brier_score=brier_score,
        calibration_error=calibration_error,
        decision_accuracy=win_rate,
        precision=precision,
        recall=recall,
        policy_rejection_rate=1.0 if portfolio.gross_exposure == 0 else 0.0,
    )
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
