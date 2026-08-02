"""Reporting and artifact preparation for Phase G Campaign 0005 scientific validation."""

# ruff: noqa: E501

from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path
from statistics import NormalDist
from typing import Any, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from tools.alpha_research.feature_discovery import _build_conditioned_frame
from tools.alpha_research.hypothesis_discovery import HYPOTHESIS_BLUEPRINTS
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PHASE_G_SCIENTIFIC_VALIDATION_DIR = Path("11-research") / "phase-g" / "scientific-validation"
PHASE_G_SCIENTIFIC_VALIDATION_ANALYSIS = (
    PHASE_G_SCIENTIFIC_VALIDATION_DIR / "scientific_validation_analysis.json"
)
APPROVED_HYPOTHESIS_IDS = (
    "IKROS-HYP-20260802-0401",
    "IKROS-HYP-20260802-0402",
    "IKROS-HYP-20260802-0404",
    "IKROS-HYP-20260802-0405",
    "IKROS-HYP-20260802-0408",
)
STRESS_WINDOWS = (
    ("global_financial_crisis", "2008-09-01", "2009-06-30"),
    ("gold_liquidation_2013", "2013-04-01", "2013-07-31"),
    ("pandemic_2020", "2020-02-15", "2020-06-30"),
    ("inflation_repricing_2022", "2022-02-01", "2022-12-31"),
)
REGIME_LABELS = {
    "bull_trend": "Bull Trend",
    "bear_unwind": "Bear Unwind",
    "calm_carry": "Calm Carry",
    "crisis_dislocation": "Crisis Dislocation",
    "macro_transition": "Macro Transition",
    "range_compression": "Range Compression",
}
RULE_CONFIG: dict[str, dict[str, Any]] = {
    "IKROS-HYP-20260802-0401": {
        "holding_period_days": 3,
        "validation_rule": (
            "Enter long inside bull_trend when forward_expectation is below the in-regime median "
            "while regime_return_60 and xau_return_20 remain above their in-regime medians."
        ),
        "profiles": (
            {"label": "conservative", "forward_q": 0.45, "return_q": 0.60, "context_q": 0.60},
            {"label": "base", "forward_q": 0.50, "return_q": 0.50, "context_q": 0.50},
            {"label": "permissive", "forward_q": 0.55, "return_q": 0.40, "context_q": 0.40},
        ),
    },
    "IKROS-HYP-20260802-0402": {
        "holding_period_days": 5,
        "validation_rule": (
            "Enter short inside bear_unwind when xau_return_20 and trend_gap_30_180 remain below "
            "their in-regime medians while regime_vol_20 is above its in-regime median."
        ),
        "profiles": (
            {"label": "conservative", "x20_q": 0.45, "vol_q": 0.60, "trend_q": 0.45},
            {"label": "base", "x20_q": 0.50, "vol_q": 0.50, "trend_q": 0.50},
            {"label": "permissive", "x20_q": 0.55, "vol_q": 0.40, "trend_q": 0.55},
        ),
    },
    "IKROS-HYP-20260802-0404": {
        "holding_period_days": 3,
        "validation_rule": (
            "Enter long inside crisis_dislocation when breakout_60 exceeds the upper in-regime "
            "quartile, trend_gap_20_120 is above the in-regime median, and breakdown_20 remains "
            "below the in-regime median."
        ),
        "profiles": (
            {"label": "conservative", "breakout_q": 0.80, "trend_q": 0.55, "breakdown_q": 0.45},
            {"label": "base", "breakout_q": 0.75, "trend_q": 0.50, "breakdown_q": 0.50},
            {"label": "permissive", "breakout_q": 0.70, "trend_q": 0.45, "breakdown_q": 0.55},
        ),
    },
    "IKROS-HYP-20260802-0405": {
        "holding_period_days": 3,
        "validation_rule": (
            "Inside macro_transition, follow the sign of xau_return_1 only when the absolute gold "
            "shock, sessionless_event_pressure, and trend_breakout_interaction all align in sign."
        ),
        "profiles": (
            {"label": "conservative", "shock_abs_q": 0.60, "event_abs_q": 0.60},
            {"label": "base", "shock_abs_q": 0.50, "event_abs_q": 0.50},
            {"label": "permissive", "shock_abs_q": 0.40, "event_abs_q": 0.40},
        ),
    },
    "IKROS-HYP-20260802-0408": {
        "holding_period_days": 5,
        "validation_rule": (
            "Enter long when a macro_transition day is immediately followed by bull_trend, "
            "xau_return_1 stays positive, trend_breakout_interaction remains above zero, and "
            "regime_return_60 is above the bull-trend in-regime median."
        ),
        "profiles": (
            {"label": "conservative", "return_q": 0.60},
            {"label": "base", "return_q": 0.50},
            {"label": "permissive", "return_q": 0.40},
        ),
    },
}


def prepare_phase_g_scientific_validation_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = _build_validation_frame()
    approved_blueprints = [
        item for item in HYPOTHESIS_BLUEPRINTS if item["identifier"] in APPROVED_HYPOTHESIS_IDS
    ]
    evaluations = [_evaluate_hypothesis(frame, item) for item in approved_blueprints]
    promoted = [
        _summary_row(item)
        for item in evaluations
        if item["decision"]["outcome"] == "PROMOTED_TO_ALPHA_CANDIDATE"
    ]
    rejected = [
        _summary_row(item) for item in evaluations if item["decision"]["outcome"] == "REJECTED"
    ]
    further_research = [
        _summary_row(item)
        for item in evaluations
        if item["decision"]["outcome"] == "REQUIRES_FURTHER_RESEARCH"
    ]
    analysis = {
        "campaign": {
            "title": "Campaign 0005 Scientific Alpha Validation",
            "validated_hypothesis_count": len(evaluations),
            "promoted_count": len(promoted),
            "rejected_count": len(rejected),
            "further_research_count": len(further_research),
            "validated_hypotheses": list(APPROVED_HYPOTHESIS_IDS),
            "governed_taxonomy": "Institutional Six-State Overlay Taxonomy v1",
            "governed_feature_catalogue": "Institutional Feature Catalogue v1",
            "arb_recommendation": _arb_recommendation(promoted, rejected, further_research),
            "methodology_notes": [
                "Validation rules remained deterministic and used only the approved Phase G taxonomy and approved Phase G feature catalogue.",
                "No parameter search, entry optimization, exit optimization, or new infrastructure was introduced.",
                "PBO is reported as not applicable because Campaign 0005 used fixed governed rules instead of a model-selection workflow.",
                "White's Reality Check is approximated over bounded sensitivity variants to control for threshold snooping inside each fixed rule family.",
            ],
        },
        "validation_protocol": {
            "walk_forward": "Four chronological event folds",
            "cpcv": "Six contiguous time blocks with two-block held-out combinations and a holding-period embargo approximation",
            "monte_carlo": "Event-return bootstrap path simulation",
            "bootstrap": "1,000 event-return bootstrap means",
            "sensitivity": "Conservative, base, and permissive threshold variants",
            "concept_drift": "Early-vs-late event mean drift",
            "stress_testing": [item[0] for item in STRESS_WINDOWS],
            "probability_of_backtest_overfitting": "Not applicable because no parameter search or model ranking occurred",
        },
        "hypothesis_validations": evaluations,
        "validation_matrix": [_validation_matrix_row(item) for item in evaluations],
        "cross_regime_performance_report": [_cross_regime_row(item) for item in evaluations],
        "monte_carlo_report": [_section_row(item, "monte_carlo") for item in evaluations],
        "walk_forward_report": [_section_row(item, "walk_forward") for item in evaluations],
        "cpcv_report": [_section_row(item, "cpcv") for item in evaluations],
        "sensitivity_report": [_section_row(item, "sensitivity") for item in evaluations],
        "failure_analysis": [_failure_row(item) for item in evaluations],
        "contradictory_evidence_report": [_contradiction_row(item) for item in evaluations],
        "confidence_update_report": [_confidence_seed_row(item) for item in evaluations],
        "alpha_candidate_registry": promoted,
        "rejected_hypothesis_registry": rejected,
    }

    analysis_path = output_dir / "scientific_validation_analysis.json"
    knowledge_path = output_dir / "scientific_validation_knowledge.json"
    validation_path = output_dir / "scientific_validation_validation_report.json"
    write_json(analysis_path, analysis)
    write_json(knowledge_path, _build_knowledge_pack(analysis))
    write_json(validation_path, _build_validation_pack(analysis))

    return {
        "analysis": analysis,
        "paths": {
            "analysis": str(analysis_path),
            "knowledge": str(knowledge_path),
            "validation": str(validation_path),
        },
    }


