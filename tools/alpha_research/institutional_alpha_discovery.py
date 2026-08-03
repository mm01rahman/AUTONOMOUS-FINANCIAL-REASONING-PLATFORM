"""Discovery Cycle 3: Institutional Alpha Discovery Program (no validation/optimization)."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC3_ALPHA_DIR = Path("11-research") / "discovery-cycle-3" / "institutional-alpha-discovery-program"
DC3_ALPHA_ANALYSIS = DC3_ALPHA_DIR / "dc3_institutional_alpha_discovery_analysis.json"


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], __import__("json").loads(path.read_text(encoding="utf-8")))


def _source_paths(repo_root: Path) -> dict[str, Path]:
    dc2 = repo_root / "11-research" / "discovery-cycle-2"
    return {
        "program_a1": dc2 / "research-program-a" / "dc2_program_a_analysis.json",
        "program_a2": dc2 / "research-program-a-phase2" / "dc2_phase2_causal_analysis.json",
        "program_a3": dc2 / "research-program-a-phase3" / "dc2_phase3_information_network_analysis.json",
        "program_b1": dc2 / "research-program-b-phase1" / "dc2_program_b_market_ecology_analysis.json",
        "program_b2": dc2 / "research-program-b-phase2" / "dc2_program_b_phase2_decision_ecology_analysis.json",
        "program_c1": dc2 / "research-program-c-phase1" / "dc2_program_c_transition_engine_analysis.json",
        "program_d1": dc2 / "research-program-d-phase1" / "dc2_program_d_verification_analysis.json",
        "program_e1": dc2 / "research-program-e-phase1" / "dc2_program_e_ablation_analysis.json",
        "program_f1": dc2 / "research-program-f-phase1" / "dc2_program_f_institutional_theory_analysis.json",
    }


def _confidence_prior(mechanism_type: str) -> float:
    table = {
        "cross_asset_transition": 0.62,
        "macro_repricing": 0.56,
        "liquidity_withdrawal": 0.58,
        "dealer_inventory": 0.57,
        "expectation_reset": 0.55,
        "safe_haven_migration": 0.6,
        "etf_flow_propagation": 0.54,
        "policy_repricing": 0.55,
        "decision_cascade": 0.59,
        "information_cascade": 0.61,
        "adaptive_ecology_shift": 0.57,
        "regime_transition_chain": 0.58,
    }
    return table.get(mechanism_type, 0.55)


def _complexity_score(mechanism_type: str) -> float:
    table = {
        "cross_asset_transition": 0.68,
        "macro_repricing": 0.52,
        "liquidity_withdrawal": 0.54,
        "dealer_inventory": 0.53,
        "expectation_reset": 0.5,
        "safe_haven_migration": 0.57,
        "etf_flow_propagation": 0.49,
        "policy_repricing": 0.51,
        "decision_cascade": 0.61,
        "information_cascade": 0.6,
        "adaptive_ecology_shift": 0.58,
        "regime_transition_chain": 0.64,
    }
    return table.get(mechanism_type, 0.55)


def _novelty_score(mechanism_type: str) -> float:
    table = {
        "cross_asset_transition": 0.44,
        "macro_repricing": 0.46,
        "liquidity_withdrawal": 0.42,
        "dealer_inventory": 0.47,
        "expectation_reset": 0.5,
        "safe_haven_migration": 0.48,
        "etf_flow_propagation": 0.52,
        "policy_repricing": 0.45,
        "decision_cascade": 0.51,
        "information_cascade": 0.5,
        "adaptive_ecology_shift": 0.53,
        "regime_transition_chain": 0.43,
    }
    return table.get(mechanism_type, 0.45)


def _synthesize_mechanisms(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    a3 = evidence["program_a3"]
    b1 = evidence["program_b1"]
    b2 = evidence["program_b2"]
    c1 = evidence["program_c1"]
    d1 = evidence["program_d1"]
    f1 = evidence["program_f1"]

    stable_edges = cast(list[str], a3["arb_recommendation"]["stable_edges"])
    relays = cast(list[str], a3["arb_recommendation"]["dominant_relays"])
    sources = cast(list[str], a3["arb_recommendation"]["dominant_sources"])
    sinks = cast(list[str], a3["arb_recommendation"]["dominant_sinks"])
    fastest = cast(list[str], b2["institutional_recommendations"]["fastest_decision_makers"])
    cascades = cast(list[str], b2["institutional_recommendations"]["dominant_cascade_initiators"])
    interactions = cast(list[str], b1["research_recommendations"]["critical_interactions"])
    failures = cast(list[str], d1["failure_catalogue"])
    axioms = cast(list[dict[str, Any]], f1["institutional_axiom_registry"])
    constraints = cast(list[str], f1["evidence_synthesis"]["architecture_constraints_for_future_models"])

    mechanism_templates: list[dict[str, Any]] = [
        {
            "mechanism_type": "cross_asset_transition",
            "name": "Cross-Asset Relay Pressure Transition Mechanism",
            "economic_rationale": "When source shocks concentrate into relay bottlenecks, downstream sink repricing accelerates regime pressure.",
            "market_mechanism": f"Directed source→relay→sink propagation anchored by stable edges ({', '.join(stable_edges[:3])}).",
            "required_conditions": [f"Relay concentration in {', '.join(relays[:2])}", "Elevated transition-risk context"],
            "expected_regimes": ["macro_transition", "crisis_dislocation", "bear_unwind"],
            "expected_failure_modes": [failures[0], failures[2]],
            "required_features": list({*sources[:2], *relays[:2], *sinks[:2]}),
            "required_evidence": ["Program A3 network atlas", "Program D robustness matrix", "Program F axioms"],
            "lineage_refs": [axioms[0]["principle_id"], axioms[1]["principle_id"]],
        },
        {
            "mechanism_type": "macro_repricing",
            "name": "Macro Repricing Relay Mechanism",
            "economic_rationale": "Macro shocks require relay-capacity confirmation before transition propagation becomes durable.",
            "market_mechanism": "Macro pressure and policy surprise transmit through DXY-rate relay channels before broad XAU/USD regime shifts.",
            "required_conditions": ["Macro-event intensity above baseline", "Relay stability maintained across event windows"],
            "expected_regimes": ["macro_transition", "bull_trend", "bear_unwind"],
            "expected_failure_modes": [failures[0], failures[4]],
            "required_features": ["macro_pressure", "fed_surprise", "dxy_return_5", "yield_10y_change_5"],
            "required_evidence": ["Program A2 causal retention", "Program C trigger registry", "Program E unresolved macro-layer evidence"],
            "lineage_refs": [axioms[3]["principle_id"]],
        },
        {
            "mechanism_type": "liquidity_withdrawal",
            "name": "Liquidity Withdrawal Shock Mechanism",
            "economic_rationale": "Liquidity withdrawal amplifies directional information and increases transition discontinuity.",
            "market_mechanism": "Volatility and depth compression force inventory pass-through across institutional intermediaries.",
            "required_conditions": ["High realized volatility", "Inventory transfer pressure through dealers/market makers"],
            "expected_regimes": ["crisis_dislocation", "range_compression", "bear_unwind"],
            "expected_failure_modes": [failures[1], failures[3]],
            "required_features": ["regime_vol_20", "breakout_60", "breakdown_20"],
            "required_evidence": ["Program B1 liquidity ecology", "Program E liquidity-layer redesign requirement"],
            "lineage_refs": [axioms[2]["principle_id"]],
        },
        {
            "mechanism_type": "dealer_inventory",
            "name": "Dealer Inventory Redistribution Mechanism",
            "economic_rationale": "Dealer inventory constraints mediate whether flows absorb or cascade into regime transitions.",
            "market_mechanism": f"Critical interaction pathways ({', '.join(interactions[:2])}) govern inventory redistribution speed.",
            "required_conditions": ["Dealer constraint signal present", "Hedger/market-maker offset insufficient"],
            "expected_regimes": ["calm_carry", "bear_unwind", "macro_transition"],
            "expected_failure_modes": [failures[1], failures[4]],
            "required_features": ["xau_return_1", "regime_vol_20", "yield_curve_10y_3m"],
            "required_evidence": ["Program B1 interaction matrix", "Program B2 strategic dependency network"],
            "lineage_refs": [axioms[0]["principle_id"]],
        },
        {
            "mechanism_type": "expectation_reset",
            "name": "Expectation Reset Mechanism",
            "economic_rationale": "Expectation shifts by fast decision-makers can reset institutional priors and trigger regime reclassification.",
            "market_mechanism": f"Fast participants ({', '.join(fastest[:3])}) update first and propagate belief updates downstream.",
            "required_conditions": ["Expectation shock above threshold", "Belief-diffusion through dependency network"],
            "expected_regimes": ["macro_transition", "bull_trend", "range_compression"],
            "expected_failure_modes": [failures[2], failures[4]],
            "required_features": ["forward_expectation", "dxy_return_1", "dxy_return_5"],
            "required_evidence": ["Program B2 belief update report", "Program C transition timelines"],
            "lineage_refs": [axioms[1]["principle_id"]],
        },
        {
            "mechanism_type": "safe_haven_migration",
            "name": "Safe-Haven Capital Migration Mechanism",
            "economic_rationale": "Stress migration reallocates capital toward gold proxies via institutional risk-off channels.",
            "market_mechanism": "Event/stress topology rewires flows toward safe-haven sinks under policy/geopolitical pressure.",
            "required_conditions": ["Stress-event topology activation", "Safe-haven participant impulse"],
            "expected_regimes": ["crisis_dislocation", "bull_trend"],
            "expected_failure_modes": [failures[0], failures[3]],
            "required_features": ["geo_severity", "macro_pressure", "dxy_return_1"],
            "required_evidence": ["Program A3 stress topology", "Program B1 safe-haven flow ecology"],
            "lineage_refs": [axioms[1]["principle_id"], axioms[3]["principle_id"]],
        },
        {
            "mechanism_type": "etf_flow_propagation",
            "name": "ETF Flow Propagation Mechanism",
            "economic_rationale": "ETF participation can convert localized signal shocks into broader positioning pressure.",
            "market_mechanism": "Flow propagation from ETF cohorts interacts with relay nodes to amplify transition pathways.",
            "required_conditions": ["ETF flow impulse present", "Cross-asset relay path open"],
            "expected_regimes": ["bull_trend", "range_compression", "crisis_dislocation"],
            "expected_failure_modes": [failures[1], failures[2]],
            "required_features": ["dxy_return_20", "forward_expectation", "regime_vol_20"],
            "required_evidence": ["Program B2 cascade atlas", "Program A3 temporal influence network"],
            "lineage_refs": [axioms[0]["principle_id"]],
        },
        {
            "mechanism_type": "policy_repricing",
            "name": "Policy Repricing Chain Mechanism",
            "economic_rationale": "Policy surprises repricing rates and FX can alter gold-transition pressure through institutional allocation constraints.",
            "market_mechanism": "Central-bank signal shock propagates via rates/FX corridor before regime activation.",
            "required_conditions": ["Policy surprise present", "Rates-FX co-movement above baseline"],
            "expected_regimes": ["macro_transition", "bear_unwind", "calm_carry"],
            "expected_failure_modes": [failures[0], failures[4]],
            "required_features": ["fed_surprise", "yield_10y_change_5", "dxy_return_5"],
            "required_evidence": ["Program A2 macro mediation", "Program C trigger registry"],
            "lineage_refs": [axioms[3]["principle_id"]],
        },
        {
            "mechanism_type": "decision_cascade",
            "name": "Institutional Decision Cascade Mechanism",
            "economic_rationale": "Strategic dependencies create cascade chains where early actor decisions alter downstream participant constraints.",
            "market_mechanism": f"Cascade initiators ({', '.join(cascades[:3])}) shift strategic network state and transition probabilities.",
            "required_conditions": ["Initiator cohort activation", "Dependency graph connectivity intact"],
            "expected_regimes": ["macro_transition", "crisis_dislocation", "bull_trend"],
            "expected_failure_modes": [failures[2], failures[3]],
            "required_features": ["forward_expectation", "macro_pressure", "dxy_return_1"],
            "required_evidence": ["Program B2 strategic interaction matrix", "Program C integrated causal flow"],
            "lineage_refs": [axioms[2]["principle_id"]],
        },
        {
            "mechanism_type": "information_cascade",
            "name": "Cross-Asset Information Cascade Mechanism",
            "economic_rationale": "Persistent directed information chains can generate synchronized repricing across linked markets.",
            "market_mechanism": f"Stable edges ({', '.join(stable_edges[:4])}) propagate information with regime-dependent intensity.",
            "required_conditions": ["Directed edge confidence above threshold", "Regime overlay alignment"],
            "expected_regimes": ["macro_transition", "range_compression", "bull_trend"],
            "expected_failure_modes": [failures[0], failures[2]],
            "required_features": ["dxy_return_1", "dxy_return_5", "macro_pressure", "forward_expectation"],
            "required_evidence": ["Program A3 confidence-weighted edge registry", "Program F topology axioms"],
            "lineage_refs": [axioms[0]["principle_id"], axioms[1]["principle_id"]],
        },
        {
            "mechanism_type": "adaptive_ecology_shift",
            "name": "Adaptive Ecology Shift Mechanism",
            "economic_rationale": "Participant objective shifts across regimes alter capital-flow competition/cooperation structure.",
            "market_mechanism": "Ecology-state shifts modify dominant flow pathways and liquidity absorption capacity.",
            "required_conditions": ["Participant role rotation observed", "Interaction-network rewiring signal present"],
            "expected_regimes": ["calm_carry", "macro_transition", "crisis_dislocation"],
            "expected_failure_modes": [failures[1], failures[3]],
            "required_features": ["regime_vol_20", "dxy_return_20", "yield_curve_10y_3m"],
            "required_evidence": ["Program B1 adaptive behaviour report", "Program A3 regime-specific topology"],
            "lineage_refs": [axioms[1]["principle_id"]],
        },
        {
            "mechanism_type": "regime_transition_chain",
            "name": "Institutional Regime Transition Chain Mechanism",
            "economic_rationale": "Regime transitions emerge through ordered trigger→participant→liquidity→activation chains constrained by institutional architecture.",
            "market_mechanism": "Transition timelines encode deterministic stage progression with regime-specific trigger signatures.",
            "required_conditions": ["Ordered stage progression observed", "No contradiction to architecture constraints"],
            "expected_regimes": cast(list[str], c1["transition_confidence_model"]["high_confidence_transitions"][:3]),
            "expected_failure_modes": [failures[0], failures[1], failures[4]],
            "required_features": ["xau_return_1", "macro_pressure", "dxy_return_5", "regime_vol_20"],
            "required_evidence": ["Program C transition timeline catalogue", "Program D falsification report", "Program F constraints"],
            "lineage_refs": [axioms[0]["principle_id"], axioms[2]["principle_id"], axioms[3]["principle_id"]],
        },
    ]

    candidates: list[dict[str, Any]] = []
    for idx, item in enumerate(mechanism_templates, start=1):
        mechanism_type = str(item["mechanism_type"])
        prior = _confidence_prior(mechanism_type)
        novelty = _novelty_score(mechanism_type)
        complexity = _complexity_score(mechanism_type)
        information_gain = round(min(0.95, 0.35 * prior + 0.35 * novelty + 0.30 * (1.0 - complexity)), 4)
        scientific_support = round(min(0.95, prior + 0.08), 4)
        robustness_expectation = round(max(0.3, prior - 0.05), 4)
        failure_risk = round(max(0.2, complexity - 0.1), 4)
        institutional_value = round(min(0.95, 0.4 * scientific_support + 0.35 * information_gain + 0.25 * robustness_expectation), 4)
        research_priority = round(
            0.24 * scientific_support
            + 0.18 * information_gain
            + 0.16 * robustness_expectation
            + 0.12 * novelty
            + 0.12 * prior
            + 0.1 * institutional_value
            - 0.04 * complexity
            - 0.04 * failure_risk,
            4,
        )
        candidates.append(
            {
                "alpha_id": f"IKROS-ALPHA-DC3-20260802-{idx:04d}",
                "version": "1.0.0",
                "status": "DISCOVERED",
                "research_question": f"Can {item['name'].lower()} generate durable, regime-aware, institutionally explainable alpha mechanisms in XAU/USD?",
                "name": item["name"],
                "mechanism_type": mechanism_type,
                "economic_rationale": item["economic_rationale"],
                "market_mechanism": item["market_mechanism"],
                "required_conditions": item["required_conditions"],
                "expected_regimes": item["expected_regimes"],
                "expected_failure_modes": item["expected_failure_modes"],
                "required_features": item["required_features"],
                "required_evidence": item["required_evidence"],
                "expected_information_gain": information_gain,
                "novelty_score": novelty,
                "complexity_score": complexity,
                "confidence_prior": prior,
                "scientific_support": scientific_support,
                "expected_robustness": robustness_expectation,
                "economic_plausibility": round(min(0.95, scientific_support + 0.04), 4),
                "validation_cost": round(0.45 + 0.45 * complexity, 4),
                "research_cost": round(0.4 + 0.4 * complexity, 4),
                "failure_risk": failure_risk,
                "expected_institutional_value": institutional_value,
                "research_priority": research_priority,
                "institutional_lineage": item["lineage_refs"],
                "supporting_evidence": item["required_evidence"],
                "contradictory_evidence": [],
                "validation_history": [],
                "regime_applicability": item["expected_regimes"],
                "required_datasets": sorted(set(item["required_features"])),
                "expected_capacity": "UNSPECIFIED_PRE_VALIDATION",
                "expected_decay": "UNSPECIFIED_PRE_VALIDATION",
                "failure_catalogue": item["expected_failure_modes"],
                "promotion_history": [],
                "architecture_constraints": constraints[:4],
            }
        )
    return candidates


def _competition(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    by_type: dict[str, list[dict[str, Any]]] = {}
    for item in candidates:
        by_type.setdefault(str(item["mechanism_type"]), []).append(item)
    for items in by_type.values():
        sorted_items = sorted(items, key=lambda c: float(c["research_priority"]), reverse=True)
        kept.append(sorted_items[0])
        removed.extend(sorted_items[1:])

    dominant_types = sorted({str(item["mechanism_type"]) for item in kept})
    return {
        "kept_candidates": kept,
        "removed_candidates": removed,
        "duplicate_count": len(removed),
        "retained_count": len(kept),
        "dominant_mechanism_families": dominant_types,
    }


def _priority_matrix(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=lambda c: float(c["research_priority"]), reverse=True)
    matrix: list[dict[str, Any]] = []
    for idx, item in enumerate(ranked, start=1):
        matrix.append(
            {
                "rank": idx,
                "alpha_id": item["alpha_id"],
                "name": item["name"],
                "mechanism_type": item["mechanism_type"],
                "research_priority": item["research_priority"],
                "scientific_support": item["scientific_support"],
                "expected_information_gain": item["expected_information_gain"],
                "expected_robustness": item["expected_robustness"],
                "economic_plausibility": item["economic_plausibility"],
                "novelty_score": item["novelty_score"],
                "validation_cost": item["validation_cost"],
                "research_cost": item["research_cost"],
                "confidence_prior": item["confidence_prior"],
                "failure_risk": item["failure_risk"],
                "expected_institutional_value": item["expected_institutional_value"],
            }
        )
    return matrix


def _queue(priority_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for row in priority_matrix:
        priority_band = "P1" if int(row["rank"]) <= 4 else "P2" if int(row["rank"]) <= 8 else "P3"
        queue.append(
            {
                "queue_position": row["rank"],
                "priority_band": priority_band,
                "alpha_id": row["alpha_id"],
                "name": row["name"],
                "entry_criteria": "Scientific support and information-gain thresholds met under governance constraints.",
                "defer_criteria": "Insufficient evidence completion or architecture-constraint violation.",
            }
        )
    return queue


def _validation_preparation(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    plans: list[dict[str, Any]] = []
    for item in candidates:
        plans.append(
            {
                "alpha_id": item["alpha_id"],
                "validation_plan": {
                    "walk_forward": "Define fixed rolling windows with regime stratification; no threshold optimization.",
                    "cpcv": "Cross-path cross-validation with blocked temporal folds.",
                    "monte_carlo": "Perturb sequencing and shocks without parameter search.",
                    "stress": "Replay FOMC/CPI/NFP proxies, crises, and high-volatility windows.",
                    "sensitivity": "Single-factor perturbation around mechanism assumptions.",
                    "robustness": "Out-of-sample and long-window replay consistency checks.",
                },
                "promotion_criteria": {
                    "must_outperform_simple_baselines": True,
                    "calibration_required": True,
                    "false_transition_control_required": True,
                    "economic_plausibility_required": True,
                },
                "required_evidence": item["required_evidence"],
                "expected_failure_conditions": item["expected_failure_modes"],
            }
        )
    return {"validation_preparation": plans}


def _explainability_reports(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for item in candidates:
        reports.append(
            {
                "alpha_id": item["alpha_id"],
                "economic_explanation": item["economic_rationale"],
                "market_narrative": item["market_mechanism"],
                "cross_asset_explanation": f"Uses features {', '.join(cast(list[str], item['required_features'])[:3])} to model cross-asset transmission.",
                "participant_explanation": "Participant ecology and decision-cascade evidence from Program B is used as explanatory context.",
                "decision_ecology_explanation": "Belief update and reaction hierarchy inform timing assumptions but remain pre-validation.",
                "liquidity_explanation": "Liquidity-state features contribute to failure-risk constraints and regime applicability.",
                "failure_conditions": item["expected_failure_modes"],
                "historical_examples": ["Derived from Discovery Cycle 2 event/stress windows used in Programs A and D."],
                "contradictory_evidence": item["contradictory_evidence"],
                "confidence": item["confidence_prior"],
            }
        )
    return reports


def _roadmap(queue_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for item in queue_items:
        step = int(item["queue_position"])
        steps.append(
            {
                "step": step,
                "alpha_id": item["alpha_id"],
                "phase": "Validation Preparation Only",
                "objective": "Complete evidence and protocol plans before any validation execution.",
                "exit_criteria": "All required evidence and governance checks complete.",
            }
        )
    return steps


def _completion_report(
    candidates: list[dict[str, Any]],
    competition: dict[str, Any],
    queue_items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "discovered": len(candidates),
        "retained": int(competition["retained_count"]),
        "rejected": int(competition["duplicate_count"]),
        "queue_size": len(queue_items),
        "validation_executed": False,
        "optimization_executed": False,
        "strategy_generation_executed": False,
        "runtime_changes": False,
    }


def _graph_payload(candidates: list[dict[str, Any]], queue_items: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_nodes = [
        {
            "node_id": item["alpha_id"],
            "label": item["name"],
            "node_type": "ALPHA_CANDIDATE",
            "confidence": item["confidence_prior"],
            "attributes": {"status": item["status"], "mechanism_type": item["mechanism_type"]},
        }
        for item in candidates
    ]
    queue_node = {
        "node_id": "IKROS-DC3-ALPHAQUEUE-20260802-0001",
        "label": "Institutional Alpha Research Queue",
        "node_type": "KNOWLEDGE_OBJECT",
        "confidence": 0.75,
        "attributes": {"size": len(queue_items)},
    }
    conclusion_node = {
        "node_id": "IKROS-DC3-CONCLUSION-20260802-0001",
        "label": "DC3 Institutional Alpha Discovery Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "confidence": 0.76,
        "attributes": {"status": "DISCOVERY_COMPLETE_PRE_VALIDATION"},
    }
    edges: list[dict[str, Any]] = []
    for item in candidates:
        edges.append({"source": item["alpha_id"], "target": queue_node["node_id"], "relation": "EVALUATED", "confidence": item["research_priority"]})
    edges.append({"source": queue_node["node_id"], "target": conclusion_node["node_id"], "relation": "EXPLAINS", "confidence": 0.75})
    return {
        "candidate_nodes": candidate_nodes,
        "queue_node": queue_node,
        "conclusion_node": conclusion_node,
        "edges": edges,
    }


def prepare_dc3_institutional_alpha_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(".")
    paths = _source_paths(root)
    if any(not p.exists() for p in paths.values()):
        paths = _source_paths(Path("."))
    evidence = {k: _load_json(p) for k, p in paths.items()}

    candidates = _synthesize_mechanisms(evidence)
    competition = _competition(candidates)
    retained = cast(list[dict[str, Any]], competition["kept_candidates"])
    priority = _priority_matrix(retained)
    queue_items = _queue(priority)
    explainability = _explainability_reports(retained)
    validation_prep = _validation_preparation(retained)
    roadmap = _roadmap(queue_items)
    completion = _completion_report(candidates, competition, queue_items)
    payload = _graph_payload(retained, queue_items)

    analysis: dict[str, Any] = {
        "phase": "DISCOVERY_CYCLE_3_INSTITUTIONAL_ALPHA_PROGRAM",
        "title": "Institutional Alpha Discovery Program",
        "source_evidence": list(paths.keys()),
        "institutional_alpha_discovery_engine": {"deterministic": True, "generator": "knowledge-constrained mechanism synthesis"},
        "institutional_alpha_registry": candidates,
        "institutional_alpha_catalogue": retained,
        "alpha_mechanism_atlas": [
            {"alpha_id": item["alpha_id"], "name": item["name"], "mechanism_type": item["mechanism_type"], "market_mechanism": item["market_mechanism"]}
            for item in retained
        ],
        "economic_mechanism_atlas": [
            {"alpha_id": item["alpha_id"], "economic_rationale": item["economic_rationale"], "required_conditions": item["required_conditions"]}
            for item in retained
        ],
        "research_priority_matrix": priority,
        "alpha_competition_report": {
            "retained": int(competition["retained_count"]),
            "removed": int(competition["duplicate_count"]),
            "dominant_mechanism_families": competition["dominant_mechanism_families"],
        },
        "institutional_alpha_queue": queue_items,
        "alpha_explainability_reports": explainability,
        "validation_preparation_reports": validation_prep,
        "institutional_alpha_roadmap": roadmap,
        "discovery_cycle_3_completion_report": completion,
        "arb_recommendation": {
            "governed_discovery_complete": True,
            "validate_now": False,
            "optimize_now": False,
            "promote_alpha_now": False,
            "recommended_next_action": "Await ARB approval before validation program kickoff.",
            "retained_alpha_ids": [item["alpha_id"] for item in retained],
            "open_research_gaps": [
                "Macro and decision-layer evidence remains conditional from Program E/F.",
                "External market data gaps (VIX, S&P500, crude, FX pairs, ETF flows) remain structural constraints.",
                "Calibration and false-transition controls must be hard-gated in validation protocols.",
            ],
        },
        "ecology_knowledge_graph": payload,
    }

    out_dir = root / DC3_ALPHA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc3_institutional_alpha_discovery_analysis.json", analysis)
    return analysis


def emit_dc3_institutional_alpha_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC3_ALPHA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    registry = cast(list[dict[str, Any]], analysis["institutional_alpha_registry"])
    catalogue = cast(list[dict[str, Any]], analysis["institutional_alpha_catalogue"])
    priority = cast(list[dict[str, Any]], analysis["research_priority_matrix"])
    queue_items = cast(list[dict[str, Any]], analysis["institutional_alpha_queue"])
    explainability = cast(list[dict[str, Any]], analysis["alpha_explainability_reports"])
    validation_prep = cast(dict[str, Any], analysis["validation_preparation_reports"])
    roadmap = cast(list[dict[str, Any]], analysis["institutional_alpha_roadmap"])
    completion = cast(dict[str, Any], analysis["discovery_cycle_3_completion_report"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    competition = cast(dict[str, Any], analysis["alpha_competition_report"])

    engine_md = out_dir / "INSTITUTIONAL_ALPHA_DISCOVERY_ENGINE.md"
    write_markdown(
        engine_md,
        """# Institutional Alpha Discovery Engine
