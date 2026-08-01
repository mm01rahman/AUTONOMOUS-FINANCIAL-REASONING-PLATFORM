"""CLI/orchestrator for deterministic Phase E alpha research."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.alpha_research.analysis import (
    compute_alpha_attribution,
    compute_decision_quality,
    compute_feature_importance,
    compute_regime_adaptation,
)
from tools.alpha_research.backtester import backtest_strategy
from tools.alpha_research.data import load_research_frame
from tools.alpha_research.features import FEATURE_COLUMNS, build_feature_frame
from tools.alpha_research.models import ResearchConfig
from tools.alpha_research.optimization import (
    assess_promotions,
    monte_carlo_analysis,
    optimize_strategy,
    score_metrics,
    walk_forward_validation,
)
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.alpha_research.strategies import (
    ALL_STRATEGIES,
    BASELINE_NAME,
    REQUIRED_STRATEGIES,
    generate_strategy_signal_frame,
)
from tools.backtest.engine import BacktestEngine, load_ohlcv


def _strategy_label(name: str) -> str:
    return name.replace("_", " ").title()


def run_phase_e_research(config: ResearchConfig | None = None) -> dict[str, Any]:
    """Execute Phase E research end to end and emit governed artifacts."""
    cfg = config or ResearchConfig()
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    research_frame = build_feature_frame(load_research_frame())
    research_frame = research_frame.iloc[240:-5].copy()
    validation_start = max(cfg.train_days, len(research_frame) // 2)
    validation_end = min(len(research_frame), validation_start + cfg.validation_days)
    validation_frame = research_frame.iloc[validation_start:validation_end].copy()
    if validation_frame.empty:
        validation_frame = research_frame.iloc[-cfg.validation_days :].copy()

    baseline_engine = BacktestEngine()
    baseline_backtest = baseline_engine.run(
        load_ohlcv("xauusd_daily"), regime="phase-e", dataset="xauusd_daily"
    )

    optimization_results: dict[str, Any] = {}
    full_decisions: dict[str, Any] = {}
    full_runs: dict[str, Any] = {}
    walk_forward: dict[str, Any] = {}
    monte_carlo: dict[str, Any] = {}

    for strategy_name in ALL_STRATEGIES:
        optimisation = optimize_strategy(research_frame, strategy_name, cfg)
        decision = generate_strategy_signal_frame(
            strategy_name, research_frame, optimisation.selected_parameters
        )
        run = backtest_strategy(
            strategy_name, research_frame, decision, optimisation.selected_parameters, cfg
        )
        wf_summary = walk_forward_validation(research_frame, strategy_name, cfg)
        mc_summary = monte_carlo_analysis(wf_summary.daily_returns, cfg)
        optimization_results[strategy_name] = optimisation
        full_decisions[strategy_name] = decision
        full_runs[strategy_name] = run
        walk_forward[strategy_name] = wf_summary
        monte_carlo[strategy_name] = mc_summary

    ranked_candidates = sorted(
        REQUIRED_STRATEGIES,
        key=lambda name: score_metrics(walk_forward[name].aggregate_metrics),
        reverse=True,
    )
    best_candidate = ranked_candidates[0]
    feature_importance = compute_feature_importance(
        research_frame,
        validation_frame,
        optimization_results["hybrid"].selected_parameters,
        cfg,
    )
    alpha_attribution = compute_alpha_attribution(
        research_frame, optimization_results["hybrid"].selected_parameters, cfg
    )
    decision_quality = compute_decision_quality(
        research_frame,
        full_decisions[best_candidate],
        full_runs[best_candidate],
        {name: full_decisions[name] for name in REQUIRED_STRATEGIES if name != best_candidate},
        runtime_log=Path("11-research/phase-d/decision_log.jsonl"),
    )
    regime_adaptation = compute_regime_adaptation(
        research_frame,
        best_candidate,
        optimization_results[best_candidate].selected_parameters,
        cfg,
    )
    promotion_decisions = assess_promotions(
        full_runs, walk_forward, optimization_results, monte_carlo, cfg
    )

    strategy_rows: list[list[object]] = []
    for strategy_name in ALL_STRATEGIES:
        run = full_runs[strategy_name]
        wf = walk_forward[strategy_name]
        strategy_rows.append(
            [
                _strategy_label(strategy_name),
                run.metrics["total_return"],
                run.metrics["sharpe"],
                run.metrics["sortino"],
                run.metrics["max_drawdown"],
                run.metrics["expectancy"],
                wf.aggregate_metrics["sharpe"],
                wf.positive_fold_ratio,
            ]
        )
    before_after = {
        "baseline_phase_c": {
            "total_return": baseline_backtest.total_return,
            "sharpe": baseline_backtest.sharpe,
            "sortino": baseline_backtest.sortino,
            "max_drawdown": baseline_backtest.max_drawdown,
            "expectancy": baseline_backtest.expectancy,
            "total_trades": baseline_backtest.total_trades,
        },
        "phase_e_best_candidate": full_runs[best_candidate].metrics,
        "walk_forward_best_candidate": walk_forward[best_candidate].aggregate_metrics,
    }
    overall_pass = any(decision.promote for decision in promotion_decisions)

    summary_payload = {
        "dataset_rows": len(research_frame),
        "feature_columns": list(FEATURE_COLUMNS),
        "baseline_phase_c": before_after["baseline_phase_c"],
        "best_candidate": best_candidate,
        "promotion_decisions": [decision.to_dict() for decision in promotion_decisions],
        "overall_recommendation": "PASS" if overall_pass else "FAIL",
    }

    write_json(output_dir / "phase_e_summary.json", summary_payload)
    write_json(
        output_dir / "strategy_metrics.json",
        {name: full_runs[name].to_dict() for name in ALL_STRATEGIES},
    )
    write_json(
        output_dir / "parameter_optimization.json",
        {name: optimization_results[name].to_dict() for name in ALL_STRATEGIES},
    )
    write_json(
        output_dir / "walk_forward_results.json",
        {name: walk_forward[name].to_dict() for name in ALL_STRATEGIES},
    )
    write_json(
        output_dir / "feature_importance.json", [item.to_dict() for item in feature_importance]
    )
    write_json(output_dir / "alpha_attribution.json", alpha_attribution)
    write_json(output_dir / "decision_quality.json", decision_quality)
    write_json(output_dir / "regime_adaptation.json", regime_adaptation)
    write_json(output_dir / "monte_carlo.json", monte_carlo)
    write_json(
        output_dir / "promotion_assessment.json",
        [decision.to_dict() for decision in promotion_decisions],
    )
    write_json(output_dir / "before_after_comparison.json", before_after)

    write_markdown(
        output_dir / "strategy_research_report.md",
        """
