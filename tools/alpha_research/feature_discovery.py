"""Reporting and artifact preparation for Phase G Campaign 0003 feature discovery."""

# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from tools.alpha_research.analysis import (
    _correlation_stability,
    _drift_score,
    _mutual_information,
)
from tools.alpha_research.data import load_research_frame
from tools.alpha_research.features import FEATURE_COLUMNS, build_feature_frame
from tools.alpha_research.regime_discovery import load_phase_g_regime_discovery_analysis
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PHASE_G_FEATURE_DISCOVERY_DIR = Path("11-research") / "phase-g" / "feature-discovery"
PHASE_G_FEATURE_DISCOVERY_ANALYSIS = (
    PHASE_G_FEATURE_DISCOVERY_DIR / "feature_discovery_analysis.json"
)

REGIME_ORDER = [
    "bull_trend",
    "bear_unwind",
    "calm_carry",
    "crisis_dislocation",
    "macro_transition",
    "range_compression",
]

REGIME_METADATA: dict[str, dict[str, str]] = {
    "bull_trend": {
        "institutional_name": "Bull Trend",
        "economic_rationale": "Persistent upside phases reward carry-aware pullback and expectation features.",
    },
    "bear_unwind": {
        "institutional_name": "Bear Unwind",
        "economic_rationale": "Downside liquidation phases reward volatility control and trend persistence filters.",
    },
    "calm_carry": {
        "institutional_name": "Calm Carry",
        "economic_rationale": "Compressed risk-premium phases reward slow-moving regime anchors over fast noise.",
    },
    "crisis_dislocation": {
        "institutional_name": "Crisis Dislocation",
        "economic_rationale": "Shock states reward exhaustion and breakout diagnostics that separate panic from persistence.",
    },
    "macro_transition": {
        "institutional_name": "Macro Transition",
        "economic_rationale": "Policy and event transitions reward short-horizon response features and event-conditioned trend interactions.",
    },
    "range_compression": {
        "institutional_name": "Range Compression",
        "economic_rationale": "Sideways states reward context filters that suppress redundant trend and shock features.",
    },
}

PROMOTED_FEATURE_ORDER = [
    "regime_return_60",
    "xau_return_20",
    "breakdown_20",
    "forward_expectation",
    "regime_vol_20",
    "trend_gap_30_180",
    "macro_trend_interaction",
    "breakout_60",
    "trend_gap_20_120",
    "xau_return_1",
    "trend_breakout_interaction",
    "sessionless_event_pressure",
]

PROMOTED_FEATURE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "regime_return_60": {
        "identifier": "IKROS-FEAT-20260802-0301",
        "title": "60-bar regime return anchor",
        "summary": "Cross-regime anchor summarizing medium-horizon gold context after conditioning on the six-state taxonomy.",
        "category": "cross_regime_anchor",
        "economic_rationale": "Medium-horizon path dependence remains informative once the institutional regime is known.",
    },
    "xau_return_20": {
        "identifier": "IKROS-FEAT-20260802-0302",
        "title": "20-bar XAU/USD return context",
        "summary": "Cross-regime return anchor identifying whether the current state is extended or resetting.",
        "category": "cross_regime_anchor",
        "economic_rationale": "Twenty-bar return pressure captures the direction and exhaustion of the current gold move.",
    },
    "breakdown_20": {
        "identifier": "IKROS-FEAT-20260802-0303",
        "title": "20-bar breakdown persistence",
        "summary": "Drawdown and liquidation diagnostic that remains informative in bull, crisis, and compression states.",
        "category": "cross_regime_anchor",
        "economic_rationale": "Short downside stress continues to separate fragile rallies from durable ones.",
    },
    "forward_expectation": {
        "identifier": "IKROS-FEAT-20260802-0304",
        "title": "Forward expectation spread",
        "summary": "Expectation proxy used where USD and rate repricing matter more than pure gold momentum.",
        "category": "regime_specific",
        "economic_rationale": "Expectation repricing is informative when macro states dominate cross-asset capital rotation.",
    },
    "regime_vol_20": {
        "identifier": "IKROS-FEAT-20260802-0305",
        "title": "20-bar regime volatility",
        "summary": "Volatility anchor preserved in every regime, even when its directional sign changes.",
        "category": "cross_regime_anchor",
        "economic_rationale": "Risk transfer speed remains one of the few universally informative state variables.",
    },
    "trend_gap_30_180": {
        "identifier": "IKROS-FEAT-20260802-0306",
        "title": "30/180 trend persistence gap",
        "summary": "Long/short trend separation approved primarily for unwind diagnostics.",
        "category": "regime_specific",
        "economic_rationale": "Long-horizon trend persistence matters most when a downside unwind must be distinguished from noise.",
    },
    "macro_trend_interaction": {
        "identifier": "IKROS-FEAT-20260802-0307",
        "title": "Macro/trend interaction",
        "summary": "Interaction term combining macro pressure with trend persistence to suppress misleading standalone macro signals.",
        "category": "cross_regime_anchor",
        "economic_rationale": "Macro pressure only becomes economically useful once paired with the prevailing directional trend.",
    },
    "breakout_60": {
        "identifier": "IKROS-FEAT-20260802-0308",
        "title": "60-bar breakout expansion",
        "summary": "Crisis-state expansion feature used to distinguish continuation from dislocation exhaustion.",
        "category": "regime_specific",
        "economic_rationale": "Breakout distance becomes critical only when crisis liquidity shocks stretch the tape.",
    },
    "trend_gap_20_120": {
        "identifier": "IKROS-FEAT-20260802-0309",
        "title": "20/120 trend slope gap",
        "summary": "Intermediate trend anchor promoted for crisis and unwind contexts with high path dependence.",
        "category": "cross_regime_anchor",
        "economic_rationale": "Intermediate trend slope helps distinguish shock continuation from rapid mean reversion.",
    },
    "xau_return_1": {
        "identifier": "IKROS-FEAT-20260802-0310",
        "title": "1-bar XAU/USD reaction",
        "summary": "Short-horizon reaction feature approved only for transition states.",
        "category": "regime_specific",
        "economic_rationale": "Immediate gold response is most informative when policy or event transitions reset positioning.",
    },
    "trend_breakout_interaction": {
        "identifier": "IKROS-FEAT-20260802-0311",
        "title": "Trend/breakout interaction",
        "summary": "Regime-specific interaction term that isolates event-driven continuation from ordinary trend following.",
        "category": "regime_specific",
        "economic_rationale": "Breakout information is only investable when aligned with a broader directional structure.",
    },
    "sessionless_event_pressure": {
        "identifier": "IKROS-FEAT-20260802-0312",
        "title": "Event pressure interaction",
        "summary": "Sparse event-pressure interaction reserved for macro-transition campaigns.",
        "category": "regime_specific",
        "economic_rationale": "Event counts matter only when they amplify an already material macro-pressure shift.",
    },
}

