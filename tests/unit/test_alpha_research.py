"""Unit tests for the Phase E alpha research toolkit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tools.alpha_research.analysis import (
    compute_alpha_attribution,
    compute_decision_quality,
    compute_feature_importance,
    compute_regime_adaptation,
)
from tools.alpha_research.backtester import backtest_strategy
from tools.alpha_research.features import FEATURE_COLUMNS, build_feature_frame
from tools.alpha_research.models import ResearchConfig, StrategyParameters
from tools.alpha_research.optimization import (
    monte_carlo_analysis,
    optimize_strategy,
    walk_forward_validation,
)
from tools.alpha_research.strategies import (
    ALL_STRATEGIES,
    REQUIRED_STRATEGIES,
    build_component_frame,
    generate_strategy_signal_frame,
)


def _base_frame(periods: int = 1_200) -> pd.DataFrame:
    dates = pd.date_range("2018-01-01", periods=periods, freq="D", tz="UTC")
    steps = [1800.0 + index * 0.4 + 25.0 * ((index % 80) / 80.0) for index in range(periods)]
    frame = pd.DataFrame(
        {
            "open": steps,
            "high": [value * 1.01 for value in steps],
            "low": [value * 0.99 for value in steps],
            "close": steps,
            "volume": [1000.0 + float(index % 25) * 25.0 for index in range(periods)],
            "dxy_close": [95.0 - index * 0.001 for index in range(periods)],
            "yield_3m": [2.0 + (index % 30) * 0.01 for index in range(periods)],
            "yield_5y": [2.5 + (index % 40) * 0.01 for index in range(periods)],
            "yield_10y": [3.0 + (index % 50) * 0.01 for index in range(periods)],
            "yield_30y": [3.5 + (index % 60) * 0.01 for index in range(periods)],
            "fed_actual": [2.0 + (index % 20) * 0.01 for index in range(periods)],
            "fed_previous": [1.95 + (index % 20) * 0.01 for index in range(periods)],
            "geo_active": [1.0 if index % 90 < 10 else 0.0 for index in range(periods)],
            "geo_severity": [0.75 if index % 90 < 10 else 0.0 for index in range(periods)],
            "geo_event_count": [1.0 if index % 90 < 10 else 0.0 for index in range(periods)],
        },
        index=dates,
    )
    return frame.astype(float)


def _feature_frame(periods: int = 1_200) -> pd.DataFrame:
    frame = build_feature_frame(_base_frame(periods))
    return frame.iloc[240:-5].copy()


def test_feature_frame_contains_phase_e_columns() -> None:
    frame = _feature_frame()
    for column in FEATURE_COLUMNS:
        assert column in frame.columns


def test_all_strategies_generate_decision_frames() -> None:
    frame = _feature_frame()
    parameters = StrategyParameters()
    for strategy_name in ALL_STRATEGIES:
        decision = generate_strategy_signal_frame(strategy_name, frame, parameters)
        assert len(decision) == len(frame)
        assert {"world_model_score", "position_target", "confidence"}.issubset(decision.columns)


def test_component_frame_for_hybrid_contains_expected_scores() -> None:
    frame = _feature_frame()
    components = build_component_frame(
        "hybrid",
        frame,
        StrategyParameters(),
    )
    assert {"macro_score", "technical_score", "liquidity_score"}.issubset(components.columns)


def test_backtester_is_deterministic_for_same_inputs() -> None:
    frame = _feature_frame()
    parameters = StrategyParameters()
    decision = generate_strategy_signal_frame("trend_following", frame, parameters)
    config = ResearchConfig(
        train_days=400,
        validation_days=120,
        test_days=120,
        monte_carlo_paths=40,
    )
    first = backtest_strategy("trend_following", frame, decision, parameters, config)
    second = backtest_strategy("trend_following", frame, decision, parameters, config)
    assert first.metrics == second.metrics
    assert first.checksum == second.checksum


def test_backtester_emits_trades_and_equity_curve() -> None:
    frame = _feature_frame()
    parameters = StrategyParameters(confidence_threshold=0.50)
    decision = generate_strategy_signal_frame("macro_only", frame, parameters)
    run = backtest_strategy("macro_only", frame, decision, parameters, ResearchConfig())
    assert len(run.equity_curve) == len(frame)
    assert len(run.trades) >= 1


def test_optimizer_returns_ranked_trials() -> None:
    frame = _feature_frame()
    config = ResearchConfig(
        train_days=400,
        validation_days=120,
        test_days=120,
        monte_carlo_paths=40,
    )
    result = optimize_strategy(frame, "hybrid", config)
    assert result.strategy_name == "hybrid"
    assert len(result.trials) >= 1
    assert result.trials[0].objective_score >= result.trials[-1].objective_score


def test_walk_forward_returns_folds_and_metrics() -> None:
    frame = _feature_frame(1_400)
    config = ResearchConfig(
        train_days=400,
        validation_days=120,
        test_days=120,
        monte_carlo_paths=40,
    )
    summary = walk_forward_validation(frame, "trend_following", config)
    assert summary.fold_count >= 1
    assert "sharpe" in summary.aggregate_metrics
    assert 0.0 <= summary.positive_fold_ratio <= 1.0


def test_monte_carlo_summary_has_expected_fields() -> None:
    summary = monte_carlo_analysis(
        (0.01, -0.005, 0.002, 0.003) * 20, ResearchConfig(monte_carlo_paths=40)
    )
    assert {
        "median_total_return",
        "ruin_probability",
        "median_max_drawdown",
    }.issubset(summary)


def test_feature_importance_classifies_records() -> None:
    frame = _feature_frame(1_400)
    validation = frame.iloc[-200:].copy()
    results = compute_feature_importance(
        frame,
        validation,
        StrategyParameters(),
        ResearchConfig(monte_carlo_paths=40),
    )
    assert len(results) == len(FEATURE_COLUMNS)
    assert all(
        record.classification in {"useful", "useless", "redundant", "unstable"}
        for record in results
    )


def test_alpha_attribution_includes_all_required_components() -> None:
    frame = _feature_frame(1_400)
    rows = compute_alpha_attribution(
        frame, StrategyParameters(), ResearchConfig(monte_carlo_paths=40)
    )
    names = {str(row["component"]) for row in rows}
    assert {
        "Macro",
        "Microstructure",
        "Liquidity",
        "Regime",
        "Forward Expectations",
        "Behavioral",
        "World Model Fusion",
        "Utility Optimizer",
        "Policy Engine",
    }.issubset(names)


def test_decision_quality_summarises_runtime_and_regret(tmp_path: Path) -> None:
    frame = _feature_frame(1_400)
    decision = generate_strategy_signal_frame("hybrid", frame, StrategyParameters())
    run = backtest_strategy(
        "hybrid",
        frame,
        decision,
        StrategyParameters(),
        ResearchConfig(),
    )
    runtime_log = tmp_path / "decision_log.jsonl"
    runtime_log.write_text(
        "\n".join(
            [
                '{"policy_outcome": {"action": "buy"}, "decision_context": {"confidence": 0.8}}',
                '{"policy_outcome": {"action": "hold"}, "decision_context": {"confidence": 0.6}}',
            ]
        ),
        encoding="utf-8",
    )
    alternatives = {
        "trend_following": generate_strategy_signal_frame(
            "trend_following", frame, StrategyParameters()
        ),
        "macro_only": generate_strategy_signal_frame(
            "macro_only",
            frame,
            StrategyParameters(),
        ),
    }
    report = compute_decision_quality(frame, decision, run, alternatives, runtime_log)
    assert report["trade_count"] >= 1
    assert "runtime_summary" in report
    assert report["runtime_summary"]["records"] == 2


def test_regime_adaptation_reports_all_named_windows() -> None:
    frame = _feature_frame(1_500)
    report = compute_regime_adaptation(
        frame,
        "hybrid",
        StrategyParameters(),
        ResearchConfig(),
    )
    assert "regimes" in report
    assert report["strategy_name"] == "hybrid"


def test_required_strategy_names_remain_present() -> None:
    assert len(REQUIRED_STRATEGIES) == 6