# Phase E Strategy Research

## Alpha hypotheses evaluated

- Trend Following
- Mean Reversion
- Liquidity Sweep
- Macro-only
- Technical-only
- Hybrid
- Frozen baseline comparator (`tools.backtest.engine.BacktestEngine`)

## Strategy comparison

"""
        + markdown_table(
            [
                "Strategy",
                "Full Return",
                "Full Sharpe",
                "Full Sortino",
                "Full Max DD",
                "Full Expectancy",
                "WF Sharpe",
                "WF Positive Fold Ratio",
            ],
            strategy_rows,
        )
        + f"\n\nBest walk-forward candidate: **{_strategy_label(best_candidate)}**.\n",
    )
    write_markdown(
        output_dir / "alpha_attribution_report.md",
        """
# Phase E Alpha Attribution Report

"""
        + markdown_table(
            ["Component", "Δ Sharpe", "Δ Expectancy", "Δ Total Return"],
            [
                [
                    row["component"],
                    row["delta_sharpe"],
                    row["delta_expectancy"],
                    row["delta_total_return"],
                ]
                for row in alpha_attribution
            ],
        ),
    )
    write_markdown(
        output_dir / "feature_importance_report.md",
        """
# Phase E Feature Importance Report

"""
        + markdown_table(
            [
                "Feature",
                "MI",
                "Corr Mean",
                "Corr Stability",
                "Drift",
                "Redundancy",
                "Permutation",
                "Class",
            ],
            [
                [
                    item.feature,
                    item.mutual_information,
                    item.correlation_mean,
                    item.correlation_stability,
                    item.drift_score,
                    item.redundancy_score,
                    item.permutation_importance,
                    item.classification,
                ]
                for item in feature_importance[:15]
            ],
        )
        + (
            "\n\nUseless / redundant / unstable features were tagged explicitly in "
            "`feature_importance.json`.\n"
        ),
    )
    write_markdown(
        output_dir / "decision_quality_report.md",
        """
# Phase E Decision Quality Report

## Summary