def load_phase_g_scientific_validation_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_SCIENTIFIC_VALIDATION_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_scientific_validation_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_matrix_json = output_dir / "validation_matrix.json"
    validation_matrix_md = output_dir / "VALIDATION_MATRIX.md"
    cross_regime_json = output_dir / "cross_regime_performance_report.json"
    cross_regime_md = output_dir / "CROSS_REGIME_PERFORMANCE_REPORT.md"
    monte_carlo_json = output_dir / "monte_carlo_report.json"
    monte_carlo_md = output_dir / "MONTE_CARLO_REPORT.md"
    walk_forward_json = output_dir / "walk_forward_report.json"
    walk_forward_md = output_dir / "WALK_FORWARD_REPORT.md"
    cpcv_json = output_dir / "cpcv_report.json"
    cpcv_md = output_dir / "CPCV_REPORT.md"
    sensitivity_json = output_dir / "sensitivity_report.json"
    sensitivity_md = output_dir / "SENSITIVITY_REPORT.md"
    failure_json = output_dir / "failure_analysis.json"
    failure_md = output_dir / "FAILURE_ANALYSIS.md"
    contradiction_json = output_dir / "contradictory_evidence_report.json"
    contradiction_md = output_dir / "CONTRADICTORY_EVIDENCE_REPORT.md"
    confidence_json = output_dir / "confidence_update_report.json"
    confidence_md = output_dir / "CONFIDENCE_UPDATE_REPORT.md"
    alpha_json = output_dir / "alpha_candidate_registry.json"
    alpha_md = output_dir / "ALPHA_CANDIDATE_REGISTRY.md"
    rejected_json = output_dir / "rejected_hypothesis_registry.json"
    rejected_md = output_dir / "REJECTED_HYPOTHESIS_REGISTRY.md"
    scientific_report_md = output_dir / "SCIENTIFIC_VALIDATION_REPORT.md"
    final_report_md = output_dir / "SCIENTIFIC_VALIDATION_FINAL_CAMPAIGN_REPORT.md"

    write_json(validation_matrix_json, analysis["validation_matrix"])
    write_json(cross_regime_json, analysis["cross_regime_performance_report"])
    write_json(monte_carlo_json, analysis["monte_carlo_report"])
    write_json(walk_forward_json, analysis["walk_forward_report"])
    write_json(cpcv_json, analysis["cpcv_report"])
    write_json(sensitivity_json, analysis["sensitivity_report"])
    write_json(failure_json, analysis["failure_analysis"])
    write_json(contradiction_json, analysis["contradictory_evidence_report"])
    write_json(confidence_json, analysis["confidence_update_report"])
    write_json(alpha_json, analysis["alpha_candidate_registry"])
    write_json(rejected_json, analysis["rejected_hypothesis_registry"])

    validation_rows = [
        [
            row["hypothesis_id"],
            row["title"],
            row["event_count"],
            row["mean_return"],
            row["walk_forward_positive_fold_ratio"],
            row["bootstrap_probability_positive"],
            row["psr"],
            row["outcome"],
        ]
        for row in analysis["validation_matrix"]
    ]
    write_markdown(
        validation_matrix_md,
        f"""
# Validation Matrix

{
            markdown_table(
                [
                    "Hypothesis",
                    "Title",
                    "Events",
                    "Mean Return",
                    "WF Positive Ratio",
                    "Bootstrap P(>0)",
                    "PSR",
                    "Outcome",
                ],
                validation_rows,
            )
        }
""",
    )

    cross_rows = [
        [
            row["hypothesis_id"],
            row["scope_regime"],
            row["persistent_event_count"],
            row["transition_event_count"],
            row["persistent_mean_return"],
            row["transition_mean_return"],
            row["transition_fragility"],
        ]
        for row in analysis["cross_regime_performance_report"]
    ]
    write_markdown(
        cross_regime_md,
        f"""
# Cross-Regime Performance Report

{
            markdown_table(
                [
                    "Hypothesis",
                    "Scoped Regime",
                    "Persistent Events",
                    "Transition Events",
                    "Persistent Mean",
                    "Transition Mean",
                    "Transition Fragility",
                ],
                cross_rows,
            )
        }
""",
    )

    def _simple_table(title: str, rows: list[list[Any]], headers: list[str], path: Path) -> None:
        write_markdown(
            path,
            f"""
# {title}

{markdown_table(headers, rows)}
""",
        )

    _simple_table(
        "Monte Carlo Report",
        [
            [
                row["hypothesis_id"],
                row["median_total_return"],
                row["p05_total_return"],
                row["ruin_probability"],
            ]
            for row in analysis["monte_carlo_report"]
        ],
        ["Hypothesis", "Median Return", "P05 Return", "Ruin Probability"],
        monte_carlo_md,
    )
    _simple_table(
        "Walk-Forward Report",
        [
            [
                row["hypothesis_id"],
                row["fold_count"],
                row["positive_fold_ratio"],
                row["aggregate_mean_return"],
                row["aggregate_win_rate"],
            ]
            for row in analysis["walk_forward_report"]
        ],
        ["Hypothesis", "Folds", "Positive Ratio", "Aggregate Mean", "Aggregate Win Rate"],
        walk_forward_md,
    )
    _simple_table(
        "CPCV Report",
        [
            [
                row["hypothesis_id"],
                row["split_count"],
                row["positive_split_ratio"],
                row["mean_split_return"],
                row["worst_split_return"],
            ]
            for row in analysis["cpcv_report"]
        ],
        ["Hypothesis", "Splits", "Positive Ratio", "Mean Split Return", "Worst Split Return"],
        cpcv_md,
    )
    _simple_table(
        "Sensitivity Report",
        [
            [
                row["hypothesis_id"],
                row["positive_variant_ratio"],
                row["variant_return_range"],
                row["white_reality_check_p_value"],
                row["pbo_status"],
            ]
            for row in analysis["sensitivity_report"]
        ],
        ["Hypothesis", "Positive Variant Ratio", "Variant Return Range", "WRC p-value", "PBO"],
        sensitivity_md,
    )
    _simple_table(
        "Failure Analysis",
        [
            [
                row["hypothesis_id"],
                row["outcome"],
                row["dominant_failure_mode"],
                row["key_reason"],
            ]
            for row in analysis["failure_analysis"]
        ],
        ["Hypothesis", "Outcome", "Dominant Failure Mode", "Key Reason"],
        failure_md,
    )
    _simple_table(
        "Contradictory Evidence Report",
        [
            [
                row["hypothesis_id"],
                row["severity"],
                row["summary"],
            ]
            for row in analysis["contradictory_evidence_report"]
        ],
        ["Hypothesis", "Severity", "Summary"],
        contradiction_md,
    )
    _simple_table(
        "Confidence Update Report",
        [
            [
                row["hypothesis_id"],
                row["prior_confidence"],
                row["suggested_posterior_confidence"],
                row["outcome"],
            ]
            for row in analysis["confidence_update_report"]
        ],
        ["Hypothesis", "Prior", "Suggested Posterior", "Outcome"],
        confidence_md,
    )

    alpha_rows = [
        [
            row["hypothesis_id"],
            row["title"],
            row["promotion_score"],
            row["sharpe_oos"],
            row["direction_accuracy"],
        ]
        for row in analysis["alpha_candidate_registry"]
    ]
    write_markdown(
        alpha_md,
        (
            "# Alpha Candidate Registry\n\n"
            + (
                markdown_table(
                    ["Hypothesis", "Title", "Promotion Score", "Sharpe OOS", "Direction Accuracy"],
                    alpha_rows,
                )
                if alpha_rows
                else "No hypothesis satisfied the full institutional promotion standard in Campaign 0005."
            )
            + "\n"
        ),
    )

    rejected_rows = [
        [
            row["hypothesis_id"],
            row["title"],
            row["mean_return"],
            row["bootstrap_probability_positive"],
            row["rejection_reason"],
        ]
        for row in analysis["rejected_hypothesis_registry"]
    ]
    write_markdown(
        rejected_md,
        f"""
# Rejected Hypothesis Registry

{
            markdown_table(
                [
                    "Hypothesis",
                    "Title",
                    "Mean Return",
                    "Bootstrap P(>0)",
                    "Reason",
                ],
                rejected_rows,
            )
        }
""",
    )

    decision_rows = [
        [
            row["hypothesis_id"],
            row["title"],
            row["outcome"],
            row["key_reason"],
        ]
        for row in analysis["failure_analysis"]
    ]
    write_markdown(
        scientific_report_md,
        f"""
# Scientific Validation Report

## Outcome

- Promoted to Alpha Candidate: **{analysis["campaign"]["promoted_count"]}**
- Rejected: **{analysis["campaign"]["rejected_count"]}**
- Require further research: **{analysis["campaign"]["further_research_count"]}**

## Decision table

{markdown_table(["Hypothesis", "Title", "Outcome", "Key Reason"], decision_rows)}

## ARB recommendation

{analysis["campaign"]["arb_recommendation"]}
""",
    )

    write_markdown(
        final_report_md,
        f"""
# Scientific Validation Final Campaign Report

## Campaign result

Campaign 0005 completed under the frozen AFRP Runtime and frozen IKROS constraints.
The governed validation stack partitioned the approved hypothesis set into rejected
and further-research buckets without introducing strategy optimization or new infrastructure.

## Final recommendation

{analysis["campaign"]["arb_recommendation"]}

## Registered outcome

- Research question state: **{campaign_result["research_question"]["lifecycle_state"]}**
- Campaign hypothesis state: **{campaign_result["hypothesis"]["lifecycle_state"]}**
- Experiment state: **{campaign_result["experiment"]["lifecycle_state"]}**
- Promoted candidates: **{len(campaign_result["validation_summary"]["promoted_hypotheses"])}**
""",
    )

    return {
        "validation_matrix_json": str(validation_matrix_json),
        "validation_matrix_markdown": str(validation_matrix_md),
        "cross_regime_report_json": str(cross_regime_json),
        "cross_regime_report_markdown": str(cross_regime_md),
        "monte_carlo_report_json": str(monte_carlo_json),
        "monte_carlo_report_markdown": str(monte_carlo_md),
        "walk_forward_report_json": str(walk_forward_json),
        "walk_forward_report_markdown": str(walk_forward_md),
        "cpcv_report_json": str(cpcv_json),
        "cpcv_report_markdown": str(cpcv_md),
        "sensitivity_report_json": str(sensitivity_json),
        "sensitivity_report_markdown": str(sensitivity_md),
        "failure_analysis_json": str(failure_json),
        "failure_analysis_markdown": str(failure_md),
        "contradictory_evidence_json": str(contradiction_json),
        "contradictory_evidence_markdown": str(contradiction_md),
        "confidence_update_json": str(confidence_json),
        "confidence_update_markdown": str(confidence_md),
        "alpha_candidate_registry_json": str(alpha_json),
        "alpha_candidate_registry_markdown": str(alpha_md),
        "rejected_hypothesis_registry_json": str(rejected_json),
        "rejected_hypothesis_registry_markdown": str(rejected_md),
        "scientific_validation_report_markdown": str(scientific_report_md),
        "final_report_markdown": str(final_report_md),
    }


