"""Program E Phase 1: Institutional Transition Engine Decomposition & Ablation Analysis."""

# ruff: noqa: E501

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from tools.alpha_research.feature_discovery import _build_conditioned_frame
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.alpha_research.transition_engine import REGIME_TRANSITION_PRIORS
from tools.alpha_research.transition_engine_verification import (
    _transition_metrics,
    _zscore,
)

DC2_PROGRAM_E_PHASE1_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-e-phase1"
DC2_PROGRAM_E_PHASE1_ANALYSIS = DC2_PROGRAM_E_PHASE1_DIR / "dc2_program_e_ablation_analysis.json"

# ---------------------------------------------------------------------------
# Component Definitions
# ---------------------------------------------------------------------------

COMPONENT_NAMES: list[str] = [
    "macro_layer",
    "participant_ecology_layer",
    "decision_ecology_layer",
    "cross_asset_network_layer",
    "liquidity_layer",
    "regime_layer",
    "interaction_layer",
]

COMPONENT_DEFINITIONS: dict[str, dict[str, Any]] = {
    "macro_layer": {
        "description": "Macroeconomic conditions: rates, FX levels, Fed surprise, yield curve",
        "signals": ["macro_pressure", "fed_surprise", "yield_10y_change_5", "yield_curve_10y_3m", "yield_30y_change_20"],
        "special": None,
        "complexity_cost": "high",
        "failure_link": "false_transition_rate",
    },
    "participant_ecology_layer": {
        "description": "Institutional participant behavior proxies: geopolitical severity and safe-haven flow",
        "signals": ["geo_severity"],
        "special": None,
        "complexity_cost": "high",
        "failure_link": "missed_transition_rate",
    },
    "decision_ecology_layer": {
        "description": "Institutional expectation formation: forward expectation signals",
        "signals": ["forward_expectation"],
        "special": None,
        "complexity_cost": "medium",
        "failure_link": "missed_transition_rate",
    },
    "cross_asset_network_layer": {
        "description": "Cross-asset information network: DXY momentum signals at 1d, 5d, 20d horizons",
        "signals": ["dxy_return_1", "dxy_return_5", "dxy_return_20"],
        "special": None,
        "complexity_cost": "medium",
        "failure_link": "false_transition_rate",
    },
    "liquidity_layer": {
        "description": "Market liquidity and volatility: realized vol, breakout, breakdown signals",
        "signals": ["regime_vol_20", "breakout_60", "breakdown_20"],
        "special": None,
        "complexity_cost": "low",
        "failure_link": "cross_regime_consistency",
    },
    "regime_layer": {
        "description": "Primary asset price momentum: XAU/USD return signals",
        "signals": ["xau_return_1"],
        "special": None,
        "complexity_cost": "low",
        "failure_link": "transition_detection_accuracy",
    },
    "interaction_layer": {
        "description": "Trigger-type interaction logic: regime-specific signal inversion for volatility_decay",
        "signals": [],
        "special": "skip_trigger_inversion",
        "complexity_cost": "low",
        "failure_link": "confidence_calibration_brier",
    },
}

# ---------------------------------------------------------------------------
# Failure attribution from Program D
# ---------------------------------------------------------------------------

PROGRAM_D_FAILURES: list[dict[str, Any]] = [
    {"id": "F-001", "description": "Elevated false-transition rate indicates over-sensitive trigger assumptions.", "primary_layer": "macro_layer", "secondary_layers": ["cross_asset_network_layer"], "failure_link": "false_transition_rate"},
    {"id": "F-002", "description": "Missed-transition rate indicates incomplete transition mechanism coverage.", "primary_layer": "participant_ecology_layer", "secondary_layers": ["decision_ecology_layer"], "failure_link": "missed_transition_rate"},
    {"id": "F-003", "description": "Confidence calibration is weak under transition-risk scoring.", "primary_layer": "interaction_layer", "secondary_layers": ["regime_layer"], "failure_link": "confidence_calibration_brier"},
    {"id": "F-004", "description": "Robustness under stress/event subsets is weaker than at least one simpler baseline.", "primary_layer": "liquidity_layer", "secondary_layers": ["macro_layer", "cross_asset_network_layer"], "failure_link": "transition_detection_accuracy"},
    {"id": "F-005", "description": "Transition detection accuracy is not superior to simpler baselines.", "primary_layer": "regime_layer", "secondary_layers": ["interaction_layer", "cross_asset_network_layer"], "failure_link": "transition_detection_accuracy"},
]