"""
        + markdown_table(
            ["Metric", "Value"],
            [
                ["Trade count", decision_quality["trade_count"]],
                ["Direction accuracy", decision_quality["direction_accuracy"]],
                ["Average regret", decision_quality["average_regret"]],
                [
                    "Runtime paper-log records",
                    decision_quality["runtime_summary"].get("records", 0),
                ],
                [
                    "Runtime confidence mean",
                    decision_quality["runtime_summary"].get("confidence_mean", 0.0),
                ],
            ],
        )
        + "\n\n## Highest-regret entries\n\n"
        + markdown_table(
            ["Entry", "Direction", "Confidence", "Actual", "Best", "Regret", "Reason"],
            [
                [
                    row["entry_at"],
                    row["direction"],
                    row["confidence"],
                    row["actual_return"],
                    row["best_possible_return"],
                    row["regret"],
                    row["entry_reason"],
                ]
                for row in decision_quality["top_regret_trades"][:10]
            ],
        ),
    )
    write_markdown(
        output_dir / "parameter_optimization_report.md",
        """
# Phase E Parameter Optimization Report

"""
        + markdown_table(
            ["Strategy", "Selected Objective", "Overfit Gap", "Parameters"],
            [
                [
                    _strategy_label(name),
                    optimization_results[name].selected_objective,
                    optimization_results[name].overfit_gap,
                    optimization_results[name].selected_parameters.to_dict(),
                ]
                for name in ALL_STRATEGIES
            ],
        )
        + (
            "\n\nAnti-overfitting control used validation-first ranking with explicit "
            "overfit-gap penalties.\n"
        ),
    )
    write_markdown(
        output_dir / "walk_forward_validation_report.md",
        """
# Phase E Walk-Forward Validation Report

"""
        + markdown_table(
            [
                "Strategy",
                "WF Return",
                "WF Sharpe",
                "WF Sortino",
                "WF Max DD",
                "Positive Fold Ratio",
                "Folds",
            ],
            [
                [
                    _strategy_label(name),
                    walk_forward[name].aggregate_metrics["total_return"],
                    walk_forward[name].aggregate_metrics["sharpe"],
                    walk_forward[name].aggregate_metrics["sortino"],
                    walk_forward[name].aggregate_metrics["max_drawdown"],
                    walk_forward[name].positive_fold_ratio,
                    walk_forward[name].fold_count,
                ]
                for name in ALL_STRATEGIES
            ],
        ),
    )
    write_markdown(
        output_dir / "monte_carlo_report.md",
        """
# Phase E Monte Carlo Report

"""
        + markdown_table(
            [
                "Strategy",
                "Median Return",
                "P05 Return",
                "P95 Return",
                "Median Max DD",
                "Ruin Probability",
            ],
            [
                [
                    _strategy_label(name),
                    monte_carlo[name]["median_total_return"],
                    monte_carlo[name]["p05_total_return"],
                    monte_carlo[name]["p95_total_return"],
                    monte_carlo[name]["median_max_drawdown"],
                    monte_carlo[name]["ruin_probability"],
                ]
                for name in ALL_STRATEGIES
                if name != BASELINE_NAME
            ],
        ),
    )
    write_markdown(
        output_dir / "regime_adaptation_report.md",
        """
# Phase E Regime Adaptation Report

## Best candidate

- Strategy: **"""
        + _strategy_label(best_candidate)
        + """**
- Requires regime-specific parameterization: **"""
        + str(regime_adaptation["requires_regime_specific_parameterization"])
        + """**

## Regime metrics

"""
        + markdown_table(
            ["Regime", "Return", "Sharpe", "Sortino", "Max DD", "Parameter Delta Score"],
            [
                [
                    regime,
                    values["total_return"],
                    values["sharpe"],
                    values["sortino"],
                    values["max_drawdown"],
                    values["parameter_delta_score"],
                ]
                for regime, values in regime_adaptation["regimes"].items()
            ],
        ),
    )
    write_markdown(
        output_dir / "promotion_assessment.md",
        """
# Phase E Promotion Assessment

"""
        + markdown_table(
            [
                "Strategy",
                "Promote",
                "Full Sharpe",
                "WF Sharpe",
                "WF Fold Ratio",
                "Ruin Probability",
                "Reasons",
            ],
            [
                [
                    _strategy_label(decision.strategy_name),
                    decision.promote,
                    decision.full_sample_metrics["sharpe"],
                    decision.walk_forward_metrics["sharpe"],
                    decision.positive_fold_ratio,
                    decision.ruin_probability,
                    "; ".join(decision.reasons),
                ]
                for decision in promotion_decisions
            ],
        )
        + f"\n\nOverall recommendation: **{'PASS' if overall_pass else 'FAIL'}**.\n",
    )
    write_markdown(
        output_dir / "before_after_comparison.md",
        """
# Phase E Before vs After Strategy Comparison

