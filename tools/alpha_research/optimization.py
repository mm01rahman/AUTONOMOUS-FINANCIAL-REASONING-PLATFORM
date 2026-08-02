"""Parameter search, walk-forward validation, and Monte Carlo analysis."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from tools.alpha_research.backtester import backtest_strategy, combine_daily_returns
from tools.alpha_research.models import (
    OptimizationResult,
    OptimizationTrial,
    PromotionDecision,
    ResearchConfig,
    WalkForwardFold,
    WalkForwardSummary,
)
from tools.alpha_research.strategies import (
    ALL_STRATEGIES,
    generate_strategy_signal_frame,
    strategy_parameter_grid,
)
from tools.backtest.metrics import compute_metrics


def score_metrics(metrics: dict[str, float]) -> float:
    """Objective score with explicit drawdown and overtrading penalties."""
    expectancy_component = metrics["expectancy"] / 5_000.0
    trade_penalty = 0.10 if metrics["trade_count"] < 12.0 else 0.0
    return (
        metrics["sharpe"]
        + 0.50 * max(metrics["sortino"], 0.0)
        + 0.10 * min(metrics["profit_factor"], 3.0)
        + expectancy_component
        - 0.75 * metrics["max_drawdown"]
        - trade_penalty
    )


def optimize_strategy(
    frame: pd.DataFrame,
    strategy_name: str,
    config: ResearchConfig,
) -> OptimizationResult:
    """Search the compact deterministic parameter grid on train/validation splits."""
    train_end = max(config.train_days, len(frame) // 2)
    validation_end = min(len(frame), train_end + config.validation_days)
    train = frame.iloc[:train_end].copy()
    validation = frame.iloc[train_end:validation_end].copy()
    if validation.empty:
        validation = frame.iloc[train_end:].copy()
    trials: list[OptimizationTrial] = []
    for parameters in strategy_parameter_grid(strategy_name):
        train_decision = generate_strategy_signal_frame(strategy_name, train, parameters)
        validation_decision = generate_strategy_signal_frame(strategy_name, validation, parameters)
        train_run = backtest_strategy(strategy_name, train, train_decision, parameters, config)
        validation_run = backtest_strategy(
            strategy_name, validation, validation_decision, parameters, config
        )
        train_score = score_metrics(train_run.metrics)
        validation_score = score_metrics(validation_run.metrics)
        overfit_gap = train_score - validation_score
        stability_penalty = (
            abs(train_run.metrics["sharpe"] - validation_run.metrics["sharpe"]) * 0.25
        )
        objective_score = validation_score - max(overfit_gap, 0.0) * 0.50 - stability_penalty
        trials.append(
            OptimizationTrial(
                parameters=parameters,
                train_score=train_score,
                validation_score=validation_score,
                objective_score=objective_score,
                overfit_gap=overfit_gap,
                train_metrics=train_run.metrics,
                validation_metrics=validation_run.metrics,
            )
        )
    ranked = tuple(sorted(trials, key=lambda trial: trial.objective_score, reverse=True))
    winner = ranked[0]
    return OptimizationResult(
        strategy_name=strategy_name,
        selected_parameters=winner.parameters,
        selected_objective=winner.objective_score,
        overfit_gap=winner.overfit_gap,
        trials=ranked,
    )


def walk_forward_validation(
    frame: pd.DataFrame,
    strategy_name: str,
    config: ResearchConfig,
) -> WalkForwardSummary:
    """Run rolling train/validation/test windows with fresh per-fold optimisation."""
    folds: list[WalkForwardFold] = []
    aggregate_daily_returns: list[float] = []
    fold_positive = 0
    start = 0
    fold_id = 1
    while start + config.train_days + config.validation_days + config.test_days <= len(frame):
        train_end = start + config.train_days
        validation_end = train_end + config.validation_days
        test_end = validation_end + config.test_days
        train = frame.iloc[start:train_end].copy()
        validation = frame.iloc[train_end:validation_end].copy()
        test = frame.iloc[validation_end:test_end].copy()
        best_trial: OptimizationTrial | None = None
        for parameters in strategy_parameter_grid(strategy_name):
            train_decision = generate_strategy_signal_frame(strategy_name, train, parameters)
            validation_decision = generate_strategy_signal_frame(
                strategy_name, validation, parameters
            )
            train_run = backtest_strategy(strategy_name, train, train_decision, parameters, config)
            validation_run = backtest_strategy(
                strategy_name, validation, validation_decision, parameters, config
            )
            train_score = score_metrics(train_run.metrics)
            validation_score = score_metrics(validation_run.metrics)
            overfit_gap = train_score - validation_score
            stability_penalty = (
                abs(train_run.metrics["sharpe"] - validation_run.metrics["sharpe"]) * 0.25
            )
            objective_score = validation_score - max(overfit_gap, 0.0) * 0.50 - stability_penalty
            trial = OptimizationTrial(
                parameters=parameters,
                train_score=train_score,
                validation_score=validation_score,
                objective_score=objective_score,
                overfit_gap=overfit_gap,
                train_metrics=train_run.metrics,
                validation_metrics=validation_run.metrics,
            )
            if best_trial is None or trial.objective_score > best_trial.objective_score:
                best_trial = trial
        if best_trial is None:
            break
        test_decision = generate_strategy_signal_frame(strategy_name, test, best_trial.parameters)
        test_run = backtest_strategy(
            strategy_name, test, test_decision, best_trial.parameters, config
        )
        aggregate_daily_returns.extend(test_run.daily_returns)
        if test_run.metrics["expectancy"] > 0.0 and test_run.metrics["sharpe"] > 0.0:
            fold_positive += 1
        folds.append(
            WalkForwardFold(
                fold_id=fold_id,
                train_start=train.index[0].isoformat(),
                train_end=train.index[-1].isoformat(),
                validation_end=validation.index[-1].isoformat(),
                test_end=test.index[-1].isoformat(),
                parameters=best_trial.parameters,
                test_metrics=test_run.metrics,
                test_checksum=test_run.checksum,
            )
        )
        start += config.test_days
        fold_id += 1
    aggregate_tuple = tuple(float(value) for value in aggregate_daily_returns)
    _, curve = combine_daily_returns(aggregate_tuple, config.initial_equity)
    combined_metrics = compute_metrics(curve, []) if curve else compute_metrics([], [])
    positive_fold_ratio = fold_positive / max(len(folds), 1)
    return WalkForwardSummary(
        strategy_name=strategy_name,
        aggregate_metrics=combined_metrics,
        positive_fold_ratio=positive_fold_ratio,
        fold_count=len(folds),
        daily_returns=aggregate_tuple,
        folds=tuple(folds),
    )


def monte_carlo_analysis(
    daily_returns: tuple[float, ...], config: ResearchConfig
) -> dict[str, float]:
    """Bootstrap daily returns into robustness/ruin statistics."""
    if not daily_returns:
        return {
            "paths": float(config.monte_carlo_paths),
            "median_total_return": 0.0,
            "p05_total_return": 0.0,
            "p95_total_return": 0.0,
            "median_max_drawdown": 0.0,
            "ruin_probability": 1.0,
        }
    rng = np.random.default_rng(config.seed)
    source = np.asarray(daily_returns, dtype=float)
    total_returns: list[float] = []
    max_drawdowns: list[float] = []
    ruin_count = 0
    max_start = max(len(source) - config.monte_carlo_block + 1, 1)
    for _ in range(config.monte_carlo_paths):
        sample: list[float] = []
        while len(sample) < len(source):
            start = int(rng.integers(0, max_start))
            end = min(start + config.monte_carlo_block, len(source))
            sample.extend(float(value) for value in source[start:end])
        path = sample[: len(source)]
        equity = config.initial_equity
        peak = config.initial_equity
        worst_drawdown = 0.0
        for daily_return in path:
            equity *= 1.0 + daily_return
            peak = max(peak, equity)
            if peak > 0.0:
                worst_drawdown = max(worst_drawdown, (peak - equity) / peak)
        total_return = equity / config.initial_equity - 1.0
        total_returns.append(total_return)
        max_drawdowns.append(worst_drawdown)
        if equity < config.initial_equity * 0.85:
            ruin_count += 1
    return {
        "paths": float(config.monte_carlo_paths),
        "median_total_return": float(np.median(total_returns)),
        "p05_total_return": float(np.percentile(total_returns, 5)),
        "p95_total_return": float(np.percentile(total_returns, 95)),
        "median_max_drawdown": float(np.median(max_drawdowns)),
        "ruin_probability": ruin_count / config.monte_carlo_paths,
    }


def assess_promotions(
    full_runs: dict[str, Any],
    walk_forward: dict[str, WalkForwardSummary],
    optimizations: dict[str, OptimizationResult],
    monte_carlo: dict[str, dict[str, float]],
    config: ResearchConfig,
) -> list[PromotionDecision]:
    """Apply governance thresholds and emit promote/do-not-promote decisions."""
    decisions: list[PromotionDecision] = []
    for strategy_name in ALL_STRATEGIES:
        if strategy_name == "baseline_afrp":
            continue
        full_metrics = full_runs[strategy_name].metrics
        walk_metrics = walk_forward[strategy_name].aggregate_metrics
        ruin_probability = float(monte_carlo[strategy_name]["ruin_probability"])
        overfit_gap = optimizations[strategy_name].overfit_gap
        thresholds = config.thresholds
        reasons: list[str] = []
        if full_metrics["expectancy"] <= thresholds.min_expectancy:
            reasons.append("full-sample expectancy not positive")
        if full_metrics["sharpe"] <= thresholds.min_sharpe:
            reasons.append("full-sample sharpe not positive enough")
        if full_metrics["sortino"] <= thresholds.min_sortino:
            reasons.append("full-sample sortino below governance bar")
        if full_metrics["max_drawdown"] > thresholds.max_drawdown:
            reasons.append("full-sample drawdown above governance bar")
        if walk_metrics["sharpe"] <= 0.0 or walk_metrics["expectancy"] <= 0.0:
            reasons.append("walk-forward out-of-sample edge not positive")
        if walk_forward[strategy_name].positive_fold_ratio < thresholds.min_positive_fold_ratio:
            reasons.append("insufficient positive walk-forward fold ratio")
        if ruin_probability > thresholds.max_ruin_probability:
            reasons.append("monte-carlo ruin probability too high")
        if overfit_gap > thresholds.max_overfit_gap:
            reasons.append("parameter search shows overfitting gap")
        decisions.append(
            PromotionDecision(
                strategy_name=strategy_name,
                promote=not reasons,
                reasons=tuple(reasons) if reasons else ("promotion criteria satisfied",),
                full_sample_metrics=full_metrics,
                walk_forward_metrics=walk_metrics,
                positive_fold_ratio=walk_forward[strategy_name].positive_fold_ratio,
                ruin_probability=ruin_probability,
                overfit_gap=overfit_gap,
            )
        )
    return decisions