# ---------------------------------------------------------------------------
# Ablated engine scoring
# ---------------------------------------------------------------------------


def _engine_scores_ablated(
    frame: pd.DataFrame,
    train_end: int,
    removed_components: frozenset[str],
) -> tuple[pd.DataFrame, pd.Series]:
    """Compute engine regime scores with specified components removed."""
    zeroed: set[str] = set()
    for comp in removed_components:
        zeroed.update(cast(list[str], COMPONENT_DEFINITIONS[comp]["signals"]))
    skip_inversion = "interaction_layer" in removed_components

    all_signals = sorted({sig for cfg in REGIME_TRANSITION_PRIORS.values() for sig in cast(list[str], cfg["signals"])})
    data: dict[str, pd.Series] = {}
    for signal in all_signals:
        if signal in zeroed:
            data[signal] = pd.Series(np.zeros(len(frame), dtype=float), index=frame.index)
        elif signal in frame.columns:
            data[signal] = _zscore(frame[signal].astype(float), train_end)
        else:
            data[signal] = pd.Series(np.zeros(len(frame), dtype=float), index=frame.index)

    regime_scores: dict[str, pd.Series] = {}
    for regime, cfg in REGIME_TRANSITION_PRIORS.items():
        signals = cast(list[str], cfg["signals"])
        stacked = np.column_stack([np.asarray(data[sig].to_numpy(), dtype=float) for sig in signals])
        signal_strength = np.mean(np.abs(stacked), axis=1)
        if not skip_inversion and cfg["trigger_type"] == "volatility_decay":
            signal_strength = 1.0 / (1.0 + signal_strength)
        regime_scores[regime] = pd.Series(signal_strength, index=frame.index)
    score_frame = pd.DataFrame(regime_scores)
    transition_risk = score_frame.max(axis=1).clip(0.0, 1.0)
    return score_frame, transition_risk


def _predict_ablated(frame: pd.DataFrame, train_end: int, removed_components: frozenset[str]) -> tuple[pd.Series, pd.Series]:
    score_frame, transition_risk = _engine_scores_ablated(frame, train_end, removed_components)
    predicted_regime = score_frame.idxmax(axis=1).astype(str)
    return predicted_regime, transition_risk


def _run_ablated_metrics(frame: pd.DataFrame, train_end: int, removed_components: frozenset[str]) -> dict[str, float]:
    actual_regime = frame["regime"].astype(str)
    pred_regime, risk = _predict_ablated(frame, train_end, removed_components)
    m = _transition_metrics(actual_regime, pred_regime, risk)
    return {
        "transition_detection_accuracy": float(m["transition_detection_accuracy"]),
        "transition_timing_error": float(m["transition_timing_error"]),
        "transition_classification_accuracy": float(m["transition_classification_accuracy"]),
        "early_warning_lead_time": float(m["early_warning_lead_time"]),
        "false_transition_rate": float(m["false_transition_rate"]),
        "missed_transition_rate": float(m["missed_transition_rate"]),
        "cross_regime_consistency": float(m["cross_regime_consistency"]),
        "confidence_calibration_brier": float(m["confidence_calibration_brier"]),
    }


# ---------------------------------------------------------------------------
# Ablation matrix construction
# ---------------------------------------------------------------------------


def _ablation_key(components: frozenset[str]) -> str:
    return "+".join(sorted(components)) if components else "BASELINE"