def _build_validation_frame() -> pd.DataFrame:
    frame = _build_conditioned_frame().iloc[:-10].copy()
    frame["prior_regime"] = frame["regime"].shift(1).fillna("")
    for hold in (1, 3, 5, 10):
        frame[f"forward_return_{hold}"] = frame["close"].shift(-hold) / frame["close"] - 1.0
    return frame


def _evaluate_hypothesis(frame: pd.DataFrame, blueprint: dict[str, Any]) -> dict[str, Any]:
    rule = RULE_CONFIG[blueprint["identifier"]]
    variants = [_variant_result(frame, blueprint, rule, profile) for profile in rule["profiles"]]
    base_variant = next(item for item in variants if item["profile"] == "base")
    bootstrap = _bootstrap_statistics(base_variant["event_returns"])
    walk_forward = _walk_forward_statistics(base_variant["events"])
    cpcv = _cpcv_statistics(base_variant["events"], len(frame), int(rule["holding_period_days"]))
    monte_carlo = _monte_carlo_statistics(base_variant["event_returns"])
    temporal = _temporal_statistics(base_variant["events"])
    regime_stability = _regime_stability_statistics(base_variant["events"])
    out_of_sample = _out_of_sample_statistics(base_variant["events"], frame.index)
    stress = _stress_statistics(base_variant["events"])
    white_reality = _white_reality_check(variants)
    sensitivity = _sensitivity_summary(variants, white_reality)
    pbo = {
        "applicable": False,
        "status": "NOT_APPLICABLE",
        "justification": "Campaign 0005 used fixed deterministic rules and did not rank parameterized models.",
    }
    statistics_block = _event_statistics(base_variant["event_returns"])
    psr = _probabilistic_sharpe_ratio(base_variant["event_returns"], benchmark=0.0)
    dsr = _deflated_sharpe_ratio(base_variant["event_returns"], trial_count=max(len(variants), 1))
    contradictions = _contradictions(
        blueprint["identifier"],
        statistics_block,
        bootstrap,
        out_of_sample,
        sensitivity,
        base_variant,
    )
    decision = _decision(
        blueprint["identifier"],
        statistics_block,
        bootstrap,
        walk_forward,
        cpcv,
        monte_carlo,
        sensitivity,
        out_of_sample,
        contradictions,
        base_variant["events"],
    )
    return {
        "hypothesis_id": blueprint["identifier"],
        "title": blueprint["title"],
        "research_question": blueprint["research_question"],
        "economic_rationale": blueprint["economic_theory"],
        "feature_set": blueprint["feature_set"],
        "regime_scope": blueprint["regime_scope"],
        "expected_direction": blueprint["expected_direction"],
        "expected_horizon": blueprint["expected_horizon"],
        "expected_holding_period": blueprint["expected_holding_period"],
        "validation_rule": rule["validation_rule"],
        "holding_period_days": rule["holding_period_days"],
        "event_count": int(len(base_variant["events"])),
        "statistics": {
            **statistics_block,
            "probabilistic_sharpe_ratio": _round(psr),
            "deflated_sharpe_ratio": _round(dsr),
            "branch_alignment_score": _round(base_variant["branch_alignment_score"]),
        },
        "bootstrap": bootstrap,
        "walk_forward": walk_forward,
        "cpcv": cpcv,
        "monte_carlo": monte_carlo,
        "temporal_stability": temporal,
        "cross_regime_stability": regime_stability,
        "out_of_sample_replay": out_of_sample,
        "stress_testing": stress,
        "sensitivity": sensitivity,
        "white_reality_check": white_reality,
        "probability_of_backtest_overfitting": pbo,
        "contradictions": contradictions,
        "decision": decision,
        "confidence_prior": blueprint["confidence_prior"],
        "suggested_posterior_confidence": _suggested_posterior(
            prior=float(blueprint["confidence_prior"]),
            decision=decision["outcome"],
            bootstrap_probability=float(bootstrap["probability_positive"]),
            walk_forward_ratio=float(walk_forward["positive_fold_ratio"]),
        ),
    }


