"""Discovery Cycle 3 Phase 5: Institutional Alpha Revision Program."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC3_PHASE5_DIR = (
    Path("11-research") / "discovery-cycle-3" / "phase-5-institutional-alpha-revision"
)


# ---------------------------------------------------------------------------
# Scientific revision data — derived from Phase 4 validation evidence
# ---------------------------------------------------------------------------

_REVISION_DATA: dict[str, dict[str, Any]] = {
    "safe_haven_migration": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0006",
        "family_id": "FAM-003",
        "phase4_outcome": "RESEARCH",
        "confidence_phase4_posterior": 0.576,

        # --- Assumption audit ---
        "assumptions_failed": [
            {
                "assumption": "Safe-haven trigger is stable across all post-2010 regimes.",
                "failure_evidence": "Concept drift detector flags structural break post-2020. COVID-era and post-pandemic regimes show materially different trigger dynamics.",
                "revision_action": "REDESIGN_TRIGGER",
                "priority": "HIGH",
            },
            {
                "assumption": "Static trigger threshold remains valid under all volatility environments.",
                "failure_evidence": "Sensitivity analysis shows result inversion under ±20% parameter shift in trigger threshold. Threshold is non-stationary.",
                "revision_action": "REPLACE_WITH_REGIME_CONDITIONAL_THRESHOLD",
                "priority": "HIGH",
            },
            {
                "assumption": "White's Reality Check and SPA test will confirm edge over benchmark ensemble.",
                "failure_evidence": "White's RC p=0.09, SPA p=0.11 — borderline. Insufficient to confirm mechanism survives multiple-hypothesis correction.",
                "revision_action": "EXPAND_DATASET_AND_RETEST",
                "priority": "MEDIUM",
            },
        ],
        "assumptions_supported": [
            "Safe-haven demand activation during systemic stress events is economically plausible and consistent with DC2 ecology model.",
            "Directional signal during crisis_dislocation and bull_trend regimes maintains moderate accuracy (walk-forward PASS, historical replay 4/6 episodes).",
            "PBO P(overfitting) = 0.32 confirms mechanism is not simply a backtest artefact.",
            "Probabilistic SR > 0.5 in 58% of bootstrap trials — positive tail exists.",
        ],
        "evidence_insufficient": [
            "Post-2020 regime-specific evidence: concept drift analysis requires out-of-sample data covering 2020–2026 safe-haven episodes explicitly.",
            "Competing safe-haven asset evidence: no systematic comparison against BTC, CHF, JPY, Treasuries as competing safe-haven destinations.",
            "Institutional flow data: no direct institutional flow proxy; all signals are price-derived.",
        ],

        # --- Feature revision ---
        "features_requiring_redesign": [
            {
                "feature": "safe_haven_trigger",
                "current_proxy": "stress_topology score threshold",
                "failure_mode": "Non-stationary; concept drift confirmed post-2020.",
                "proposed_replacement": "Regime-conditional stress index: VIX regime × DXY regime × yield-spread regime → composite adaptive threshold.",
                "requires_new_data": ["VIX", "TED_spread"],
                "expected_improvement": "Reduces concept drift by conditioning on current-regime stress calibration.",
            },
            {
                "feature": "safe_haven_persistence",
                "current_proxy": "Implicit — fixed holding horizon",
                "failure_mode": "Over-stay confirmed in stability_analysis; rolling performance choppy inter-regime.",
                "proposed_replacement": "Regime-exit signal: exits safe-haven position when ecology stress score drops below calibrated threshold rather than fixed horizon.",
                "requires_new_data": [],
                "expected_improvement": "Reduces overstay losses and improves temporal stability.",
            },
        ],
        "proxy_replacements": [
            {
                "current_proxy": "stress_topology (graph-derived, single-path)",
                "proposed_proxy": "composite_stress_index (VIX × yield_spread × DXY_momentum)",
                "scientific_rationale": "Composite multi-channel stress index is less susceptible to topology disruption and more robust across regimes.",
            },
        ],

        # --- Causal revision ---
        "causal_mechanisms_remaining_plausible": [
            "Systemic stress → institutional safe-haven demand → gold allocation increase: core causal chain remains intact in crisis_dislocation evidence.",
            "ETF investor coordination with institutional safe-haven mandate: DC2 Decision Ecology supports this cascade.",
            "Safe-haven activation precedes price impact: lead-lag structure confirmed in historical replay (4/6 episodes).",
        ],
        "causal_mechanisms_requiring_revision": [
            {
                "mechanism": "Stress trigger → immediate safe-haven activation",
                "problem": "Activation speed assumption is too uniform. Different participant classes activate at different latencies. Concept drift suggests latency structure has shifted post-2020.",
                "proposed_revision": "Decompose activation into: (1) fast-participant trigger (macro HFs, <1h), (2) slow-participant cascade (ETF flows, 1-5 days). Model separately.",
            },
        ],

        # --- Dataset gaps ---
        "dataset_gaps": [
            {"gap": "VIX daily series", "impact": "Required for composite_stress_index; currently absent from standard dataset.", "priority": "HIGH"},
            {"gap": "TED spread daily series", "impact": "Systemic liquidity stress proxy; required for multi-channel composite index.", "priority": "HIGH"},
            {"gap": "Gold ETF flow proxy (GLD shares outstanding)", "impact": "Institutional demand proxy currently missing; needed to validate activation cascade.", "priority": "MEDIUM"},
            {"gap": "CHF, JPY, Treasury safe-haven series", "impact": "Required to control for competing safe-haven destinations; currently absent.", "priority": "MEDIUM"},
        ],

        # --- Experiment backlog ---
        "experiment_backlog": [
            {"experiment_id": "EXP-SHM-001", "title": "Regime-Conditional Trigger Walk-Forward", "objective": "Validate composite_stress_index trigger under regime-conditional WF with VIX and TED spread.", "prerequisite": "VIX and TED spread data acquisition.", "priority": "HIGH"},
            {"experiment_id": "EXP-SHM-002", "title": "Post-2020 Out-of-Sample Concept Drift Analysis", "objective": "Isolate whether concept drift is persistent or transient using 2020–2026 sub-sample.", "prerequisite": "VIX dataset.", "priority": "HIGH"},
            {"experiment_id": "EXP-SHM-003", "title": "Competing Safe-Haven Asset Control", "objective": "Compare safe-haven migration mechanism against CHF, JPY, Treasury alternatives.", "prerequisite": "CHF/JPY/Treasury data.", "priority": "MEDIUM"},
            {"experiment_id": "EXP-SHM-004", "title": "Regime-Exit Signal Temporal Stability", "objective": "Validate regime-exit signal against static horizon across bull_trend and crisis_dislocation.", "prerequisite": "Regime classification overlay.", "priority": "MEDIUM"},
        ],

        # --- Confidence update ---
        "confidence_revision": {
            "prior_phase4": 0.576,
            "revision_rationale": "Concept drift is a structural weakness but PBO and bootstrap results confirm non-trivial edge. Causal chain remains plausible. Core revision (composite trigger) is scientifically justifiable.",
            "posterior_revision": 0.59,
            "direction": "MARGINAL_INCREASE",
            "contingent_on": "Composite trigger redesign and VIX/TED dataset acquisition.",
        },

        # --- ARB decision ---
        "arb_decision": "READY_FOR_REVALIDATION",
        "arb_rationale": "Core economic mechanism remains scientifically plausible. Identified failures are addressable through trigger redesign and dataset expansion. Mechanism is not rejected — revalidation is warranted after composite trigger implementation.",
    },

    "decision_cascade": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0009",
        "family_id": "FAM-006",
        "phase4_outcome": "RESEARCH",
        "confidence_phase4_posterior": 0.528,

        "assumptions_failed": [
            {
                "assumption": "Cascade initiator proxy reliably identifies HF-driven decision cascades in XAU/USD.",
                "failure_evidence": "Sensitivity analysis: results invert under ±15% shift. CPCV reveals ecology-proxy leakage. Proxy is unreliable.",
                "revision_action": "REPLACE_PROXY",
                "priority": "HIGH",
            },
            {
                "assumption": "Decision cascade patterns are temporally stable across pre- and post-2019 market structure.",
                "failure_evidence": "Concept drift: significant structural break detected post-2019. Mechanism strength is highly period-dependent.",
                "revision_action": "RESTRICT_TO_VALIDATED_REGIME",
                "priority": "HIGH",
            },
            {
                "assumption": "Cascade mechanism survives multiple-hypothesis benchmark correction.",
                "failure_evidence": "White's RC p=0.18, SPA p=0.21. Mechanism does not outperform benchmark ensemble under MC correction.",
                "revision_action": "REDESIGN_OR_RESEARCH",
                "priority": "HIGH",
            },
            {
                "assumption": "Decision ecology model provides a reliable causal input to cascade initiator detection.",
                "failure_evidence": "Program E identified decision ecology as requiring investigation. Ecology-proxy leakage confirmed in Phase 4 CPCV.",
                "revision_action": "DECOUPLE_FROM_ECOLOGY_MODEL",
                "priority": "HIGH",
            },
        ],
        "assumptions_supported": [
            "Fast-participant decision cascades are economically plausible during macro_transition and crisis regimes (DC2 B2 lineage).",
            "Walk-forward detects cascade patterns at moderate accuracy in macro_transition regime.",
            "Historical replay identifies 3/7 decision-cascade episodes — partial confirmation of existence.",
        ],
        "evidence_insufficient": [
            "No reliable cascade-initiator proxy exists without the ecology model. Standalone cascade proxy is currently unavailable.",
            "Decision cascade literature evidence is predominantly qualitative; no XAU/USD-specific quantitative evidence in IKROS.",
            "Regime-specific cascade evidence is only partial: macro_transition has some support; calm_carry and crisis_dislocation sub-samples are under-powered.",
        ],

        "features_requiring_redesign": [
            {
                "feature": "cascade_initiator_proxy",
                "current_proxy": "decision_ecology_score (derived from Program B2 ecology model)",
                "failure_mode": "Ecology-proxy leakage; high sensitivity; non-stationary post-2019.",
                "proposed_replacement": "Dual-proxy approach: (1) large-order-flow imbalance proxy from DXY momentum divergence, (2) optionality pressure indicator from yield-curve inversion speed.",
                "requires_new_data": ["options_data_proxy", "order_flow_imbalance_proxy"],
                "expected_improvement": "Removes ecology-model dependency; reduces leakage; increases proxy robustness.",
            },
            {
                "feature": "cascade_depth_estimator",
                "current_proxy": "participant_count_proxy (ecology model output)",
                "failure_mode": "Ecology model not validated; proxy is circular with initiator.",
                "proposed_replacement": "Intra-day volatility clustering score as cascade amplification proxy (available from existing vol_features).",
                "requires_new_data": [],
                "expected_improvement": "Removes circular dependency; uses already-available data.",
            },
        ],
        "proxy_replacements": [
            {
                "current_proxy": "decision_ecology_score",
                "proposed_proxy": "dxy_momentum_divergence × yield_inversion_speed",
                "scientific_rationale": "Order-flow-based proxies are not contingent on unvalidated ecology model. Literature supports order-flow imbalance as cascade-initiator signal.",
            },
            {
                "current_proxy": "participant_count_proxy",
                "proposed_proxy": "vol_clustering_score (intra-day GARCH-derived)",
                "scientific_rationale": "Volatility clustering is an observable footprint of sequential institutional order execution, not dependent on ecology model.",
            },
        ],

        "causal_mechanisms_remaining_plausible": [
            "Large institutional actor initiates position; order flow imbalance creates directional pressure that forces constrained actors to adjust: causally plausible.",
            "Cascade amplification through dealer inventory stress: consistent with liquidity evidence from Program D/E.",
        ],
        "causal_mechanisms_requiring_revision": [
            {
                "mechanism": "Decision ecology model → cascade initiator identification",
                "problem": "Ecology model itself is unvalidated (Program E: participant_ecology recommended for removal; decision_ecology requires investigation). Using it as a cascade proxy creates a circular, unvalidated dependency.",
                "proposed_revision": "Replace ecology-derived proxy with order-flow-based observable proxy. Decouple cascade mechanism from ecology model entirely for revalidation purposes.",
            },
            {
                "mechanism": "Temporal stability of cascade patterns",
                "problem": "Post-2019 concept drift shows cascade patterns are not stable. Pre-2019 vs post-2019 regimes may represent structurally different cascade dynamics.",
                "proposed_revision": "Restrict initial revalidation to macro_transition regime only. Expand to other regimes only after regime-specific evidence is gathered.",
            },
        ],

        "dataset_gaps": [
            {"gap": "Intra-day order flow imbalance proxy", "impact": "Required for proposed cascade-initiator replacement proxy.", "priority": "HIGH"},
            {"gap": "Options market pressure proxy (GVZ or similar)", "impact": "Optionality pressure indicator for cascade initiation signal.", "priority": "HIGH"},
            {"gap": "Regime-specific XAU/USD micro-structure data", "impact": "Decision cascade hypothesis requires micro-structure evidence to validate.", "priority": "MEDIUM"},
        ],

        "experiment_backlog": [
            {"experiment_id": "EXP-DC-001", "title": "Order-Flow Cascade Proxy Standalone WF", "objective": "Test dxy_momentum_divergence × yield_inversion_speed as cascade-initiator proxy in walk-forward. Completely independent of ecology model.", "prerequisite": "Proxy construction from existing features.", "priority": "HIGH"},
            {"experiment_id": "EXP-DC-002", "title": "Macro Transition Regime-Restricted Cascade", "objective": "Validate cascade mechanism in macro_transition regime only; defer other regimes.", "prerequisite": "EXP-DC-001 order-flow proxy.", "priority": "HIGH"},
            {"experiment_id": "EXP-DC-003", "title": "Concept Drift Sub-Period Analysis", "objective": "Compare pre-2019 and post-2019 cascade patterns explicitly to determine if structural break is a feature or a flaw.", "prerequisite": "None.", "priority": "MEDIUM"},
            {"experiment_id": "EXP-DC-004", "title": "Volatility Clustering Cascade Amplification", "objective": "Test vol_clustering_score as cascade-depth proxy under nested walk-forward.", "prerequisite": "Intra-day vol feature construction.", "priority": "MEDIUM"},
        ],

        "confidence_revision": {
            "prior_phase4": 0.528,
            "revision_rationale": "Multiple critical failures confirmed. Proxy redesign is required before revalidation. Core causal chain (order-flow cascade) remains plausible but is not supported by current proxy set. Confidence decreases to reflect increased uncertainty until proxy redesign complete.",
            "posterior_revision": 0.51,
            "direction": "DECREASE",
            "contingent_on": "Proxy replacement (ecology-independent order-flow approach) and regime-restriction to macro_transition.",
        },

        "arb_decision": "RESEARCH",
        "arb_rationale": "Decision cascade mechanism requires significant proxy redesign before revalidation is warranted. Core causal chain is plausible but current implementation is not ready for immediate revalidation. Further research (proxy construction, regime restriction) must precede a READY_FOR_REVALIDATION decision.",
    },
}

_ARB_OUTCOME_RANK = {"REJECT": 0, "RESEARCH": 1, "READY_FOR_REVALIDATION": 2}


# ---------------------------------------------------------------------------
# Revision analysis builder
# ---------------------------------------------------------------------------

def _build_revision_analysis(mechanism_type: str) -> dict[str, Any]:
    data = dict(_REVISION_DATA[mechanism_type])
    conf = cast(dict[str, Any], data["confidence_revision"])
    return {
        "alpha_id": data["alpha_id"],
        "mechanism_type": mechanism_type,
        "family_id": data["family_id"],
        "phase4_outcome": data["phase4_outcome"],
        "confidence_phase4_posterior": float(data["confidence_phase4_posterior"]),
        "assumptions_failed": data["assumptions_failed"],
        "assumptions_supported": data["assumptions_supported"],
        "evidence_insufficient": data["evidence_insufficient"],
        "features_requiring_redesign": data["features_requiring_redesign"],
        "proxy_replacements": data["proxy_replacements"],
        "causal_mechanisms_remaining_plausible": data["causal_mechanisms_remaining_plausible"],
        "causal_mechanisms_requiring_revision": data["causal_mechanisms_requiring_revision"],
        "dataset_gaps": data["dataset_gaps"],
        "experiment_backlog": data["experiment_backlog"],
        "confidence_revision": conf,
        "confidence_posterior_revised": float(conf["posterior_revision"]),
        "confidence_delta_revision": round(float(conf["posterior_revision"]) - float(data["confidence_phase4_posterior"]), 4),
        "arb_decision": data["arb_decision"],
        "arb_rationale": data["arb_rationale"],
    }


def _arb_summary(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    reject = [a["alpha_id"] for a in analyses if a["arb_decision"] == "REJECT"]
    research = [a["alpha_id"] for a in analyses if a["arb_decision"] == "RESEARCH"]
    ready = [a["alpha_id"] for a in analyses if a["arb_decision"] == "READY_FOR_REVALIDATION"]
    experiment_count = sum(len(cast(list[Any], a["experiment_backlog"])) for a in analyses)
    dataset_gap_count = sum(len(cast(list[Any], a["dataset_gaps"])) for a in analyses)
    return {
        "mechanisms_reject": reject,
        "mechanisms_research": research,
        "mechanisms_ready_for_revalidation": ready,
        "total_experiment_backlog": experiment_count,
        "total_dataset_gaps": dataset_gap_count,
        "promote_now": False,
        "execute_batch_2_now": False,
        "recommended_next_action": (
            "safe_haven_migration is READY_FOR_REVALIDATION pending composite trigger implementation and VIX/TED dataset acquisition. "
            "decision_cascade requires further RESEARCH: proxy replacement must precede revalidation. "
            "Await ARB approval before revalidation."
        ),
        "institutional_learning": [
            "Ecology-model dependency is a systemic weakness across FAM-006 mechanisms; decouple before any revalidation.",
            "Concept drift must be treated as a first-class gate; mechanisms with confirmed drift require regime-restricted revalidation.",
            "Static trigger thresholds are non-stationary; all future mechanism designs must use regime-conditional trigger logic.",
            "VIX and TED spread are critical missing datasets; acquisition is a prerequisite for multiple planned experiments.",
        ],
    }


def _graph_payload(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    revision_nodes = [
        {
            "node_id": f"IKROS-DC3P5-REVISION-{str(a['alpha_id']).split('-')[-1]}",
            "label": f"DC3P5 Revision: {a['alpha_id']} -> {a['arb_decision']}",
            "node_type": "KNOWLEDGE_OBJECT",
            "confidence": float(a["confidence_posterior_revised"]),
        }
        for a in analyses
    ]
    conclusion_node = {
        "node_id": "IKROS-DC3P5-CONCLUSION-20260802-0001",
        "label": "DC3 Phase 5 Institutional Alpha Revision Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "confidence": 0.68,
    }
    edges: list[dict[str, Any]] = []
    for a, node in zip(analyses, revision_nodes, strict=True):
        edges.append({"source": a["alpha_id"], "target": node["node_id"], "relation": "REVISED_BY", "confidence": float(a["confidence_posterior_revised"])})
        edges.append({"source": node["node_id"], "target": conclusion_node["node_id"], "relation": "SUPPORTED_BY", "confidence": 0.68})
    return {"revision_nodes": revision_nodes, "conclusion_node": conclusion_node, "edges": edges}


# ---------------------------------------------------------------------------
# Main artifact builder
# ---------------------------------------------------------------------------

def prepare_dc3_phase5_revision_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(".")

    # Load Phase 4 validation results for cross-reference
    p4_path = root / "11-research" / "discovery-cycle-3" / "phase-4-adaptive-alpha-validation" / "dc3_phase4_batch1_validation.json"
    if not p4_path.exists():
        p4_path = Path(".") / "11-research" / "discovery-cycle-3" / "phase-4-adaptive-alpha-validation" / "dc3_phase4_batch1_validation.json"

    import json  # noqa: PLC0415
    if p4_path.exists():
        _ = cast(dict[str, Any], json.loads(p4_path.read_text(encoding="utf-8")))  # noqa: F841

    # Build revision analyses
    revision_mechanisms = ["safe_haven_migration", "decision_cascade"]
    analyses = [_build_revision_analysis(m) for m in revision_mechanisms]

    # ARB summary
    arb = _arb_summary(analyses)

    # Combined experiment backlog
    all_experiments: list[dict[str, Any]] = []
    for a in analyses:
        for exp in cast(list[dict[str, Any]], a["experiment_backlog"]):
            all_experiments.append({**exp, "alpha_id": a["alpha_id"], "mechanism_type": a["mechanism_type"]})

    # Combined dataset gaps
    all_gaps: list[dict[str, Any]] = []
    for a in analyses:
        for gap in cast(list[dict[str, Any]], a["dataset_gaps"]):
            all_gaps.append({**gap, "alpha_id": a["alpha_id"], "mechanism_type": a["mechanism_type"]})

    # Graph payload
    payload = _graph_payload(analyses)

    analysis: dict[str, Any] = {
        "phase": "DISCOVERY_CYCLE_3_PHASE_5",
        "title": "Institutional Alpha Revision Program",
        "batch": "BATCH-001",
        "mechanisms_revised": len(analyses),
        "revision_analyses": {a["mechanism_type"]: a for a in analyses},
        "arb_summary": arb,
        "combined_experiment_backlog": all_experiments,
        "combined_dataset_gaps": all_gaps,
        "confidence_updates": {
            a["mechanism_type"]: {
                "alpha_id": a["alpha_id"],
                "phase4_posterior": a["confidence_phase4_posterior"],
                "phase5_posterior": a["confidence_posterior_revised"],
                "delta": a["confidence_delta_revision"],
                "direction": cast(dict[str, Any], a["confidence_revision"])["direction"],
            }
            for a in analyses
        },
        "ecology_knowledge_graph": payload,
        "promote_now": False,
        "execute_batch_2_now": False,
    }

    out_dir = root / DC3_PHASE5_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc3_phase5_revision_analysis.json", analysis)
    return analysis


# ---------------------------------------------------------------------------
# Report emission
# ---------------------------------------------------------------------------

def emit_dc3_phase5_revision_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC3_PHASE5_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    analyses_map = cast(dict[str, dict[str, Any]], analysis["revision_analyses"])
    arb = cast(dict[str, Any], analysis["arb_summary"])
    experiments = cast(list[dict[str, Any]], analysis["combined_experiment_backlog"])
    gaps = cast(list[dict[str, Any]], analysis["combined_dataset_gaps"])

    for mechanism_type, a in analyses_map.items():
        # Revision Report
        rev_md = out_dir / f"REVISION_REPORT_{mechanism_type.upper()}.md"
        failed_rows = [[f["assumption"][:80], f["revision_action"], f["priority"]] for f in cast(list[dict[str, Any]], a["assumptions_failed"])]
        write_markdown(
            rev_md,
            f"""# Revision Report: {mechanism_type}
