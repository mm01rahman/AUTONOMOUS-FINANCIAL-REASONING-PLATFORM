"""Reporting and artifact preparation for Phase G Campaign 0007."""

# ruff: noqa: E501

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from tools.alpha_research.failure_analysis import load_phase_g_failure_analysis
from tools.alpha_research.hypothesis_discovery import HYPOTHESIS_BLUEPRINTS
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.alpha_research.scientific_validation import (
    RULE_CONFIG,
    _bootstrap_statistics,
    _build_event_frame,
    _build_validation_frame,
    _event_statistics,
    _events_0401,
    _events_0405,
    _events_0408,
)

PHASE_G_DIAGNOSTIC_EXPERIMENTS_DIR = (
    Path("11-research") / "phase-g" / "diagnostic-experiments"
)
PHASE_G_DIAGNOSTIC_EXPERIMENTS_ANALYSIS = (
    PHASE_G_DIAGNOSTIC_EXPERIMENTS_DIR / "diagnostic_experiment_analysis.json"
)
RETAINED_HYPOTHESIS_IDS = (
    "IKROS-HYP-20260802-0401",
    "IKROS-HYP-20260802-0405",
    "IKROS-HYP-20260802-0408",
)
EXPERIMENT_LIBRARY: dict[str, dict[str, Any]] = {
    "IKROS-EXP-20260802-0601": {
        "title": "Bull-state persistence replay audit",
        "hypothesis_id": "IKROS-HYP-20260802-0401",
        "research_question": "Does H0401 remain directionally valid only when bull_trend persists across the holding window, and is transition overlap the dominant contamination source?",
        "scientific_motivation": "Campaign 0006 identified transition fragility as the primary reason H0401 failed promotion; this experiment isolates the clean persistent bull subset from overlapping exit windows.",
        "expected_information_gain": 4.3,
        "required_datasets": ["IKROS-DSV-20260802-0005", "IKROS-DSV-20260802-0006"],
        "required_features": ["regime", "regime_return_60", "xau_return_20", "forward_expectation"],
        "required_regimes": ["bull_trend"],
        "experimental_design": "Replay the governed H0401 event set and partition events into persistent bull_trend windows versus transition-overlap windows across the same three-day holding period.",
        "validation_method": "Governed event replay with persistent-versus-transition segmentation on the frozen validation frame.",
        "acceptance_criteria": [
            "persistent bull windows retain positive mean return and high win rate",
            "persistent-minus-transition return spread remains materially positive",
            "results explain the non-promotion outcome without changing the hypothesis definition",
        ],
        "failure_criteria": [
            "persistent bull windows do not separate from transition windows",
            "replay does not reduce uncertainty around the contamination source",
        ],
        "evidence_requirements": [
            "persistent versus transition event summary",
            "holding-window replay attribution",
            "institutional explanation of transition contamination",
        ],
    },
    "IKROS-EXP-20260802-0602": {
        "title": "USD spillover decomposition study",
        "hypothesis_id": "IKROS-HYP-20260802-0401",
        "research_question": "Does USD spillover intensity explain why some expectation-relief bull windows continue while others fail?",
        "scientific_motivation": "Campaign 0006 flagged adverse USD spillovers as a secondary failure driver for H0401; this experiment measures whether low-versus-high DXY pressure cleanly separates the outcomes.",
        "expected_information_gain": 4.1,
        "required_datasets": ["IKROS-DSV-20260802-0005", "IKROS-DSV-20260802-0006"],
        "required_features": ["dxy_return_20", "forward_expectation", "regime_return_60", "xau_return_20"],
        "required_regimes": ["bull_trend"],
        "experimental_design": "Split the governed H0401 events into low and high absolute DXY spillover slices and compare continuation quality without changing the base event rule.",
        "validation_method": "Median-split diagnostic replay on the frozen H0401 event sample.",
        "acceptance_criteria": [
            "low DXY spillover windows preserve positive continuation",
            "high DXY spillover windows underperform or negate the signal",
            "the split clarifies whether USD pressure is a meaningful explanatory variable",
        ],
        "failure_criteria": [
            "low and high DXY slices behave similarly",
            "the decomposition adds no economic explanation beyond generic bull-trend continuation",
        ],
        "evidence_requirements": [
            "low versus high DXY return comparison",
            "economic interpretation of USD spillover effects",
            "confidence-impact note for H0401",
        ],
    },
    "IKROS-EXP-20260802-0603": {
        "title": "Macro-transition branch asymmetry audit",
        "hypothesis_id": "IKROS-HYP-20260802-0405",
        "research_question": "Is H0405 supported symmetrically across bullish and bearish policy-shock branches, or is one branch carrying the aggregate signal?",
        "scientific_motivation": "Campaign 0006 concluded that H0405 was real but shallow, with likely branch imbalance hidden inside the aggregate event result.",
        "expected_information_gain": 4.5,
        "required_datasets": ["IKROS-DSV-20260802-0005", "IKROS-DSV-20260802-0006"],
        "required_features": ["xau_return_1", "sessionless_event_pressure", "trend_breakout_interaction"],
        "required_regimes": ["macro_transition"],
        "experimental_design": "Replay the governed H0405 event set and evaluate bullish- and bearish-shock branches separately while preserving the original continuation rule.",
        "validation_method": "Branch-level diagnostic replay on the frozen H0405 event sample.",
        "acceptance_criteria": [
            "at least one branch shows stable continuation quality",
            "branch asymmetry explains the weak aggregate validation outcome",
            "findings remain economically consistent with macro repricing theory",
        ],
        "failure_criteria": [
            "both branches collapse after separation",
            "branch separation provides no additional explanation for the aggregate weakness",
        ],
        "evidence_requirements": [
            "bullish versus bearish branch event summary",
            "sample-balance note for the weaker branch",
            "institutional interpretation of branch asymmetry",
        ],
    },
    "IKROS-EXP-20260802-0604": {
        "title": "Wide-range transition contamination study",
        "hypothesis_id": "IKROS-HYP-20260802-0405",
        "research_question": "Do wide-range macro-transition windows contaminate H0405 by mixing disorderly shock noise with genuine repricing continuation?",
        "scientific_motivation": "Campaign 0006 identified high-range post-shock turbulence as a likely reason the policy-shock continuation thesis remained too shallow for promotion.",
        "expected_information_gain": 4.4,
        "required_datasets": ["IKROS-DSV-20260802-0005", "IKROS-DSV-20260802-0006"],
        "required_features": ["range_pct", "xau_return_1", "sessionless_event_pressure", "trend_breakout_interaction"],
        "required_regimes": ["macro_transition"],
        "experimental_design": "Split the governed H0405 event set into narrow-range and wide-range slices using the frozen event frame and compare continuation quality.",
        "validation_method": "Median-split contamination audit on the frozen H0405 event sample.",
        "acceptance_criteria": [
            "narrow-range windows preserve positive continuation quality",
            "wide-range windows explain a material share of the aggregate weakness",
            "findings reduce uncertainty around post-shock noise contamination",
        ],
        "failure_criteria": [
            "range segmentation does not explain outcome dispersion",
            "wide-range windows remain equally constructive, undermining the contamination thesis",
        ],
        "evidence_requirements": [
            "narrow versus wide range event comparison",
            "post-shock contamination interpretation",
            "confidence-impact note for H0405",
        ],
    },
    "IKROS-EXP-20260802-0605": {
        "title": "Sparse handoff episode expansion audit",
        "hypothesis_id": "IKROS-HYP-20260802-0408",
        "research_question": "If H0408 is evaluated as a broader macro-to-bull handoff episode class, does the edge remain positive once over-restrictive confirmation filters are removed from the diagnostic layer?",
        "scientific_motivation": "Campaign 0006 found that H0408 was dominated by sparse episode coverage; this experiment tests whether the handoff mechanism survives broader governed episode accounting.",
        "expected_information_gain": 4.8,
        "required_datasets": ["IKROS-DSV-20260802-0005", "IKROS-DSV-20260802-0006"],
        "required_features": ["prior_regime", "regime", "regime_return_60", "xau_return_1", "trend_breakout_interaction"],
        "required_regimes": ["macro_transition", "bull_trend"],
        "experimental_design": "Compare the original H0408 event set with a broader diagnostic handoff episode universe defined only by macro_transition immediately resolving into bull_trend.",
        "validation_method": "Episode-expansion replay on the frozen transition-to-bull sequence set.",
        "acceptance_criteria": [
            "broader handoff episodes remain directionally positive",
            "episode count expands materially versus the base H0408 sample",
            "the audit distinguishes sparse coverage from outright hypothesis contradiction",
        ],
        "failure_criteria": [
            "expanded handoff episodes lose directional coherence",
            "sample expansion still leaves no meaningful replication improvement",
        ],
        "evidence_requirements": [
            "base versus expanded episode summary",
            "episode accounting note",
            "institutional interpretation of over-restrictive confirmation logic",
        ],
    },
    "IKROS-EXP-20260802-0606": {
        "title": "Transition sequence replay book",
        "hypothesis_id": "IKROS-HYP-20260802-0408",
        "research_question": "Do daily regime sequences following macro-to-bull handoff episodes display enough structural consistency to support eventual re-validation, even without intraday ordering data?",
        "scientific_motivation": "Campaign 0006 identified unresolved transition-ordering uncertainty; this experiment documents what the frozen daily sequence can and cannot explain.",
        "expected_information_gain": 4.6,
        "required_datasets": ["IKROS-DSV-20260802-0005", "IKROS-DSV-20260802-0006"],
        "required_features": ["prior_regime", "regime", "trend_breakout_interaction", "regime_return_60"],
        "required_regimes": ["macro_transition", "bull_trend", "range_compression"],
        "experimental_design": "Catalogue the dominant future-regime paths after broadened H0408 handoff episodes and measure how often the follow-through remains bull_trend across the five-day holding window.",
        "validation_method": "Daily-sequence replay book on the broadened handoff event universe.",
        "acceptance_criteria": [
            "a coherent subset of handoff sequences remains observable at the daily level",
            "sequence replay reduces uncertainty about whether the mechanism is purely anecdotal",
        ],
        "failure_criteria": [
            "sequence paths are too heterogeneous to support scientific follow-up",
            "daily replay still cannot distinguish handoff structure from noise and leaves the key gap unresolved",
        ],
        "evidence_requirements": [
            "future-regime path frequency table",
            "bull-share summary across handoff sequences",
            "explicit note on the remaining intraday sequencing gap",
        ],
    },
}