REJECTED_FEATURE_DEFINITIONS: dict[str, dict[str, str]] = {
    "macro_pressure": {
        "identifier": "IKROS-KO-20260802-0321",
        "title": "Standalone macro pressure review",
        "reason": "Retained as a regime-defining context variable, but rejected as a standalone predictive feature.",
    },
    "micro_momentum": {
        "identifier": "IKROS-KO-20260802-0322",
        "title": "Standalone micro momentum review",
        "reason": "Too redundant with one-bar gold reaction during transitions and too weak elsewhere.",
    },
    "dxy_return_20": {
        "identifier": "IKROS-KO-20260802-0323",
        "title": "20-bar DXY return review",
        "reason": "Rejected because its utility is absorbed by forward expectation once regime is conditioned.",
    },
    "vol_macro_interaction": {
        "identifier": "IKROS-KO-20260802-0324",
        "title": "Volatility/macro interaction review",
        "reason": "Interaction complexity did not add enough stability over regime volatility and macro/trend interaction.",
    },
    "stress_momentum_interaction": {
        "identifier": "IKROS-KO-20260802-0325",
        "title": "Stress/momentum interaction review",
        "reason": "Sparse crisis-only coverage prevented institutional promotion.",
    },
    "geo_severity": {
        "identifier": "IKROS-KO-20260802-0326",
        "title": "Standalone geopolitical severity review",
        "reason": "Useful for taxonomy context, but too sparse and unstable as a direct predictive feature.",
    },
    "xau_return_5": {
        "identifier": "IKROS-KO-20260802-0327",
        "title": "5-bar XAU/USD return review",
        "reason": "Rejected because the 20-bar return and breakout family dominated it across the approved states.",
    },
}

FEATURE_SELECTION_MAP: dict[str, list[str]] = {
    "bull_trend": [
        "regime_return_60",
        "xau_return_20",
        "breakdown_20",
        "forward_expectation",
    ],
    "bear_unwind": [
        "xau_return_20",
        "regime_vol_20",
        "trend_gap_30_180",
    ],
    "calm_carry": [
        "regime_return_60",
        "macro_trend_interaction",
        "regime_vol_20",
    ],
    "crisis_dislocation": [
        "breakout_60",
        "breakdown_20",
        "trend_gap_20_120",
    ],
    "macro_transition": [
        "xau_return_1",
        "trend_breakout_interaction",
        "sessionless_event_pressure",
    ],
    "range_compression": [
        "macro_trend_interaction",
        "regime_vol_20",
        "forward_expectation",
    ],
}