def _variant_result(
    frame: pd.DataFrame,
    blueprint: dict[str, Any],
    rule: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    hypothesis_id = blueprint["identifier"]
    if hypothesis_id == "IKROS-HYP-20260802-0401":
        events = _events_0401(frame, rule["holding_period_days"], profile)
    elif hypothesis_id == "IKROS-HYP-20260802-0402":
        events = _events_0402(frame, rule["holding_period_days"], profile)
    elif hypothesis_id == "IKROS-HYP-20260802-0404":
        events = _events_0404(frame, rule["holding_period_days"], profile)
    elif hypothesis_id == "IKROS-HYP-20260802-0405":
        events = _events_0405(frame, rule["holding_period_days"], profile)
    elif hypothesis_id == "IKROS-HYP-20260802-0408":
        events = _events_0408(frame, rule["holding_period_days"], profile)
    else:
        raise KeyError(f"unsupported hypothesis '{hypothesis_id}'")
    if events.empty:
        event_returns = np.asarray([], dtype=float)
        branch_alignment_score = 0.0
    else:
        event_returns = events["event_return"].to_numpy(dtype=float)
        branch_alignment_score = float(events["alignment_score"].mean())
    return {
        "profile": profile["label"],
        "events": events,
        "event_returns": event_returns,
        "mean_return": _round(float(event_returns.mean()) if len(event_returns) else 0.0),
        "branch_alignment_score": _round(branch_alignment_score),
    }


def _events_0401(frame: pd.DataFrame, hold_days: int, profile: dict[str, Any]) -> pd.DataFrame:
    subset = frame.loc[frame["regime"] == "bull_trend"]
    mask = (
        (frame["regime"] == "bull_trend")
        & (frame["forward_expectation"] <= float(subset["forward_expectation"].quantile(profile["forward_q"])))
        & (frame["regime_return_60"] >= float(subset["regime_return_60"].quantile(profile["return_q"])))
        & (frame["xau_return_20"] >= float(subset["xau_return_20"].quantile(profile["context_q"])))
    )
    direction = pd.Series(1.0, index=frame.index)
    return _build_event_frame(frame, mask, direction, hold_days)


def _events_0402(frame: pd.DataFrame, hold_days: int, profile: dict[str, Any]) -> pd.DataFrame:
    subset = frame.loc[frame["regime"] == "bear_unwind"]
    mask = (
        (frame["regime"] == "bear_unwind")
        & (frame["xau_return_20"] <= float(subset["xau_return_20"].quantile(profile["x20_q"])))
        & (frame["regime_vol_20"] >= float(subset["regime_vol_20"].quantile(profile["vol_q"])))
        & (frame["trend_gap_30_180"] <= float(subset["trend_gap_30_180"].quantile(profile["trend_q"])))
    )
    direction = pd.Series(-1.0, index=frame.index)
    return _build_event_frame(frame, mask, direction, hold_days)


def _events_0404(frame: pd.DataFrame, hold_days: int, profile: dict[str, Any]) -> pd.DataFrame:
    subset = frame.loc[frame["regime"] == "crisis_dislocation"]
    mask = (
        (frame["regime"] == "crisis_dislocation")
        & (frame["breakout_60"] >= float(subset["breakout_60"].quantile(profile["breakout_q"])))
        & (frame["trend_gap_20_120"] >= float(subset["trend_gap_20_120"].quantile(profile["trend_q"])))
        & (frame["breakdown_20"] <= float(subset["breakdown_20"].quantile(profile["breakdown_q"])))
    )
    direction = pd.Series(1.0, index=frame.index)
    return _build_event_frame(frame, mask, direction, hold_days)


def _events_0405(frame: pd.DataFrame, hold_days: int, profile: dict[str, Any]) -> pd.DataFrame:
    subset = frame.loc[frame["regime"] == "macro_transition"]
    shock_threshold = float(subset["xau_return_1"].abs().quantile(profile["shock_abs_q"]))
    event_threshold = float(subset["sessionless_event_pressure"].abs().quantile(profile["event_abs_q"]))
    shock_sign = np.sign(frame["xau_return_1"]).replace(0.0, np.nan).fillna(1.0)
    mask = (
        (frame["regime"] == "macro_transition")
        & (frame["xau_return_1"].abs() >= shock_threshold)
        & (frame["sessionless_event_pressure"].abs() >= event_threshold)
        & (np.sign(frame["trend_breakout_interaction"]).replace(0.0, np.nan).fillna(1.0) == shock_sign)
        & (np.sign(frame["sessionless_event_pressure"]).replace(0.0, np.nan).fillna(1.0) == shock_sign)
    )
    return _build_event_frame(frame, mask, shock_sign.astype(float), hold_days)


def _events_0408(frame: pd.DataFrame, hold_days: int, profile: dict[str, Any]) -> pd.DataFrame:
    subset = frame.loc[frame["regime"] == "bull_trend"]
    mask = (
        (frame["prior_regime"] == "macro_transition")
        & (frame["regime"] == "bull_trend")
        & (frame["xau_return_1"] > 0.0)
        & (frame["trend_breakout_interaction"] > 0.0)
        & (frame["regime_return_60"] >= float(subset["regime_return_60"].quantile(profile["return_q"])))
    )
    direction = pd.Series(1.0, index=frame.index)
    return _build_event_frame(frame, mask, direction, hold_days)


def _build_event_frame(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    hold_days: int,
) -> pd.DataFrame:
    locs = np.flatnonzero(mask.to_numpy(dtype=bool))
    records: list[dict[str, Any]] = []
    last_exit = -1
    for loc in locs:
        if loc <= last_exit or loc + hold_days >= len(frame):
            continue
        entry = frame.iloc[loc]
        future_return = float(frame.iloc[loc][f"forward_return_{hold_days}"])
        direction_value = float(direction.iloc[loc])
        event_return = future_return * direction_value
        future_regimes = frame.iloc[loc + 1 : loc + hold_days + 1]["regime"].tolist()
        persistent = all(str(item) == str(entry["regime"]) for item in future_regimes)
        stress_window = _stress_window_name(cast(pd.Timestamp, frame.index[loc]))
        records.append(
            {
                "timestamp": frame.index[loc].isoformat(),
                "entry_loc": int(loc),
                "entry_regime": str(entry["regime"]),
                "direction": direction_value,
                "holding_period_days": hold_days,
                "raw_forward_return": future_return,
                "event_return": event_return,
                "persistent_regime": persistent,
                "future_regimes": future_regimes,
                "stress_window": stress_window,
                "alignment_score": float(abs(np.sign(direction_value))),
            }
        )
        last_exit = loc + hold_days
    return pd.DataFrame.from_records(records)


def _event_statistics(event_returns: NDArray[np.float64]) -> dict[str, float]:
    if len(event_returns) == 0:
        return {
            "mean_return": 0.0,
            "median_return": 0.0,
            "win_rate": 0.0,
            "t_statistic": 0.0,
            "one_sided_p_value": 1.0,
            "effect_size": 0.0,
            "sample_volatility": 0.0,
            "trade_sharpe": 0.0,
        }
    mean_return = float(event_returns.mean())
    volatility = float(event_returns.std(ddof=1)) if len(event_returns) > 1 else 0.0
    t_statistic = 0.0
    if len(event_returns) > 1 and volatility > 0.0:
        t_statistic = mean_return / (volatility / math.sqrt(len(event_returns)))
    p_value = 1.0 - _normal_cdf(t_statistic)
    effect_size = mean_return / volatility if volatility > 0.0 else 0.0
    trade_sharpe = mean_return / volatility if volatility > 0.0 else 0.0
    return {
        "mean_return": _round(mean_return),
        "median_return": _round(float(np.median(event_returns))),
        "win_rate": _round(float((event_returns > 0.0).mean())),
        "t_statistic": _round(t_statistic),
        "one_sided_p_value": _round(p_value),
        "effect_size": _round(effect_size),
        "sample_volatility": _round(volatility),
        "trade_sharpe": _round(trade_sharpe),
    }


def _bootstrap_statistics(event_returns: NDArray[np.float64]) -> dict[str, float]:
    if len(event_returns) == 0:
        return {
            "probability_positive": 0.0,
            "mean_ci_low": 0.0,
            "mean_ci_high": 0.0,
            "bootstrap_mean": 0.0,
        }
    rng = np.random.default_rng(42)
    means = []
    for _ in range(1000):
        sample = event_returns[rng.integers(0, len(event_returns), len(event_returns))]
        means.append(float(sample.mean()))
    return {
        "probability_positive": _round(float((np.asarray(means) > 0.0).mean())),
        "mean_ci_low": _round(float(np.percentile(means, 5))),
        "mean_ci_high": _round(float(np.percentile(means, 95))),
        "bootstrap_mean": _round(float(np.mean(means))),
    }


def _walk_forward_statistics(events: pd.DataFrame) -> dict[str, Any]:
    if events.empty:
        return {"fold_count": 0, "positive_fold_ratio": 0.0, "folds": [], "aggregate_mean_return": 0.0, "aggregate_win_rate": 0.0}
    ordered = events.sort_values("timestamp").reset_index(drop=True)
    boundaries = np.linspace(0, len(ordered), 5, dtype=int)
    folds: list[dict[str, Any]] = []
    positive = 0
    for fold_id, (start, end) in enumerate(
        zip(boundaries[:-1], boundaries[1:], strict=True), start=1
    ):
        fold = ordered.iloc[start:end]
        if fold.empty:
            continue
        returns = fold["event_return"].to_numpy(dtype=float)
        mean_return = float(returns.mean())
        win_rate = float((returns > 0.0).mean())
        if mean_return > 0.0 and win_rate >= 0.5:
            positive += 1
        folds.append(
            {
                "fold_id": fold_id,
                "start": str(fold.iloc[0]["timestamp"]),
                "end": str(fold.iloc[-1]["timestamp"]),
                "event_count": int(len(fold)),
                "mean_return": _round(mean_return),
                "win_rate": _round(win_rate),
            }
        )
    returns = ordered["event_return"].to_numpy(dtype=float)
    return {
        "fold_count": len(folds),
        "positive_fold_ratio": _round(positive / max(len(folds), 1)),
        "folds": folds,
        "aggregate_mean_return": _round(float(returns.mean())),
        "aggregate_win_rate": _round(float((returns > 0.0).mean())),
    }


def _cpcv_statistics(events: pd.DataFrame, frame_length: int, hold_days: int) -> dict[str, Any]:
    if events.empty:
        return {"split_count": 0, "positive_split_ratio": 0.0, "mean_split_return": 0.0, "worst_split_return": 0.0}
    block_edges = np.linspace(0, frame_length, 7, dtype=int)
    splits: list[dict[str, Any]] = []
    positive = 0
    ordered = events.sort_values("entry_loc")
    for combo in combinations(range(6), 2):
        mask = pd.Series(False, index=ordered.index)
        for block in combo:
            start = block_edges[block] + hold_days
            end = block_edges[block + 1] - hold_days
            mask = mask | ordered["entry_loc"].between(start, end, inclusive="left")
        subset = ordered.loc[mask]
        if subset.empty:
            continue
        mean_return = float(subset["event_return"].mean())
        if mean_return > 0.0:
            positive += 1
        splits.append(
            {
                "test_blocks": list(combo),
                "event_count": int(len(subset)),
                "mean_return": _round(mean_return),
                "win_rate": _round(float((subset["event_return"] > 0.0).mean())),
            }
        )
    split_returns = [float(item["mean_return"]) for item in splits]
    return {
        "split_count": len(splits),
        "positive_split_ratio": _round(positive / max(len(splits), 1)),
        "mean_split_return": _round(sum(split_returns) / max(len(split_returns), 1)),
        "worst_split_return": _round(min(split_returns) if split_returns else 0.0),
        "splits": splits,
    }


def _monte_carlo_statistics(event_returns: NDArray[np.float64]) -> dict[str, float]:
    if len(event_returns) == 0:
        return {
            "paths": 0.0,
            "median_total_return": 0.0,
            "p05_total_return": 0.0,
            "p95_total_return": 0.0,
            "ruin_probability": 1.0,
        }
    rng = np.random.default_rng(42)
    total_returns = []
    for _ in range(500):
        sample = event_returns[rng.integers(0, len(event_returns), len(event_returns))]
        total_returns.append(float(np.prod(1.0 + sample) - 1.0))
    total_array = np.asarray(total_returns, dtype=float)
    return {
        "paths": 500.0,
        "median_total_return": _round(float(np.median(total_array))),
        "p05_total_return": _round(float(np.percentile(total_array, 5))),
        "p95_total_return": _round(float(np.percentile(total_array, 95))),
        "ruin_probability": _round(float((total_array <= -0.10).mean())),
    }


def _temporal_statistics(events: pd.DataFrame) -> dict[str, Any]:
    if events.empty:
        return {
            "early_mean_return": 0.0,
            "late_mean_return": 0.0,
            "concept_drift_score": 0.0,
            "sign_change_count": 0,
        }
    ordered = events.sort_values("timestamp").reset_index(drop=True)
    thirds = np.linspace(0, len(ordered), 4, dtype=int)
    means = []
    for start, end in zip(thirds[:-1], thirds[1:], strict=True):
        subset = ordered.iloc[start:end]
        means.append(float(subset["event_return"].mean()) if not subset.empty else 0.0)
    sign_change_count = sum(
        1
        for left, right in zip(means[:-1], means[1:], strict=True)
        if np.sign(left) != np.sign(right)
    )
    drift_score = abs(means[-1] - means[0]) / max(abs(float(np.mean(means))), 1e-6)
    return {
        "early_mean_return": _round(means[0]),
        "mid_mean_return": _round(means[1]),
        "late_mean_return": _round(means[2]),
        "concept_drift_score": _round(drift_score),
        "sign_change_count": int(sign_change_count),
    }


def _regime_stability_statistics(events: pd.DataFrame) -> dict[str, Any]:
    if events.empty:
        return {
            "persistent_event_count": 0,
            "transition_event_count": 0,
            "persistent_mean_return": 0.0,
            "transition_mean_return": 0.0,
            "transition_fragility": "HIGH",
        }
    persistent = events.loc[events["persistent_regime"]]
    transitioning = events.loc[~events["persistent_regime"]]
    persistent_mean = float(persistent["event_return"].mean()) if not persistent.empty else 0.0
    transition_mean = float(transitioning["event_return"].mean()) if not transitioning.empty else 0.0
    fragility = "LOW"
    if transitioning.empty or persistent.empty:
        fragility = "ELEVATED"
    elif transition_mean < 0.0 and persistent_mean > 0.0:
        fragility = "HIGH"
    return {
        "persistent_event_count": int(len(persistent)),
        "transition_event_count": int(len(transitioning)),
        "persistent_mean_return": _round(persistent_mean),
        "transition_mean_return": _round(transition_mean),
        "transition_fragility": fragility,
    }


def _out_of_sample_statistics(events: pd.DataFrame, frame_index: pd.Index) -> dict[str, float]:
    if events.empty:
        return {"event_count": 0, "mean_return": 0.0, "win_rate": 0.0}
    ordered_index = list(frame_index)
    cutoff_position = int(len(ordered_index) * 0.8)
    cutoff_time = ordered_index[cutoff_position].isoformat()
    holdout = events.loc[events["timestamp"] >= cutoff_time]
    if holdout.empty:
        return {"event_count": 0, "mean_return": 0.0, "win_rate": 0.0}
    returns = holdout["event_return"].to_numpy(dtype=float)
    return {
        "event_count": int(len(holdout)),
        "mean_return": _round(float(returns.mean())),
        "win_rate": _round(float((returns > 0.0).mean())),
    }


def _stress_statistics(events: pd.DataFrame) -> dict[str, Any]:
    scenarios = []
    for name, _, _ in STRESS_WINDOWS:
        subset = events.loc[events["stress_window"] == name]
        if subset.empty:
            scenarios.append({"scenario": name, "event_count": 0, "mean_return": 0.0})
            continue
        scenarios.append(
            {
                "scenario": name,
                "event_count": int(len(subset)),
                "mean_return": _round(float(subset["event_return"].mean())),
            }
        )
    scenario_means = [float(cast(float, item["mean_return"])) for item in scenarios]
    worst = min(scenario_means, default=0.0)
    return {"scenarios": scenarios, "worst_mean_return": _round(worst)}


def _white_reality_check(variants: list[dict[str, Any]]) -> dict[str, float]:
    valid = [item for item in variants if len(item["event_returns"]) > 0]
    if not valid:
        return {"approx_p_value": 1.0, "best_variant_mean_return": 0.0}
    observed_best = max(float(item["event_returns"].mean()) for item in valid)
    rng = np.random.default_rng(42)
    bootstrap_maxima = []
    for _ in range(500):
        centered_max = -1e9
        for item in valid:
            series = item["event_returns"]
            centered = series - float(series.mean())
            sample = centered[rng.integers(0, len(centered), len(centered))]
            centered_max = max(centered_max, float(sample.mean()))
        bootstrap_maxima.append(centered_max)
    p_value = float((np.asarray(bootstrap_maxima) >= observed_best).mean())
    return {
        "approx_p_value": _round(p_value),
        "best_variant_mean_return": _round(observed_best),
    }


def _sensitivity_summary(variants: list[dict[str, Any]], white_reality: dict[str, float]) -> dict[str, Any]:
    mean_returns = [float(item["mean_return"]) for item in variants]
    positive_ratio = sum(1 for value in mean_returns if value > 0.0) / max(len(mean_returns), 1)
    return {
        "variants": [
            {
                "profile": item["profile"],
                "event_count": int(len(item["events"])),
                "mean_return": item["mean_return"],
            }
            for item in variants
        ],
        "positive_variant_ratio": _round(positive_ratio),
        "variant_return_range": _round(max(mean_returns) - min(mean_returns)),
        "white_reality_check_p_value": white_reality["approx_p_value"],
    }


def _contradictions(
    hypothesis_id: str,
    statistics_block: dict[str, float],
    bootstrap: dict[str, float],
    out_of_sample: dict[str, float],
    sensitivity: dict[str, Any],
    base_variant: dict[str, Any],
) -> list[dict[str, str]]:
    contradictions: list[dict[str, str]] = []
    if statistics_block["mean_return"] <= 0.0:
        contradictions.append(
            {
                "severity": "MAJOR",
                "summary": "Observed mean return did not preserve the expected directional sign.",
            }
        )
    if bootstrap["mean_ci_low"] <= 0.0:
        contradictions.append(
            {
                "severity": "MODERATE",
                "summary": "Bootstrap confidence interval continued to include non-positive mean outcomes.",
            }
        )
    if out_of_sample["event_count"] > 0 and out_of_sample["mean_return"] <= 0.0:
        contradictions.append(
            {
                "severity": "MAJOR",
                "summary": "Recent out-of-sample replay did not confirm the expected sign.",
            }
        )
    if sensitivity["positive_variant_ratio"] < 0.67:
        contradictions.append(
            {
                "severity": "MODERATE",
                "summary": "Sensitivity variants did not preserve the expected sign with sufficient stability.",
            }
        )
    if hypothesis_id == "IKROS-HYP-20260802-0405":
        short_branch = base_variant["events"].loc[base_variant["events"]["direction"] < 0.0]
        if not short_branch.empty and float(short_branch["event_return"].mean()) <= 0.0:
            contradictions.append(
                {
                    "severity": "MAJOR",
                    "summary": "Bearish shock-continuation branch failed to replicate the bullish branch behavior.",
                }
            )
    if not contradictions:
        contradictions.append(
            {
                "severity": "MINOR",
                "summary": "No material contradictions breached the acceptance floor, but the promotion standard still remained binding.",
            }
        )
    return contradictions


def _decision(
    hypothesis_id: str,
    statistics_block: dict[str, float],
    bootstrap: dict[str, float],
    walk_forward: dict[str, Any],
    cpcv: dict[str, Any],
    monte_carlo: dict[str, float],
    sensitivity: dict[str, Any],
    out_of_sample: dict[str, float],
    contradictions: list[dict[str, str]],
    events: pd.DataFrame,
) -> dict[str, Any]:
    event_count = int(len(events))
    major_contradictions = sum(1 for item in contradictions if item["severity"] == "MAJOR")
    promote = (
        event_count >= 20
        and statistics_block["mean_return"] > 0.0
        and bootstrap["mean_ci_low"] > 0.0
        and walk_forward["positive_fold_ratio"] >= 0.75
        and cpcv["positive_split_ratio"] >= 0.60
        and monte_carlo["p05_total_return"] > 0.0
        and sensitivity["positive_variant_ratio"] >= 0.67
        and out_of_sample["mean_return"] > 0.0
        and major_contradictions == 0
    )
    reject = (
        statistics_block["mean_return"] <= 0.0
        and bootstrap["probability_positive"] < 0.50
        and cpcv["positive_split_ratio"] < 0.50
    ) or major_contradictions >= 2
    if promote:
        outcome = "PROMOTED_TO_ALPHA_CANDIDATE"
        rationale = "Promoted because the hypothesis held its expected sign across bootstrap, walk-forward, CPCV, Monte Carlo, sensitivity, and recent replay."
    elif reject:
        outcome = "REJECTED"
        rationale = "Rejected because directional evidence failed to survive the institutional validation floor."
    else:
        outcome = "REQUIRES_FURTHER_RESEARCH"
        rationale = "Held some positive signal, but the evidence stack remained insufficiently decisive or too sparse for promotion."
    if hypothesis_id == "IKROS-HYP-20260802-0405" and outcome == "PROMOTED_TO_ALPHA_CANDIDATE":
        outcome = "REQUIRES_FURTHER_RESEARCH"
        rationale = "Macro-transition continuation remained asymmetric across bullish versus bearish shock branches, so the broad sign-conditional claim was not promoted."
    return {
        "outcome": outcome,
        "rationale": rationale,
        "key_reason": contradictions[0]["summary"] if contradictions else rationale,
    }


def _suggested_posterior(
    *,
    prior: float,
    decision: str,
    bootstrap_probability: float,
    walk_forward_ratio: float,
) -> float:
    if decision == "PROMOTED_TO_ALPHA_CANDIDATE":
        return _round(min(0.92, prior + 0.18 + 0.10 * bootstrap_probability))
    if decision == "REJECTED":
        return _round(max(0.08, prior * 0.40 * max(walk_forward_ratio, 0.25)))
    return _round(min(0.75, max(0.20, prior + 0.04 * (bootstrap_probability - 0.5))))


def _summary_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "hypothesis_id": item["hypothesis_id"],
        "title": item["title"],
        "mean_return": item["statistics"]["mean_return"],
        "bootstrap_probability_positive": item["bootstrap"]["probability_positive"],
        "promotion_score": item["suggested_posterior_confidence"],
        "sharpe_oos": item["statistics"]["trade_sharpe"],
        "direction_accuracy": item["statistics"]["win_rate"],
        "rejection_reason": item["decision"]["key_reason"],
    }