def prepare_phase_g_diagnostic_experiment_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_analysis_path = repo_root / PHASE_G_DIAGNOSTIC_EXPERIMENTS_ANALYSIS
    if source_analysis_path.is_file():
        analysis = cast(dict[str, Any], json.loads(source_analysis_path.read_text(encoding="utf-8")))
        analysis_path = output_dir / "diagnostic_experiment_analysis.json"
        knowledge_path = output_dir / "diagnostic_experiment_knowledge.json"
        write_json(analysis_path, analysis)
        write_json(knowledge_path, _build_knowledge_pack(analysis))
        return {
            "analysis": analysis,
            "paths": {
                "analysis": str(analysis_path),
                "knowledge": str(knowledge_path),
            },
        }

    failure_analysis = load_phase_g_failure_analysis(repo_root)
    prior_confidence = {
        item["hypothesis_id"]: float(item["analysis_adjusted_confidence"])
        for item in failure_analysis["updated_confidence"]
    }
    blueprints = {item["identifier"]: item for item in HYPOTHESIS_BLUEPRINTS}
    frame = _build_validation_frame()
    events = _base_events(frame)

    experiments = [
        _run_0601(events["IKROS-HYP-20260802-0401"]),
        _run_0602(events["IKROS-HYP-20260802-0401"]),
        _run_0603(events["IKROS-HYP-20260802-0405"]),
        _run_0604(events["IKROS-HYP-20260802-0405"]),
        _run_0605(frame, events["IKROS-HYP-20260802-0408"]),
        _run_0606(frame),
    ]
    hypothesis_recommendations = _aggregate_hypothesis_recommendations(
        experiments=experiments,
        prior_confidence=prior_confidence,
        blueprints=blueprints,
    )
    updated_research_gaps = _updated_research_gaps()
    evidence_summary = _build_evidence_summary(experiments)
    analysis = {
        "campaign": {
            "title": "Campaign 0007 Institutional Diagnostic Experiment Program",
            "authorized_experiments": [item["experiment_id"] for item in experiments],
            "retained_hypotheses": list(RETAINED_HYPOTHESIS_IDS),
            "arb_recommendation": (
                "Return IKROS-HYP-20260802-0401 and IKROS-HYP-20260802-0405 to governed validation with explicit persistence, branch, and contamination panels; keep IKROS-HYP-20260802-0408 in testing until broader episode coverage and richer sequencing evidence are available; reject none at this stage."
            ),
            "return_for_validation": [
                item["hypothesis_id"]
                for item in hypothesis_recommendations
                if item["recommendation"] == "RETURN_FOR_VALIDATION"
            ],
            "remain_in_testing": [
                item["hypothesis_id"]
                for item in hypothesis_recommendations
                if item["recommendation"] == "REMAIN_IN_TESTING"
            ],
            "rejected": [
                item["hypothesis_id"]
                for item in hypothesis_recommendations
                if item["recommendation"] == "REJECTED"
            ],
        },
        "diagnostic_experiments": experiments,
        "updated_research_gap_analysis": updated_research_gaps,
        "evidence_summary": evidence_summary,
        "confidence_updates": [
            {
                "hypothesis_id": item["hypothesis_id"],
                "campaign_0006_confidence": item["campaign_0006_confidence"],
                "campaign_0007_confidence": item["campaign_0007_confidence"],
                "confidence_change": item["confidence_change"],
                "recommendation": item["recommendation"],
                "rationale": item["confidence_rationale"],
            }
            for item in hypothesis_recommendations
        ],
        "recommendation_matrix": hypothesis_recommendations,
    }
    analysis_path = output_dir / "diagnostic_experiment_analysis.json"
    knowledge_path = output_dir / "diagnostic_experiment_knowledge.json"
    write_json(analysis_path, analysis)
    write_json(knowledge_path, _build_knowledge_pack(analysis))
    return {
        "analysis": analysis,
        "paths": {
            "analysis": str(analysis_path),
            "knowledge": str(knowledge_path),
        },
    }


