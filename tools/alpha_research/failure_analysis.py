"""Reporting and artifact preparation for Phase G Campaign 0006 failure analysis."""

# ruff: noqa: E501

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from tools.alpha_research.hypothesis_discovery import HYPOTHESIS_BLUEPRINTS
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.alpha_research.scientific_validation import (
    RULE_CONFIG,
    _bootstrap_statistics,
    _build_validation_frame,
    _cpcv_statistics,
    _event_statistics,
    _events_0401,
    _events_0405,
    _events_0408,
    _monte_carlo_statistics,
    _out_of_sample_statistics,
    _regime_stability_statistics,
    _sensitivity_summary,
    _stress_statistics,
    _temporal_statistics,
    _walk_forward_statistics,
    _white_reality_check,
    load_phase_g_scientific_validation_analysis,
)

PHASE_G_FAILURE_ANALYSIS_DIR = Path("11-research") / "phase-g" / "failure-analysis"
PHASE_G_FAILURE_ANALYSIS_ANALYSIS = (
    PHASE_G_FAILURE_ANALYSIS_DIR / "failure_analysis_analysis.json"
)
RETAINED_HYPOTHESIS_IDS = (
    "IKROS-HYP-20260802-0401",
    "IKROS-HYP-20260802-0405",
    "IKROS-HYP-20260802-0408",
)

ROOT_CAUSE_GUIDANCE: dict[str, dict[str, Any]] = {
    "IKROS-HYP-20260802-0401": {
        "root_cause": "The continuation thesis is strongest only while bull_trend persists; negative transition windows and adverse USD spillovers diluted a positive but modest core effect below the institutional promotion floor.",
        "alternative_explanations": [
            "Observed continuation may reflect generic benign-USD carry conditions rather than a distinct expectation-relief mechanism.",
            "The few crisis-overlap bull windows can overwhelm otherwise constructive expectation resets and make the thesis look weaker than the pure bull-trend episodes.",
        ],
        "missing_data_assessment": [
            {
                "gap_id": "gap-0401-crowding",
                "theme": "Participant crowding and positioning",
                "severity": "HIGH",
                "missing_artifact": "No governed CTA positioning, futures crowding, or ETF-flow series exists to distinguish clean trend continuation from overcrowded bull exhaustion.",
            },
            {
                "gap_id": "gap-0401-real-yields",
                "theme": "Cross-asset macro decomposition",
                "severity": "MEDIUM",
                "missing_artifact": "Forward expectation is present, but there is no richer governed decomposition separating real-yield relief from USD weakness and reserve-demand impulses.",
            },
            {
                "gap_id": "gap-0401-crisis-overlap",
                "theme": "Crisis overlap labelling",
                "severity": "MEDIUM",
                "missing_artifact": "The frozen regime stack does not isolate crisis-overlap bull windows beyond the top-level taxonomy, leaving tail episodes pooled with cleaner continuation states.",
            },
        ],
        "recommended_refinements": [
            "Retain the hypothesis statement but require future validation runs to report bull-state persistence separately from transition-overlap windows.",
            "Treat DXY and expectation relief as a conditioning panel, not a single blended success criterion, so adverse USD spillovers are visible rather than hidden inside the aggregate result.",
            "Require a dedicated exhaustion-versus-continuation replay pack for pandemic-style shock windows before reconsidering institutional promotion.",
        ],
        "recommended_experiments": [
            {
                "experiment_id": "IKROS-EXP-20260802-0601",
                "title": "Bull-state persistence replay audit",
                "objective": "Replay only the persistent bull_trend windows and compare them with transition-overlap windows to quantify contamination from regime exits.",
                "priority": "P1",
                "expected_information_gain": 4.3,
            },
            {
                "experiment_id": "IKROS-EXP-20260802-0602",
                "title": "USD spillover decomposition study",
                "objective": "Measure how low-versus-high DXY pressure changes continuation reliability without altering the hypothesis rule.",
                "priority": "P1",
                "expected_information_gain": 4.1,
            },
        ],
    },
    "IKROS-HYP-20260802-0405": {
        "root_cause": "The policy-shock thesis contains a real but shallow edge; it degrades when macro-transition events expand into noisy, high-range follow-through and when the regime handoff remains unresolved after the first shock day.",
        "alternative_explanations": [
            "The retained edge may be generic post-event drift rather than specifically policy repricing continuation.",
            "The event-alignment rule may be capturing broad directional coherence while the explicit event-magnitude threshold adds little incremental information.",
        ],
        "missing_data_assessment": [
            {
                "gap_id": "gap-0405-event-taxonomy",
                "theme": "Event taxonomy granularity",
                "severity": "HIGH",
                "missing_artifact": "The frozen stack lacks richer governed distinctions between scheduled policy decisions, surprise macro prints, and disorderly headlines inside macro_transition.",
            },
            {
                "gap_id": "gap-0405-rates-ordering",
                "theme": "Cross-asset sequencing",
                "severity": "HIGH",
                "missing_artifact": "There is no governed intraday ordering between rates, USD, and gold reactions, so the study cannot tell whether gold is leading or simply following a broader repricing wave.",
            },
            {
                "gap_id": "gap-0405-liquidity-quality",
                "theme": "Liquidity and event-quality proxies",
                "severity": "MEDIUM",
                "missing_artifact": "Range and event-pressure proxies exist, but no governed session-depth or spread proxy distinguishes orderly follow-through from illiquid headline noise.",
            },
        ],
        "recommended_refinements": [
            "Retain the hypothesis statement but split future reporting into bullish and bearish policy-shock branches so event asymmetry is measured rather than averaged away.",
            "Treat the sign-alignment condition as the critical validation gate and downgrade the standalone event-magnitude threshold to a diagnostic panel unless new evidence shows it adds information.",
            "Require future validation to segment narrow-range follow-through from wide-range post-shock turbulence before any promotion review.",
        ],
        "recommended_experiments": [
            {
                "experiment_id": "IKROS-EXP-20260802-0603",
                "title": "Macro-transition branch asymmetry audit",
                "objective": "Evaluate bullish and bearish policy-shock branches separately to determine whether one side is carrying the aggregate result.",
                "priority": "P1",
                "expected_information_gain": 4.5,
            },
            {
                "experiment_id": "IKROS-EXP-20260802-0604",
                "title": "Wide-range transition contamination study",
                "objective": "Compare narrow-range and high-range macro-transition events to isolate noisy post-shock follow-through from genuine repricing continuation.",
                "priority": "P1",
                "expected_information_gain": 4.4,
            },
        ],
    },
    "IKROS-HYP-20260802-0408": {
        "root_cause": "The handoff thesis never failed on direction, but the sample is too sparse and too transition-specific to satisfy institutional replication standards; most explanatory power comes from identifying the rare macro-to-trend handoff itself, not from the added confirmation filters.",
        "alternative_explanations": [
            "The observed positive windows may be ordinary bull-trend persistence that happens to follow a macro_transition label rather than a distinct handoff mechanism.",
            "A handful of high-magnitude historical regime changes may dominate the result and make the transition logic appear more stable than it really is.",
        ],
        "missing_data_assessment": [
            {
                "gap_id": "gap-0408-sample-depth",
                "theme": "Episode coverage",
                "severity": "HIGH",
                "missing_artifact": "Only a very small number of governed handoff episodes exist, leaving no meaningful out-of-sample replay coverage in the recent sample.",
            },
            {
                "gap_id": "gap-0408-session-sequencing",
                "theme": "Intraday transition structure",
                "severity": "HIGH",
                "missing_artifact": "The frozen daily research frame cannot resolve whether the macro shock, liquidity transfer, and trend confirmation occurred in a causally coherent sequence.",
            },
            {
                "gap_id": "gap-0408-positioning",
                "theme": "Participant adoption",
                "severity": "MEDIUM",
                "missing_artifact": "No governed systematic-positioning proxy exists to tell whether trend followers actually took over after the initial macro shock.",
            },
        ],
        "recommended_refinements": [
            "Retain the hypothesis statement but require future work to treat macro-to-trend handoffs as a sparse episode class with dedicated episode accounting rather than a generic fold-based sample.",
            "Remove redundant confirmation filters from future diagnostics and focus on validating whether the prior macro-transition label itself is the scarce source of information.",
            "Require any future validation to document why no recent out-of-sample handoff episodes exist before interpreting the absence of holdout evidence as weakness or strength.",
        ],
        "recommended_experiments": [
            {
                "experiment_id": "IKROS-EXP-20260802-0605",
                "title": "Sparse handoff episode expansion audit",
                "objective": "Reconstruct and catalogue every governed macro-to-bull handoff episode to determine whether the edge survives broader historical coverage.",
                "priority": "P1",
                "expected_information_gain": 4.8,
            },
            {
                "experiment_id": "IKROS-EXP-20260802-0606",
                "title": "Transition sequence replay book",
                "objective": "Document event ordering, regime label changes, and subsequent trend adoption for each handoff episode without changing the hypothesis definition.",
                "priority": "P1",
                "expected_information_gain": 4.6,
            },
        ],
    },
}