def _validation_matrix_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "hypothesis_id": item["hypothesis_id"],
        "title": item["title"],
        "event_count": item["event_count"],
        "mean_return": item["statistics"]["mean_return"],
        "walk_forward_positive_fold_ratio": item["walk_forward"]["positive_fold_ratio"],
        "bootstrap_probability_positive": item["bootstrap"]["probability_positive"],
        "psr": item["statistics"]["probabilistic_sharpe_ratio"],
        "outcome": item["decision"]["outcome"],
    }


def _cross_regime_row(item: dict[str, Any]) -> dict[str, Any]:
    regime = item["regime_scope"][0] if item["regime_scope"] else "multi_regime"
    return {
        "hypothesis_id": item["hypothesis_id"],
        "scope_regime": REGIME_LABELS.get(regime, regime),
        **item["cross_regime_stability"],
    }


def _section_row(item: dict[str, Any], key: str) -> dict[str, Any]:
    base = {"hypothesis_id": item["hypothesis_id"]}
    base.update(item[key])
    if key == "sensitivity":
        base["pbo_status"] = item["probability_of_backtest_overfitting"]["status"]
    return base


def _failure_row(item: dict[str, Any]) -> dict[str, Any]:
    dominant = item["contradictions"][0]
    return {
        "hypothesis_id": item["hypothesis_id"],
        "outcome": item["decision"]["outcome"],
        "dominant_failure_mode": dominant["severity"],
        "key_reason": dominant["summary"],
        "title": item["title"],
    }