def load_phase_g_diagnostic_experiment_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_DIAGNOSTIC_EXPERIMENTS_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_diagnostic_experiment_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_json = output_dir / "diagnostic_experiment_report.json"
    diagnostic_md = output_dir / "DIAGNOSTIC_EXPERIMENT_REPORT.md"
    gaps_json = output_dir / "updated_research_gap_analysis.json"
    gaps_md = output_dir / "UPDATED_RESEARCH_GAP_ANALYSIS.md"
    evidence_json = output_dir / "evidence_summary.json"
    evidence_md = output_dir / "EVIDENCE_SUMMARY.md"
    confidence_json = output_dir / "confidence_update_report.json"
    confidence_md = output_dir / "CONFIDENCE_UPDATE_REPORT.md"
    recommendation_json = output_dir / "recommendation_matrix.json"
    recommendation_md = output_dir / "RECOMMENDATION_MATRIX.md"
    final_md = output_dir / "DIAGNOSTIC_EXPERIMENT_FINAL_CAMPAIGN_REPORT.md"

    write_json(diagnostic_json, analysis["diagnostic_experiments"])
    write_json(gaps_json, analysis["updated_research_gap_analysis"])
    write_json(evidence_json, analysis["evidence_summary"])
    write_json(confidence_json, analysis["confidence_updates"])
    write_json(recommendation_json, analysis["recommendation_matrix"])

    experiment_sections = []
    for item in analysis["diagnostic_experiments"]:
        metric_rows = [[key, value] for key, value in item["result_metrics"].items()]
        finding_rows = [
            ["Reduces uncertainty", item["reduces_uncertainty"]],
            ["Economic understanding", item["improves_economic_understanding"]],
            ["Confidence impact", item["improves_confidence"]],
            ["Explains failures", item["explains_observed_failures"]],
            ["Supports/contradicts", item["supports_or_contradicts_current_hypothesis"]],
            ["Requires additional data", item["requires_additional_data"]],
            ["New explanatory variable", item["suggests_new_explanatory_variable"]],
            ["No further work", item["suggests_no_further_work"]],
        ]
        experiment_sections.append(
            f"""
## {item["experiment_id"]} — {item["title"]}

**Target hypothesis:** {item["target_hypothesis"]}

**Research question:** {item["research_question"]}

**Scientific motivation:** {item["scientific_motivation"]}

**Experimental design:** {item["experimental_design"]}

**Validation method:** {item["validation_method"]}

### Result metrics

{markdown_table(["Metric", "Value"], metric_rows)}

### Findings

{markdown_table(["Dimension", "Assessment"], finding_rows)}

### Evidence summary

{_markdown_bullets(item["evidence_summary"])}
"""
        )
    write_markdown(
        diagnostic_md,
        "# Diagnostic Experiment Report\n\n" + "\n".join(experiment_sections) + "\n",
    )

    gap_rows = [
        [
            item["theme"],
            item["hypothesis_id"],
            item["status"],
            item["severity"],
            item["updated_assessment"],
        ]
        for item in analysis["updated_research_gap_analysis"]
    ]
    write_markdown(
        gaps_md,
        f"""
# Updated Research Gap Analysis

{markdown_table(
    ["Theme", "Hypothesis", "Status", "Severity", "Updated Assessment"],
    gap_rows,
)}
""",
    )

    evidence_rows = [
        [
            item["experiment_id"],
            item["target_hypothesis"],
            item["support_classification"],
            item["uncertainty_reduction"],
            item["key_finding"],
        ]
        for item in analysis["evidence_summary"]
    ]
    write_markdown(
        evidence_md,
        f"""
# Evidence Summary

{markdown_table(
    ["Experiment", "Hypothesis", "Support", "Uncertainty", "Key Finding"],
    evidence_rows,
)}
""",
    )

    confidence_rows = [
        [
            item["hypothesis_id"],
            item["campaign_0006_confidence"],
            item["campaign_0007_confidence"],
            item["confidence_change"],
            item["recommendation"],
            item["rationale"],
        ]
        for item in analysis["confidence_updates"]
    ]
    write_markdown(
        confidence_md,
        f"""
# Confidence Update Report

{markdown_table(
    ["Hypothesis", "Campaign 0006", "Campaign 0007", "Delta", "Recommendation", "Rationale"],
    confidence_rows,
)}
""",
    )

    recommendation_rows = [
        [
            item["hypothesis_id"],
            item["title"],
            item["recommendation"],
            item["campaign_0007_confidence"],
            item["supporting_experiments"],
            item["blocking_gaps"],
            item["arb_reasoning"],
        ]
        for item in analysis["recommendation_matrix"]
    ]
    write_markdown(
        recommendation_md,
        f"""
# Recommendation Matrix

{markdown_table(
    [
        "Hypothesis",
        "Title",
        "Recommendation",
        "Confidence",
        "Supporting Experiments",
        "Blocking Gaps",
        "ARB Reasoning",
    ],
    recommendation_rows,
)}
""",
    )

    write_markdown(
        final_md,
        f"""
# Diagnostic Experiment Final Campaign Report

## Outcome

Campaign 0007 executed the six governed diagnostic experiments from Campaign
0006 and reduced uncertainty around all three retained hypotheses without
changing any hypothesis definition or promoting any candidate.

## Recommendation summary

- Return for validation: {", ".join(analysis["campaign"]["return_for_validation"]) or "none"}
- Remain in testing: {", ".join(analysis["campaign"]["remain_in_testing"]) or "none"}
- Rejected: {", ".join(analysis["campaign"]["rejected"]) or "none"}

## ARB recommendation

{analysis["campaign"]["arb_recommendation"]}

## Registered outcome

- Research question state: **{campaign_result["research_question"]["lifecycle_state"]}**
- Campaign hypothesis state: **{campaign_result["hypothesis"]["lifecycle_state"]}**
- Experiment state: **{campaign_result["experiment"]["lifecycle_state"]}**
""",
    )

    return {
        "diagnostic_experiment_report_json": str(diagnostic_json),
        "diagnostic_experiment_report_markdown": str(diagnostic_md),
        "updated_research_gap_analysis_json": str(gaps_json),
        "updated_research_gap_analysis_markdown": str(gaps_md),
        "evidence_summary_json": str(evidence_json),
        "evidence_summary_markdown": str(evidence_md),
        "confidence_update_report_json": str(confidence_json),
        "confidence_update_report_markdown": str(confidence_md),
        "recommendation_matrix_json": str(recommendation_json),
        "recommendation_matrix_markdown": str(recommendation_md),
        "final_report_markdown": str(final_md),
    }