def prepare_phase_g_failure_analysis_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_analysis_path = repo_root / PHASE_G_FAILURE_ANALYSIS_ANALYSIS
    if source_analysis_path.is_file():
        analysis = cast(dict[str, Any], json.loads(source_analysis_path.read_text(encoding="utf-8")))
        analysis_path = output_dir / "failure_analysis_analysis.json"
        knowledge_path = output_dir / "failure_analysis_knowledge.json"
        write_json(analysis_path, analysis)
        write_json(knowledge_path, _build_knowledge_pack(analysis))
        return {
            "analysis": analysis,
            "paths": {
                "analysis": str(analysis_path),
                "knowledge": str(knowledge_path),
            },
        }

    validation_analysis = load_phase_g_scientific_validation_analysis(repo_root)
    validation_by_id = {
        item["hypothesis_id"]: item for item in validation_analysis["hypothesis_validations"]
    }
    blueprints = {item["identifier"]: item for item in HYPOTHESIS_BLUEPRINTS}
    frame = _build_validation_frame()
    retained = [
        _analyse_retained_hypothesis(
            frame=frame,
            blueprint=blueprints[hypothesis_id],
            validation_record=validation_by_id[hypothesis_id],
        )
        for hypothesis_id in RETAINED_HYPOTHESIS_IDS
    ]
    root_cause_catalogue = [
        {
            "hypothesis_id": item["hypothesis_id"],
            "title": item["title"],
            "primary_root_cause": item["root_cause_analysis"]["primary_root_cause"],
            "secondary_root_causes": item["root_cause_analysis"]["secondary_root_causes"],
            "confidence_change": item["updated_confidence"]["analysis_adjusted_confidence"],
            "expected_information_gain": item["expected_information_gain"]["score"],
        }
        for item in retained
    ]
    research_gap_analysis = _aggregate_research_gaps(retained)
    experiment_backlog = _aggregate_experiment_backlog(retained)
    confidence_updates = [
        {
            "hypothesis_id": item["hypothesis_id"],
            "prior_confidence": item["updated_confidence"]["campaign_0005_confidence"],
            "analysis_adjusted_confidence": item["updated_confidence"]["analysis_adjusted_confidence"],
            "confidence_change": item["updated_confidence"]["confidence_change"],
            "reason": item["updated_confidence"]["rationale"],
        }
        for item in retained
    ]
    lineage_updates = [
        {
            "hypothesis_id": item["hypothesis_id"],
            "new_experiment_id": "IKROS-EXP-20260802-0006",
            "new_evidence_id": "IKROS-EVIDENCE-20260802-0006",
            "new_contradictory_evidence_id": "IKROS-CONTRA-20260802-0006",
            "linked_reports": [
                "11-research/phase-g/failure-analysis/failure_analysis_analysis.json",
                "11-research/phase-g/failure-analysis/ALPHA_FAILURE_ATLAS.md",
            ],
        }
        for item in retained
    ]
    analysis = {
        "campaign": {
            "title": "Campaign 0006 Institutional Alpha Failure Analysis & Hypothesis Refinement",
            "retained_hypotheses": list(RETAINED_HYPOTHESIS_IDS),
            "alpha_failure_atlas": "Institutional Alpha Failure Atlas v1",
            "arb_recommendation": (
                "ARB recommendation: preserve the retained hypothesis set unchanged, treat "
                "IKROS-HYP-20260802-0401 and IKROS-HYP-20260802-0405 as transition-fragility "
                "refinement cases, treat IKROS-HYP-20260802-0408 as a sparse-episode coverage case, "
                "and execute only the recommended diagnostic experiments before Campaign 0007."
            ),
            "completed_hypothesis_count": len(retained),
            "mean_adjusted_confidence": round(
                sum(
                    item["updated_confidence"]["analysis_adjusted_confidence"] for item in retained
                )
                / len(retained),
                4,
            ),
        },
        "retained_hypotheses": retained,
        "alpha_failure_atlas": [
            {
                "hypothesis_id": item["hypothesis_id"],
                "title": item["title"],
                "root_cause": item["root_cause_analysis"]["primary_root_cause"],
                "expected_information_gain": item["expected_information_gain"]["score"],
                "analysis_adjusted_confidence": item["updated_confidence"][
                    "analysis_adjusted_confidence"
                ],
            }
            for item in retained
        ],
        "root_cause_catalogue": root_cause_catalogue,
        "research_gap_analysis": research_gap_analysis,
        "recommended_experiment_backlog": experiment_backlog,
        "updated_confidence": confidence_updates,
        "lineage_updates": lineage_updates,
    }
    analysis_path = output_dir / "failure_analysis_analysis.json"
    knowledge_path = output_dir / "failure_analysis_knowledge.json"
    write_json(analysis_path, analysis)
    write_json(knowledge_path, _build_knowledge_pack(analysis))
    return {
        "analysis": analysis,
        "paths": {
            "analysis": str(analysis_path),
            "knowledge": str(knowledge_path),
        },
    }