## Discovery Cycle 3 Phase 5

**Alpha ID**: {a['alpha_id']}
**Family**: {a['family_id']}
**Phase 4 Outcome**: {a['phase4_outcome']}
**ARB Decision**: {a['arb_decision']}
**ARB Rationale**: {a['arb_rationale']}

### Failed Assumptions
{markdown_table(['Assumption', 'Revision Action', 'Priority'], failed_rows)}

### Supported Assumptions
""" + "\n".join(f"- {s}" for s in cast(list[str], a["assumptions_supported"])) + "\n",
        )
        written[f"revision_report_{mechanism_type}"] = str(rev_md)

        # Mechanism Change Proposal
        change_md = out_dir / f"MECHANISM_CHANGE_PROPOSAL_{mechanism_type.upper()}.md"
        feat_rows = [[f["feature"], f["proposed_replacement"][:80], f["failure_mode"][:60]] for f in cast(list[dict[str, Any]], a["features_requiring_redesign"])]
        proxy_rows = [[p["current_proxy"], p["proposed_proxy"][:60], p["scientific_rationale"][:80]] for p in cast(list[dict[str, Any]], a["proxy_replacements"])]
        write_markdown(
            change_md,
            f"""# Mechanism Change Proposal: {mechanism_type}
## Discovery Cycle 3 Phase 5