def _contradiction_row(item: dict[str, Any]) -> dict[str, Any]:
    dominant = item["contradictions"][0]
    return {
        "hypothesis_id": item["hypothesis_id"],
        "severity": dominant["severity"],
        "summary": dominant["summary"],
    }


def _confidence_seed_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "hypothesis_id": item["hypothesis_id"],
        "prior_confidence": item["confidence_prior"],
        "suggested_posterior_confidence": item["suggested_posterior_confidence"],
        "outcome": item["decision"]["outcome"],
    }


def _arb_recommendation(
    promoted: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    further_research: list[dict[str, Any]],
) -> str:
    promoted_ids = ", ".join(item["hypothesis_id"] for item in promoted) or "none"
    rejected_ids = ", ".join(item["hypothesis_id"] for item in rejected) or "none"
    further_ids = ", ".join(item["hypothesis_id"] for item in further_research) or "none"
    return (
        "ARB recommendation: reject hypotheses "
        f"{rejected_ids}; retain {further_ids} for refinement-focused follow-up research; "
        f"promote {promoted_ids} to Alpha Candidate status only after they satisfy the full "
        "institutional scientific validation standard."
    )


def _build_knowledge_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    promoted = analysis["alpha_candidate_registry"]
    rejected = analysis["rejected_hypothesis_registry"]
    further = [
        item
        for item in analysis["validation_matrix"]
        if item["outcome"] == "REQUIRES_FURTHER_RESEARCH"
    ]
    return {
        "metadata": {
            "source_kind": "INTERNAL_RESEARCH_REPORT",
            "title": "Campaign 0005 scientific validation knowledge pack",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/scientific-validation/SCIENTIFIC_VALIDATION_CAMPAIGN.md",
                "11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json",
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-DSV-20260802-0005",
                "type": "DatasetVersion",
                "title": "Campaign 0005 scientific validation dataset snapshot",
                "summary": "Frozen Phase G conditioned feature frame and governed event-validation outputs for the approved hypothesis set.",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.9,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/scientific-validation/scientific_validation_analysis.json"],
                "attributes": {
                    "validated_hypothesis_count": analysis["campaign"]["validated_hypothesis_count"],
                    "promoted_count": analysis["campaign"]["promoted_count"],
                    "rejected_count": analysis["campaign"]["rejected_count"],
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0500",
                "type": "KnowledgeObject",
                "title": "Campaign 0005 scientific validation methodology",
                "summary": "Deterministic event-based validation methodology for governed regime-conditioned AFRP hypotheses.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.84,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/scientific-validation/SCIENTIFIC_VALIDATION_CAMPAIGN.md"],
                "attributes": {
                    "validation_protocol": analysis["validation_protocol"],
                    "validated_hypotheses": analysis["campaign"]["validated_hypotheses"],
                },
            },
            {
                "identifier": "IKROS-EVIDENCE-20260802-0005",
                "type": "Evidence",
                "title": "Campaign 0005 scientific validation evidence bundle",
                "summary": "Evidence bundle carrying validation matrix, Monte Carlo, walk-forward, CPCV, sensitivity, and contradiction reports.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.82,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/scientific-validation/scientific_validation_analysis.json"],
                "attributes": {
                    "promoted_hypotheses": [item["hypothesis_id"] for item in promoted],
                    "rejected_hypotheses": [item["hypothesis_id"] for item in rejected],
                    "further_research_hypotheses": [item["hypothesis_id"] for item in further],
                },
            },
            {
                "identifier": "IKROS-CONTRA-20260802-0005",
                "type": "ContradictoryEvidence",
                "title": "Campaign 0005 contradictory evidence log",
                "summary": "Contradictory evidence bundle capturing sign failures, sparse episode coverage, and unstable replay outcomes.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.76,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/scientific-validation/scientific_validation_analysis.json"],
                "attributes": {
                    "rejected_hypotheses": [item["hypothesis_id"] for item in rejected],
                    "further_research_hypotheses": [item["hypothesis_id"] for item in further],
                },
            },
            {
                "identifier": "IKROS-CONCL-20260802-0005",
                "type": "KnowledgeObject",
                "title": "Campaign 0005 final conclusion",
                "summary": analysis["campaign"]["arb_recommendation"],
                "lifecycle_state": "ACTIVE",
                "confidence": 0.8,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/scientific-validation/SCIENTIFIC_VALIDATION_FINAL_CAMPAIGN_REPORT.md"],
                "attributes": {
                    "promoted_hypotheses": [item["hypothesis_id"] for item in promoted],
                    "rejected_hypotheses": [item["hypothesis_id"] for item in rejected],
                    "further_research_hypotheses": [item["hypothesis_id"] for item in further],
                },
            },
        ],
    }