def load_phase_g_failure_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_FAILURE_ANALYSIS_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_failure_analysis_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_json = output_dir / "alpha_failure_atlas.json"
    atlas_md = output_dir / "ALPHA_FAILURE_ATLAS.md"
    root_json = output_dir / "root_cause_catalogue.json"
    root_md = output_dir / "ROOT_CAUSE_CATALOGUE.md"
    refinement_json = output_dir / "hypothesis_refinement_report.json"
    refinement_md = output_dir / "HYPOTHESIS_REFINEMENT_REPORT.md"
    gaps_json = output_dir / "research_gap_analysis.json"
    gaps_md = output_dir / "RESEARCH_GAP_ANALYSIS.md"
    backlog_json = output_dir / "recommended_experiment_backlog.json"
    backlog_md = output_dir / "RECOMMENDED_EXPERIMENT_BACKLOG.md"
    confidence_json = output_dir / "updated_ikros_confidence.json"
    confidence_md = output_dir / "UPDATED_IKROS_CONFIDENCE.md"
    lineage_json = output_dir / "updated_lineage.json"
    lineage_md = output_dir / "UPDATED_LINEAGE.md"
    final_report_md = output_dir / "FAILURE_ANALYSIS_FINAL_CAMPAIGN_REPORT.md"

    write_json(atlas_json, analysis["alpha_failure_atlas"])
    write_json(root_json, analysis["root_cause_catalogue"])
    write_json(refinement_json, analysis["retained_hypotheses"])
    write_json(gaps_json, analysis["research_gap_analysis"])
    write_json(backlog_json, analysis["recommended_experiment_backlog"])
    write_json(confidence_json, analysis["updated_confidence"])
    write_json(lineage_json, analysis["lineage_updates"])

    atlas_sections = []
    for item in analysis["retained_hypotheses"]:
        evidence_rows = [
            [row["dimension"], row["signal"], row["implication"]]
            for row in item["evidence_matrix"]
        ]
        failure_rows = [
            [row["level"], row["node"], row["evidence"]]
            for row in item["failure_tree"]
        ]
        feature_rows = [
            [
                row["condition"],
                row["base_mean_return"],
                row["dropped_condition_mean_return"],
                row["classification"],
                row["interpretation"],
            ]
            for row in item["feature_gap_analysis"]
        ]
        atlas_sections.append(
            f"""
## {item["hypothesis_id"]} — {item["title"]}

**Root cause:** {item["root_cause_analysis"]["primary_root_cause"]}

### Evidence matrix

{markdown_table(["Dimension", "Signal", "Implication"], evidence_rows)}

### Failure tree

{markdown_table(["Level", "Node", "Evidence"], failure_rows)}

### Feature gap analysis

{markdown_table(["Condition", "Base Mean", "Drop Mean", "Class", "Interpretation"], feature_rows)}
"""
        )
    write_markdown(atlas_md, "# Alpha Failure Atlas\n\n" + "\n".join(atlas_sections) + "\n")

    root_rows = [
        [
            row["hypothesis_id"],
            row["title"],
            row["primary_root_cause"],
            row["secondary_root_causes"],
            row["confidence_change"],
            row["expected_information_gain"],
        ]
        for row in analysis["root_cause_catalogue"]
    ]
    write_markdown(
        root_md,
        f"""
# Root Cause Catalogue

{markdown_table(
    [
        "Hypothesis",
        "Title",
        "Primary Root Cause",
        "Secondary Root Causes",
        "Confidence",
        "Info Gain",
    ],
    root_rows,
)}
""",
    )

    refinement_sections = []
    for item in analysis["retained_hypotheses"]:
        refinement_sections.append(
            f"""
## {item["hypothesis_id"]} — {item["title"]}

### Recommended refinements

{_markdown_bullets(item["recommended_refinements"])}

### Alternative economic explanations

{_markdown_bullets(item["alternative_economic_explanations"])}
"""
        )
    write_markdown(
        refinement_md,
        "# Hypothesis Refinement Report\n\n" + "\n".join(refinement_sections) + "\n",
    )

    gap_rows = [
        [
            row["theme"],
            row["affected_hypotheses"],
            row["severity"],
            row["research_value"],
            row["summary"],
        ]
        for row in analysis["research_gap_analysis"]
    ]
    write_markdown(
        gaps_md,
        f"""
# Research Gap Analysis

{markdown_table(
    ["Theme", "Affected Hypotheses", "Severity", "Research Value", "Summary"],
    gap_rows,
)}
""",
    )

    backlog_rows = [
        [
            row["experiment_id"],
            row["title"],
            row["hypothesis_id"],
            row["priority"],
            row["expected_information_gain"],
            row["objective"],
        ]
        for row in analysis["recommended_experiment_backlog"]
    ]
    write_markdown(
        backlog_md,
        f"""
# Recommended Experiment Backlog

{markdown_table(
    ["Experiment", "Title", "Hypothesis", "Priority", "Info Gain", "Objective"],
    backlog_rows,
)}
""",
    )

    confidence_rows = [
        [
            row["hypothesis_id"],
            row["prior_confidence"],
            row["analysis_adjusted_confidence"],
            row["confidence_change"],
            row["reason"],
        ]
        for row in analysis["updated_confidence"]
    ]
    write_markdown(
        confidence_md,
        f"""
# Updated IKROS Confidence

{markdown_table(
    ["Hypothesis", "Campaign 0005", "Campaign 0006", "Delta", "Reason"],
    confidence_rows,
)}
""",
    )

    lineage_rows = [
        [
            row["hypothesis_id"],
            row["new_experiment_id"],
            row["new_evidence_id"],
            row["new_contradictory_evidence_id"],
            ", ".join(row["linked_reports"]),
        ]
        for row in analysis["lineage_updates"]
    ]
    write_markdown(
        lineage_md,
        f"""
# Updated Lineage

{markdown_table(
    ["Hypothesis", "Experiment", "Evidence", "Contradiction", "Reports"],
    lineage_rows,
)}
""",
    )

    write_markdown(
        final_report_md,
        f"""
# Failure Analysis Final Campaign Report

## Outcome

Campaign 0006 completed the institutional failure-analysis pass for the retained
Campaign 0005 hypotheses without changing any hypothesis definition or promoting
any candidate.

## Retained hypotheses analysed

{_markdown_bullets(analysis["campaign"]["retained_hypotheses"])}

## ARB recommendation

{analysis["campaign"]["arb_recommendation"]}

## Registered outcome

- Research question state: **{campaign_result["research_question"]["lifecycle_state"]}**
- Campaign hypothesis state: **{campaign_result["hypothesis"]["lifecycle_state"]}**
- Experiment state: **{campaign_result["experiment"]["lifecycle_state"]}**
""",
    )

    return {
        "alpha_failure_atlas_json": str(atlas_json),
        "alpha_failure_atlas_markdown": str(atlas_md),
        "root_cause_catalogue_json": str(root_json),
        "root_cause_catalogue_markdown": str(root_md),
        "hypothesis_refinement_report_json": str(refinement_json),
        "hypothesis_refinement_report_markdown": str(refinement_md),
        "research_gap_analysis_json": str(gaps_json),
        "research_gap_analysis_markdown": str(gaps_md),
        "experiment_backlog_json": str(backlog_json),
        "experiment_backlog_markdown": str(backlog_md),
        "updated_confidence_json": str(confidence_json),
        "updated_confidence_markdown": str(confidence_md),
        "updated_lineage_json": str(lineage_json),
        "updated_lineage_markdown": str(lineage_md),
        "final_report_markdown": str(final_report_md),
    }


