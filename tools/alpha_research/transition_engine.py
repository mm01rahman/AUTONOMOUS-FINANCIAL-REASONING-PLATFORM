"""Institutional Market Transition Engine for Discovery Cycle 2 Program C Phase 1.

Integrates approved Discovery Cycle 2 institutional knowledge into a unified
systems-level explanation of how XAU/USD regime transitions emerge.
"""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.cross_asset_ecology import REGIME_LABELS, REGIME_ORDER
from tools.alpha_research.decision_ecology import prepare_dc2_program_b_phase2_artifacts
from tools.alpha_research.information_network import prepare_dc2_phase3_artifacts
from tools.alpha_research.market_ecology import prepare_dc2_program_b_artifacts
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC2_PROGRAM_C_PHASE1_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-c-phase1"
DC2_PROGRAM_C_PHASE1_ANALYSIS = DC2_PROGRAM_C_PHASE1_DIR / "dc2_program_c_transition_engine_analysis.json"

REGIME_TRANSITION_PRIORS: dict[str, dict[str, Any]] = {
    "bull_trend": {
        "trigger_type": "trend_reinforcement",
        "signals": ["forward_expectation", "xau_return_1", "dxy_return_20"],
        "participants": ["macro_hedge_funds", "ctas", "etf_investors", "bullion_banks"],
        "mechanism": "trend_amplification",
        "liquidity_mode": "directional_depth_thins_as_trend_strengthens",
        "capital_flow_mode": "convex trend-following and allocation inflows accelerate",
        "early_warning": ["forward_expectation", "dxy_return_20", "macro_hedge_funds"],
    },
    "bear_unwind": {
        "trigger_type": "real_rate_shock",
        "signals": ["yield_10y_change_5", "dxy_return_1", "xau_return_1"],
        "participants": ["dealers", "bullion_banks", "commercial_hedgers", "macro_hedge_funds"],
        "mechanism": "inventory_unwind",
        "liquidity_mode": "dealer balance sheets pass de-risking outward",
        "capital_flow_mode": "tactical outflows and hedge monetization dominate",
        "early_warning": ["yield_10y_change_5", "dxy_return_1", "dealers"],
    },
    "calm_carry": {
        "trigger_type": "range_stabilization",
        "signals": ["yield_curve_10y_3m", "yield_30y_change_20", "forward_expectation"],
        "participants": ["commercial_hedgers", "market_makers", "bullion_banks", "dealers"],
        "mechanism": "inventory_absorption",
        "liquidity_mode": "market makers and hedgers absorb flow into balanced inventory",
        "capital_flow_mode": "carry-sensitive hedging and range-bound rebalancing dominate",
        "early_warning": ["yield_curve_10y_3m", "yield_30y_change_20", "market_makers"],
    },
    "crisis_dislocation": {
        "trigger_type": "systemic_stress",
        "signals": ["geo_severity", "macro_pressure", "dxy_return_1"],
        "participants": ["safe_haven_capital_flows", "dealers", "market_makers", "etf_investors"],
        "mechanism": "safe_haven_reallocation",
        "liquidity_mode": "normal depth collapses as defensive flow overwhelms intermediaries",
        "capital_flow_mode": "urgent defensive reallocation crowds into gold proxies",
        "early_warning": ["geo_severity", "macro_pressure", "safe_haven_capital_flows"],
    },
    "macro_transition": {
        "trigger_type": "macro_repricing",
        "signals": ["fed_surprise", "macro_pressure", "dxy_return_5"],
        "participants": ["central_banks", "macro_hedge_funds", "bullion_banks", "dealers"],
        "mechanism": "policy_signal_repricing",
        "liquidity_mode": "relay channels rewire as macro conviction reallocates balance sheets",
        "capital_flow_mode": "cross-asset macro capital rotates through USD, rates, and gold",
        "early_warning": ["fed_surprise", "macro_pressure", "central_banks"],
    },
    "range_compression": {
        "trigger_type": "volatility_decay",
        "signals": ["dxy_return_20", "yield_curve_10y_3m", "xau_return_1"],
        "participants": ["market_makers", "bullion_banks", "retail_traders", "commercial_hedgers"],
        "mechanism": "liquidity_rebalancing",
        "liquidity_mode": "quoted depth recovers while directional urgency fades",
        "capital_flow_mode": "incremental rebalancing displaces high-conviction directional flow",
        "early_warning": ["dxy_return_20", "yield_curve_10y_3m", "bullion_banks"],
    },
}


