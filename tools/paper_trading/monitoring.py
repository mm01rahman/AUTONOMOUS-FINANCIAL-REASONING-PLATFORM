"""Performance monitoring for paper trading periods and rolling metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class PerformanceSnapshot:
    total_return: float
    sharpe: float
    sortino: float
    calmar: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    exposure_mean: float


def _returns(values: list[float]) -> list[float]:
    if len(values) < 2:
        return []
    out: list[float] = []
    for idx in range(1, len(values)):
        prev = values[idx - 1]
        cur = values[idx]
        if prev != 0:
            out.append((cur - prev) / prev)
    return out


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    var = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return sqrt(var)


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return worst


def compute_performance(
    equity: list[float],
    trade_pnls: list[float],
    exposures: list[float],
    risk_free_rate: float = 0.0,
) -> PerformanceSnapshot:
    rets = _returns(equity)
    std = _std(rets)
    rf_per_step = risk_free_rate / 252 if rets else 0.0
    excess = [ret - rf_per_step for ret in rets]
    sharpe = (mean(excess) / std * sqrt(252)) if std > 0 else 0.0
    downside = [ret for ret in rets if ret < 0]
    downside_std = _std(downside)
    sortino = (mean(excess) / downside_std * sqrt(252)) if downside_std > 0 else 0.0

    mdd = _max_drawdown(equity)
    total_return = (equity[-1] / equity[0] - 1) if len(equity) >= 2 and equity[0] != 0 else 0.0
    calmar = total_return / mdd if mdd > 0 else 0.0

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    win_rate = len(wins) / len(trade_pnls) if trade_pnls else 0.0
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    profit_factor = (
        gross_win / gross_loss if gross_loss > 0 else (float("inf") if gross_win > 0 else 0.0)
    )
    exposure_mean = mean(exposures) if exposures else 0.0

    return PerformanceSnapshot(
        total_return=total_return,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        win_rate=win_rate,
        profit_factor=profit_factor,
        max_drawdown=mdd,
        exposure_mean=exposure_mean,
    )


def period_summaries(timeline: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    if not timeline:
        return {"daily": {}, "weekly": {}, "monthly": {}}

    by_day: dict[str, list[float]] = {}
    by_week: dict[str, list[float]] = {}
    by_month: dict[str, list[float]] = {}

    for row in timeline:
        ts = datetime.fromisoformat(str(row["timestamp"]))
        eq = float(row["equity"])
        by_day.setdefault(ts.strftime("%Y-%m-%d"), []).append(eq)
        by_week.setdefault(f"{ts.isocalendar().year}-W{ts.isocalendar().week:02d}", []).append(eq)
        by_month.setdefault(ts.strftime("%Y-%m"), []).append(eq)

    def _summary(source: dict[str, list[float]]) -> dict[str, float]:
        returns = []
        for values in source.values():
            if len(values) >= 2 and values[0] != 0:
                returns.append(values[-1] / values[0] - 1)
        if not returns:
            return {"periods": 0.0, "avg_return": 0.0, "best_return": 0.0, "worst_return": 0.0}
        return {
            "periods": float(len(returns)),
            "avg_return": mean(returns),
            "best_return": max(returns),
            "worst_return": min(returns),
        }

    return {
        "daily": _summary(by_day),
        "weekly": _summary(by_week),
        "monthly": _summary(by_month),
    }