def _analyse_retained_hypothesis(
    *,
    frame: pd.DataFrame,
    blueprint: dict[str, Any],
    validation_record: dict[str, Any],
) -> dict[str, Any]:
    hypothesis_id = str(blueprint["identifier"])
    rule = RULE_CONFIG[hypothesis_id]
    variants = [_variant_data(frame, hypothesis_id, profile) for profile in rule["profiles"]]
    base = next(item for item in variants if item["profile"] == "base")
    statistics_block = _event_statistics(base["event_returns"])
    bootstrap = _bootstrap_statistics(base["event_returns"])
    walk_forward = _walk_forward_statistics(base["events"])
    cpcv = _cpcv_statistics(base["events"], len(frame), int(rule["holding_period_days"]))
    monte_carlo = _monte_carlo_statistics(base["event_returns"])
    temporal = _temporal_statistics(base["events"])
    regime = _regime_stability_statistics(base["events"])
    out_of_sample = _out_of_sample_statistics(base["events"], frame.index)
    stress = _stress_statistics(base["events"])
    white_reality = _white_reality_check(variants)
    sensitivity = _sensitivity_summary(variants, white_reality)
    enriched_events = _attach_event_context(base["events"], frame)
    dependence = _dependence_panels(hypothesis_id, enriched_events)
    feature_gaps = _feature_gap_analysis(frame, hypothesis_id, base["summary"])
    guidance = ROOT_CAUSE_GUIDANCE[hypothesis_id]
    updated_confidence = _updated_confidence(
        campaign_0005_confidence=float(
            validation_record["suggested_posterior_confidence"]
        ),
        bootstrap=bootstrap,
        regime=regime,
        out_of_sample=out_of_sample,
        temporal=temporal,
        event_count=int(len(base["events"])),
    )
    failure_tree = _failure_tree(hypothesis_id, statistics_block, regime, temporal, feature_gaps)
    evidence_matrix = _evidence_matrix(
        statistics_block=statistics_block,
        bootstrap=bootstrap,
        regime=regime,
        temporal=temporal,
        out_of_sample=out_of_sample,
        dependence=dependence,
        feature_gaps=feature_gaps,
        monte_carlo=monte_carlo,
        sensitivity=sensitivity,
        stress=stress,
    )
    return {
        "hypothesis_id": hypothesis_id,
        "title": blueprint["title"],
        "validation_context": {
            "campaign_0005_outcome": validation_record["decision"]["outcome"],
            "campaign_0005_reason": validation_record["decision"]["key_reason"],
            "event_count": len(base["events"]),
            "holding_period_days": int(rule["holding_period_days"]),
        },
        "root_cause_analysis": {
            "primary_root_cause": guidance["root_cause"],
            "secondary_root_causes": _secondary_root_causes(
                bootstrap=bootstrap,
                regime=regime,
                temporal=temporal,
                feature_gaps=feature_gaps,
                out_of_sample=out_of_sample,
            ),
        },
        "failure_tree": failure_tree,
        "evidence_matrix": evidence_matrix,
        "feature_gap_analysis": feature_gaps,
        "dependence_analysis": dependence,
        "missing_data_assessment": guidance["missing_data_assessment"],
        "alternative_economic_explanations": guidance["alternative_explanations"],
        "recommended_refinements": guidance["recommended_refinements"],
        "recommended_additional_experiments": guidance["recommended_experiments"],
        "validation_weaknesses": _validation_weaknesses(
            statistics_block=statistics_block,
            bootstrap=bootstrap,
            walk_forward=walk_forward,
            cpcv=cpcv,
            out_of_sample=out_of_sample,
            event_count=len(base["events"]),
        ),
        "expected_information_gain": _expected_information_gain(
            event_count=len(base["events"]),
            bootstrap=bootstrap,
            out_of_sample=out_of_sample,
            temporal=temporal,
            missing_data=guidance["missing_data_assessment"],
        ),
        "updated_confidence": updated_confidence,
        "computed_diagnostics": {
            "monte_carlo": monte_carlo,
            "stress_testing": stress,
            "sensitivity": sensitivity,
        },
        "campaign_0005_reference": {
            "statistics": validation_record["statistics"],
            "bootstrap": validation_record["bootstrap"],
            "walk_forward": {
                key: value
                for key, value in validation_record["walk_forward"].items()
                if key != "folds"
            },
            "cross_regime_stability": validation_record["cross_regime_stability"],
            "out_of_sample_replay": validation_record["out_of_sample_replay"],
        },
    }