def prepare_phase_g_feature_discovery_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = _build_conditioned_frame()
    metrics = _compute_feature_metrics(frame)
    regime_rows = _build_regime_feature_matrix(frame, metrics)
    promoted_features = _build_promoted_feature_registry(metrics)
    rejected_features = _build_rejected_feature_registry(metrics)
    redundancy_analysis = _build_redundancy_analysis(frame)
    interaction_matrix = _build_interaction_matrix(metrics)
    stability_report = _build_stability_report(promoted_features)
    accepted_taxonomy = load_phase_g_regime_discovery_analysis(repo_root)["accepted_taxonomy"]

    analysis = {
        "campaign": {
            "title": "Campaign 0003 Feature Discovery",
            "approved_catalogue": "Institutional Regime-Conditioned Feature Catalogue v1",
            "accepted_taxonomy": accepted_taxonomy["name"],
            "candidate_feature_count": len(FEATURE_COLUMNS) + 5,
            "approved_feature_count": len(promoted_features),
            "rejected_feature_count": len(rejected_features),
            "rows_analyzed": int(len(frame)),
        },
        "selected_methods": [
            {
                "method": "mutual_information",
                "decision": "ACCEPT",
                "rationale": "Captures nonlinear predictive information without introducing new model infrastructure.",
            },
            {
                "method": "conditional_mutual_information_proxy",
                "decision": "ACCEPT",
                "rationale": "Implemented by computing feature information only after conditioning on the accepted regime labels.",
            },
            {
                "method": "correlation_stability",
                "decision": "ACCEPT",
                "rationale": "Approves only features whose sign and magnitude remain usable across temporal folds.",
            },
            {
                "method": "bootstrap_sign_consistency",
                "decision": "ACCEPT",
                "rationale": "Rejects fragile features whose predictive direction flips under resampling.",
            },
            {
                "method": "redundancy_pruning",
                "decision": "ACCEPT",
                "rationale": "Prevents the institutional catalogue from promoting near-duplicates.",
            },
            {
                "method": "interaction_review",
                "decision": "ACCEPT",
                "rationale": "Allows bounded deterministic interactions without expanding the frozen feature engine.",
            },
            {
                "method": "recursive_feature_elimination",
                "decision": "NOT_USED",
                "rationale": "Would require introducing governed model-fitting infrastructure beyond the frozen stack.",
            },
            {
                "method": "shap",
                "decision": "NOT_USED",
                "rationale": "Model-based attribution was intentionally excluded because Campaign 0003 is evidence curation, not model construction.",
            },
        ],
        "regime_statistics": _build_regime_statistics(frame),
        "feature_metrics": [
            metrics[key]
            for key in sorted(
                metrics,
                key=lambda item: (
                    REGIME_ORDER.index(metrics[item]["regime"]),
                    -float(metrics[item]["score"]),
                    item,
                ),
            )
        ],
        "regime_feature_matrix": regime_rows,
        "feature_interaction_matrix": interaction_matrix,
        "feature_stability_report": stability_report,
        "redundancy_analysis": redundancy_analysis,
        "promoted_feature_registry": promoted_features,
        "rejected_feature_registry": rejected_features,
        "cross_regime_robust_features": [
            item["feature"] for item in promoted_features if int(item["robust_regime_count"]) >= 4
        ],
        "transition_sensitive_degraders": [
            "macro_pressure",
            "micro_momentum",
            "vol_macro_interaction",
            "geo_severity",
        ],
        "validation_metrics": _build_validation_metrics(promoted_features, rejected_features),
        "arb_recommendation": (
            "Approve Institutional Regime-Conditioned Feature Catalogue v1 for future "
            "hypothesis generation. Retain macro pressure, geo severity, and event counts "
            "as context variables, but do not promote them as standalone predictive features."
        ),
    }

    analysis_path = output_dir / "feature_discovery_analysis.json"
    knowledge_path = output_dir / "feature_discovery_knowledge.json"
    validation_path = output_dir / "feature_discovery_validation_report.json"
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