def _transition_pairs() -> list[tuple[str, str]]:
    return [(source, target) for source in REGIME_ORDER for target in REGIME_ORDER if source != target]


def _regime_summary(phase3: dict[str, Any], regime: str) -> dict[str, Any]:
    network = phase3["regime_network_atlas"][regime]
    centrality = network["centrality"]
    return {
        "regime": regime,
        "label": REGIME_LABELS[regime],
        "density": float(network["density"]),
        "top_sources": list(centrality["top_sources"][:3]),
        "top_relays": list(centrality["top_relays"][:3]),
        "top_sinks": list(centrality["top_sinks"][:3]),
        "edge_count": len(network["edges"]),
    }


def _relevant_capital_flows(program_b: dict[str, Any], participants: list[str]) -> list[dict[str, Any]]:
    flows = [
        edge
        for edge in cast(list[dict[str, Any]], program_b["capital_flow_network"]["edges"])
        if str(edge["participant"]) in participants
    ]
    return flows[:6]


def _relevant_liquidity(program_b: dict[str, Any], participants: list[str]) -> list[dict[str, Any]]:
    edges = [
        edge
        for edge in cast(list[dict[str, Any]], program_b["liquidity_network"]["edges"])
        if str(edge["source"]) in participants or str(edge["target"]) in participants
    ]
    return edges[:6]


def _relevant_information_edges(phase3: dict[str, Any], focus_signals: list[str]) -> list[dict[str, Any]]:
    registry = cast(list[dict[str, Any]], phase3["confidence_weighted_edge_registry"])
    filtered = [
        edge
        for edge in registry
        if str(edge["source"]) in focus_signals or str(edge["target"]) in focus_signals
    ]
    return filtered[:6]


def _participant_actions(
    program_b: dict[str, Any],
    phase2: dict[str, Any],
    participants: list[str],
) -> list[dict[str, Any]]:
    ecology_profiles = cast(dict[str, dict[str, Any]], program_b["participant_profiles"])
    decision_profiles = cast(dict[str, dict[str, Any]], phase2["decision_profiles"])
    actions: list[dict[str, Any]] = []
    for participant in participants:
        ecology = ecology_profiles[participant]
        decision = decision_profiles[participant]
        actions.append(
            {
                "participant": participant,
                "ecology_role": ecology["ecology_role"],
                "reaction_function": ecology["reaction_function"],
                "belief_update_process": decision["belief_update_process"],
                "reaction_speed": decision["reaction_speed"],
            }
        )
    return actions


def _decision_sequence(
    phase2: dict[str, Any],
    participants: list[str],
) -> list[dict[str, Any]]:
    hierarchy = cast(list[dict[str, Any]], phase2["reaction_time_hierarchy"])
    belief_edges = cast(list[dict[str, Any]], phase2["belief_update_network"]["edges"])
    cascade_models = cast(list[dict[str, Any]], phase2["decision_cascade_models"])
    sequence: list[dict[str, Any]] = []
    fast = [item for item in hierarchy if str(item["participant"]) in participants][:3]
    for idx, item in enumerate(fast, start=1):
        outgoing = [edge for edge in belief_edges if str(edge["source"]) == str(item["participant"])][:2]
        sequence.append(
            {
                "step": idx,
                "participant": item["participant"],
                "reaction_speed": item["reaction_speed"],
                "propagates_to": [edge["target"] for edge in outgoing],
            }
        )
    if cascade_models:
        dominant = cascade_models[0]
        sequence.append(
            {
                "step": len(sequence) + 1,
                "participant": dominant["initiator"],
                "reaction_speed": "cascade",
                "propagates_to": dominant["stage_2"],
            }
        )
    return sequence


def _failure_modes(
    phase2: dict[str, Any],
    participants: list[str],
) -> list[dict[str, Any]]:
    failures = cast(list[dict[str, Any]], phase2["decision_failure_catalogue"])
    return [item for item in failures if str(item["participant"]) in participants][:5]