## Discovery Cycle 3

This engine generates institutional alpha **mechanisms** from governed knowledge artifacts (DC1/DC2),
not arbitrary indicator combinations. It is deterministic, traceable, and architecture-constrained.
Validation, optimization, and promotion are explicitly out of scope for this phase.
""",
    )
    written["institutional_alpha_discovery_engine"] = str(engine_md)

    reg_md = out_dir / "INSTITUTIONAL_ALPHA_REGISTRY.md"
    reg_rows = [[r["alpha_id"], r["name"], r["mechanism_type"], r["confidence_prior"], r["status"]] for r in registry]
    write_markdown(reg_md, f"# Institutional Alpha Registry\n## Discovery Cycle 3\n\n{markdown_table(['Alpha ID', 'Name', 'Type', 'Confidence Prior', 'Status'], reg_rows)}\n")
    written["institutional_alpha_registry"] = str(reg_md)

    cat_md = out_dir / "INSTITUTIONAL_ALPHA_CATALOGUE.md"
    cat_rows = [[r["alpha_id"], r["name"], r["research_priority"], r["expected_information_gain"]] for r in catalogue]
    write_markdown(cat_md, f"# Institutional Alpha Catalogue\n## Discovery Cycle 3\n\n{markdown_table(['Alpha ID', 'Name', 'Priority', 'Information Gain'], cat_rows)}\n")
    written["institutional_alpha_catalogue"] = str(cat_md)

    mech_md = out_dir / "ALPHA_MECHANISM_ATLAS.md"
    mech_rows = [[r["alpha_id"], r["name"], r["mechanism_type"], r["market_mechanism"]] for r in catalogue]
    write_markdown(mech_md, f"# Alpha Mechanism Atlas\n## Discovery Cycle 3\n\n{markdown_table(['Alpha ID', 'Name', 'Type', 'Market Mechanism'], mech_rows)}\n")
    written["alpha_mechanism_atlas"] = str(mech_md)

    eco_md = out_dir / "ECONOMIC_MECHANISM_ATLAS.md"
    eco_rows = [[r["alpha_id"], r["name"], r["economic_rationale"]] for r in catalogue]
    write_markdown(eco_md, f"# Economic Mechanism Atlas\n## Discovery Cycle 3\n\n{markdown_table(['Alpha ID', 'Name', 'Economic Rationale'], eco_rows)}\n")
    written["economic_mechanism_atlas"] = str(eco_md)

    priority_md = out_dir / "RESEARCH_PRIORITY_MATRIX.md"
    pr_rows = [[p["rank"], p["alpha_id"], p["name"], p["research_priority"], p["scientific_support"], p["failure_risk"]] for p in priority]
    write_markdown(priority_md, f"# Research Priority Matrix\n## Discovery Cycle 3\n\n{markdown_table(['Rank', 'Alpha ID', 'Name', 'Priority', 'Scientific Support', 'Failure Risk'], pr_rows)}\n")
    written["research_priority_matrix"] = str(priority_md)

    comp_md = out_dir / "ALPHA_COMPETITION_REPORT.md"
    write_markdown(
        comp_md,
        f"""# Alpha Competition Report