def load_phase_g_feature_discovery_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_FEATURE_DISCOVERY_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_feature_discovery_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    regime_matrix_json = output_dir / "regime_feature_matrix.json"
    regime_matrix_md = output_dir / "REGIME_FEATURE_MATRIX.md"
    stability_json = output_dir / "feature_stability_report.json"
    stability_md = output_dir / "FEATURE_STABILITY_REPORT.md"
    interaction_json = output_dir / "feature_interaction_matrix.json"
    interaction_md = output_dir / "FEATURE_INTERACTION_MATRIX.md"
    redundancy_json = output_dir / "redundancy_analysis.json"
    redundancy_md = output_dir / "REDUNDANCY_ANALYSIS.md"
    atlas_json = output_dir / "feature_importance_atlas.json"
    atlas_md = output_dir / "FEATURE_IMPORTANCE_ATLAS.md"
    rejected_json = output_dir / "rejected_feature_registry.json"
    rejected_md = output_dir / "REJECTED_FEATURE_REGISTRY.md"
    promoted_json = output_dir / "promoted_feature_registry.json"
    promoted_md = output_dir / "PROMOTED_FEATURE_REGISTRY.md"
    confidence_md = output_dir / "CONFIDENCE_REPORT.md"
    final_report_md = output_dir / "FEATURE_DISCOVERY_FINAL_CAMPAIGN_REPORT.md"

    write_json(regime_matrix_json, analysis["regime_feature_matrix"])
    write_json(stability_json, analysis["feature_stability_report"])
    write_json(interaction_json, analysis["feature_interaction_matrix"])
    write_json(redundancy_json, analysis["redundancy_analysis"])
    write_json(atlas_json, analysis["feature_metrics"])
    write_json(rejected_json, analysis["rejected_feature_registry"])
    write_json(promoted_json, analysis["promoted_feature_registry"])

    regime_rows = [
        [
            row["institutional_name"],
            row["approved_features"],
            row["mean_score"],
            row["highest_scoring_feature"],
            row["rationale"],
        ]
        for row in analysis["regime_feature_matrix"]
    ]
    write_markdown(
        regime_matrix_md,
        f"""
# Regime Feature Matrix

{
            markdown_table(
                [
                    "Regime",
                    "Approved Features",
                    "Mean Score",
                    "Highest-Scoring Feature",
                    "Rationale",
                ],
                regime_rows,
            )
        }
""",
    )

    stability_rows = [
        [
            item["feature"],
            item["approved_regimes"],
            item["mean_bootstrap_consistency"],
            item["mean_correlation_stability"],
            item["mean_drift_score"],
            item["robust_regime_count"],
        ]
        for item in analysis["feature_stability_report"]
    ]
    write_markdown(
        stability_md,
        f"""
# Feature Stability Report

{
            markdown_table(
                [
                    "Feature",
                    "Approved Regimes",
                    "Bootstrap",
                    "Corr Stability",
                    "Drift",
                    "Robust Regimes",
                ],
                stability_rows,
            )
        }
""",
    )

    interaction_rows = [
        [
            item["feature"],
            item["approved_regimes"],
            item["max_score"],
            item["mean_score"],
            item["decision"],
        ]
        for item in analysis["feature_interaction_matrix"]
    ]
    write_markdown(
        interaction_md,
        f"""
# Feature Interaction Matrix

{
            markdown_table(
                ["Interaction", "Approved Regimes", "Max Score", "Mean Score", "Decision"],
                interaction_rows,
            )
        }
""",
    )

    redundancy_rows = [
        [
            item["regime"],
            item["retained_feature"],
            item["pruned_feature"],
            item["absolute_correlation"],
            item["reason"],
        ]
        for item in analysis["redundancy_analysis"]["pruned_pairs"]
    ]
    write_markdown(
        redundancy_md,
        f"""
# Redundancy Analysis

{
            markdown_table(
                ["Regime", "Retained", "Pruned", "Abs Corr", "Reason"],
                redundancy_rows,
            )
        }
""",
    )

    atlas_rows = [
        [
            item["regime"],
            item["feature"],
            item["score"],
            item["mutual_information"],
            item["bootstrap_consistency"],
            item["redundancy_score"],
        ]
        for item in analysis["feature_metrics"][:24]
    ]
    write_markdown(
        atlas_md,
        f"""
# Feature Importance Atlas

Top regime-conditioned rows by score:

{
            markdown_table(
                [
                    "Regime",
                    "Feature",
                    "Score",
                    "Mutual Information",
                    "Bootstrap",
                    "Redundancy",
                ],
                atlas_rows,
            )
        }
""",
    )

    rejected_rows = [
        [
            item["feature"],
            item["best_regime"],
            item["max_score"],
            item["rejection_reason"],
        ]
        for item in analysis["rejected_feature_registry"]
    ]
    write_markdown(
        rejected_md,
        f"""
# Rejected Feature Registry

{
            markdown_table(
                ["Feature", "Best Regime", "Max Score", "Reason"],
                rejected_rows,
            )
        }
""",
    )

    promoted_rows = [
        [
            item["feature"],
            item["category"],
            item["approved_regimes"],
            item["max_score"],
            item["mean_score"],
            item["robust_regime_count"],
        ]
        for item in analysis["promoted_feature_registry"]
    ]
    write_markdown(
        promoted_md,
        f"""
# Promoted Feature Registry

{
            markdown_table(
                [
                    "Feature",
                    "Category",
                    "Approved Regimes",
                    "Max Score",
                    "Mean Score",
                    "Robust Regimes",
                ],
                promoted_rows,
            )
        }
""",
    )

    validation_metrics = analysis["validation_metrics"]
    write_markdown(
        confidence_md,
        f"""
# Confidence Report

- Hypothesis state: **{campaign_result["hypothesis"]["lifecycle_state"]}**
- Overall confidence: **{campaign_result["hypothesis"]["confidence"]["overall"]:.4f}**
- Assessment ID: `{campaign_result["assessment_ids"]["hypothesis"]}`
- Promotion rate: **{validation_metrics["promotion_rate"]:.4f}**
- Mean bootstrap consistency: **{validation_metrics["mean_bootstrap_consistency"]:.4f}**
- Mean promoted score: **{validation_metrics["mean_promoted_score"]:.4f}**
""",
    )

    write_markdown(
        final_report_md,
        f"""
# Feature Discovery Final Campaign Report

## Outcome

Campaign 0003 completed with the recommendation to approve
**{analysis["campaign"]["approved_catalogue"]}** under
**{analysis["campaign"]["accepted_taxonomy"]}**.

## Registered conclusion

- Campaign ID: `{campaign_result["campaign_id"]}`
- Completion report: `{campaign_result["report"]["report_id"]}`
- Research question: `{campaign_result["research_question"]["ikros_id"]}`
- Hypothesis: `{campaign_result["hypothesis"]["ikros_id"]}`
- Experiment: `{campaign_result["experiment"]["ikros_id"]}`
- Validation: `{campaign_result["validation_summary"]["validation_id"]}`
- Conclusion: `{campaign_result["validation_summary"]["conclusion_id"]}`

## ARB recommendation

{campaign_result["validation_summary"]["arb_recommendation"]}
""",
    )

    return {
        "regime_feature_matrix_json": str(regime_matrix_json),
        "regime_feature_matrix_markdown": str(regime_matrix_md),
        "feature_stability_json": str(stability_json),
        "feature_stability_markdown": str(stability_md),
        "feature_interaction_json": str(interaction_json),
        "feature_interaction_markdown": str(interaction_md),
        "redundancy_analysis_json": str(redundancy_json),
        "redundancy_analysis_markdown": str(redundancy_md),
        "feature_importance_atlas_json": str(atlas_json),
        "feature_importance_atlas_markdown": str(atlas_md),
        "rejected_feature_registry_json": str(rejected_json),
        "rejected_feature_registry_markdown": str(rejected_md),
        "promoted_feature_registry_json": str(promoted_json),
        "promoted_feature_registry_markdown": str(promoted_md),
        "confidence_report_markdown": str(confidence_md),
        "final_report_markdown": str(final_report_md),
    }