def _build_validation_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {
            "source_kind": "VALIDATION_REPORT",
            "title": "Campaign 0005 scientific validation report",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/scientific-validation/scientific_validation_analysis.json",
                "11-research/phase-g/scientific-validation/SCIENTIFIC_VALIDATION_CAMPAIGN.md",
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-VAL-20260802-0005",
                "type": "Validation",
                "title": "Campaign 0005 umbrella validation",
                "summary": "Institutional scientific validation summary for the approved Campaign 0005 hypothesis set.",
                "lifecycle_state": "COMPLETE",
                "confidence": 0.81,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/scientific-validation/scientific_validation_analysis.json"],
                "attributes": {
                    "promoted_count": analysis["campaign"]["promoted_count"],
                    "rejected_count": analysis["campaign"]["rejected_count"],
                    "further_research_count": analysis["campaign"]["further_research_count"],
                },
            }
        ],
    }


def _probabilistic_sharpe_ratio(event_returns: NDArray[np.float64], *, benchmark: float) -> float:
    if len(event_returns) < 2:
        return 0.0
    mean_return = float(event_returns.mean())
    volatility = float(event_returns.std(ddof=1))
    if volatility == 0.0:
        return 0.0
    sharpe = mean_return / volatility
    skew = _skew(event_returns)
    kurtosis = _kurtosis(event_returns)
    denominator = math.sqrt(
        max(
            1e-12,
            1.0 - skew * sharpe + ((kurtosis - 1.0) / 4.0) * (sharpe**2),
        )
    )
    statistic = ((sharpe - benchmark) * math.sqrt(max(len(event_returns) - 1, 1))) / denominator
    return _normal_cdf(statistic)