def _variant_data(
    frame: pd.DataFrame,
    hypothesis_id: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    hold_days = int(RULE_CONFIG[hypothesis_id]["holding_period_days"])
    if hypothesis_id == "IKROS-HYP-20260802-0401":
        events = _events_0401(frame, hold_days, profile)
    elif hypothesis_id == "IKROS-HYP-20260802-0405":
        events = _events_0405(frame, hold_days, profile)
    elif hypothesis_id == "IKROS-HYP-20260802-0408":
        events = _events_0408(frame, hold_days, profile)
    else:
        raise KeyError(f"unsupported retained hypothesis '{hypothesis_id}'")
    event_returns = (
        events["event_return"].to_numpy(dtype=np.float64)
        if not events.empty
        else np.asarray([], dtype=np.float64)
    )
    return {
        "profile": profile["label"],
        "events": events,
        "event_returns": event_returns,
        "mean_return": _round(float(event_returns.mean()) if len(event_returns) else 0.0),
        "summary": {
            "event_count": int(len(events)),
            "mean_return": float(events["event_return"].mean()) if not events.empty else 0.0,
        },
    }


def _attach_event_context(events: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    context = frame.reset_index(drop=True).copy()
    context["timestamp"] = frame.index.map(lambda value: value.isoformat())
    columns = [
        "timestamp",
        "macro_pressure",
        "regime_vol_20",
        "dxy_return_20",
        "yield_10y_change_5",
        "forward_expectation",
        "range_pct",
        "sessionless_event_pressure",
        "trend_breakout_interaction",
    ]
    return events.merge(context[columns], on="timestamp", how="left")


def _dependence_panels(hypothesis_id: str, events: pd.DataFrame) -> dict[str, Any]:
    panels = {
        "macro_dependence": _split_panel(events, "macro_pressure", absolute=True),
        "liquidity_dependence": {
            "volatility": _split_panel(events, "regime_vol_20"),
            "range": _split_panel(events, "range_pct"),
        },
        "cross_asset_dependence": _split_panel(events, "dxy_return_20", absolute=True),
    }
    if hypothesis_id == "IKROS-HYP-20260802-0405":
        branch_rows = []
        if not events.empty:
            for direction in sorted(events["direction"].unique()):
                branch = events.loc[events["direction"] == direction, "event_return"]
                branch_rows.append(
                    {
                        "branch": "bearish_shock" if direction < 0 else "bullish_shock",
                        "event_count": int(len(branch)),
                        "mean_return": _round(float(branch.mean())),
                        "win_rate": _round(float((branch > 0.0).mean())),
                    }
                )
        panels["macro_dependence"]["branch_asymmetry"] = branch_rows
    return panels


def _split_panel(
    events: pd.DataFrame,
    column: str,
    *,
    absolute: bool = False,
) -> dict[str, Any]:
    if events.empty or column not in events:
        return {
            "event_count": 0,
            "split_available": False,
            "low_mean_return": 0.0,
            "high_mean_return": 0.0,
            "interpretation": "No event coverage.",
        }
    series = events[column].abs() if absolute else events[column]
    median = float(series.median())
    low = events.loc[series <= median, "event_return"]
    high = events.loc[series > median, "event_return"]
    if high.empty or low.empty:
        return {
            "event_count": int(len(events)),
            "split_available": False,
            "low_mean_return": _round(float(low.mean())) if not low.empty else 0.0,
            "high_mean_return": _round(float(high.mean())) if not high.empty else 0.0,
            "interpretation": "Event coverage was too concentrated to form a meaningful split.",
        }
    low_mean = float(low.mean())
    high_mean = float(high.mean())
    if high_mean > low_mean:
        interpretation = "Higher-pressure slice carried stronger average continuation."
    elif high_mean < low_mean:
        interpretation = "Higher-pressure slice weakened average continuation."
    else:
        interpretation = "Both slices behaved similarly."
    return {
        "event_count": int(len(events)),
        "split_available": True,
        "median": _round(median),
        "low_mean_return": _round(low_mean),
        "high_mean_return": _round(high_mean),
        "interpretation": interpretation,
    }


def _feature_gap_analysis(
    frame: pd.DataFrame,
    hypothesis_id: str,
    base_summary: dict[str, float],
) -> list[dict[str, Any]]:
    base_mean = _round(float(base_summary["mean_return"]))
    if hypothesis_id == "IKROS-HYP-20260802-0401":
        scope, direction, hold_days, conditions = _conditions_0401(frame)
    elif hypothesis_id == "IKROS-HYP-20260802-0405":
        scope, direction, hold_days, conditions = _conditions_0405(frame)
    elif hypothesis_id == "IKROS-HYP-20260802-0408":
        scope, direction, hold_days, conditions = _conditions_0408(frame)
    else:
        raise KeyError(f"unsupported retained hypothesis '{hypothesis_id}'")
    rows = []
    for condition_name in conditions:
        mask = scope.copy()
        for other_name, condition in conditions.items():
            if other_name != condition_name:
                mask = mask & condition
        event_returns = _event_returns(frame, mask, direction, hold_days)
        dropped_mean = float(event_returns.mean()) if len(event_returns) else 0.0
        classification = _classify_feature_gap(base_mean, dropped_mean, len(event_returns), int(base_summary["event_count"]))
        rows.append(
            {
                "condition": condition_name,
                "base_mean_return": base_mean,
                "dropped_condition_mean_return": _round(dropped_mean),
                "dropped_condition_event_count": int(len(event_returns)),
                "classification": classification,
                "interpretation": _feature_gap_interpretation(
                    condition_name=condition_name,
                    classification=classification,
                    base_mean=base_mean,
                    dropped_mean=_round(dropped_mean),
                ),
            }
        )
    return rows


def _conditions_0401(
    frame: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, int, dict[str, pd.Series]]:
    bull = frame["regime"] == "bull_trend"
    subset = frame.loc[bull]
    conditions = {
        "forward_expectation_low": frame["forward_expectation"]
        <= float(subset["forward_expectation"].quantile(0.50)),
        "regime_return_high": frame["regime_return_60"]
        >= float(subset["regime_return_60"].quantile(0.50)),
        "xau_return_high": frame["xau_return_20"]
        >= float(subset["xau_return_20"].quantile(0.50)),
    }
    direction = pd.Series(1.0, index=frame.index)
    return bull, direction, 3, conditions


def _conditions_0405(
    frame: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, int, dict[str, pd.Series]]:
    macro = frame["regime"] == "macro_transition"
    subset = frame.loc[macro]
    shock_sign = pd.Series(
        np.sign(frame["xau_return_1"]).replace(0.0, np.nan).fillna(1.0), index=frame.index
    )
    conditions = {
        "shock_abs": frame["xau_return_1"].abs()
        >= float(subset["xau_return_1"].abs().quantile(0.50)),
        "event_abs": frame["sessionless_event_pressure"].abs()
        >= float(subset["sessionless_event_pressure"].abs().quantile(0.50)),
        "trend_align": np.sign(frame["trend_breakout_interaction"]).replace(0.0, np.nan).fillna(1.0)
        == shock_sign,
        "event_align": np.sign(frame["sessionless_event_pressure"]).replace(0.0, np.nan).fillna(1.0)
        == shock_sign,
    }
    return macro, shock_sign.astype(float), 3, conditions


def _conditions_0408(
    frame: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, int, dict[str, pd.Series]]:
    bull = frame["regime"] == "bull_trend"
    subset = frame.loc[bull]
    conditions = {
        "prior_macro_transition": frame["prior_regime"] == "macro_transition",
        "xau_return_positive": frame["xau_return_1"] > 0.0,
        "trend_breakout_positive": frame["trend_breakout_interaction"] > 0.0,
        "regime_return_high": frame["regime_return_60"]
        >= float(subset["regime_return_60"].quantile(0.50)),
    }
    direction = pd.Series(1.0, index=frame.index)
    return bull, direction, 5, conditions


def _event_returns(
    frame: pd.DataFrame,
    mask: pd.Series,
    direction: pd.Series,
    hold_days: int,
) -> NDArray[np.float64]:
    locs = np.flatnonzero(mask.to_numpy(dtype=bool))
    returns: list[float] = []
    last_exit = -1
    for loc in locs:
        loc_idx = int(loc)
        if loc_idx <= last_exit or loc_idx + hold_days >= len(frame):
            continue
        returns.append(
            float(frame.iloc[loc_idx][f"forward_return_{hold_days}"]) * float(direction.iloc[loc_idx])
        )
        last_exit = loc_idx + hold_days
    return np.asarray(returns, dtype=float)


def _classify_feature_gap(
    base_mean: float,
    dropped_mean: float,
    dropped_count: int,
    base_count: int,
) -> str:
    if dropped_count > base_count and dropped_mean >= base_mean:
        return "OVER_RESTRICTIVE"
    if dropped_mean <= base_mean - 0.0015:
        return "BINDING"
    if abs(dropped_mean - base_mean) <= 0.0003:
        return "REDUNDANT"
    return "SUPPORTING"


def _feature_gap_interpretation(
    *,
    condition_name: str,
    classification: str,
    base_mean: float,
    dropped_mean: float,
) -> str:
    if classification == "BINDING":
        return (
            f"Removing {condition_name} materially weakened the average event return "
            f"({base_mean:.4f} -> {dropped_mean:.4f})."
        )
    if classification == "OVER_RESTRICTIVE":
        return (
            f"Removing {condition_name} preserved or improved the mean return while broadening "
            "coverage, suggesting that the filter may be too tight."
        )
    if classification == "REDUNDANT":
        return (
            f"Removing {condition_name} left the mean return essentially unchanged, implying "
            "that the condition is not adding independent information."
        )
    return (
        f"Removing {condition_name} changed the result modestly, so the condition still helps "
        "explain the mechanism even if it is not the sole driver."
    )


def _secondary_root_causes(
    *,
    bootstrap: dict[str, float],
    regime: dict[str, Any],
    temporal: dict[str, Any],
    feature_gaps: list[dict[str, Any]],
    out_of_sample: dict[str, float],
) -> list[str]:
    causes: list[str] = []
    if bootstrap["mean_ci_low"] <= 0.0:
        causes.append("bootstrap uncertainty remained too wide for promotion")
    if regime["transition_fragility"] in {"HIGH", "ELEVATED"}:
        causes.append("edge weakened outside the cleanest in-regime subset")
    if temporal["sign_change_count"] >= 2:
        causes.append("temporal adaptation and sign instability weakened repeatability")
    if out_of_sample["event_count"] == 0:
        causes.append("no recent holdout evidence existed for institutional replay")
    if any(row["classification"] == "REDUNDANT" for row in feature_gaps):
        causes.append("at least one rule component behaved as redundant rather than additive")
    return causes


def _failure_tree(
    hypothesis_id: str,
    statistics_block: dict[str, float],
    regime: dict[str, Any],
    temporal: dict[str, Any],
    feature_gaps: list[dict[str, Any]],
) -> list[dict[str, str]]:
    redundant = ", ".join(
        row["condition"] for row in feature_gaps if row["classification"] in {"REDUNDANT", "OVER_RESTRICTIVE"}
    )
    nodes = [
        {
            "level": "Root",
            "node": "Institutional promotion failure",
            "evidence": f"Mean return {statistics_block['mean_return']:.4f}, win rate {statistics_block['win_rate']:.4f}.",
        },
        {
            "level": "Primary",
            "node": "Regime fragility",
            "evidence": f"Transition fragility={regime['transition_fragility']}, transition mean={regime['transition_mean_return']:.4f}.",
        },
        {
            "level": "Primary",
            "node": "Temporal degradation",
            "evidence": f"Concept drift={temporal['concept_drift_score']:.4f}, sign changes={temporal['sign_change_count']}.",
        },
    ]
    if redundant:
        nodes.append(
            {
                "level": "Secondary",
                "node": "Feature interaction weakness",
                "evidence": f"Redundant or over-restrictive conditions: {redundant}.",
            }
        )
    if hypothesis_id == "IKROS-HYP-20260802-0408":
        nodes.append(
            {
                "level": "Secondary",
                "node": "Episode scarcity",
                "evidence": "Too few handoff episodes existed to satisfy replication and out-of-sample replay requirements.",
            }
        )
    return nodes


def _evidence_matrix(
    *,
    statistics_block: dict[str, float],
    bootstrap: dict[str, float],
    regime: dict[str, Any],
    temporal: dict[str, Any],
    out_of_sample: dict[str, float],
    dependence: dict[str, Any],
    feature_gaps: list[dict[str, Any]],
    monte_carlo: dict[str, float],
    sensitivity: dict[str, Any],
    stress: dict[str, Any],
) -> list[dict[str, str]]:
    rows = [
        {
            "dimension": "Statistical signal",
            "signal": f"mean={statistics_block['mean_return']:.4f}, t={statistics_block['t_statistic']:.4f}, p={statistics_block['one_sided_p_value']:.4f}",
            "implication": "Positive direction survived, but statistical amplitude remained below promotion strength.",
        },
        {
            "dimension": "Bootstrap robustness",
            "signal": f"CI=[{bootstrap['mean_ci_low']:.4f}, {bootstrap['mean_ci_high']:.4f}], P(>0)={bootstrap['probability_positive']:.4f}",
            "implication": "Confidence interval still touched non-positive territory.",
        },
        {
            "dimension": "Regime dependence",
            "signal": f"persistent={regime['persistent_mean_return']:.4f}, transition={regime['transition_mean_return']:.4f}, fragility={regime['transition_fragility']}",
            "implication": "Performance was not equally portable across clean persistent states and transition-overlap states.",
        },
        {
            "dimension": "Temporal degradation",
            "signal": f"drift={temporal['concept_drift_score']:.4f}, sign_changes={temporal['sign_change_count']}",
            "implication": "Temporal stability weakened enough to block institutional promotion.",
        },
        {
            "dimension": "Out-of-sample replay",
            "signal": f"events={out_of_sample['event_count']}, mean={out_of_sample['mean_return']:.4f}, win={out_of_sample['win_rate']:.4f}",
            "implication": "Recent replay support existed only where event coverage was sufficient.",
        },
        {
            "dimension": "Monte Carlo resilience",
            "signal": f"median={monte_carlo['median_total_return']:.4f}, downside_p05={monte_carlo['p05_total_return']:.4f}",
            "implication": "Path-level variation still exposed a non-trivial downside tail even where the average event sign stayed positive.",
        },
        {
            "dimension": "Sensitivity",
            "signal": f"positive_variant_ratio={sensitivity['positive_variant_ratio']:.4f}, return_range={sensitivity['variant_return_range']:.4f}",
            "implication": "Threshold variants kept the sign positive, but robustness alone was not enough to offset weak aggregate evidence.",
        },
        {
            "dimension": "Cross-asset dependence",
            "signal": (
                f"DXY low={dependence['cross_asset_dependence']['low_mean_return']:.4f}, "
                f"DXY high={dependence['cross_asset_dependence']['high_mean_return']:.4f}"
            ),
            "implication": dependence["cross_asset_dependence"]["interpretation"],
        },
        {
            "dimension": "Stress windows",
            "signal": f"worst_window_mean={stress['worst_mean_return']:.4f}",
            "implication": "Stress episodes remained too sparse or too uneven to establish institutional robustness on their own.",
        },
        {
            "dimension": "Feature interaction gaps",
            "signal": ", ".join(
                f"{row['condition']}={row['classification']}" for row in feature_gaps
            ),
            "implication": "Some rule components remained critical, while others looked redundant or over-restrictive.",
        },
    ]
    return rows


def _validation_weaknesses(
    *,
    statistics_block: dict[str, float],
    bootstrap: dict[str, float],
    walk_forward: dict[str, Any],
    cpcv: dict[str, Any],
    out_of_sample: dict[str, float],
    event_count: int,
) -> list[str]:
    weaknesses = []
    if statistics_block["one_sided_p_value"] > 0.10:
        weaknesses.append("One-sided statistical significance remained below the institutional bar.")
    if bootstrap["mean_ci_low"] <= 0.0:
        weaknesses.append("Bootstrap confidence interval continued to include non-positive outcomes.")
    if float(walk_forward["positive_fold_ratio"]) < 0.75:
        weaknesses.append("Walk-forward fold positivity was not strong enough for institutional promotion.")
    if float(cpcv["positive_split_ratio"]) < 0.60:
        weaknesses.append("CPCV positivity remained too uneven across held-out combinations.")
    if out_of_sample["event_count"] == 0:
        weaknesses.append("No recent out-of-sample replay events were available.")
    if event_count < 12:
        weaknesses.append("Event coverage was too sparse for reliable replication.")
    return weaknesses


def _expected_information_gain(
    *,
    event_count: int,
    bootstrap: dict[str, float],
    out_of_sample: dict[str, float],
    temporal: dict[str, Any],
    missing_data: list[dict[str, str]],
) -> dict[str, Any]:
    severity_score = sum(
        1.0 if item["severity"] == "HIGH" else 0.5 for item in missing_data
    )
    score = 3.0
    score += max(0.0, 0.9 - float(bootstrap["probability_positive"])) * 2.0
    score += 0.6 if event_count < 30 else 0.0
    score += 0.5 if out_of_sample["event_count"] == 0 else 0.0
    score += 0.4 if int(temporal["sign_change_count"]) >= 2 else 0.0
    score += min(severity_score * 0.15, 0.9)
    score = round(min(score, 5.0), 2)
    return {
        "score": score,
        "rationale": "Information gain is highest where uncertainty is still material, event coverage is thin, and missing-data gaps directly block mechanism discrimination.",
    }


def _updated_confidence(
    *,
    campaign_0005_confidence: float,
    bootstrap: dict[str, float],
    regime: dict[str, Any],
    out_of_sample: dict[str, float],
    temporal: dict[str, Any],
    event_count: int,
) -> dict[str, Any]:
    penalty = 0.0
    if bootstrap["mean_ci_low"] <= 0.0:
        penalty += 0.03
    if regime["transition_fragility"] in {"HIGH", "ELEVATED"}:
        penalty += 0.03
    if event_count < 12:
        penalty += 0.07
    elif event_count < 30:
        penalty += 0.03
    if out_of_sample["event_count"] == 0:
        penalty += 0.05
    elif out_of_sample["mean_return"] <= 0.0:
        penalty += 0.03
    if int(temporal["sign_change_count"]) >= 2:
        penalty += 0.03
    adjusted = max(0.10, round(campaign_0005_confidence - penalty + 0.01, 4))
    return {
        "campaign_0005_confidence": round(campaign_0005_confidence, 4),
        "analysis_adjusted_confidence": adjusted,
        "confidence_change": round(adjusted - campaign_0005_confidence, 4),
        "rationale": "Campaign 0006 reduced confidence where failure drivers remained unresolved, while preserving a small credit for surviving directional signal and clearer failure attribution.",
    }


def _aggregate_research_gaps(retained: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "theme": "",
            "affected_hypotheses": [],
            "severity_rank": 0,
            "research_value": 0.0,
            "summaries": [],
        }
    )
    severity_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    for item in retained:
        for gap in item["missing_data_assessment"]:
            entry = grouped[gap["theme"]]
            entry["theme"] = gap["theme"]
            entry["affected_hypotheses"].append(item["hypothesis_id"])
            entry["severity_rank"] = max(entry["severity_rank"], severity_order[gap["severity"]])
            entry["research_value"] = max(
                float(entry["research_value"]),
                float(item["expected_information_gain"]["score"]),
            )
            entry["summaries"].append(gap["missing_artifact"])
    severity_lookup = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}
    rows = []
    for theme, entry in grouped.items():
        rows.append(
            {
                "theme": theme,
                "affected_hypotheses": ", ".join(sorted(set(entry["affected_hypotheses"]))),
                "severity": severity_lookup.get(entry["severity_rank"], "LOW"),
                "research_value": round(float(entry["research_value"]), 2),
                "summary": entry["summaries"][0],
            }
        )
    return sorted(rows, key=lambda item: (-item["research_value"], item["theme"]))