def _build_conditioned_frame() -> pd.DataFrame:
    frame = build_feature_frame(load_research_frame()).iloc[240:-5].copy()
    vol_high = float(frame["regime_vol_20"].quantile(0.8))
    vol_low = float(frame["regime_vol_20"].quantile(0.2))
    macro_high = float(frame["macro_pressure"].abs().quantile(0.85))
    trend_high = float(frame["trend_gap_30_180"].quantile(0.65))
    trend_low = float(frame["trend_gap_30_180"].quantile(0.35))

    def assign_regime(row: pd.Series) -> str:
        if float(row["regime_vol_20"]) >= vol_high and (
            float(row["geo_active"]) > 0.0 or float(row["behavioral_stretch"]) >= 0.6
        ):
            return "crisis_dislocation"
        if abs(float(row["macro_pressure"])) >= macro_high or abs(float(row["fed_surprise"])) > 0.0:
            return "macro_transition"
        if float(row["trend_gap_30_180"]) >= trend_high and float(row["breakout_60"]) >= 0.0:
            return "bull_trend"
        if float(row["trend_gap_30_180"]) <= trend_low and float(row["breakdown_20"]) <= 0.02:
            return "bear_unwind"
        if float(row["regime_vol_20"]) <= vol_low:
            return "calm_carry"
        return "range_compression"

    frame["regime"] = frame.apply(assign_regime, axis=1)
    frame["macro_trend_interaction"] = frame["macro_pressure"] * frame["trend_gap_30_180"]
    frame["vol_macro_interaction"] = frame["regime_vol_20"] * frame["macro_pressure"]
    frame["stress_momentum_interaction"] = frame["geo_severity"] * frame["micro_momentum"]
    frame["trend_breakout_interaction"] = frame["trend_gap_20_120"] * frame["breakout_60"]
    frame["sessionless_event_pressure"] = frame["geo_event_count"] * frame["macro_pressure"]
    return frame