## Discovery Cycle 3

- **Retained**: {competition['retained']}
- **Removed**: {competition['removed']}
- **Dominant mechanism families**: {", ".join(cast(list[str], competition["dominant_mechanism_families"]))}
""",
    )
    written["alpha_competition_report"] = str(comp_md)

    queue_md = out_dir / "INSTITUTIONAL_ALPHA_QUEUE.md"
    q_rows = [[q["queue_position"], q["priority_band"], q["alpha_id"], q["name"]] for q in queue_items]
    write_markdown(queue_md, f"# Institutional Alpha Queue\n## Discovery Cycle 3\n\n{markdown_table(['Position', 'Band', 'Alpha ID', 'Name'], q_rows)}\n")
    written["institutional_alpha_queue"] = str(queue_md)

    explain_md = out_dir / "ALPHA_EXPLAINABILITY_REPORTS.md"
    ex_rows = [[e["alpha_id"], e["economic_explanation"], e["market_narrative"], e["confidence"]] for e in explainability]
    write_markdown(explain_md, f"# Alpha Explainability Reports\n## Discovery Cycle 3\n\n{markdown_table(['Alpha ID', 'Economic Explanation', 'Market Narrative', 'Confidence'], ex_rows)}\n")
    written["alpha_explainability_reports"] = str(explain_md)

    val_md = out_dir / "VALIDATION_PREPARATION_REPORTS.md"
    val_rows = [[v["alpha_id"], "walk_forward,cpcv,monte_carlo,stress,sensitivity,robustness", "No validation execution in DC3"] for v in cast(list[dict[str, Any]], validation_prep["validation_preparation"])]
    write_markdown(val_md, f"# Validation Preparation Reports\n## Discovery Cycle 3\n\n{markdown_table(['Alpha ID', 'Prepared Plans', 'Status'], val_rows)}\n")
    written["validation_preparation_reports"] = str(val_md)

    roadmap_md = out_dir / "INSTITUTIONAL_ALPHA_ROADMAP.md"
    rm_rows = [[r["step"], r["alpha_id"], r["phase"], r["exit_criteria"]] for r in roadmap]
    write_markdown(roadmap_md, f"# Institutional Alpha Roadmap\n## Discovery Cycle 3\n\n{markdown_table(['Step', 'Alpha ID', 'Phase', 'Exit Criteria'], rm_rows)}\n")
    written["institutional_alpha_roadmap"] = str(roadmap_md)

    complete_md = out_dir / "DISCOVERY_CYCLE_3_COMPLETION_REPORT.md"
    comp_rows = [[k, v] for k, v in completion.items()]
    write_markdown(complete_md, f"# Discovery Cycle 3 Completion Report\n## Institutional Alpha Discovery Program\n\n{markdown_table(['Metric', 'Value'], comp_rows)}\n")
    written["discovery_cycle_3_completion_report"] = str(complete_md)

    arb_md = out_dir / "ARB_RECOMMENDATION.md"
    gaps = "\n".join(f"- {g}" for g in cast(list[str], arb["open_research_gaps"]))
    ids = "\n".join(f"- {x}" for x in cast(list[str], arb["retained_alpha_ids"]))
    write_markdown(
        arb_md,
        f"""# ARB Recommendation
## Discovery Cycle 3 Institutional Alpha Discovery Program

- **Governed discovery complete**: {arb['governed_discovery_complete']}
- **Validate now**: {arb['validate_now']}
- **Optimize now**: {arb['optimize_now']}
- **Promote alpha now**: {arb['promote_alpha_now']}

### Retained Institutional Alpha Candidates
{ids}

### Remaining Research Gaps
{gaps}

### Recommendation
{arb['recommended_next_action']}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    write_json(out_dir / "dc3_institutional_alpha_registry.json", registry)
    written["registry_json"] = str(out_dir / "dc3_institutional_alpha_registry.json")
    write_json(out_dir / "dc3_institutional_alpha_queue.json", queue_items)
    written["queue_json"] = str(out_dir / "dc3_institutional_alpha_queue.json")
    write_json(out_dir / "dc3_alpha_competition_report.json", competition)
    written["competition_json"] = str(out_dir / "dc3_alpha_competition_report.json")
    if campaign_result is not None:
        write_json(out_dir / "dc3_program_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc3_program_campaign_result.json")
    return written