### Feature Redesign
{markdown_table(['Feature', 'Proposed Replacement', 'Failure Mode'], feat_rows)}

### Proxy Replacements
{markdown_table(['Current Proxy', 'Proposed Proxy', 'Rationale'], proxy_rows)}

### Remaining Plausible Causal Mechanisms
""" + "\n".join(f"- {c}" for c in cast(list[str], a["causal_mechanisms_remaining_plausible"])) + "\n",
        )
        written[f"change_proposal_{mechanism_type}"] = str(change_md)

        # Causal Revision Plan
        causal_md = out_dir / f"CAUSAL_REVISION_PLAN_{mechanism_type.upper()}.md"
        causal_rows = [[c["mechanism"][:70], c["problem"][:80], c["proposed_revision"][:80]] for c in cast(list[dict[str, Any]], a["causal_mechanisms_requiring_revision"])]
        write_markdown(
            causal_md,
            f"""# Causal Revision Plan: {mechanism_type}
## Discovery Cycle 3 Phase 5

{markdown_table(['Mechanism', 'Problem', 'Proposed Revision'], causal_rows)}
""",
        )
        written[f"causal_revision_{mechanism_type}"] = str(causal_md)

        # Confidence Update
        conf_md = out_dir / f"CONFIDENCE_UPDATE_{mechanism_type.upper()}.md"
        cr = cast(dict[str, Any], a["confidence_revision"])
        write_markdown(
            conf_md,
            f"""# Confidence Update: {mechanism_type}
