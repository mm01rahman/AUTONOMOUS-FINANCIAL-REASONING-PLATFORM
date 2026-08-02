"""Deterministic portfolio backtester for Phase E strategies."""

from __future__ import annotations

import hashlib
import json

import pandas as pd

from tools.alpha_research.models import (
    ResearchConfig,
    StrategyParameters,
    StrategyRun,
    TradeRecord,
)
from tools.backtest.metrics import compute_metrics

_COMPONENT_EXPORTS = (
    "macro_score",
    "microstructure_score",
    "liquidity_score",
    "regime_score",
    "forward_score",
    "behavioral_score",
    "technical_score",
)


def _trade_checksum(trades: list[TradeRecord]) -> str:
    payload = [
        {
            "entry_at": trade.entry_at,
            "exit_at": trade.exit_at,
            "direction": trade.direction,
            "position": round(trade.position, 6),
            "pnl": round(trade.pnl, 6),
            "score": round(trade.score, 6),
        }
        for trade in trades
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _extract_trades(
    frame: pd.DataFrame,
    decision_frame: pd.DataFrame,
    config: ResearchConfig,
) -> list[TradeRecord]:
    trades: list[TradeRecord] = []
    active_position = 0.0
    entry_price = 0.0
    entry_equity = config.initial_equity
    entry_time = ""
    entry_reason = ""
    entry_confidence = 0.5
    entry_score = 0.0
    entry_components: dict[str, float] = {}

    equity = config.initial_equity
    for idx in range(len(frame)):
        timestamp = frame.index[idx].isoformat()
        close_price = float(frame["close"].iloc[idx])
        target = float(decision_frame["position_target"].iloc[idx])
        signal = float(decision_frame["world_model_score"].iloc[idx])
        confidence = float(decision_frame["confidence"].iloc[idx])
        reason = (
            f"{decision_frame['primary_reason'].iloc[idx]}:"
            f"{decision_frame['policy_reason'].iloc[idx]}"
        )
        components = {
            column: round(float(decision_frame[column].iloc[idx]), 6)
            for column in _COMPONENT_EXPORTS
        }
        if active_position == 0.0 and target != 0.0:
            active_position = target
            entry_price = close_price
            entry_equity = equity
            entry_time = timestamp
            entry_reason = reason
            entry_confidence = confidence
            entry_score = signal
            entry_components = components
            continue
        if active_position != 0.0 and target != active_position:
            direction = "long" if active_position > 0.0 else "short"
            gross_return = (close_price / entry_price - 1.0) * (
                1.0 if active_position > 0.0 else -1.0
            )
            net_return = (
                gross_return * abs(active_position)
                - (config.cost_bps / 10_000.0) * abs(active_position) * 2.0
            )
            pnl = entry_equity * net_return
            trades.append(
                TradeRecord(
                    entry_at=entry_time,
                    exit_at=timestamp,
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=close_price,
                    position=active_position,
                    pnl=pnl,
                    return_pct=net_return,
                    confidence=entry_confidence,
                    score=entry_score,
                    entry_reason=entry_reason,
                    exit_reason=reason,
                    components=entry_components,
                )
            )
            equity += pnl
            active_position = target
            if target != 0.0:
                entry_price = close_price
                entry_equity = equity
                entry_time = timestamp
                entry_reason = reason
                entry_confidence = confidence
                entry_score = signal
                entry_components = components
            else:
                entry_price = 0.0
                entry_time = ""
                entry_reason = ""
                entry_components = {}
    if active_position != 0.0 and len(frame) > 0:
        close_price = float(frame["close"].iloc[-1])
        timestamp = frame.index[-1].isoformat()
        direction = "long" if active_position > 0.0 else "short"
        gross_return = (close_price / entry_price - 1.0) * (1.0 if active_position > 0.0 else -1.0)
        net_return = (
            gross_return * abs(active_position)
            - (config.cost_bps / 10_000.0) * abs(active_position) * 2.0
        )
        pnl = entry_equity * net_return
        trades.append(
            TradeRecord(
                entry_at=entry_time,
                exit_at=timestamp,
                direction=direction,
                entry_price=entry_price,
                exit_price=close_price,
                position=active_position,
                pnl=pnl,
                return_pct=net_return,
                confidence=entry_confidence,
                score=entry_score,
                entry_reason=entry_reason,
                exit_reason="forced_close",
                components=entry_components,
            )
        )
    return trades


def backtest_strategy(
    strategy_name: str,
    frame: pd.DataFrame,
    decision_frame: pd.DataFrame,
    parameters: StrategyParameters,
    config: ResearchConfig,
) -> StrategyRun:
    """Run deterministic portfolio accounting on a prepared decision frame."""
    target_positions = decision_frame["position_target"].astype(float)
    executed_positions = target_positions.shift(1).fillna(0.0)
    asset_returns = frame["xau_return_1"].astype(float).fillna(0.0)
    turnover = executed_positions.diff().abs().fillna(executed_positions.abs())
    transaction_cost = turnover * config.cost_bps / 10_000.0
    strategy_returns = executed_positions * asset_returns - transaction_cost

    equity_curve: list[float] = []
    equity = config.initial_equity
    for daily_return in strategy_returns:
        equity *= 1.0 + float(daily_return)
        equity_curve.append(equity)

    trades = _extract_trades(frame, decision_frame, config)
    net_pnls = [trade.pnl for trade in trades]
    metrics = compute_metrics(equity_curve, net_pnls)
    rejection_count = int((decision_frame["authorized"] == False).sum())  # noqa: E712
    checksum = _trade_checksum(trades)
    return StrategyRun(
        name=strategy_name,
        parameters=parameters,
        metrics=metrics,
        daily_returns=tuple(float(value) for value in strategy_returns.tolist()),
        equity_curve=tuple(float(value) for value in equity_curve),
        positions=tuple(float(value) for value in executed_positions.tolist()),
        trades=tuple(trades),
        checksum=checksum,
        policy_rejection_rate=rejection_count / max(len(decision_frame), 1),
    )


def combine_daily_returns(
    daily_returns: tuple[float, ...], initial_equity: float
) -> tuple[list[float], list[float]]:
    """Rebuild equity curve from concatenated daily returns."""
    curve: list[float] = []
    equity = initial_equity
    for daily_return in daily_returns:
        equity *= 1.0 + daily_return
        curve.append(equity)
    return list(daily_returns), curve
