"""Attribution, feature importance, decision quality, and regime analysis."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from tools.alpha_research.backtester import backtest_strategy
from tools.alpha_research.features import FEATURE_COLUMNS
from tools.alpha_research.models import (
    FeatureImportanceRecord,
    ResearchConfig,
    StrategyParameters,
    StrategyRun,
)
from tools.alpha_research.optimization import score_metrics
from tools.alpha_research.strategies import (
    build_component_frame,
    compose_decision_frame,
    generate_strategy_signal_frame,
)


def _mutual_information(feature: pd.Series, target: pd.Series, bins: int = 5) -> float:
    clean = (
        pd.DataFrame({"feature": feature, "target": target})
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    if len(clean) < bins * 3:
        return 0.0
    x_bins = pd.qcut(
        clean["feature"],
        q=min(bins, clean["feature"].nunique()),
        duplicates="drop",
    )
    y_values = np.sign(clean["target"]).astype(int)
    joint = pd.crosstab(x_bins, y_values, normalize=True)
    if joint.empty:
        return 0.0
    px = joint.sum(axis=1)
    py = joint.sum(axis=0)
    value = 0.0
    for row_key in joint.index:
        for col_key in joint.columns:
            probability = float(joint.loc[row_key, col_key])
            if probability <= 0.0:
                continue
            px_value = float(px.loc[row_key])
            py_value = float(py.loc[col_key])
            value += probability * math.log(probability / (px_value * py_value))
    return value


def _correlation_stability(
    feature: pd.Series, target: pd.Series, window: int = 252
) -> tuple[float, float]:
    clean = (
        pd.DataFrame({"feature": feature, "target": target})
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    correlations: list[float] = []
    for start in range(0, len(clean) - window + 1, window):
        subset = clean.iloc[start : start + window]
        if float(subset["feature"].std()) == 0.0 or float(subset["target"].std()) == 0.0:
            continue
        corr = subset["feature"].corr(subset["target"])
        if corr == corr:
            correlations.append(float(corr))
    if not correlations:
        if float(clean["feature"].std()) == 0.0 or float(clean["target"].std()) == 0.0:
            return (0.0, 0.0)
        overall = clean["feature"].corr(clean["target"])
        return (float(overall) if overall == overall else 0.0, 0.0)
    mean_corr = sum(correlations) / len(correlations)
    variance = sum((value - mean_corr) ** 2 for value in correlations) / len(correlations)
    return mean_corr, math.sqrt(variance)


def _drift_score(feature: pd.Series) -> float:
    clean = feature.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 20:
        return 0.0
    midpoint = len(clean) // 2
    first = clean.iloc[:midpoint]
    second = clean.iloc[midpoint:]
    pooled_std = float(clean.std())
    if pooled_std == 0.0 or pooled_std != pooled_std:
        return 0.0
    return abs(float(first.mean()) - float(second.mean())) / pooled_std


def compute_feature_importance(
    frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    parameters: StrategyParameters,
    config: ResearchConfig,
) -> list[FeatureImportanceRecord]:
    """Compute MI, stability, drift, redundancy, and permutation importance."""
    validation_decision = generate_strategy_signal_frame("hybrid", validation_frame, parameters)
    validation_run = backtest_strategy(
        "hybrid", validation_frame, validation_decision, parameters, config
    )
    baseline_score = score_metrics(validation_run.metrics)
    results: list[FeatureImportanceRecord] = []
    rng = np.random.default_rng(config.seed)
    for feature_name in FEATURE_COLUMNS:
        feature = frame[feature_name].astype(float)
        target = frame["future_return_5"].astype(float)
        mi_value = _mutual_information(feature, target)
        corr_mean, corr_stability = _correlation_stability(feature, target)
        drift = _drift_score(feature)
        redundancy = 0.0
        for other_name in FEATURE_COLUMNS:
            if other_name == feature_name:
                continue
            other_feature = frame[other_name].astype(float)
            if float(feature.std()) == 0.0 or float(other_feature.std()) == 0.0:
                continue
            corr = feature.corr(other_feature)
            if corr == corr:
                redundancy = max(redundancy, abs(float(corr)))
        permuted = validation_frame.copy()
        permuted[feature_name] = rng.permutation(permuted[feature_name].to_numpy())
        permuted_decision = generate_strategy_signal_frame(
            "hybrid",
            permuted,
            parameters,
        )
        permuted_run = backtest_strategy(
            "hybrid",
            permuted,
            permuted_decision,
            parameters,
            config,
        )
        permutation_importance = baseline_score - score_metrics(permuted_run.metrics)
        classification = "useful"
        if mi_value < 0.002 and permutation_importance < 0.02:
            classification = "useless"
        elif redundancy > 0.85:
            classification = "redundant"
        elif corr_stability > 0.20 or drift > 0.75:
            classification = "unstable"
        results.append(
            FeatureImportanceRecord(
                feature=feature_name,
                mutual_information=mi_value,
                correlation_mean=corr_mean,
                correlation_stability=corr_stability,
                drift_score=drift,
                redundancy_score=redundancy,
                permutation_importance=permutation_importance,
                classification=classification,
            )
        )
    return sorted(results, key=lambda item: item.permutation_importance, reverse=True)


def compute_alpha_attribution(
    frame: pd.DataFrame,
    parameters: StrategyParameters,
    config: ResearchConfig,
) -> list[dict[str, float | str]]:
    """Ablate hybrid research families and pipeline stages."""
    components = build_component_frame("hybrid", frame, parameters)
    full_decision = compose_decision_frame(frame, parameters, "hybrid", components)
    full_run = backtest_strategy("hybrid", frame, full_decision, parameters, config)
    outputs: list[dict[str, float | str]] = []
    family_map = {
        "Macro": "macro_score",
        "Microstructure": "microstructure_score",
        "Liquidity": "liquidity_score",
        "Regime": "regime_score",
        "Forward Expectations": "forward_score",
        "Behavioral": "behavioral_score",
    }
    for label, column in family_map.items():
        ablated = components.copy()
        ablated[column] = 0.0
        decision = compose_decision_frame(frame, parameters, "hybrid", ablated)
        run = backtest_strategy("hybrid", frame, decision, parameters, config)
        outputs.append(
            {
                "component": label,
                "delta_sharpe": full_run.metrics["sharpe"] - run.metrics["sharpe"],
                "delta_expectancy": full_run.metrics["expectancy"] - run.metrics["expectancy"],
                "delta_total_return": full_run.metrics["total_return"]
                - run.metrics["total_return"],
            }
        )
    fusion_decision = compose_decision_frame(
        frame, parameters, "hybrid", components, fusion_mode="max_component"
    )
    fusion_run = backtest_strategy(
        "hybrid",
        frame,
        fusion_decision,
        parameters,
        config,
    )
    outputs.append(
        {
            "component": "World Model Fusion",
            "delta_sharpe": full_run.metrics["sharpe"] - fusion_run.metrics["sharpe"],
            "delta_expectancy": full_run.metrics["expectancy"] - fusion_run.metrics["expectancy"],
            "delta_total_return": full_run.metrics["total_return"]
            - fusion_run.metrics["total_return"],
        }
    )
    utility_decision = compose_decision_frame(
        frame, parameters, "hybrid", components, bypass_utility=True
    )
    utility_run = backtest_strategy(
        "hybrid",
        frame,
        utility_decision,
        parameters,
        config,
    )
    outputs.append(
        {
            "component": "Utility Optimizer",
            "delta_sharpe": full_run.metrics["sharpe"] - utility_run.metrics["sharpe"],
            "delta_expectancy": full_run.metrics["expectancy"] - utility_run.metrics["expectancy"],
            "delta_total_return": full_run.metrics["total_return"]
            - utility_run.metrics["total_return"],
        }
    )
    policy_decision = compose_decision_frame(
        frame, parameters, "hybrid", components, bypass_policy=True
    )
    policy_run = backtest_strategy(
        "hybrid",
        frame,
        policy_decision,
        parameters,
        config,
    )
    outputs.append(
        {
            "component": "Policy Engine",
            "delta_sharpe": full_run.metrics["sharpe"] - policy_run.metrics["sharpe"],
            "delta_expectancy": full_run.metrics["expectancy"] - policy_run.metrics["expectancy"],
            "delta_total_return": full_run.metrics["total_return"]
            - policy_run.metrics["total_return"],
        }
    )
    return outputs


def _trade_regret(trade: dict[str, Any]) -> float:
    best = max(float(trade["best_possible_return"]), 0.0)
    actual = float(trade["actual_return"])
    return best - actual


def compute_decision_quality(
    frame: pd.DataFrame,
    decision_frame: pd.DataFrame,
    run: StrategyRun,
    alternative_decisions: dict[str, pd.DataFrame],
    runtime_log: Path | None = None,
) -> dict[str, Any]:
    """Evaluate direction correctness, regret, and alternative disagreement."""
    trade_rows: list[dict[str, Any]] = []
    for trade in run.trades:
        entry_ts = pd.Timestamp(trade.entry_at)
        if entry_ts not in frame.index:
            continue
        start = list(frame.index).index(entry_ts)
        horizon_end = min(len(frame) - 1, start + 10)
        entry_price = float(frame["close"].iloc[start])
        future_price = float(frame["close"].iloc[horizon_end])
        future_return = future_price / entry_price - 1.0
        actual_direction = 1.0 if trade.direction == "long" else -1.0
        actual_return = actual_direction * future_return
        best_possible = max(future_return, -future_return, 0.0)
        disagreements = 0
        alternative_votes: dict[str, str] = {}
        for name, alternative in alternative_decisions.items():
            action = str(alternative.loc[entry_ts, "action"])
            alternative_votes[name] = action
            if action != trade.direction and action != "flat":
                disagreements += 1
        trade_rows.append(
            {
                "entry_at": trade.entry_at,
                "direction": trade.direction,
                "confidence": trade.confidence,
                "actual_return": actual_return,
                "best_possible_return": best_possible,
                "regret": best_possible - actual_return,
                "alternative_disagreements": disagreements,
                "entry_reason": trade.entry_reason,
                "alternative_votes": alternative_votes,
            }
        )
    accuracy = 0.0
    avg_regret = 0.0
    if trade_rows:
        accuracy = sum(1 for row in trade_rows if float(row["actual_return"]) > 0.0) / len(
            trade_rows
        )
        avg_regret = sum(float(row["regret"]) for row in trade_rows) / len(trade_rows)
    runtime_summary: dict[str, Any] = {}
    if runtime_log is not None and runtime_log.is_file():
        actions: dict[str, int] = {}
        confidences: list[float] = []
        for line in runtime_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            action = str(payload.get("policy_outcome", {}).get("action", "unknown"))
            actions[action] = actions.get(action, 0) + 1
            confidence = payload.get("decision_context", {}).get("confidence")
            if isinstance(confidence, int | float) and not isinstance(confidence, bool):
                confidences.append(float(confidence))
        runtime_summary = {
            "records": sum(actions.values()),
            "actions": actions,
            "confidence_mean": sum(confidences) / len(confidences) if confidences else 0.0,
        }
    ranked = sorted(trade_rows, key=_trade_regret, reverse=True)
    return {
        "trade_count": len(trade_rows),
        "direction_accuracy": accuracy,
        "average_regret": avg_regret,
        "top_regret_trades": ranked[:10],
        "runtime_summary": runtime_summary,
    }


def compute_regime_adaptation(
    frame: pd.DataFrame,
    strategy_name: str,
    parameters: StrategyParameters,
    config: ResearchConfig,
) -> dict[str, Any]:
    """Compare strategy performance across bull/bear/sideways and volatility regimes."""
    labels = {
        "bull": frame["regime_return_60"] > 0.05,
        "bear": frame["regime_return_60"] < -0.05,
        "sideways": frame["regime_return_60"].abs() <= 0.05,
        "high_vol": frame["regime_vol_20"] >= frame["regime_vol_20"].median(),
        "low_vol": frame["regime_vol_20"] < frame["regime_vol_20"].median(),
        "macro_event": (frame["geo_active"] > 0.0) | (frame["calendar_event"] > 0.0),
    }
    decision = generate_strategy_signal_frame(strategy_name, frame, parameters)
    baseline_run = backtest_strategy(strategy_name, frame, decision, parameters, config)
    regimes: dict[str, dict[str, float]] = {}
    improvements: list[float] = []
    for label, mask in labels.items():
        subset = frame.loc[mask].copy()
        if len(subset) < 60:
            continue
        subset_decision = generate_strategy_signal_frame(
            strategy_name,
            subset,
            parameters,
        )
        subset_run = backtest_strategy(
            strategy_name,
            subset,
            subset_decision,
            parameters,
            config,
        )
        exploratory_parameters = StrategyParameters(
            confidence_threshold=max(0.50, parameters.confidence_threshold - 0.05),
            vol_ceiling=parameters.vol_ceiling * 1.10,
            position_scale=min(1.0, parameters.position_scale + 0.10),
            max_position=parameters.max_position,
            score_threshold=max(0.05, parameters.score_threshold - 0.02),
            macro_weight=parameters.macro_weight,
            microstructure_weight=parameters.microstructure_weight,
            liquidity_weight=parameters.liquidity_weight,
            regime_weight=parameters.regime_weight,
            forward_weight=parameters.forward_weight,
            behavioral_weight=parameters.behavioral_weight,
            technical_weight=parameters.technical_weight,
            utility_weight=parameters.utility_weight,
            policy_limit=parameters.policy_limit,
        )
        exploratory = generate_strategy_signal_frame(
            strategy_name,
            subset,
            exploratory_parameters,
        )
        exploratory_run = backtest_strategy(
            strategy_name,
            subset,
            exploratory,
            parameters,
            config,
        )
        delta = score_metrics(exploratory_run.metrics) - score_metrics(subset_run.metrics)
        improvements.append(delta)
        regimes[label] = {
            "total_return": subset_run.metrics["total_return"],
            "sharpe": subset_run.metrics["sharpe"],
            "sortino": subset_run.metrics["sortino"],
            "max_drawdown": subset_run.metrics["max_drawdown"],
            "parameter_delta_score": delta,
        }
    requires_adaptation = any(delta > 0.15 for delta in improvements)
    return {
        "strategy_name": strategy_name,
        "baseline_metrics": baseline_run.metrics,
        "regimes": regimes,
        "requires_regime_specific_parameterization": requires_adaptation,
    }