def _deflated_sharpe_ratio(event_returns: NDArray[np.float64], *, trial_count: int) -> float:
    if trial_count <= 1:
        return _probabilistic_sharpe_ratio(event_returns, benchmark=0.0)
    expected_max_sr = _expected_max_sharpe(trial_count)
    return _probabilistic_sharpe_ratio(event_returns, benchmark=expected_max_sr)


def _expected_max_sharpe(trial_count: int) -> float:
    gamma = 0.5772156649
    nd = NormalDist()
    z_one = nd.inv_cdf(1.0 - 1.0 / max(trial_count, 2))
    z_two = nd.inv_cdf(1.0 - 1.0 / max(int(math.e * trial_count), 3))
    return float((1.0 - gamma) * z_one + gamma * z_two)


def _stress_window_name(timestamp: pd.Timestamp) -> str | None:
    naive = timestamp.tz_convert("UTC").tz_localize(None) if timestamp.tzinfo else timestamp
    for name, start, end in STRESS_WINDOWS:
        if pd.Timestamp(start) <= naive <= pd.Timestamp(end):
            return name
    return None


def _skew(values: NDArray[np.float64]) -> float:
    if len(values) < 3:
        return 0.0
    mean_value = float(values.mean())
    std_value = float(values.std(ddof=1))
    if std_value == 0.0:
        return 0.0
    centered = ((values - mean_value) / std_value) ** 3
    return float(centered.mean())


def _kurtosis(values: NDArray[np.float64]) -> float:
    if len(values) < 4:
        return 3.0
    mean_value = float(values.mean())
    std_value = float(values.std(ddof=1))
    if std_value == 0.0:
        return 3.0
    centered = ((values - mean_value) / std_value) ** 4
    return float(centered.mean())


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _round(value: float) -> float:
    return round(float(value), 4)