def _transition_confidence(
    source_regime: dict[str, Any],
    target_regime: dict[str, Any],
    phase3: dict[str, Any],
    phase2: dict[str, Any],
    participants: list[str],
) -> float:
    decision_profiles = cast(dict[str, dict[str, Any]], phase2["decision_profiles"])
    participant_conf = [float(decision_profiles[participant]["confidence"]) for participant in participants]
    stability = float(phase3["network_stability_analysis"]["mean_overlap"])
    density_balance = (float(source_regime["density"]) + float(target_regime["density"])) / 2.0
    participant_mean = sum(participant_conf) / max(1, len(participant_conf))
    return round(min(0.95, 0.35 * density_balance + 0.35 * participant_mean + 0.30 * stability), 4)


def _supporting_evidence(source: str, target: str) -> list[str]:
    return [
        f"Program A Phase 3 regime network atlas: {REGIME_LABELS[source]} -> {REGIME_LABELS[target]}",
        "Program A Phase 3 ARB network recommendation",
        "Program B Phase 1 institutional market ecology atlas",
        "Program B Phase 2 decision ecology report",
    ]


def _transition_entry(
    source: str,
    target: str,
    phase3: dict[str, Any],
    program_b: dict[str, Any],
    phase2: dict[str, Any],
) -> dict[str, Any]:
    prior = REGIME_TRANSITION_PRIORS[target]
    source_regime = _regime_summary(phase3, source)
    target_regime = _regime_summary(phase3, target)
    participants = cast(list[str], prior["participants"])
    signals = cast(list[str], prior["signals"])
    participant_actions = _participant_actions(program_b, phase2, participants)
    decision_sequence = _decision_sequence(phase2, participants)
    capital_flows = _relevant_capital_flows(program_b, participants)
    liquidity = _relevant_liquidity(program_b, participants)
    information_edges = _relevant_information_edges(phase3, signals)
    failure_modes = _failure_modes(phase2, participants)
    confidence = _transition_confidence(source_regime, target_regime, phase3, phase2, participants)
    trigger_signal = signals[0]
    return {
        "transition_id": f"{source}__to__{target}",
        "source_regime": source,
        "target_regime": target,
        "initial_conditions": {
            "regime": source_regime["label"],
            "dominant_sources": source_regime["top_sources"],
            "dominant_relays": source_regime["top_relays"],
            "dominant_sinks": source_regime["top_sinks"],
            "network_density": source_regime["density"],
        },
        "trigger": {
            "type": prior["trigger_type"],
            "primary_signal": trigger_signal,
            "supporting_signals": signals[1:],
            "mechanism": prior["mechanism"],
        },
        "participant_actions": participant_actions,
        "decision_sequence": decision_sequence,
        "capital_flow": capital_flows,
        "liquidity_evolution": {
            "mode": prior["liquidity_mode"],
            "edges": liquidity,
        },
        "cross_asset_propagation": information_edges,
        "regime_activation": {
            "regime": target_regime["label"],
            "dominant_sources": target_regime["top_sources"],
            "dominant_relays": target_regime["top_relays"],
        },
        "observed_outcome": (
            f"{REGIME_LABELS[source]} transitions toward {REGIME_LABELS[target]} as "
            f"{prior['trigger_type']} propagates through {prior['mechanism']}."
        ),
        "failure_modes": failure_modes,
        "early_warning_indicators": list(prior["early_warning"]),
        "confidence": confidence,
        "supporting_evidence": _supporting_evidence(source, target),
    }


def _transition_library(
    phase3: dict[str, Any],
    program_b: dict[str, Any],
    phase2: dict[str, Any],
) -> list[dict[str, Any]]:
    transitions = [
        _transition_entry(source, target, phase3, program_b, phase2)
        for source, target in _transition_pairs()
    ]
    transitions.sort(key=lambda item: (float(item["confidence"]), str(item["transition_id"])), reverse=True)
    return transitions