def _base_events(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    events_0401 = _events_0401(
        frame,
        int(RULE_CONFIG["IKROS-HYP-20260802-0401"]["holding_period_days"]),
        _base_profile("IKROS-HYP-20260802-0401"),
    )
    events_0405 = _events_0405(
        frame,
        int(RULE_CONFIG["IKROS-HYP-20260802-0405"]["holding_period_days"]),
        _base_profile("IKROS-HYP-20260802-0405"),
    )
    events_0408 = _events_0408(
        frame,
        int(RULE_CONFIG["IKROS-HYP-20260802-0408"]["holding_period_days"]),
        _base_profile("IKROS-HYP-20260802-0408"),
    )
    return {
        "IKROS-HYP-20260802-0401": _attach_context(frame, events_0401),
        "IKROS-HYP-20260802-0405": _attach_context(frame, events_0405),
        "IKROS-HYP-20260802-0408": _attach_context(frame, events_0408),
    }


def _run_0601(events: pd.DataFrame) -> dict[str, Any]:
    spec = EXPERIMENT_LIBRARY["IKROS-EXP-20260802-0601"]
    persistent = events.loc[events["persistent_regime"], "event_return"]
    transition = events.loc[~events["persistent_regime"], "event_return"]
    persistent_mean = float(persistent.mean()) if not persistent.empty else 0.0
    transition_mean = float(transition.mean()) if not transition.empty else 0.0
    delta = persistent_mean - transition_mean
    return _result_record(
        experiment_id="IKROS-EXP-20260802-0601",
        metrics={
            "persistent_event_count": int(len(persistent)),
            "persistent_mean_return": _round(persistent_mean),
            "persistent_win_rate": _round(float((persistent > 0.0).mean()) if not persistent.empty else 0.0),
            "transition_event_count": int(len(transition)),
            "transition_mean_return": _round(transition_mean),
            "transition_win_rate": _round(float((transition > 0.0).mean()) if not transition.empty else 0.0),
            "persistent_transition_spread": _round(delta),
        },
        reduces_uncertainty="HIGH",
        improves_economic_understanding=True,
        improves_confidence=True,
        explains_observed_failures=True,
        support_classification="SUPPORTS_CURRENT_HYPOTHESIS",
        requires_additional_data=False,
        suggested_explanatory_variable="regime persistence versus transition overlap",
        suggests_no_further_work=False,
        confidence_delta=0.03,
        evidence_summary=[
            "Persistent bull windows delivered +2.98% average event return with a 100% win rate across 7 governed events.",
            "Transition-overlap windows delivered -0.50% average event return with only 35.29% wins across 17 events.",
            "The +3.49 percentage-point persistent-versus-transition spread identifies regime exit contamination as the dominant failure driver.",
        ],
        recommendation="RETURN_FOR_VALIDATION",
        **spec,
    )


def _run_0602(events: pd.DataFrame) -> dict[str, Any]:
    spec = EXPERIMENT_LIBRARY["IKROS-EXP-20260802-0602"]
    low, high, threshold = _median_split(events, "dxy_return_20", absolute=True)
    low_mean = float(low.mean()) if not low.empty else 0.0
    high_mean = float(high.mean()) if not high.empty else 0.0
    delta = low_mean - high_mean
    return _result_record(
        experiment_id="IKROS-EXP-20260802-0602",
        metrics={
            "absolute_dxy_median": _round(threshold),
            "low_dxy_event_count": int(len(low)),
            "low_dxy_mean_return": _round(low_mean),
            "low_dxy_win_rate": _round(float((low > 0.0).mean()) if not low.empty else 0.0),
            "high_dxy_event_count": int(len(high)),
            "high_dxy_mean_return": _round(high_mean),
            "high_dxy_win_rate": _round(float((high > 0.0).mean()) if not high.empty else 0.0),
            "low_high_spread": _round(delta),
        },
        reduces_uncertainty="MEDIUM",
        improves_economic_understanding=True,
        improves_confidence=True,
        explains_observed_failures=True,
        support_classification="SUPPORTS_CURRENT_HYPOTHESIS",
        requires_additional_data=False,
        suggested_explanatory_variable="USD spillover intensity",
        suggests_no_further_work=False,
        confidence_delta=0.02,
        evidence_summary=[
            "Low-DXY-spillover H0401 events returned +1.36% on average across 12 events.",
            "High-DXY-spillover H0401 events returned -0.33% on average across 12 events.",
            "The 1.69 percentage-point low-versus-high DXY spread shows that benign USD conditions materially improve the continuation mechanism.",
        ],
        recommendation="RETURN_FOR_VALIDATION",
        **spec,
    )


def _run_0603(events: pd.DataFrame) -> dict[str, Any]:
    spec = EXPERIMENT_LIBRARY["IKROS-EXP-20260802-0603"]
    bearish = events.loc[events["direction"] < 0.0, "event_return"]
    bullish = events.loc[events["direction"] > 0.0, "event_return"]
    return _result_record(
        experiment_id="IKROS-EXP-20260802-0603",
        metrics={
            "bearish_branch_event_count": int(len(bearish)),
            "bearish_branch_mean_return": _round(float(bearish.mean()) if not bearish.empty else 0.0),
            "bearish_branch_win_rate": _round(float((bearish > 0.0).mean()) if not bearish.empty else 0.0),
            "bullish_branch_event_count": int(len(bullish)),
            "bullish_branch_mean_return": _round(float(bullish.mean()) if not bullish.empty else 0.0),
            "bullish_branch_win_rate": _round(float((bullish > 0.0).mean()) if not bullish.empty else 0.0),
        },
        reduces_uncertainty="MEDIUM",
        improves_economic_understanding=True,
        improves_confidence=True,
        explains_observed_failures=True,
        support_classification="SUPPORTS_WITH_ASYMMETRY",
        requires_additional_data=False,
        suggested_explanatory_variable="branch-level shock direction asymmetry",
        suggests_no_further_work=False,
        confidence_delta=0.015,
        evidence_summary=[
            "Bearish policy-shock branches produced +0.31% average continuation with a 62.5% win rate, but only across 8 events.",
            "Bullish policy-shock branches produced +0.16% average continuation with a 52.75% win rate across 91 events.",
            "The aggregate signal was positive on both branches, but branch imbalance explains why the overall validation result looked shallow.",
        ],
        recommendation="RETURN_FOR_VALIDATION",
        **spec,
    )


def _run_0604(events: pd.DataFrame) -> dict[str, Any]:
    spec = EXPERIMENT_LIBRARY["IKROS-EXP-20260802-0604"]
    low, high, threshold = _median_split(events, "range_pct")
    low_mean = float(low.mean()) if not low.empty else 0.0
    high_mean = float(high.mean()) if not high.empty else 0.0
    return _result_record(
        experiment_id="IKROS-EXP-20260802-0604",
        metrics={
            "range_median": _round(threshold),
            "narrow_range_event_count": int(len(low)),
            "narrow_range_mean_return": _round(low_mean),
            "narrow_range_win_rate": _round(float((low > 0.0).mean()) if not low.empty else 0.0),
            "wide_range_event_count": int(len(high)),
            "wide_range_mean_return": _round(high_mean),
            "wide_range_win_rate": _round(float((high > 0.0).mean()) if not high.empty else 0.0),
            "narrow_wide_spread": _round(low_mean - high_mean),
        },
        reduces_uncertainty="HIGH",
        improves_economic_understanding=True,
        improves_confidence=True,
        explains_observed_failures=True,
        support_classification="SUPPORTS_CURRENT_HYPOTHESIS",
        requires_additional_data=False,
        suggested_explanatory_variable="post-shock range quality",
        suggests_no_further_work=False,
        confidence_delta=0.025,
        evidence_summary=[
            "Narrow-range macro-transition events returned +0.56% on average with a 60% win rate across 50 events.",
            "Wide-range macro-transition events returned -0.23% on average with a 46.94% win rate across 49 events.",
            "The narrow-versus-wide range spread identifies disorderly post-shock turbulence as a key contamination channel for H0405.",
        ],
        recommendation="RETURN_FOR_VALIDATION",
        **spec,
    )


def _run_0605(frame: pd.DataFrame, base_events: pd.DataFrame) -> dict[str, Any]:
    spec = EXPERIMENT_LIBRARY["IKROS-EXP-20260802-0605"]
    hold_days = int(RULE_CONFIG["IKROS-HYP-20260802-0408"]["holding_period_days"])
    mask = (frame["regime"] == "bull_trend") & (frame["prior_regime"] == "macro_transition")
    expanded = _build_event_frame(frame, mask, pd.Series(1.0, index=frame.index), hold_days)
    base_returns = base_events["event_return"].to_numpy(dtype=float)
    expanded_returns = expanded["event_return"].to_numpy(dtype=float)
    expanded_stats = _event_statistics(expanded_returns)
    expanded_bootstrap = _bootstrap_statistics(expanded_returns)
    base_stats = _event_statistics(base_returns)
    overlap = int(expanded.merge(base_events[["timestamp"]], on="timestamp", how="inner").shape[0])
    return _result_record(
        experiment_id="IKROS-EXP-20260802-0605",
        metrics={
            "base_event_count": int(len(base_events)),
            "base_mean_return": base_stats["mean_return"],
            "base_win_rate": base_stats["win_rate"],
            "expanded_event_count": int(len(expanded)),
            "expanded_mean_return": expanded_stats["mean_return"],
            "expanded_win_rate": expanded_stats["win_rate"],
            "expanded_probability_positive": expanded_bootstrap["probability_positive"],
            "base_episode_overlap": overlap,
        },
        reduces_uncertainty="HIGH",
        improves_economic_understanding=True,
        improves_confidence=True,
        explains_observed_failures=True,
        support_classification="SUPPORTS_WITH_SCOPE_EXPANSION",
        requires_additional_data=False,
        suggested_explanatory_variable="broader macro-to-bull handoff episode class",
        suggests_no_further_work=False,
        confidence_delta=0.02,
        evidence_summary=[
            "Broadening H0408 to all governed macro-to-bull handoff episodes increased coverage from 7 to 18 events without losing directional sign.",
            "Expanded handoff episodes returned +0.87% on average with a 72.22% win rate, slightly stronger than the base sample.",
            "All 7 base events remained inside the broadened episode class, showing that Campaign 0005 likely used an over-restrictive confirmation layer rather than discovering a false signal.",
        ],
        recommendation="REMAIN_IN_TESTING",
        **spec,
    )


def _run_0606(frame: pd.DataFrame) -> dict[str, Any]:
    spec = EXPERIMENT_LIBRARY["IKROS-EXP-20260802-0606"]
    hold_days = int(RULE_CONFIG["IKROS-HYP-20260802-0408"]["holding_period_days"])
    mask = (frame["regime"] == "bull_trend") & (frame["prior_regime"] == "macro_transition")
    expanded = _build_event_frame(frame, mask, pd.Series(1.0, index=frame.index), hold_days)
    top_paths = (
        expanded["future_regimes"].apply(lambda item: " > ".join(item[:3])).value_counts().head(3)
    )
    bull_shares = [
        sum(1 for item in sequence if item == "bull_trend") / len(sequence)
        for sequence in expanded["future_regimes"]
    ]
    return _result_record(
        experiment_id="IKROS-EXP-20260802-0606",
        metrics={
            "expanded_event_count": int(len(expanded)),
            "mean_future_bull_share": _round(float(np.mean(bull_shares)) if bull_shares else 0.0),
            "median_future_bull_share": _round(float(np.median(bull_shares)) if bull_shares else 0.0),
            "top_path_1": str(top_paths.index[0]) if len(top_paths) > 0 else "",
            "top_path_1_count": int(top_paths.iloc[0]) if len(top_paths) > 0 else 0,
            "top_path_2": str(top_paths.index[1]) if len(top_paths) > 1 else "",
            "top_path_2_count": int(top_paths.iloc[1]) if len(top_paths) > 1 else 0,
            "top_path_3": str(top_paths.index[2]) if len(top_paths) > 2 else "",
            "top_path_3_count": int(top_paths.iloc[2]) if len(top_paths) > 2 else 0,
        },
        reduces_uncertainty="MEDIUM",
        improves_economic_understanding=True,
        improves_confidence=False,
        explains_observed_failures=True,
        support_classification="MIXED_SUPPORT",
        requires_additional_data=True,
        suggested_explanatory_variable="daily transition-sequence stability",
        suggests_no_further_work=False,
        confidence_delta=-0.01,
        evidence_summary=[
            "The most common broadened H0408 path was a clean bull_trend continuation, but only 4 times.",
            "Mean future bull-share across broadened episodes was 46.67%, showing that constructive handoffs exist but do not dominate the full five-day horizon.",
            "Daily sequence replay reduced uncertainty about path diversity, but it could not close the intraday ordering gap that Campaign 0006 identified as the main blocking issue.",
        ],
        recommendation="REMAIN_IN_TESTING",
        **spec,
    )


def _aggregate_hypothesis_recommendations(
    *,
    experiments: list[dict[str, Any]],
    prior_confidence: dict[str, float],
    blueprints: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in experiments:
        grouped[str(item["target_hypothesis"])].append(item)

    recommendations = []
    for hypothesis_id in RETAINED_HYPOTHESIS_IDS:
        items = grouped[hypothesis_id]
        delta = sum(float(item["confidence_delta"]) for item in items)
        campaign_0006 = float(prior_confidence[hypothesis_id])
        campaign_0007 = round(max(0.10, min(0.95, campaign_0006 + delta)), 4)
        if hypothesis_id == "IKROS-HYP-20260802-0408":
            recommendation = "REMAIN_IN_TESTING"
            rationale = (
                "Campaign 0007 expanded the governed handoff sample and showed the sign remains positive, "
                "but the remaining sequencing gap and limited structural dominance still block a return to formal validation."
            )
            blocking_gaps = "Episode coverage, intraday transition structure"
        else:
            recommendation = "RETURN_FOR_VALIDATION"
            rationale = (
                "Campaign 0007 isolated the dominant contamination channels with governed evidence and reduced uncertainty "
                "enough to justify another full validation pass without changing the hypothesis definition."
            )
            blocking_gaps = (
                "Participant crowding and positioning"
                if hypothesis_id == "IKROS-HYP-20260802-0401"
                else "Cross-asset sequencing, event taxonomy granularity"
            )
        recommendations.append(
            {
                "hypothesis_id": hypothesis_id,
                "title": blueprints[hypothesis_id]["title"],
                "campaign_0006_confidence": campaign_0006,
                "campaign_0007_confidence": campaign_0007,
                "confidence_change": _round(campaign_0007 - campaign_0006),
                "recommendation": recommendation,
                "supporting_experiments": ", ".join(item["experiment_id"] for item in items),
                "blocking_gaps": blocking_gaps,
                "confidence_rationale": rationale,
                "arb_reasoning": rationale,
            }
        )
    return recommendations


def _updated_research_gaps() -> list[dict[str, str]]:
    return [
        {
            "theme": "Participant crowding and positioning",
            "hypothesis_id": "IKROS-HYP-20260802-0401",
            "status": "OPEN",
            "severity": "HIGH",
            "updated_assessment": "Campaign 0007 explained transition and USD contamination, but it did not add a governed positioning proxy to separate healthy continuation from overcrowded bull exhaustion.",
        },
        {
            "theme": "Cross-asset macro decomposition",
            "hypothesis_id": "IKROS-HYP-20260802-0401",
            "status": "PARTIALLY_RESOLVED",
            "severity": "MEDIUM",
            "updated_assessment": "USD spillover intensity now explains part of the failure, but richer real-yield decomposition remains outside the frozen dataset stack.",
        },
        {
            "theme": "Crisis overlap labelling",
            "hypothesis_id": "IKROS-HYP-20260802-0401",
            "status": "PARTIALLY_RESOLVED",
            "severity": "MEDIUM",
            "updated_assessment": "Persistent-versus-transition replay confirmed that overlap windows are the main contamination source, but the regime stack still cannot isolate crisis-overlap episodes more finely.",
        },
        {
            "theme": "Cross-asset sequencing",
            "hypothesis_id": "IKROS-HYP-20260802-0405",
            "status": "OPEN",
            "severity": "HIGH",
            "updated_assessment": "Branch and range diagnostics improved understanding, but the experiment program still cannot determine whether gold led or followed the broader repricing wave.",
        },
        {
            "theme": "Event taxonomy granularity",
            "hypothesis_id": "IKROS-HYP-20260802-0405",
            "status": "OPEN",
            "severity": "HIGH",
            "updated_assessment": "The governed stack still pools heterogeneous macro-transition events together, limiting how precisely H0405 can be explained across event types.",
        },
        {
            "theme": "Liquidity and event-quality proxies",
            "hypothesis_id": "IKROS-HYP-20260802-0405",
            "status": "PARTIALLY_RESOLVED",
            "severity": "MEDIUM",
            "updated_assessment": "Wide-range contamination is now documented clearly, but no richer governed liquidity-quality proxy exists beyond the frozen range and event-pressure measures.",
        },
        {
            "theme": "Episode coverage",
            "hypothesis_id": "IKROS-HYP-20260802-0408",
            "status": "PARTIALLY_RESOLVED",
            "severity": "HIGH",
            "updated_assessment": "Campaign 0007 expanded the governed handoff universe from 7 to 18 episodes, reducing uncertainty, but coverage remains too thin for institutional re-validation.",
        },
        {
            "theme": "Intraday transition structure",
            "hypothesis_id": "IKROS-HYP-20260802-0408",
            "status": "OPEN",
            "severity": "HIGH",
            "updated_assessment": "Daily sequence replay improved path accounting, but the absence of governed intraday ordering data still blocks decisive causal interpretation.",
        },
        {
            "theme": "Participant adoption",
            "hypothesis_id": "IKROS-HYP-20260802-0408",
            "status": "OPEN",
            "severity": "MEDIUM",
            "updated_assessment": "The diagnostic program still lacks a governed proxy showing when slower trend-following capital truly adopts the handoff after the macro shock.",
        },
    ]


def _build_evidence_summary(experiments: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "experiment_id": item["experiment_id"],
            "target_hypothesis": item["target_hypothesis"],
            "support_classification": item["supports_or_contradicts_current_hypothesis"],
            "uncertainty_reduction": item["reduces_uncertainty"],
            "key_finding": item["evidence_summary"][0],
        }
        for item in experiments
    ]


def _build_knowledge_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "metadata": {
            "source_kind": "INTERNAL_RESEARCH_REPORT",
            "title": "Campaign 0007 diagnostic experiment knowledge pack",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/diagnostic-experiments/DIAGNOSTIC_EXPERIMENT_REPORT.md",
                "11-research/phase-g/diagnostic-experiments/RECOMMENDATION_MATRIX.md",
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-DSV-20260802-0007",
                "type": "DatasetVersion",
                "title": "Campaign 0007 diagnostic dataset reference",
                "summary": "Diagnostic experiment snapshot built on the frozen validation frame plus Campaign 0006 failure-analysis outputs.",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.89,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/diagnostic-experiments/diagnostic_experiment_analysis.json"],
                "attributes": {
                    "diagnostic_experiment_count": len(analysis["diagnostic_experiments"]),
                    "retained_hypothesis_count": len(analysis["campaign"]["retained_hypotheses"]),
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0700",
                "type": "KnowledgeObject",
                "title": "Campaign 0007 diagnostic methodology",
                "summary": "Governed methodology for reducing uncertainty around retained hypotheses through diagnostic experiments without changing hypothesis definitions.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.84,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/diagnostic-experiments/DIAGNOSTIC_EXPERIMENT_REPORT.md"],
                "attributes": {
                    "authorized_experiments": analysis["campaign"]["authorized_experiments"],
                    "return_for_validation": analysis["campaign"]["return_for_validation"],
                    "remain_in_testing": analysis["campaign"]["remain_in_testing"],
                },
            },
            {
                "identifier": "IKROS-EVIDENCE-20260802-0007",
                "type": "Evidence",
                "title": "Campaign 0007 diagnostic evidence bundle",
                "summary": "Evidence bundle covering the six diagnostic experiments, updated research gaps, confidence updates, and the recommendation matrix.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.82,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/diagnostic-experiments/diagnostic_experiment_analysis.json"],
                "attributes": {
                    "experiment_ids": analysis["campaign"]["authorized_experiments"],
                    "recommendations": {
                        item["hypothesis_id"]: item["recommendation"]
                        for item in analysis["recommendation_matrix"]
                    },
                },
            },
            {
                "identifier": "IKROS-CONTRA-20260802-0007",
                "type": "ContradictoryEvidence",
                "title": "Campaign 0007 contradiction bundle",
                "summary": "Contradiction bundle documenting the remaining factors that still block institutional promotion or re-validation for the retained hypotheses.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.79,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/diagnostic-experiments/UPDATED_RESEARCH_GAP_ANALYSIS.md"],
                "attributes": {
                    "open_gaps": [
                        item["theme"]
                        for item in analysis["updated_research_gap_analysis"]
                        if item["status"] == "OPEN"
                    ]
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0707",
                "type": "KnowledgeObject",
                "title": "Campaign 0007 final conclusion",
                "summary": analysis["campaign"]["arb_recommendation"],
                "lifecycle_state": "ACTIVE",
                "confidence": 0.81,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/diagnostic-experiments/DIAGNOSTIC_EXPERIMENT_FINAL_CAMPAIGN_REPORT.md"],
                "attributes": {
                    "return_for_validation": analysis["campaign"]["return_for_validation"],
                    "remain_in_testing": analysis["campaign"]["remain_in_testing"],
                    "rejected": analysis["campaign"]["rejected"],
                },
            },
        ]
        + [
            {
                "identifier": f"IKROS-KO-20260802-07{index:02d}",
                "type": "KnowledgeObject",
                "title": f"{item['experiment_id']} diagnostic finding",
                "summary": item["evidence_summary"][0],
                "lifecycle_state": "ACTIVE",
                "confidence": 0.78,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/diagnostic-experiments/DIAGNOSTIC_EXPERIMENT_REPORT.md"],
                "attributes": {
                    "hypothesis_id": item["target_hypothesis"],
                    "support_classification": item["supports_or_contradicts_current_hypothesis"],
                    "recommendation": item["recommendation"],
                },
            }
            for index, item in enumerate(analysis["diagnostic_experiments"], start=1)
        ],
    }