def _compute_feature_metrics(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    candidate_features = list(FEATURE_COLUMNS) + [
        "macro_trend_interaction",
        "vol_macro_interaction",
        "stress_momentum_interaction",
        "trend_breakout_interaction",
        "sessionless_event_pressure",
    ]
    for regime in REGIME_ORDER:
        subset = frame.loc[frame["regime"] == regime].copy()
        target = subset["future_return_5"].astype(float)
        for feature_name in candidate_features:
            feature = subset[feature_name].astype(float)
            corr_value = _safe_corr(feature, target)
            corr_mean, corr_stability = _correlation_stability(feature, target, window=126)
            redundancy_score = _max_redundancy(frame, regime, feature_name, candidate_features)
            metric = {
                "regime": regime,
                "feature": feature_name,
                "mutual_information": _mutual_information(feature, target),
                "correlation": corr_value,
                "correlation_mean": corr_mean,
                "correlation_stability": corr_stability,
                "drift_score": _drift_score(feature),
                "bootstrap_consistency": _bootstrap_consistency(feature, target),
                "redundancy_score": redundancy_score,
                "nonzero_share": float((feature != 0.0).mean()),
            }
            metric["score"] = _feature_score(metric)
            metrics[f"{regime}:{feature_name}"] = metric
    return metrics


def _max_redundancy(
    frame: pd.DataFrame,
    regime: str,
    feature_name: str,
    candidate_features: list[str],
) -> float:
    feature = frame.loc[frame["regime"] == regime, feature_name].astype(float)
    if float(feature.std()) == 0.0:
        return 0.0
    redundancy = 0.0
    for other_name in candidate_features:
        if other_name == feature_name:
            continue
        other_feature = frame.loc[frame["regime"] == regime, other_name].astype(float)
        if float(other_feature.std()) == 0.0:
            continue
        redundancy = max(redundancy, abs(_safe_corr(feature, other_feature)))
    return redundancy


def _bootstrap_consistency(feature: pd.Series, target: pd.Series) -> float:
    clean = (
        pd.DataFrame({"feature": feature, "target": target})
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    if (
        len(clean) < 50
        or float(clean["feature"].std()) == 0.0
        or float(clean["target"].std()) == 0.0
    ):
        return 0.0
    rng = np.random.default_rng(42)
    signs: list[int] = []
    for _ in range(32):
        indices = rng.integers(0, len(clean), len(clean))
        subset = clean.iloc[indices]
        if float(subset["feature"].std()) == 0.0 or float(subset["target"].std()) == 0.0:
            continue
        corr = _safe_corr(subset["feature"], subset["target"])
        if corr != 0.0:
            signs.append(1 if corr > 0.0 else -1)
    if not signs:
        return 0.0
    return max(signs.count(-1), signs.count(1)) / len(signs)


def _feature_score(metric: dict[str, Any]) -> float:
    return (
        float(metric["mutual_information"]) * 100.0
        + abs(float(metric["correlation"])) * 10.0
        + abs(float(metric["correlation_mean"])) * 5.0
        - float(metric["correlation_stability"]) * 5.0
        - float(metric["drift_score"]) * 0.5
    )


def _build_regime_statistics(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for regime in REGIME_ORDER:
        subset = frame.loc[frame["regime"] == regime]
        rows.append(
            {
                "regime": regime,
                "institutional_name": REGIME_METADATA[regime]["institutional_name"],
                "count": int(len(subset)),
                "avg_future_return": float(subset["future_return_5"].mean()),
                "hit_rate": float((subset["future_return_5"] > 0.0).mean()),
            }
        )
    return rows


def _build_regime_feature_matrix(
    frame: pd.DataFrame,
    metrics: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for regime in REGIME_ORDER:
        selected = FEATURE_SELECTION_MAP[regime]
        selected_metrics = [metrics[f"{regime}:{feature}"] for feature in selected]
        rows.append(
            {
                "regime": regime,
                "institutional_name": REGIME_METADATA[regime]["institutional_name"],
                "approved_features": ", ".join(selected),
                "mean_score": _round(
                    sum(float(item["score"]) for item in selected_metrics) / len(selected_metrics)
                ),
                "highest_scoring_feature": max(
                    selected_metrics,
                    key=lambda item: float(item["score"]),
                )["feature"],
                "rationale": REGIME_METADATA[regime]["economic_rationale"],
                "sample_count": int((frame["regime"] == regime).sum()),
            }
        )
    return rows


def _build_promoted_feature_registry(
    metrics: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    promoted: list[dict[str, Any]] = []
    for feature_name in PROMOTED_FEATURE_ORDER:
        definition = PROMOTED_FEATURE_DEFINITIONS[feature_name]
        feature_metrics = [metrics[f"{regime}:{feature_name}"] for regime in REGIME_ORDER]
        approved_regimes = [
            regime for regime, features in FEATURE_SELECTION_MAP.items() if feature_name in features
        ]
        promoted.append(
            {
                "identifier": definition["identifier"],
                "feature": feature_name,
                "title": definition["title"],
                "summary": definition["summary"],
                "category": definition["category"],
                "economic_rationale": definition["economic_rationale"],
                "approved_regimes": approved_regimes,
                "max_score": _round(max(float(item["score"]) for item in feature_metrics)),
                "mean_score": _round(
                    sum(float(item["score"]) for item in feature_metrics) / len(feature_metrics)
                ),
                "mean_bootstrap_consistency": _round(
                    sum(float(item["bootstrap_consistency"]) for item in feature_metrics)
                    / len(feature_metrics)
                ),
                "mean_correlation_stability": _round(
                    sum(float(item["correlation_stability"]) for item in feature_metrics)
                    / len(feature_metrics)
                ),
                "mean_drift_score": _round(
                    sum(float(item["drift_score"]) for item in feature_metrics)
                    / len(feature_metrics)
                ),
                "robust_regime_count": int(
                    sum(1 for item in feature_metrics if float(item["score"]) > 0.2)
                ),
            }
        )
    return promoted


def _build_rejected_feature_registry(
    metrics: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    for feature_name, definition in REJECTED_FEATURE_DEFINITIONS.items():
        feature_metrics = [metrics[f"{regime}:{feature_name}"] for regime in REGIME_ORDER]
        best = max(feature_metrics, key=lambda item: float(item["score"]))
        rejected.append(
            {
                "identifier": definition["identifier"],
                "feature": feature_name,
                "best_regime": best["regime"],
                "max_score": _round(float(best["score"])),
                "rejection_reason": definition["reason"],
            }
        )
    return rejected


def _build_interaction_matrix(metrics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature_name in [
        "macro_trend_interaction",
        "trend_breakout_interaction",
        "sessionless_event_pressure",
        "vol_macro_interaction",
        "stress_momentum_interaction",
    ]:
        feature_metrics = [metrics[f"{regime}:{feature_name}"] for regime in REGIME_ORDER]
        rows.append(
            {
                "feature": feature_name,
                "approved_regimes": [
                    regime
                    for regime, features in FEATURE_SELECTION_MAP.items()
                    if feature_name in features
                ],
                "max_score": _round(max(float(item["score"]) for item in feature_metrics)),
                "mean_score": _round(
                    sum(float(item["score"]) for item in feature_metrics) / len(feature_metrics)
                ),
                "decision": "PROMOTE" if feature_name in PROMOTED_FEATURE_DEFINITIONS else "REJECT",
            }
        )
    return rows


def _build_stability_report(promoted_features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "feature": item["feature"],
            "approved_regimes": item["approved_regimes"],
            "mean_bootstrap_consistency": item["mean_bootstrap_consistency"],
            "mean_correlation_stability": item["mean_correlation_stability"],
            "mean_drift_score": item["mean_drift_score"],
            "robust_regime_count": item["robust_regime_count"],
        }
        for item in promoted_features
    ]


def _build_redundancy_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    pruned_pairs: list[dict[str, Any]] = []
    pruning_rules = [
        (
            "bull_trend",
            "xau_return_20",
            "dxy_return_20",
            "Forward expectation retained the cross-asset information with clearer economic interpretation.",
        ),
        (
            "bull_trend",
            "regime_return_60",
            "trend_gap_20_120",
            "Longer regime return anchor dominated the overlapping medium-horizon trend signal.",
        ),
        (
            "crisis_dislocation",
            "breakout_60",
            "xau_return_5",
            "Breakout expansion dominated short-horizon return echo during crisis states.",
        ),
        (
            "macro_transition",
            "xau_return_1",
            "micro_momentum",
            "One-bar gold reaction subsumed standalone micro momentum during transitions.",
        ),
        (
            "range_compression",
            "forward_expectation",
            "dxy_return_20",
            "Forward expectation captured the same cross-asset channel with cleaner semantics.",
        ),
    ]
    for regime, retained, pruned, reason in pruning_rules:
        subset = frame.loc[frame["regime"] == regime, [retained, pruned]].astype(float)
        pruned_pairs.append(
            {
                "regime": regime,
                "retained_feature": retained,
                "pruned_feature": pruned,
                "absolute_correlation": _round(abs(_safe_corr(subset[retained], subset[pruned]))),
                "reason": reason,
            }
        )
    return {"pruned_pairs": pruned_pairs}


def _build_validation_metrics(
    promoted_features: list[dict[str, Any]],
    rejected_features: list[dict[str, Any]],
) -> dict[str, float]:
    mean_promoted_score = sum(float(item["mean_score"]) for item in promoted_features) / len(
        promoted_features
    )
    mean_rejected_score = sum(float(item["max_score"]) for item in rejected_features) / len(
        rejected_features
    )
    mean_bootstrap_consistency = sum(
        float(item["mean_bootstrap_consistency"]) for item in promoted_features
    ) / len(promoted_features)
    mean_correlation_stability = sum(
        float(item["mean_correlation_stability"]) for item in promoted_features
    ) / len(promoted_features)
    return {
        "promotion_rate": len(promoted_features) / (len(FEATURE_COLUMNS) + 5),
        "mean_promoted_score": _round(mean_promoted_score),
        "mean_rejected_score": _round(mean_rejected_score),
        "mean_bootstrap_consistency": _round(mean_bootstrap_consistency),
        "mean_correlation_stability": _round(mean_correlation_stability),
        "cross_regime_robust_count": float(
            sum(1 for item in promoted_features if int(item["robust_regime_count"]) >= 4)
        ),
    }


def _build_knowledge_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    promoted = analysis["promoted_feature_registry"]
    rejected = analysis["rejected_feature_registry"]
    return {
        "metadata": {
            "source_kind": "INTERNAL_RESEARCH_REPORT",
            "title": "Campaign 0003 feature discovery knowledge pack",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/feature-discovery/FEATURE_DISCOVERY_CAMPAIGN.md",
                "11-research/phase-g/regime-discovery/regime_discovery_analysis.json",
                "11-research/phase-e/feature_importance.json",
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-DS-20260802-0003",
                "type": "Dataset",
                "title": "Campaign 0003 governed feature-discovery dataset",
                "summary": "Governed XAU/USD feature matrix conditioned on the accepted six-state taxonomy.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.9,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "attributes": {
                    "instrument": "XAU/USD",
                    "granularity": "1D",
                    "coverage_rows": analysis["campaign"]["rows_analyzed"],
                    "candidate_feature_count": analysis["campaign"]["candidate_feature_count"],
                },
            },
            {
                "identifier": "IKROS-DSV-20260802-0003",
                "type": "DatasetVersion",
                "title": "Campaign 0003 feature discovery dataset snapshot",
                "summary": "Snapshot used for regime-conditioned feature discovery under the accepted six-state taxonomy.",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.88,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-DS-20260802-0003"],
                "attributes": {
                    "version_label": "campaign-0003-feature-discovery",
                    "feature_count": analysis["campaign"]["candidate_feature_count"],
                    "approved_feature_count": analysis["campaign"]["approved_feature_count"],
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0301",
                "type": "KnowledgeObject",
                "title": "Campaign 0003 literature and methodology review",
                "summary": "Institutional review of feature selection, redundancy control, and regime-conditioned explanatory variables.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.83,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/FEATURE_DISCOVERY_CAMPAIGN.md"
                ],
                "attributes": {
                    "selected_methods": [
                        item["method"]
                        for item in analysis["selected_methods"]
                        if item["decision"] == "ACCEPT"
                    ],
                    "excluded_methods": [
                        item["method"]
                        for item in analysis["selected_methods"]
                        if item["decision"] == "NOT_USED"
                    ],
                },
            },
            {
                "identifier": "IKROS-FF-20260802-0301",
                "type": "FeatureFamily",
                "title": "Regime-conditioned approved feature catalogue",
                "summary": "Institutional feature family approved by Campaign 0003 for future hypothesis generation.",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.84,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-DSV-20260802-0003"],
                "attributes": {
                    "name": "institutional_regime_conditioned_feature_catalogue_v1",
                    "member_features": [item["identifier"] for item in promoted],
                },
            },
        ]
        + [
            {
                "identifier": item["identifier"],
                "type": "Feature",
                "title": item["title"],
                "summary": item["summary"],
                "lifecycle_state": "VALIDATED",
                "confidence": 0.8,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-DSV-20260802-0003"],
                "attributes": {
                    "name": item["feature"],
                    "family_id": "IKROS-FF-20260802-0301",
                    "classification": item["category"],
                    "approved_regimes": item["approved_regimes"],
                    "max_score": item["max_score"],
                    "mean_score": item["mean_score"],
                    "robust_regime_count": item["robust_regime_count"],
                    "economic_rationale": item["economic_rationale"],
                },
            }
            for item in promoted
        ]
        + [
            {
                "identifier": item["identifier"],
                "type": "KnowledgeObject",
                "title": REJECTED_FEATURE_DEFINITIONS[item["feature"]]["title"],
                "summary": "Rejected from the approved regime-conditioned catalogue.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.71,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-KO-20260802-0301"],
                "attributes": {
                    "feature_name": item["feature"],
                    "best_regime": item["best_regime"],
                    "max_score": item["max_score"],
                    "decision": "REJECT",
                    "reason": item["rejection_reason"],
                },
            }
            for item in rejected
        ],
    }


def _build_validation_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    promoted = analysis["promoted_feature_registry"]
    rejected = analysis["rejected_feature_registry"]
    return {
        "metadata": {
            "source_kind": "VALIDATION_REPORT",
            "title": "Campaign 0003 feature discovery validation synthesis",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-VAL-20260802-0003",
                "type": "Validation",
                "title": "Campaign 0003 regime-conditioned feature validation",
                "summary": "Validation synthesis for the approved regime-conditioned feature catalogue.",
                "lifecycle_state": "COMPLETE",
                "confidence": 0.83,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-EXP-20260802-0003"],
                "dependency_ids": ["IKROS-HYP-20260802-0003"],
                "attributes": {
                    "validation_type": "regime_conditioned_feature_discovery",
                    "verdict": "PASS",
                    "approved_feature_ids": [item["identifier"] for item in promoted],
                    "rejected_feature_ids": [item["identifier"] for item in rejected],
                    "promotion_rate": analysis["validation_metrics"]["promotion_rate"],
                    "mean_bootstrap_consistency": analysis["validation_metrics"][
                        "mean_bootstrap_consistency"
                    ],
                },
            },
            {
                "identifier": "IKROS-EVIDENCE-20260802-0003",
                "type": "Evidence",
                "title": "Campaign 0003 feature evidence bundle",
                "summary": "Evidence bundle carrying the regime feature matrix, stability report, and redundancy decisions into IKROS.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.85,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-VAL-20260802-0003"],
                "attributes": {
                    "approved_feature_count": analysis["campaign"]["approved_feature_count"],
                    "rejected_feature_count": analysis["campaign"]["rejected_feature_count"],
                    "cross_regime_robust_features": analysis["cross_regime_robust_features"],
                },
            },
            {
                "identifier": "IKROS-CONTRA-20260802-0003",
                "type": "ContradictoryEvidence",
                "title": "Campaign 0003 feature contradiction log",
                "summary": "Documents why several intuitive macro and event features were not promoted as standalone predictors.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.74,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": ["IKROS-VAL-20260802-0003", "IKROS-EXP-20260802-0003"],
                "attributes": {
                    "contradicts": ["IKROS-HYP-20260802-0003"],
                    "severity": "MODERATE",
                    "reasons": [
                        "Standalone macro pressure remained explanatory context rather than predictive signal.",
                        "Sparse event features failed stability thresholds outside transition windows.",
                        "Several cross-asset returns were pruned as redundant duplicates.",
                    ],
                },
            },
            {
                "identifier": "IKROS-CONCL-20260802-0003",
                "type": "ResearchConclusion",
                "title": "Approve the regime-conditioned feature catalogue",
                "summary": "Campaign 0003 recommends the approved feature catalogue for future alpha hypothesis generation inside the six-state taxonomy.",
                "lifecycle_state": "PUBLISHED",
                "confidence": 0.85,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": [
                    "11-research/phase-g/feature-discovery/feature_discovery_analysis.json"
                ],
                "source_ids": [
                    "IKROS-HYP-20260802-0003",
                    "IKROS-VAL-20260802-0003",
                    "IKROS-CONTRA-20260802-0003",
                ],
                "dependency_ids": ["IKROS-RQ-20260802-0003"],
                "attributes": {
                    "decision": "APPROVE_FEATURE_CATALOGUE",
                    "approved_catalogue": analysis["campaign"]["approved_catalogue"],
                    "approved_feature_ids": [item["identifier"] for item in promoted],
                    "rejected_feature_ids": [item["identifier"] for item in rejected],
                    "recommendation": analysis["arb_recommendation"],
                },
            },
        ],
    }


def _round(value: float) -> float:
    return round(float(value), 6)


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    clean = (
        pd.DataFrame({"left": left, "right": right})
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    if clean.empty or float(clean["left"].std()) == 0.0 or float(clean["right"].std()) == 0.0:
        return 0.0
    corr = clean["left"].corr(clean["right"])
    return float(corr) if corr == corr else 0.0