def _aggregate_experiment_backlog(retained: list[dict[str, Any]]) -> list[dict[str, Any]]:
    backlog = []
    for item in retained:
        for experiment in item["recommended_additional_experiments"]:
            backlog.append(
                {
                    **experiment,
                    "hypothesis_id": item["hypothesis_id"],
                }
            )
    return sorted(
        backlog,
        key=lambda item: (-float(item["expected_information_gain"]), item["experiment_id"]),
    )


def _build_knowledge_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    retained = analysis["retained_hypotheses"]
    return {
        "metadata": {
            "source_kind": "INTERNAL_RESEARCH_REPORT",
            "title": "Campaign 0006 failure analysis knowledge pack",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/failure-analysis/FAILURE_ANALYSIS_FINAL_CAMPAIGN_REPORT.md",
                "11-research/phase-g/scientific-validation/scientific_validation_analysis.json",
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-DSV-20260802-0006",
                "type": "DatasetVersion",
                "title": "Campaign 0006 failure analysis dataset reference",
                "summary": "Failure-analysis snapshot combining the frozen validation frame with Campaign 0005 retained-hypothesis diagnostics.",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.88,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/failure-analysis/failure_analysis_analysis.json"],
                "attributes": {
                    "retained_hypothesis_count": len(retained),
                    "source_validation_campaign": "IKROS-EXP-20260802-0005",
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0600",
                "type": "KnowledgeObject",
                "title": "Campaign 0006 failure-analysis methodology",
                "summary": "Institutional methodology for explaining why retained hypotheses failed promotion without changing their definitions.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.83,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/failure-analysis/ALPHA_FAILURE_ATLAS.md"],
                "attributes": {
                    "retained_hypotheses": analysis["campaign"]["retained_hypotheses"],
                    "mean_adjusted_confidence": analysis["campaign"]["mean_adjusted_confidence"],
                },
            },
            {
                "identifier": "IKROS-EVIDENCE-20260802-0006",
                "type": "Evidence",
                "title": "Campaign 0006 failure-analysis evidence bundle",
                "summary": "Evidence bundle carrying the failure atlas, root-cause catalogue, research gaps, experiment backlog, and confidence update report.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.81,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/failure-analysis/failure_analysis_analysis.json"],
                "attributes": {
                    "retained_hypotheses": analysis["campaign"]["retained_hypotheses"],
                    "root_cause_count": len(analysis["root_cause_catalogue"]),
                },
            },
            {
                "identifier": "IKROS-CONTRA-20260802-0006",
                "type": "ContradictoryEvidence",
                "title": "Campaign 0006 contradiction bundle",
                "summary": "Contradiction bundle explaining why retained hypotheses remained below the institutional promotion standard.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.76,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/failure-analysis/failure_analysis_analysis.json"],
                "attributes": {
                    "retained_hypotheses": analysis["campaign"]["retained_hypotheses"],
                    "primary_failures": [
                        item["root_cause_analysis"]["primary_root_cause"]
                        for item in retained
                    ],
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0606",
                "type": "KnowledgeObject",
                "title": "Campaign 0006 final conclusion",
                "summary": analysis["campaign"]["arb_recommendation"],
                "lifecycle_state": "ACTIVE",
                "confidence": 0.8,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/failure-analysis/FAILURE_ANALYSIS_FINAL_CAMPAIGN_REPORT.md"],
                "attributes": {
                    "retained_hypotheses": analysis["campaign"]["retained_hypotheses"],
                    "recommended_experiments": [
                        item["experiment_id"] for item in analysis["recommended_experiment_backlog"]
                    ],
                },
            },
        ]
        + [
            {
                "identifier": f"IKROS-KO-20260802-06{index:02d}",
                "type": "KnowledgeObject",
                "title": f"{item['hypothesis_id']} root cause card",
                "summary": item["root_cause_analysis"]["primary_root_cause"],
                "lifecycle_state": "ACTIVE",
                "confidence": item["updated_confidence"]["analysis_adjusted_confidence"],
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/failure-analysis/ALPHA_FAILURE_ATLAS.md"],
                "attributes": {
                    "hypothesis_id": item["hypothesis_id"],
                    "secondary_root_causes": item["root_cause_analysis"]["secondary_root_causes"],
                    "expected_information_gain": item["expected_information_gain"]["score"],
                    "updated_confidence": item["updated_confidence"]["analysis_adjusted_confidence"],
                },
            }
            for index, item in enumerate(retained, start=1)
        ],
    }


def _markdown_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _round(value: float) -> float:
    return round(float(value), 4)