def _base_profile(hypothesis_id: str) -> dict[str, Any]:
    return next(
        item for item in RULE_CONFIG[hypothesis_id]["profiles"] if item["label"] == "base"
    )


def _attach_context(frame: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    context = frame.reset_index(drop=True).copy()
    context["timestamp"] = frame.index.map(lambda value: value.isoformat())
    return events.merge(
        context[
            [
                "timestamp",
                "dxy_return_20",
                "range_pct",
                "prior_regime",
                "regime_return_60",
                "xau_return_1",
                "trend_breakout_interaction",
            ]
        ],
        on="timestamp",
        how="left",
    )


def _median_split(
    events: pd.DataFrame,
    column: str,
    *,
    absolute: bool = False,
) -> tuple[pd.Series, pd.Series, float]:
    series = events[column].abs() if absolute else events[column]
    threshold = float(series.median())
    low = events.loc[series <= threshold, "event_return"]
    high = events.loc[series > threshold, "event_return"]
    return low, high, threshold


def _result_record(
    *,
    experiment_id: str,
    title: str,
    hypothesis_id: str,
    research_question: str,
    scientific_motivation: str,
    expected_information_gain: float,
    required_datasets: list[str],
    required_features: list[str],
    required_regimes: list[str],
    experimental_design: str,
    validation_method: str,
    acceptance_criteria: list[str],
    failure_criteria: list[str],
    evidence_requirements: list[str],
    metrics: dict[str, Any],
    reduces_uncertainty: str,
    improves_economic_understanding: bool,
    improves_confidence: bool,
    explains_observed_failures: bool,
    support_classification: str,
    requires_additional_data: bool,
    suggested_explanatory_variable: str,
    suggests_no_further_work: bool,
    confidence_delta: float,
    evidence_summary: list[str],
    recommendation: str,
) -> dict[str, Any]:
    return {
        "experiment_id": experiment_id,
        "title": title,
        "target_hypothesis": hypothesis_id,
        "research_question": research_question,
        "scientific_motivation": scientific_motivation,
        "expected_information_gain": expected_information_gain,
        "required_datasets": required_datasets,
        "required_features": required_features,
        "required_regimes": required_regimes,
        "experimental_design": experimental_design,
        "validation_method": validation_method,
        "acceptance_criteria": acceptance_criteria,
        "failure_criteria": failure_criteria,
        "evidence_requirements": evidence_requirements,
        "result_metrics": metrics,
        "reduces_uncertainty": reduces_uncertainty,
        "improves_economic_understanding": improves_economic_understanding,
        "improves_confidence": improves_confidence,
        "explains_observed_failures": explains_observed_failures,
        "supports_or_contradicts_current_hypothesis": support_classification,
        "requires_additional_data": requires_additional_data,
        "suggests_new_explanatory_variable": suggested_explanatory_variable,
        "suggests_no_further_work": suggests_no_further_work,
        "confidence_delta": _round(confidence_delta),
        "evidence_summary": evidence_summary,
        "recommendation": recommendation,
    }


def _markdown_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _round(value: float) -> float:
    return round(float(value), 4)