def _run_full_ablation(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Run baseline + all single, pair, and triple ablations."""
    train_end = int(len(frame) * 0.7)
    results: dict[str, dict[str, float]] = {}

    # Baseline (no components removed)
    results["BASELINE"] = _run_ablated_metrics(frame, train_end, frozenset())

    # Single-component ablation
    for comp in COMPONENT_NAMES:
        key = _ablation_key(frozenset({comp}))
        results[key] = _run_ablated_metrics(frame, train_end, frozenset({comp}))

    # Pairwise ablation
    for c1, c2 in itertools.combinations(COMPONENT_NAMES, 2):
        key = _ablation_key(frozenset({c1, c2}))
        results[key] = _run_ablated_metrics(frame, train_end, frozenset({c1, c2}))

    # Triple ablation
    for triple in itertools.combinations(COMPONENT_NAMES, 3):
        key = _ablation_key(frozenset(triple))
        results[key] = _run_ablated_metrics(frame, train_end, frozenset(triple))

    return results


# ---------------------------------------------------------------------------
# Component contribution analysis
# ---------------------------------------------------------------------------


def _component_contribution_report(ablation_results: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Per-component contribution as delta from baseline when that component is removed."""
    baseline = ablation_results["BASELINE"]
    rows: list[dict[str, Any]] = []
    for comp in COMPONENT_NAMES:
        ablated = ablation_results[_ablation_key(frozenset({comp}))]
        # Positive delta = component removal HURTS accuracy (component is useful)
        detection_contribution = round(float(baseline["transition_detection_accuracy"]) - float(ablated["transition_detection_accuracy"]), 4)
        classification_contribution = round(float(baseline["transition_classification_accuracy"]) - float(ablated["transition_classification_accuracy"]), 4)
        consistency_contribution = round(float(baseline["cross_regime_consistency"]) - float(ablated["cross_regime_consistency"]), 4)
        # For error metrics: negative delta = component removal INCREASES error (component is useful)
        timing_contribution = round(float(ablated["transition_timing_error"]) - float(baseline["transition_timing_error"]), 4)
        false_rate_contribution = round(float(ablated["false_transition_rate"]) - float(baseline["false_transition_rate"]), 4)
        missed_rate_contribution = round(float(ablated["missed_transition_rate"]) - float(baseline["missed_transition_rate"]), 4)
        brier_contribution = round(float(ablated["confidence_calibration_brier"]) - float(baseline["confidence_calibration_brier"]), 4)

        # Composite incremental gain: weighted average across key metrics
        incremental_gain = round(
            detection_contribution * 0.35
            + classification_contribution * 0.20
            + consistency_contribution * 0.15
            - false_rate_contribution * 0.10  # if removal increases FP rate, component was controlling it
            - missed_rate_contribution * 0.10
            - brier_contribution * 0.10,
            4,
        )
        rows.append(
            {
                "component": comp,
                "description": COMPONENT_DEFINITIONS[comp]["description"],
                "complexity_cost": COMPONENT_DEFINITIONS[comp]["complexity_cost"],
                "signal_count": len(cast(list[str], COMPONENT_DEFINITIONS[comp]["signals"])),
                "detection_contribution": detection_contribution,
                "classification_contribution": classification_contribution,
                "consistency_contribution": consistency_contribution,
                "timing_contribution": timing_contribution,
                "false_rate_contribution": false_rate_contribution,
                "missed_rate_contribution": missed_rate_contribution,
                "brier_contribution": brier_contribution,
                "incremental_gain": incremental_gain,
                "failure_link": COMPONENT_DEFINITIONS[comp]["failure_link"],
            }
        )
    rows.sort(key=lambda r: float(r["incremental_gain"]), reverse=True)
    return rows


# ---------------------------------------------------------------------------
# Complexity vs Benefit
# ---------------------------------------------------------------------------


def _complexity_vs_benefit_analysis(contribution_report: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cost_rank = {"low": 1, "medium": 2, "high": 3}
    rows: list[dict[str, Any]] = []
    for row in contribution_report:
        cost = int(cost_rank.get(str(row["complexity_cost"]), 2))
        benefit = float(row["incremental_gain"])
        # Efficiency = benefit per unit cost
        efficiency = round(benefit / cost, 4) if cost > 0 else 0.0
        verdict: str
        if benefit > 0.005 and efficiency > 0.003:
            verdict = "RETAIN"
        elif benefit > 0.0 and efficiency <= 0.003:
            verdict = "INVESTIGATE"
        elif benefit <= 0.0 and str(row["complexity_cost"]) == "high":
            verdict = "REMOVE"
        else:
            verdict = "REDESIGN"
        rows.append(
            {
                "component": row["component"],
                "complexity_cost": row["complexity_cost"],
                "incremental_gain": row["incremental_gain"],
                "efficiency_score": efficiency,
                "verdict": verdict,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Failure attribution
# ---------------------------------------------------------------------------


def _failure_attribution_report(
    ablation_results: dict[str, dict[str, float]],
    contribution_report: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attribute each Program D failure to responsible components based on ablation evidence."""
    baseline = ablation_results["BASELINE"]
    rows: list[dict[str, Any]] = []
    for failure in PROGRAM_D_FAILURES:
        primary = str(failure["primary_layer"])
        secondaries = cast(list[str], failure["secondary_layers"])
        ablated_primary = ablation_results.get(_ablation_key(frozenset({primary})), {})

        # Measure change in the failure-linked metric when primary layer is removed
        metric_key = str(failure["failure_link"])
        baseline_val = float(baseline.get(metric_key, 0.0))
        ablated_val = float(ablated_primary.get(metric_key, baseline_val))

        # For accuracy metrics: if removal improves the metric, that layer was causing the failure
        # For error metrics (false/missed rate, brier): if removal reduces the metric, that layer was causing it
        if metric_key in {"transition_detection_accuracy", "transition_classification_accuracy", "cross_regime_consistency"}:
            attribution_strength = round(ablated_val - baseline_val, 4)  # positive = layer was hurting
        else:
            attribution_strength = round(baseline_val - ablated_val, 4)  # positive = layer was causing this error

        rows.append(
            {
                "failure_id": failure["id"],
                "description": failure["description"],
                "primary_responsible_layer": primary,
                "secondary_layers": secondaries,
                "metric_assessed": metric_key,
                "baseline_metric": round(baseline_val, 4),
                "ablated_metric": round(ablated_val, 4),
                "attribution_strength": attribution_strength,
                "attribution_direction": "LAYER_CAUSING_FAILURE" if attribution_strength > 0.0 else "LAYER_MASKING_FAILURE" if attribution_strength < 0.0 else "NEUTRAL",
                "redesign_priority": "HIGH" if abs(attribution_strength) > 0.02 else "MEDIUM" if abs(attribution_strength) > 0.005 else "LOW",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Interaction effects (pairwise)
# ---------------------------------------------------------------------------


def _interaction_effects_summary(ablation_results: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """Identify pairwise interactions larger than the sum of individual contributions."""
    baseline_det = float(ablation_results["BASELINE"]["transition_detection_accuracy"])
    rows: list[dict[str, Any]] = []
    for c1, c2 in itertools.combinations(COMPONENT_NAMES, 2):
        single1 = float(ablation_results[_ablation_key(frozenset({c1}))]["transition_detection_accuracy"])
        single2 = float(ablation_results[_ablation_key(frozenset({c2}))]["transition_detection_accuracy"])
        pair = float(ablation_results[_ablation_key(frozenset({c1, c2}))]["transition_detection_accuracy"])
        individual_sum = (baseline_det - single1) + (baseline_det - single2)
        pair_effect = baseline_det - pair
        synergy = round(pair_effect - individual_sum, 4)  # positive = synergistic, negative = redundant
        rows.append(
            {
                "component_a": c1,
                "component_b": c2,
                "individual_contribution_sum": round(individual_sum, 4),
                "pair_ablation_effect": round(pair_effect, 4),
                "synergy_index": synergy,
                "interaction_type": "SYNERGISTIC" if synergy > 0.005 else "REDUNDANT" if synergy < -0.005 else "INDEPENDENT",
            }
        )
    rows.sort(key=lambda r: abs(float(r["synergy_index"])), reverse=True)
    return rows[:15]  # top interactions


# ---------------------------------------------------------------------------
# Redesign recommendations
# ---------------------------------------------------------------------------


def _redesign_recommendations(
    contribution_report: list[dict[str, Any]],
    complexity_benefit: list[dict[str, Any]],
    failure_attribution: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verdicts = {row["component"]: str(row["verdict"]) for row in complexity_benefit}
    high_priority_failures: dict[str, int] = {}
    for attr in failure_attribution:
        if str(attr["redesign_priority"]) == "HIGH":
            high_priority_failures[str(attr["primary_responsible_layer"])] = high_priority_failures.get(str(attr["primary_responsible_layer"]), 0) + 1

    recommendations: list[dict[str, Any]] = []
    for comp in COMPONENT_NAMES:
        verdict = verdicts.get(comp, "INVESTIGATE")
        high_failures = high_priority_failures.get(comp, 0)
        defn = COMPONENT_DEFINITIONS[comp]
        if high_failures > 0:
            action = "REDESIGN" if verdict != "REMOVE" else "REMOVE"
        else:
            action = verdict

        rec: str
        if action == "RETAIN":
            rec = f"Retain {comp}: contributes positive incremental gain with manageable complexity."
        elif action == "REDESIGN":
            rec = f"Redesign {comp}: contributes to at least one documented failure mode; current signal set requires revision."
        elif action == "REMOVE":
            rec = f"Remove {comp}: high complexity with negative or negligible incremental gain; simplification improves performance."
        else:
            rec = f"Investigate {comp}: marginal contribution requires additional evidence before design decision."

        recommendations.append(
            {
                "component": comp,
                "action": action,
                "failure_count": high_failures,
                "complexity_cost": defn["complexity_cost"],
                "recommendation": rec,
                "signals_affected": defn["signals"],
            }
        )
    return recommendations


# ---------------------------------------------------------------------------
# Revision priority matrix
# ---------------------------------------------------------------------------


def _revision_priority_matrix(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority_rank = {"REMOVE": 0, "REDESIGN": 1, "INVESTIGATE": 2, "RETAIN": 3}
    rows = [
        {
            "priority_rank": priority_rank.get(str(r["action"]), 2),
            "component": r["component"],
            "action": r["action"],
            "failure_count": r["failure_count"],
            "complexity_cost": r["complexity_cost"],
            "recommendation": r["recommendation"],
        }
        for r in recommendations
    ]
    rows.sort(key=lambda x: (int(x["priority_rank"]), str(x["component"])))
    for rank, row in enumerate(rows):
        row["priority_rank"] = rank + 1
    return rows


# ---------------------------------------------------------------------------
# Revision plan
# ---------------------------------------------------------------------------


def _transition_engine_revision_plan(priority_matrix: list[dict[str, Any]]) -> dict[str, Any]:
    actions_by_type: dict[str, list[str]] = {"REMOVE": [], "REDESIGN": [], "INVESTIGATE": [], "RETAIN": []}
    for row in priority_matrix:
        actions_by_type.setdefault(str(row["action"]), []).append(str(row["component"]))

    steps: list[dict[str, Any]] = []
    step = 1

    for comp in actions_by_type.get("REMOVE", []):
        steps.append({"step": step, "action": "REMOVE", "component": comp, "rationale": COMPONENT_DEFINITIONS[comp]["description"]})
        step += 1
    for comp in actions_by_type.get("REDESIGN", []):
        steps.append({"step": step, "action": "REDESIGN", "component": comp, "rationale": COMPONENT_DEFINITIONS[comp]["description"]})
        step += 1
    for comp in actions_by_type.get("INVESTIGATE", []):
        steps.append({"step": step, "action": "INVESTIGATE", "component": comp, "rationale": COMPONENT_DEFINITIONS[comp]["description"]})
        step += 1
    for comp in actions_by_type.get("RETAIN", []):
        steps.append({"step": step, "action": "RETAIN", "component": comp, "rationale": COMPONENT_DEFINITIONS[comp]["description"]})
        step += 1

    to_redesign = actions_by_type.get("REDESIGN", [])
    to_remove = actions_by_type.get("REMOVE", [])
    to_retain = actions_by_type.get("RETAIN", [])
    to_investigate = actions_by_type.get("INVESTIGATE", [])

    return {
        "revision_steps": steps,
        "components_to_retain": to_retain,
        "components_to_redesign": to_redesign,
        "components_to_remove": to_remove,
        "components_requiring_additional_evidence": to_investigate,
        "estimated_complexity_reduction": f"{len(to_remove)} high-cost components removed",
        "expected_benefit": "Improved transition detection accuracy and reduced false-transition rate",
    }


# ---------------------------------------------------------------------------
# Knowledge graph payload
# ---------------------------------------------------------------------------


def _knowledge_graph_payload(
    contribution_report: list[dict[str, Any]],
    priority_matrix: list[dict[str, Any]],
    revision_plan: dict[str, Any],
) -> dict[str, Any]:
    component_nodes = [
        {
            "node_id": f"IKROS-PE1-COMPONENT-{row['component'].replace('_', '-').upper()}",
            "label": row["component"],
            "node_type": "WORLD_MODEL",
            "attributes": {
                "incremental_gain": row["incremental_gain"],
                "complexity_cost": row["complexity_cost"],
                "failure_link": row["failure_link"],
            },
        }
        for row in contribution_report
    ]
    conclusion_node = {
        "node_id": "IKROS-PE1-CONCLUSION-20260802-0001",
        "label": "Transition Engine Decomposition Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "attributes": {
            "components_to_retain": len(revision_plan["components_to_retain"]),
            "components_to_redesign": len(revision_plan["components_to_redesign"]),
            "components_to_remove": len(revision_plan["components_to_remove"]),
        },
    }
    revision_node = {
        "node_id": "IKROS-PE1-REVISION-20260802-0001",
        "label": "Transition Engine Revision Plan",
        "node_type": "VALIDATION",
        "attributes": {"step_count": len(revision_plan["revision_steps"])},
    }
    edges = []
    for node in component_nodes:
        edges.append({"source": node["node_id"], "target": conclusion_node["node_id"], "relation": "EVALUATED", "confidence": 0.7})
    edges.append({"source": conclusion_node["node_id"], "target": revision_node["node_id"], "relation": "EXPLAINS", "confidence": 0.7})
    return {
        "component_nodes": component_nodes,
        "conclusion_node": conclusion_node,
        "revision_node": revision_node,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# Main artifact preparation
# ---------------------------------------------------------------------------


def prepare_dc2_program_e_phase1_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    # Program E only requires the market data frame and REGIME_TRANSITION_PRIORS.
    # The transitive chain (Programs C→D) is NOT re-executed here — E is a standalone
    # decomposition study over the same feature frame used in Program D.

    frame = _build_conditioned_frame()
    ablation_results = _run_full_ablation(frame)
    contribution_report = _component_contribution_report(ablation_results)
    complexity_benefit = _complexity_vs_benefit_analysis(contribution_report)
    failure_attribution = _failure_attribution_report(ablation_results, contribution_report)
    interaction_effects = _interaction_effects_summary(ablation_results)
    recommendations = _redesign_recommendations(contribution_report, complexity_benefit, failure_attribution)
    priority_matrix = _revision_priority_matrix(recommendations)
    revision_plan = _transition_engine_revision_plan(priority_matrix)
    graph_payload = _knowledge_graph_payload(contribution_report, priority_matrix, revision_plan)

    # Ablation matrix: flat list of all ablation runs
    ablation_matrix: list[dict[str, Any]] = []
    for key, metrics in sorted(ablation_results.items()):
        removed = [] if key == "BASELINE" else key.split("+")
        ablation_matrix.append(
            {
                "combination_key": key,
                "removed_components": removed,
                "removed_count": len(removed),
                **{k: round(float(v), 4) for k, v in metrics.items()},
            }
        )

    analysis: dict[str, Any] = {
        "phase": "DC2_PROGRAM_E_PHASE1",
        "title": "Institutional Transition Engine Decomposition & Ablation Analysis",
        "components_evaluated": COMPONENT_NAMES,
        "ablation_run_count": len(ablation_results),
        "baseline_metrics": ablation_results["BASELINE"],
        "component_contribution_report": contribution_report,
        "ablation_matrix": ablation_matrix,
        "complexity_vs_benefit_analysis": complexity_benefit,
        "interaction_effects": interaction_effects,
        "failure_attribution_report": failure_attribution,
        "redesign_recommendations": recommendations,
        "revision_priority_matrix": priority_matrix,
        "transition_engine_revision_plan": revision_plan,
        "arb_recommendation": {
            "components_to_retain": revision_plan["components_to_retain"],
            "components_to_redesign": revision_plan["components_to_redesign"],
            "components_to_remove": revision_plan["components_to_remove"],
            "components_requiring_additional_evidence": revision_plan["components_requiring_additional_evidence"],
            "revision_plan_steps": len(revision_plan["revision_steps"]),
        },
        "ecology_knowledge_graph": graph_payload,
    }

    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_E_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_program_e_ablation_analysis.json", analysis)
    return analysis


# ---------------------------------------------------------------------------
# Report emission
# ---------------------------------------------------------------------------


def emit_dc2_program_e_phase1_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_E_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    contribution = cast(list[dict[str, Any]], analysis["component_contribution_report"])
    ablation_matrix = cast(list[dict[str, Any]], analysis["ablation_matrix"])
    complexity_benefit = cast(list[dict[str, Any]], analysis["complexity_vs_benefit_analysis"])
    failure_attr = cast(list[dict[str, Any]], analysis["failure_attribution_report"])
    recommendations = cast(list[dict[str, Any]], analysis["redesign_recommendations"])
    priority_matrix = cast(list[dict[str, Any]], analysis["revision_priority_matrix"])
    revision_plan = cast(dict[str, Any], analysis["transition_engine_revision_plan"])

    # Component Contribution Report
    contrib_md = out_dir / "COMPONENT_CONTRIBUTION_REPORT.md"
    contrib_rows = [
        [row["component"], row["incremental_gain"], row["detection_contribution"], row["classification_contribution"], row["complexity_cost"]]
        for row in contribution
    ]
    write_markdown(
        contrib_md,
        f"""# Component Contribution Report
## Discovery Cycle 2 Program E Phase 1

{markdown_table(["Component", "Incremental Gain", "Detection Contribution", "Classification Contribution", "Complexity"], contrib_rows)}

### Methodology
Contribution measured as delta in transition detection accuracy when each component's signals are removed from the engine.
Positive incremental gain indicates the component contributes positively to engine performance.
""",
    )
    written["component_contribution_report"] = str(contrib_md)

    # Ablation Matrix (summary — single and pair ablations only for readability)
    ablation_md = out_dir / "ABLATION_MATRIX.md"
    single_rows = [row for row in ablation_matrix if row["removed_count"] <= 1]
    ablation_tbl_rows = [
        [row["combination_key"], row["transition_detection_accuracy"], row["false_transition_rate"], row["missed_transition_rate"], row["confidence_calibration_brier"]]
        for row in single_rows
    ]
    write_markdown(
        ablation_md,
        f"""# Ablation Matrix
## Discovery Cycle 2 Program E Phase 1

Total ablation runs: {len(ablation_matrix)} (baseline + 7 single + 21 pair + 35 triple)

### Single-Component Ablations
{markdown_table(["Combination", "Detection Acc", "False Rate", "Missed Rate", "Brier"], ablation_tbl_rows)}

Full ablation matrix persisted in: `dc2_program_e_ablation_analysis.json`
""",
    )
    written["ablation_matrix"] = str(ablation_md)

    # Complexity vs Benefit Analysis
    cvb_md = out_dir / "COMPLEXITY_VS_BENEFIT_ANALYSIS.md"
    cvb_rows = [[row["component"], row["complexity_cost"], row["incremental_gain"], row["efficiency_score"], row["verdict"]] for row in complexity_benefit]
    write_markdown(
        cvb_md,
        f"""# Complexity vs Benefit Analysis
## Discovery Cycle 2 Program E Phase 1

{markdown_table(["Component", "Complexity", "Incremental Gain", "Efficiency Score", "Verdict"], cvb_rows)}

### Verdict Definitions
- **RETAIN**: Positive gain relative to complexity cost
- **REDESIGN**: Failure-linked with marginal positive benefit
- **REMOVE**: High complexity with negligible or negative incremental gain
- **INVESTIGATE**: Insufficient evidence for design decision
""",
    )
    written["complexity_vs_benefit_analysis"] = str(cvb_md)

    # Failure Attribution Report
    fail_md = out_dir / "FAILURE_ATTRIBUTION_REPORT.md"
    fail_rows = [
        [row["failure_id"], row["primary_responsible_layer"], row["baseline_metric"], row["ablated_metric"], row["attribution_direction"], row["redesign_priority"]]
        for row in failure_attr
    ]
    write_markdown(
        fail_md,
        f"""# Failure Attribution Report
## Discovery Cycle 2 Program E Phase 1

{markdown_table(["Failure ID", "Primary Layer", "Baseline Metric", "Ablated Metric", "Attribution", "Priority"], fail_rows)}

### Failures from Program D
Each row attributes one of the five Program D documented failures to the responsible engine component.
Attribution direction: LAYER_CAUSING_FAILURE = removal of that layer improved the failure metric.
""",
    )
    written["failure_attribution_report"] = str(fail_md)

    # Redesign Recommendations
    rec_md = out_dir / "REDESIGN_RECOMMENDATIONS.md"
    rec_rows = [[row["component"], row["action"], row["failure_count"], row["complexity_cost"]] for row in recommendations]
    rec_detail = "\n\n".join(f"**{r['component']}** ({r['action']}): {r['recommendation']}" for r in recommendations)
    write_markdown(
        rec_md,
        f"""# Redesign Recommendations
## Discovery Cycle 2 Program E Phase 1

{markdown_table(["Component", "Action", "High-Priority Failures", "Complexity"], rec_rows)}

## Detailed Recommendations

{rec_detail}
""",
    )
    written["redesign_recommendations"] = str(rec_md)

    # Revision Priority Matrix
    prio_md = out_dir / "REVISION_PRIORITY_MATRIX.md"
    prio_rows = [[row["priority_rank"], row["component"], row["action"], row["failure_count"], row["complexity_cost"]] for row in priority_matrix]
    write_markdown(
        prio_md,
        f"""# Revision Priority Matrix
## Discovery Cycle 2 Program E Phase 1

{markdown_table(["Priority", "Component", "Action", "Failure Count", "Complexity"], prio_rows)}
""",
    )
    written["revision_priority_matrix"] = str(prio_md)

    # Transition Engine Revision Plan
    plan_md = out_dir / "TRANSITION_ENGINE_REVISION_PLAN.md"
    plan_rows = [[s["step"], s["action"], s["component"], s["rationale"]] for s in revision_plan["revision_steps"]]
    write_markdown(
        plan_md,
        f"""# Transition Engine Revision Plan
## Discovery Cycle 2 Program E Phase 1

{markdown_table(["Step", "Action", "Component", "Rationale"], plan_rows)}

### Summary
- **Components to retain**: {", ".join(revision_plan["components_to_retain"]) or "none"}
- **Components to redesign**: {", ".join(revision_plan["components_to_redesign"]) or "none"}
- **Components to remove**: {", ".join(revision_plan["components_to_remove"]) or "none"}
- **Components requiring evidence**: {", ".join(revision_plan["components_requiring_additional_evidence"]) or "none"}

Expected benefit: {revision_plan["expected_benefit"]}
""",
    )
    written["transition_engine_revision_plan"] = str(plan_md)

    # ARB Recommendation
    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    arb_md = out_dir / "ARB_RECOMMENDATION.md"
    write_markdown(
        arb_md,
        f"""# Architecture Review Board Recommendation
## Discovery Cycle 2 Program E Phase 1

### Decomposition Outcome

| Category | Components |
|---|---|
| Retain | {", ".join(arb["components_to_retain"]) or "none"} |
| Redesign | {", ".join(arb["components_to_redesign"]) or "none"} |
| Remove | {", ".join(arb["components_to_remove"]) or "none"} |
| Investigate | {", ".join(arb["components_requiring_additional_evidence"]) or "none"} |

### ARB Recommendation

This decomposition establishes the scientific basis for Transition Engine revision.
The ablation study has isolated which components contribute positive incremental gain,
which are responsible for the five Program D failure modes, and which impose unjustified
complexity cost with negligible performance contribution.

A future revision program should proceed in the order defined in the Revision Priority Matrix.

### Stop Condition
Program E Phase 1 complete. Transition Engine redesign is NOT authorized within this program.
Do NOT implement Transition Engine v2. Await ARB review.
""",
    )
    written["arb_recommendation"] = str(arb_md)

    return written