def _state_machine(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    states = [
        {"regime": regime, "label": REGIME_LABELS[regime]}
        for regime in REGIME_ORDER
    ]
    edges = [
        {
            "source": item["source_regime"],
            "target": item["target_regime"],
            "trigger": item["trigger"]["type"],
            "confidence": item["confidence"],
        }
        for item in transitions
    ]
    return {"states": states, "edges": edges}


def _timeline_library(transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    library: list[dict[str, Any]] = []
    for item in transitions:
        steps = [
            {"stage": 1, "name": "initial_conditions", "detail": item["initial_conditions"]["regime"]},
            {"stage": 2, "name": "trigger", "detail": item["trigger"]["type"]},
            {"stage": 3, "name": "participant_actions", "detail": ", ".join(action["participant"] for action in item["participant_actions"][:3])},
            {"stage": 4, "name": "decision_sequence", "detail": ", ".join(step["participant"] for step in item["decision_sequence"][:3])},
            {"stage": 5, "name": "liquidity_transformation", "detail": item["liquidity_evolution"]["mode"]},
            {"stage": 6, "name": "regime_activation", "detail": item["regime_activation"]["regime"]},
        ]
        library.append({"transition_id": item["transition_id"], "timeline": steps})
    return library


def _dependency_graph(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: set[str] = set()
    edges: list[dict[str, Any]] = []
    for item in transitions:
        transition_node = item["transition_id"]
        trigger_node = f"trigger:{item['trigger']['type']}"
        mechanism_node = f"mechanism:{item['trigger']['mechanism']}"
        nodes.update([item["source_regime"], item["target_regime"], transition_node, trigger_node, mechanism_node])
        edges.extend(
            [
                {"source": item["source_regime"], "target": transition_node, "edge_type": "CAUSES"},
                {"source": trigger_node, "target": transition_node, "edge_type": "CAUSES"},
                {"source": mechanism_node, "target": transition_node, "edge_type": "DEPENDS_ON"},
                {"source": transition_node, "target": item["target_regime"], "edge_type": "CAUSES"},
            ]
        )
        for action in item["participant_actions"][:3]:
            participant_node = f"participant:{action['participant']}"
            nodes.add(participant_node)
            edges.append({"source": participant_node, "target": transition_node, "edge_type": "RELATED_TO"})
    return {"nodes": sorted(nodes), "edges": edges}


def _integrated_causal_flow(transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flows: list[dict[str, Any]] = []
    for item in transitions:
        flows.append(
            {
                "transition_id": item["transition_id"],
                "flow_chain": [
                    item["trigger"]["primary_signal"],
                    item["participant_actions"][0]["participant"],
                    item["decision_sequence"][0]["participant"] if item["decision_sequence"] else item["participant_actions"][0]["participant"],
                    item["regime_activation"]["regime"],
                ],
                "confidence": item["confidence"],
            }
        )
    return flows


def _confidence_report(transitions: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(transitions, key=lambda item: float(item["confidence"]), reverse=True)
    high_conf = [item["transition_id"] for item in ranked if float(item["confidence"]) >= 0.65][:10]
    medium_conf = [item["transition_id"] for item in ranked if 0.55 <= float(item["confidence"]) < 0.65][:10]
    low_conf = [item["transition_id"] for item in ranked if float(item["confidence"]) < 0.55][:10]
    return {
        "high_confidence_transitions": high_conf,
        "medium_confidence_transitions": medium_conf,
        "low_confidence_transitions": low_conf,
        "mean_confidence": round(sum(float(item["confidence"]) for item in transitions) / max(1, len(transitions)), 4),
    }


def _early_warning_catalogue(transitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalogue: dict[str, dict[str, Any]] = {}
    for item in transitions:
        for indicator in cast(list[str], item["early_warning_indicators"]):
            entry = catalogue.setdefault(
                indicator,
                {"indicator": indicator, "transitions": [], "mean_confidence": 0.0, "count": 0},
            )
            entry["transitions"].append(item["transition_id"])
            entry["mean_confidence"] += float(item["confidence"])
            entry["count"] += 1
    result: list[dict[str, Any]] = []
    for indicator, entry in catalogue.items():
        result.append(
            {
                "indicator": indicator,
                "transition_count": entry["count"],
                "mean_confidence": round(float(entry["mean_confidence"]) / max(1, int(entry["count"])), 4),
                "transitions": entry["transitions"][:8],
            }
        )
    result.sort(key=lambda item: (int(item["transition_count"]), float(item["mean_confidence"])), reverse=True)
    return result


def _research_recommendations(
    transitions: list[dict[str, Any]],
    early_warning: list[dict[str, Any]],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    top = sorted(transitions, key=lambda item: float(item["confidence"]), reverse=True)[:5]
    return {
        "priority_transitions": [item["transition_id"] for item in top],
        "priority_early_warnings": [item["indicator"] for item in early_warning[:5]],
        "mean_transition_confidence": confidence["mean_confidence"],
        "arb_recommendation": (
            "Adopt an institutional transition engine in which macro repricing, "
            "dealer relay capacity, liquidity withdrawal, and participant decision "
            "cascades jointly determine how XAU/USD moves between the six approved regimes."
        ),
    }


def _knowledge_graph_payload(
    transitions: list[dict[str, Any]],
    recommendations: dict[str, Any],
) -> dict[str, Any]:
    regime_nodes = [
        {
            "node_id": f"IKROS-PC1-REGIME-{regime.replace('_', '-').upper()}",
            "label": REGIME_LABELS[regime],
            "node_type": "REGIME",
            "attributes": {"regime": regime},
        }
        for regime in REGIME_ORDER
    ]
    transition_nodes = [
        {
            "node_id": f"IKROS-PC1-TRANSITION-{item['transition_id'].replace('_', '-').upper()}",
            "label": item["transition_id"],
            "node_type": "MARKET_EVENT",
            "attributes": {
                "source_regime": item["source_regime"],
                "target_regime": item["target_regime"],
                "confidence": item["confidence"],
            },
        }
        for item in transitions
    ]
    mechanism_ids = sorted(
        {
            str(item["trigger"]["mechanism"])
            for item in transitions
        }
    )
    mechanism_nodes = [
        {
            "node_id": f"IKROS-PC1-MECHANISM-{mechanism.replace('_', '-').upper()}",
            "label": mechanism.replace("_", " ").title(),
            "node_type": "KNOWLEDGE_OBJECT",
            "attributes": {"mechanism": mechanism},
        }
        for mechanism in mechanism_ids
    ]
    transition_edges: list[dict[str, Any]] = []
    mechanism_edges: list[dict[str, Any]] = []
    for item in transitions:
        transition_id = f"IKROS-PC1-TRANSITION-{item['transition_id'].replace('_', '-').upper()}"
        source_id = f"IKROS-PC1-REGIME-{item['source_regime'].replace('_', '-').upper()}"
        target_id = f"IKROS-PC1-REGIME-{item['target_regime'].replace('_', '-').upper()}"
        mechanism_id = f"IKROS-PC1-MECHANISM-{str(item['trigger']['mechanism']).replace('_', '-').upper()}"
        transition_edges.extend(
            [
                {"source": source_id, "target": transition_id, "relation": "CAUSES", "confidence": item["confidence"]},
                {"source": transition_id, "target": target_id, "relation": "CAUSES", "confidence": item["confidence"]},
            ]
        )
        mechanism_edges.append(
            {
                "source": mechanism_id,
                "target": transition_id,
                "relation": "DEPENDS_ON",
                "confidence": item["confidence"],
            }
        )
    return {
        "regime_nodes": regime_nodes,
        "transition_nodes": transition_nodes,
        "mechanism_nodes": mechanism_nodes,
        "transition_edges": transition_edges,
        "mechanism_edges": mechanism_edges,
        "priority_transitions": recommendations["priority_transitions"],
    }


def prepare_dc2_program_c_phase1_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    phase3 = prepare_dc2_phase3_artifacts(repo_root=repo_root)
    program_b = prepare_dc2_program_b_artifacts(repo_root=repo_root)
    phase2 = prepare_dc2_program_b_phase2_artifacts(repo_root=repo_root)
    transitions = _transition_library(phase3, program_b, phase2)
    state_machine = _state_machine(transitions)
    timelines = _timeline_library(transitions)
    dependency_graph = _dependency_graph(transitions)
    causal_flow = _integrated_causal_flow(transitions)
    confidence = _confidence_report(transitions)
    early_warning = _early_warning_catalogue(transitions)
    recommendations = _research_recommendations(transitions, early_warning, confidence)
    kg_payload = _knowledge_graph_payload(transitions, recommendations)

    analysis = {
        "phase": "DC2_PROGRAM_C_PHASE1",
        "title": "Institutional Market Transition Engine",
        "date_range": phase3["date_range"],
        "institutional_transition_engine": transitions,
        "transition_state_machine": state_machine,
        "transition_timeline_library": timelines,
        "transition_dependency_graph": dependency_graph,
        "integrated_causal_flow": causal_flow,
        "transition_confidence_model": confidence,
        "early_warning_indicator_catalogue": early_warning,
        "transition_failure_catalogue": [
            {
                "transition_id": item["transition_id"],
                "failure_modes": item["failure_modes"],
            }
            for item in transitions
        ],
        "transition_trigger_registry": [
            {
                "transition_id": item["transition_id"],
                "trigger_type": item["trigger"]["type"],
                "primary_signal": item["trigger"]["primary_signal"],
                "mechanism": item["trigger"]["mechanism"],
            }
            for item in transitions
        ],
        "transition_causal_graph": {
            "nodes": dependency_graph["nodes"],
            "edges": dependency_graph["edges"],
        },
        "ecology_knowledge_graph": kg_payload,
        "research_recommendations": recommendations,
        "program_a_foundations": phase3["arb_recommendation"],
        "program_b_phase1_foundations": program_b["research_recommendations"],
        "program_b_phase2_foundations": phase2["institutional_recommendations"],
    }

    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_C_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_program_c_transition_engine_analysis.json", analysis)
    return analysis


def emit_dc2_program_c_phase1_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_C_PHASE1_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    transitions = cast(list[dict[str, Any]], analysis["institutional_transition_engine"])
    state_machine = cast(dict[str, Any], analysis["transition_state_machine"])
    timelines = cast(list[dict[str, Any]], analysis["transition_timeline_library"])
    causal_graph = cast(dict[str, Any], analysis["transition_causal_graph"])
    trigger_registry = cast(list[dict[str, Any]], analysis["transition_trigger_registry"])
    confidence = cast(dict[str, Any], analysis["transition_confidence_model"])
    early_warning = cast(list[dict[str, Any]], analysis["early_warning_indicator_catalogue"])
    recommendations = cast(dict[str, Any], analysis["research_recommendations"])

    atlas_md = out_dir / "INSTITUTIONAL_TRANSITION_ATLAS.md"
    atlas_rows: list[list[object]] = [
        [item["transition_id"], item["trigger"]["type"], item["regime_activation"]["regime"], item["confidence"]]
        for item in transitions[:12]
    ]
    write_markdown(
        atlas_md,
        f"""# Institutional Transition Atlas
## Discovery Cycle 2 Program C Phase 1

{markdown_table(["Transition", "Trigger", "Activated Regime", "Confidence"], atlas_rows)}

### ARB Recommendation
{recommendations["arb_recommendation"]}
""",
    )
    written["institutional_transition_atlas"] = str(atlas_md)

    spec_md = out_dir / "TRANSITION_ENGINE_SPECIFICATION.md"
    write_markdown(
        spec_md,
        f"""# Transition Engine Specification
## Discovery Cycle 2 Program C Phase 1

### States
{", ".join(state["regime"] for state in state_machine["states"])}

### Transition Count
{len(state_machine["edges"])}

### Governing Description
The transition engine integrates macro triggers, participant ecology, decision cascades, liquidity transformation, and cross-asset propagation into a single institutional state machine.
""",
    )
    written["transition_engine_specification"] = str(spec_md)

    timeline_md = out_dir / "TRANSITION_TIMELINE_CATALOGUE.md"
    timeline_rows: list[list[object]] = [
        [item["transition_id"], item["timeline"][1]["detail"], item["timeline"][3]["detail"], item["timeline"][5]["detail"]]
        for item in timelines[:15]
    ]
    write_markdown(
        timeline_md,
        f"""# Transition Timeline Catalogue
## Discovery Cycle 2 Program C Phase 1

{markdown_table(["Transition", "Trigger", "Decision Cascade", "Activation"], timeline_rows)}
""",
    )
    written["transition_timeline_catalogue"] = str(timeline_md)

    causal_md = out_dir / "TRANSITION_CAUSAL_GRAPH.md"
    write_markdown(
        causal_md,
        f"""# Transition Causal Graph
## Discovery Cycle 2 Program C Phase 1

- **Node Count:** {len(causal_graph["nodes"])}
- **Edge Count:** {len(causal_graph["edges"])}
- **Priority Transitions:** {", ".join(recommendations["priority_transitions"][:5])}
""",
    )
    written["transition_causal_graph"] = str(causal_md)

    trigger_md = out_dir / "TRANSITION_TRIGGER_REGISTRY.md"
    trigger_rows: list[list[object]] = [
        [item["transition_id"], item["trigger_type"], item["primary_signal"], item["mechanism"]]
        for item in trigger_registry[:15]
    ]
    write_markdown(
        trigger_md,
        f"""# Transition Trigger Registry
## Discovery Cycle 2 Program C Phase 1

{markdown_table(["Transition", "Trigger Type", "Primary Signal", "Mechanism"], trigger_rows)}
""",
    )
    written["transition_trigger_registry"] = str(trigger_md)

    confidence_md = out_dir / "TRANSITION_CONFIDENCE_REPORT.md"
    write_markdown(
        confidence_md,
        f"""# Transition Confidence Report
## Discovery Cycle 2 Program C Phase 1

- **Mean Confidence:** {confidence["mean_confidence"]}
- **High Confidence:** {", ".join(confidence["high_confidence_transitions"][:8])}
- **Medium Confidence:** {", ".join(confidence["medium_confidence_transitions"][:8])}
- **Lower Confidence:** {", ".join(confidence["low_confidence_transitions"][:8])}
""",
    )
    written["transition_confidence_report"] = str(confidence_md)

    early_md = out_dir / "EARLY_WARNING_INDICATOR_CATALOGUE.md"
    early_rows: list[list[object]] = [
        [item["indicator"], item["transition_count"], item["mean_confidence"]]
        for item in early_warning[:12]
    ]
    write_markdown(
        early_md,
        f"""# Early Warning Indicator Catalogue
## Discovery Cycle 2 Program C Phase 1

{markdown_table(["Indicator", "Transition Count", "Mean Confidence"], early_rows)}
""",
    )
    written["early_warning_indicator_catalogue"] = str(early_md)

    integrated_md = out_dir / "INTEGRATED_MARKET_TRANSITION_REPORT.md"
    top_transition = transitions[0]
    write_markdown(
        integrated_md,
        f"""# Integrated Market Transition Report
## Discovery Cycle 2 Program C Phase 1

### Governing Transition
- **Transition:** {top_transition["transition_id"]}
- **Trigger:** {top_transition["trigger"]["type"]}
- **Mechanism:** {top_transition["trigger"]["mechanism"]}
- **Confidence:** {top_transition["confidence"]}

### Systems Interpretation
Market regime transitions emerge when macro repricing shocks are transformed by participant ecology, accelerated by decision cascades, and either amplified or absorbed by available liquidity capacity.
""",
    )
    written["integrated_market_transition_report"] = str(integrated_md)

    rec_md = out_dir / "RESEARCH_RECOMMENDATIONS.md"
    write_markdown(
        rec_md,
        f"""# Research Recommendations
## Discovery Cycle 2 Program C Phase 1

### Priority Transitions
{chr(10).join(f"- {item}" for item in recommendations["priority_transitions"][:8])}

### Priority Early Warnings
{chr(10).join(f"- {item}" for item in recommendations["priority_early_warnings"][:8])}

### ARB Recommendation
{recommendations["arb_recommendation"]}
""",
    )
    written["research_recommendations"] = str(rec_md)

    write_json(out_dir / "transition_engine.json", transitions)
    write_json(out_dir / "transition_state_machine.json", state_machine)
    write_json(out_dir / "transition_timeline_library.json", timelines)
    write_json(out_dir / "transition_dependency_graph.json", analysis["transition_dependency_graph"])
    write_json(out_dir / "integrated_causal_flow.json", analysis["integrated_causal_flow"])
    write_json(out_dir / "transition_confidence_model.json", confidence)
    write_json(out_dir / "early_warning_indicator_catalogue.json", early_warning)
    write_json(out_dir / "transition_failure_catalogue.json", analysis["transition_failure_catalogue"])
    write_json(out_dir / "transition_trigger_registry.json", trigger_registry)
    write_json(out_dir / "transition_causal_graph.json", causal_graph)
    write_json(out_dir / "research_recommendations.json", recommendations)

    written["transition_engine_json"] = str(out_dir / "transition_engine.json")
    written["transition_state_machine_json"] = str(out_dir / "transition_state_machine.json")
    written["transition_timeline_library_json"] = str(out_dir / "transition_timeline_library.json")
    written["transition_dependency_graph_json"] = str(out_dir / "transition_dependency_graph.json")
    written["integrated_causal_flow_json"] = str(out_dir / "integrated_causal_flow.json")
    written["transition_confidence_model_json"] = str(out_dir / "transition_confidence_model.json")
    written["early_warning_indicator_catalogue_json"] = str(out_dir / "early_warning_indicator_catalogue.json")
    written["transition_failure_catalogue_json"] = str(out_dir / "transition_failure_catalogue.json")
    written["transition_trigger_registry_json"] = str(out_dir / "transition_trigger_registry.json")
    written["transition_causal_graph_json"] = str(out_dir / "transition_causal_graph.json")
    written["research_recommendations_json"] = str(out_dir / "research_recommendations.json")

    return written