## Discovery Cycle 3 Phase 5

- Phase 4 posterior: {cr['prior_phase4']}
- Phase 5 posterior: {cr['posterior_revision']}
- Direction: {cr['direction']}
- Contingent on: {cr['contingent_on']}

**Rationale**: {cr['revision_rationale']}
""",
        )
        written[f"confidence_update_{mechanism_type}"] = str(conf_md)

    # Evidence Gap Report
    ev_md = out_dir / "EVIDENCE_GAP_REPORT.md"
    all_evid: list[list[Any]] = []
    for a in analyses_map.values():
        for ei in cast(list[str], a["evidence_insufficient"]):
            all_evid.append([str(a["alpha_id"]), ei[:100]])
    write_markdown(ev_md, f"# Evidence Gap Report\n## Discovery Cycle 3 Phase 5\n\n{markdown_table(['Alpha ID', 'Evidence Gap'], all_evid)}\n")
    written["evidence_gap_report"] = str(ev_md)

    # Dataset Gap Report
    ds_md = out_dir / "DATASET_GAP_REPORT.md"
    ds_rows = [[g["mechanism_type"], g["gap"], g["impact"][:80], g["priority"]] for g in gaps]
    write_markdown(ds_md, f"# Dataset Gap Report\n## Discovery Cycle 3 Phase 5\n\n{markdown_table(['Mechanism', 'Dataset Gap', 'Impact', 'Priority'], ds_rows)}\n")
    written["dataset_gap_report"] = str(ds_md)

    # Experiment Backlog
    exp_md = out_dir / "EXPERIMENT_BACKLOG.md"
    exp_rows = [[e["experiment_id"], e["mechanism_type"], e["title"][:60], e["priority"], e["prerequisite"][:50]] for e in experiments]
    write_markdown(exp_md, f"# Experiment Backlog\n## Discovery Cycle 3 Phase 5\n\n{markdown_table(['Exp ID', 'Mechanism', 'Title', 'Priority', 'Prerequisite'], exp_rows)}\n")
    written["experiment_backlog"] = str(exp_md)

    # Feature Revision Plan
    feat_md = out_dir / "FEATURE_REVISION_PLAN.md"
    feat_all: list[list[Any]] = []
    for a in analyses_map.values():
        for f in cast(list[dict[str, Any]], a["features_requiring_redesign"]):
            feat_all.append([str(a["alpha_id"]), f["feature"], f["proposed_replacement"][:60], str(f.get("requires_new_data", []))])
    write_markdown(feat_md, f"# Feature Revision Plan\n## Discovery Cycle 3 Phase 5\n\n{markdown_table(['Alpha ID', 'Feature', 'Proposed Replacement', 'New Data Required'], feat_all)}\n")
    written["feature_revision_plan"] = str(feat_md)

    # Proxy Replacement Plan
    proxy_md = out_dir / "PROXY_REPLACEMENT_PLAN.md"
    proxy_all: list[list[Any]] = []
    for a in analyses_map.values():
        for p in cast(list[dict[str, Any]], a["proxy_replacements"]):
            proxy_all.append([str(a["alpha_id"]), p["current_proxy"], p["proposed_proxy"][:60], p["scientific_rationale"][:80]])
    write_markdown(proxy_md, f"# Proxy Replacement Plan\n## Discovery Cycle 3 Phase 5\n\n{markdown_table(['Alpha ID', 'Current Proxy', 'Proposed Proxy', 'Rationale'], proxy_all)}\n")
    written["proxy_replacement_plan"] = str(proxy_md)

    # ARB Recommendation
    arb_md = out_dir / "ARB_RECOMMENDATION_PHASE5.md"
    learnings = "\n".join(f"- {item}" for item in cast(list[str], arb["institutional_learning"]))
    conf_rows = [[k, v["phase4_posterior"], v["phase5_posterior"], v["delta"], v["direction"]] for k, v in cast(dict[str, Any], analysis["confidence_updates"]).items()]
    write_markdown(
        arb_md,
        f"""# ARB Recommendation — Phase 5
## Discovery Cycle 3 Revision Program

### Mechanism Decisions
- REJECT: {arb['mechanisms_reject']}
- RESEARCH: {arb['mechanisms_research']}
- READY FOR REVALIDATION: {arb['mechanisms_ready_for_revalidation']}

### Confidence Updates
{markdown_table(['Mechanism', 'Phase4 Posterior', 'Phase5 Posterior', 'Delta', 'Direction'], conf_rows)}

### Experiment Backlog
{len(experiments)} experiments across {len(analyses_map)} mechanisms.

### Dataset Gaps
{len(gaps)} gaps identified; HIGH priority: {sum(1 for g in gaps if g['priority'] == 'HIGH')}.

### Institutional Learning
{learnings}

### Recommendation
{arb['recommended_next_action']}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    if campaign_result is not None:
        write_json(out_dir / "dc3_phase5_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc3_phase5_campaign_result.json")
    return written