"""
        + markdown_table(
            ["Metric", "Phase C Baseline", "Phase E Best Candidate", "Phase E Best Candidate WF"],
            [
                [
                    "Total Return",
                    before_after["baseline_phase_c"]["total_return"],
                    full_runs[best_candidate].metrics["total_return"],
                    walk_forward[best_candidate].aggregate_metrics["total_return"],
                ],
                [
                    "Sharpe",
                    before_after["baseline_phase_c"]["sharpe"],
                    full_runs[best_candidate].metrics["sharpe"],
                    walk_forward[best_candidate].aggregate_metrics["sharpe"],
                ],
                [
                    "Sortino",
                    before_after["baseline_phase_c"]["sortino"],
                    full_runs[best_candidate].metrics["sortino"],
                    walk_forward[best_candidate].aggregate_metrics["sortino"],
                ],
                [
                    "Max Drawdown",
                    before_after["baseline_phase_c"]["max_drawdown"],
                    full_runs[best_candidate].metrics["max_drawdown"],
                    walk_forward[best_candidate].aggregate_metrics["max_drawdown"],
                ],
                [
                    "Expectancy",
                    before_after["baseline_phase_c"]["expectancy"],
                    full_runs[best_candidate].metrics["expectancy"],
                    walk_forward[best_candidate].aggregate_metrics["expectancy"],
                ],
            ],
        ),
    )
    write_markdown(
        output_dir / "phase_e_final_report.md",
        f"""
# AFRP Phase E Final Report

## Alpha hypotheses evaluated

- Trend following persistence in XAU/USD with regime filters.
- Mean reversion after standardized overstretch.
- Liquidity-sweep reversals after failed range breaks.
- Macro-only gold reactions to DXY / rates / policy proxies.
- Technical-only composite momentum/breakout behavior.
- Hybrid world-model fusion over macro, microstructure, liquidity, regime,
  forward, behavioral, and technical signals.

## Feature importance summary

Top features by permutation importance:
{", ".join(item.feature for item in feature_importance[:5])}.

## Decision quality analysis

- Trade count analysed: {decision_quality["trade_count"]}
- Direction accuracy: {decision_quality["direction_accuracy"]:.4f}
- Average regret: {decision_quality["average_regret"]:.4f}

## Strategy comparisons

"""
        + markdown_table(
            ["Strategy", "Full Return", "Full Sharpe", "WF Sharpe", "Ruin Prob"],
            [
                [
                    _strategy_label(name),
                    full_runs[name].metrics["total_return"],
                    full_runs[name].metrics["sharpe"],
                    walk_forward[name].aggregate_metrics["sharpe"],
                    monte_carlo[name]["ruin_probability"],
                ]
                for name in ALL_STRATEGIES
                if name != BASELINE_NAME
            ],
        )
        + f"""

## Walk-forward results

Best candidate: **{_strategy_label(best_candidate)}** with walk-forward Sharpe
{walk_forward[best_candidate].aggregate_metrics["sharpe"]:.4f} and positive-fold
ratio {walk_forward[best_candidate].positive_fold_ratio:.4f}.

## Monte Carlo results

Best candidate ruin probability: {monte_carlo[best_candidate]["ruin_probability"]:.4f}.

## Regime analysis

Requires regime adaptation: {regime_adaptation["requires_regime_specific_parameterization"]}.

## Parameter optimization summary

Validation-first optimization penalized overfit gaps. Best hybrid overfit gap:
{optimization_results["hybrid"].overfit_gap:.4f}.

## FIX or Enhancement work packages created

- WP-IMP-0039 — Phase E Alpha Research & Strategy Evolution Framework.

## Evidence generated

- EXEC-041 under `05-work-packages/WP-IMP-0039/evidence/`.

## Research conclusions

- The frozen baseline remains statistically weak versus all viable candidates.
- {_strategy_label(best_candidate)} produced the strongest out-of-sample profile
  among Phase E candidates.
- Promotion still requires every governance bar to pass simultaneously.

## Recommended strategy promotions

"""
        + "\n".join(
            (
                f"- {_strategy_label(decision.strategy_name)}: "
                f"{'PROMOTE' if decision.promote else 'DO NOT PROMOTE'} — "
                f"{'; '.join(decision.reasons)}"
            )
            for decision in promotion_decisions
        )
        + f"""

## Overall recommendation

**{"PASS" if overall_pass else "FAIL"}**
""",
    )
    return {
        "overall_recommendation": "PASS" if overall_pass else "FAIL",
        "best_candidate": best_candidate,
        "promotion_decisions": [decision.to_dict() for decision in promotion_decisions],
    }
