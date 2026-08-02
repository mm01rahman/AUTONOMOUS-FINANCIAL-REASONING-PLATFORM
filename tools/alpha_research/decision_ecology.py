"""Institutional Decision Ecology for Discovery Cycle 2 Program B Phase 2.

Builds the first governed decision-ecology model explaining how institutional
market participants transform information into coordinated market decisions that
generate market-wide behavior and XAU/USD regime transitions.
"""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.market_ecology import prepare_dc2_program_b_artifacts
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC2_PROGRAM_B_PHASE2_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-b-phase2"
DC2_PROGRAM_B_PHASE2_ANALYSIS = DC2_PROGRAM_B_PHASE2_DIR / "dc2_program_b_phase2_decision_ecology_analysis.json"

DECISION_THEMES = [
    "expectation_formation",
    "belief_updating",
    "decision_latency",
    "strategic_interaction",
    "information_asymmetry",
    "decision_cascades",
    "adaptive_decision_behaviour",
]


def _expectation_style(profile: dict[str, Any]) -> str:
    capital_role = str(profile["capital_role"])
    liquidity_role = str(profile["liquidity_role"])
    if capital_role in {"sovereign_allocator", "tactical_allocator"}:
        return "macro_scenario"
    if capital_role in {"investment_flow", "defensive_reallocator"}:
        return "allocation_narrative"
    if liquidity_role in {"intermediation_core", "balance_sheet_intermediary"}:
        return "flow_balancing"
    if liquidity_role == "liquidity_provider":
        return "microstructure_state"
    if liquidity_role == "trend_amplifier":
        return "systematic_trend"
    return "hedge_optimization"


def _belief_update_speed(profile: dict[str, Any]) -> tuple[str, float]:
    capital_role = str(profile["capital_role"])
    liquidity_role = str(profile["liquidity_role"])
    score = float(profile["aggregate_ecology_score"])
    if liquidity_role == "liquidity_provider":
        return "intraday", round(0.90 + min(0.08, score * 0.02), 4)
    if capital_role == "tactical_allocator":
        return "fast", round(0.84 + min(0.08, score * 0.02), 4)
    if capital_role in {"investment_flow", "defensive_reallocator"}:
        return "medium", round(0.72 + min(0.08, score * 0.02), 4)
    if capital_role == "sovereign_allocator":
        return "slow", round(0.60 + min(0.06, score * 0.02), 4)
    return "medium", round(0.68 + min(0.08, score * 0.02), 4)


def _decision_profiles(program_b: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profiles = cast(dict[str, dict[str, Any]], program_b["participant_profiles"])
    result: dict[str, dict[str, Any]] = {}
    for pid, profile in profiles.items():
        update_speed, speed_score = _belief_update_speed(profile)
        expectation_style = _expectation_style(profile)
        decision_constraint = (
            "policy_credibility"
            if profile["capital_role"] == "sovereign_allocator"
            else "balance_sheet"
            if profile["liquidity_role"] in {"intermediation_core", "balance_sheet_intermediary"}
            else "flow_toxicity"
            if profile["liquidity_role"] == "liquidity_provider"
            else "model_rules"
            if profile["liquidity_role"] == "trend_amplifier"
            else "mandate_and_liquidity"
        )
        information_sources = sorted(cast(dict[str, float], profile["signals"]).keys())
        confidence = round(min(0.92, 0.50 + 0.08 * float(profile["source_exposure"]) + 0.10 * float(profile["relay_exposure"]) + 0.06 * speed_score), 4)
        result[pid] = {
            "participant": pid,
            "label": profile["label"],
            "information_sources": information_sources,
            "belief_update_process": expectation_style,
            "reaction_speed": update_speed,
            "reaction_score": speed_score,
            "decision_objectives": profile["objectives"],
            "decision_constraints": decision_constraint,
            "typical_responses_by_regime": profile["expected_behaviour_by_regime"],
            "historical_examples": profile["historical_behaviour"],
            "failure_modes": profile["failure_modes"],
            "confidence": confidence,
            "ecology_role": profile["ecology_role"],
        }
    return result


def _reaction_hierarchy(decision_profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        decision_profiles.values(),
        key=lambda item: (float(item["reaction_score"]), float(item["confidence"])),
        reverse=True,
    )
    return [
        {
            "rank": idx + 1,
            "participant": item["participant"],
            "label": item["label"],
            "reaction_speed": item["reaction_speed"],
            "reaction_score": item["reaction_score"],
            "belief_update_process": item["belief_update_process"],
        }
        for idx, item in enumerate(ranked)
    ]


def _belief_update_network(
    decision_profiles: dict[str, dict[str, Any]],
    interaction_network: dict[str, Any],
) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    for edge in cast(list[dict[str, Any]], interaction_network["edges"]):
        source = str(edge["source"])
        target = str(edge["target"])
        source_speed = float(decision_profiles[source]["reaction_score"])
        target_speed = float(decision_profiles[target]["reaction_score"])
        asymmetry = round(source_speed - target_speed, 4)
        update_strength = round(abs(float(edge["interaction_score"])) * (0.6 + source_speed), 4)
        if update_strength < 0.20:
            continue
        edges.append(
            {
                "source": source,
                "target": target,
                "update_strength": update_strength,
                "information_asymmetry": asymmetry,
                "channel": decision_profiles[source]["belief_update_process"],
            }
        )
    edges.sort(key=lambda item: float(item["update_strength"]), reverse=True)
    return {"edges": edges}


def _strategic_dependency_network(
    decision_profiles: dict[str, dict[str, Any]],
    interaction_network: dict[str, Any],
) -> dict[str, Any]:
    dependencies: list[dict[str, Any]] = []
    matrix: dict[str, dict[str, float]] = {
        pid: {other: 0.0 for other in decision_profiles}
        for pid in decision_profiles
    }
    for edge in cast(list[dict[str, Any]], interaction_network["edges"]):
        source = str(edge["source"])
        target = str(edge["target"])
        source_role = str(decision_profiles[source]["ecology_role"])
        target_speed = float(decision_profiles[target]["reaction_score"])
        dep = round(abs(float(edge["interaction_score"])) * (1.0 + target_speed) * (1.15 if source_role in {"ecology_driver", "ecology_relay"} else 0.90), 4)
        matrix[source][target] = dep
        if dep >= 0.30:
            dependencies.append(
                {
                    "source": source,
                    "target": target,
                    "dependency_strength": dep,
                    "dependency_type": "strategic_follow" if float(edge["interaction_score"]) > 0 else "strategic_counterposition",
                }
            )
    dependencies.sort(key=lambda item: float(item["dependency_strength"]), reverse=True)
    return {"matrix": matrix, "edges": dependencies}


def _information_asymmetry(decision_profiles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items = sorted(
        (
            {
                "participant": pid,
                "label": profile["label"],
                "source_count": len(cast(list[str], profile["information_sources"])),
                "reaction_score": float(profile["reaction_score"]),
                "asymmetry_score": round(len(cast(list[str], profile["information_sources"])) * 0.20 + float(profile["reaction_score"]) * 0.60 + float(profile["confidence"]) * 0.20, 4),
            }
            for pid, profile in decision_profiles.items()
        ),
        key=lambda item: float(item["asymmetry_score"]),
        reverse=True,
    )
    return items


def _decision_cascades(
    hierarchy: list[dict[str, Any]],
    strategic: dict[str, Any],
    belief_network: dict[str, Any],
) -> list[dict[str, Any]]:
    top_fast = [item["participant"] for item in hierarchy[:4]]
    dependency_targets: dict[str, list[str]] = {}
    for edge in cast(list[dict[str, Any]], strategic["edges"]):
        dependency_targets.setdefault(str(edge["source"]), []).append(str(edge["target"]))
    belief_targets: dict[str, list[str]] = {}
    for edge in cast(list[dict[str, Any]], belief_network["edges"]):
        belief_targets.setdefault(str(edge["source"]), []).append(str(edge["target"]))
    cascades: list[dict[str, Any]] = []
    for participant in top_fast:
        stage2 = dependency_targets.get(participant, [])[:2]
        stage3: list[str] = []
        for target in stage2:
            stage3.extend(belief_targets.get(target, [])[:2])
        cascades.append(
            {
                "initiator": participant,
                "stage_1": [participant],
                "stage_2": stage2,
                "stage_3": sorted(dict.fromkeys(stage3)),
                "cascade_strength": round(0.35 + 0.12 * len(stage2) + 0.08 * len(stage3), 4),
            }
        )
    cascades.sort(key=lambda item: float(item["cascade_strength"]), reverse=True)
    return cascades


def _decision_failure_catalogue(decision_profiles: dict[str, dict[str, Any]], cascades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    cascade_initiators = {str(item["initiator"]) for item in cascades[:4]}
    for pid, profile in decision_profiles.items():
        failure_mode = str(profile["failure_modes"])
        category = (
            "cascade_amplification"
            if pid in cascade_initiators
            else "information_delay"
            if profile["reaction_speed"] in {"slow", "medium"}
            else "execution_mismatch"
        )
        failures.append(
            {
                "participant": pid,
                "failure_category": category,
                "failure_mode": failure_mode,
                "confidence": profile["confidence"],
            }
        )
    return failures


def _knowledge_graph_payload(
    decision_profiles: dict[str, dict[str, Any]],
    belief_network: dict[str, Any],
    strategic: dict[str, Any],
    cascades: list[dict[str, Any]],
) -> dict[str, Any]:
    decision_nodes = [
        {
            "node_id": f"IKROS-PB2-DECISION-{pid.replace('_', '-').upper()}",
            "label": f"{profile['label']} Decision Model",
            "node_type": "DECISION",
            "attributes": {
                "participant": pid,
                "belief_update_process": profile["belief_update_process"],
                "reaction_speed": profile["reaction_speed"],
                "confidence": profile["confidence"],
            },
        }
        for pid, profile in decision_profiles.items()
    ]
    belief_edges = [
        {
            "source": f"IKROS-PB2-DECISION-{str(edge['source']).replace('_', '-').upper()}",
            "target": f"IKROS-PB2-DECISION-{str(edge['target']).replace('_', '-').upper()}",
            "relation": "CAUSES",
            "confidence": edge["update_strength"],
            "attributes": {
                "information_asymmetry": edge["information_asymmetry"],
                "channel": edge["channel"],
            },
        }
        for edge in cast(list[dict[str, Any]], belief_network["edges"][:40])
    ]
    strategic_edges = [
        {
            "source": f"IKROS-PB2-DECISION-{str(edge['source']).replace('_', '-').upper()}",
            "target": f"IKROS-PB2-DECISION-{str(edge['target']).replace('_', '-').upper()}",
            "relation": "DEPENDS_ON",
            "confidence": edge["dependency_strength"],
            "attributes": {"dependency_type": edge["dependency_type"]},
        }
        for edge in cast(list[dict[str, Any]], strategic["edges"][:40])
    ]
    cascade_nodes = [
        {
            "node_id": f"IKROS-PB2-CASCADE-{idx + 1:04d}",
            "label": f"Decision Cascade {idx + 1}",
            "node_type": "RESEARCH_CONCLUSION",
            "attributes": {
                "initiator": cascade["initiator"],
                "cascade_strength": cascade["cascade_strength"],
            },
        }
        for idx, cascade in enumerate(cascades[:10])
    ]
    return {
        "decision_nodes": decision_nodes,
        "belief_edges": belief_edges,
        "strategic_edges": strategic_edges,
        "cascade_nodes": cascade_nodes,
    }


def _institutional_recommendations(
    hierarchy: list[dict[str, Any]],
    asymmetry: list[dict[str, Any]],
    cascades: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "fastest_decision_makers": [item["participant"] for item in hierarchy[:5]],
        "highest_information_asymmetry": [item["participant"] for item in asymmetry[:5]],
        "dominant_cascade_initiators": [item["initiator"] for item in cascades[:5]],
        "arb_recommendation": (
            "Adopt a layered decision ecology in which macro hedge funds and market makers update fastest, "
            "central banks and bullion banks anchor belief formation, dealers relay strategic dependencies, "
            "and ETF/safe-haven flows turn localized decisions into market-wide cascades."
        ),
    }


def prepare_dc2_program_b_phase2_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    program_b = prepare_dc2_program_b_artifacts(repo_root=repo_root)
    decision_profiles = _decision_profiles(program_b)
    hierarchy = _reaction_hierarchy(decision_profiles)
    belief_network = _belief_update_network(decision_profiles, program_b["participant_interaction_network"])
    strategic = _strategic_dependency_network(decision_profiles, program_b["participant_interaction_network"])
    asymmetry = _information_asymmetry(decision_profiles)
    cascades = _decision_cascades(hierarchy, strategic, belief_network)
    failures = _decision_failure_catalogue(decision_profiles, cascades)
    kg_payload = _knowledge_graph_payload(decision_profiles, belief_network, strategic, cascades)
    recommendations = _institutional_recommendations(hierarchy, asymmetry, cascades)

    analysis = {
        "phase": "DC2_PROGRAM_B_PHASE2",
        "title": "Institutional Decision Ecology",
        "date_range": program_b["date_range"],
        "decision_profiles": decision_profiles,
        "belief_update_network": belief_network,
        "reaction_time_hierarchy": hierarchy,
        "strategic_dependency_network": strategic,
        "information_asymmetry": asymmetry,
        "decision_cascade_models": cascades,
        "regime_decision_matrix": {
            pid: profile["typical_responses_by_regime"]
            for pid, profile in decision_profiles.items()
        },
        "decision_failure_catalogue": failures,
        "decision_graph": {
            "participants": list(decision_profiles.keys()),
            "fastest_decision_makers": recommendations["fastest_decision_makers"],
            "dominant_cascade_initiators": recommendations["dominant_cascade_initiators"],
        },
        "ecology_knowledge_graph": kg_payload,
        "institutional_recommendations": recommendations,
        "program_b_phase1_foundations": program_b["research_recommendations"],
    }

    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_B_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_program_b_phase2_decision_ecology_analysis.json", analysis)
    return analysis


def emit_dc2_program_b_phase2_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_B_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    profiles = analysis["decision_profiles"]
    belief = analysis["belief_update_network"]
    hierarchy = analysis["reaction_time_hierarchy"]
    strategic = analysis["strategic_dependency_network"]
    cascades = analysis["decision_cascade_models"]
    failures = analysis["decision_failure_catalogue"]
    recommendations = analysis["institutional_recommendations"]
    asymmetry = analysis["information_asymmetry"]

    report_md = out_dir / "DECISION_ECOLOGY_REPORT.md"
    report_rows: list[list[object]] = [
        [pid, profile["belief_update_process"], profile["reaction_speed"], profile["confidence"]]
        for pid, profile in profiles.items()
    ]
    write_markdown(
        report_md,
        f"""# Decision Ecology Report
## Discovery Cycle 2 Program B Phase 2

{markdown_table(["Participant", "Belief Update", "Reaction Speed", "Confidence"], report_rows)}

### ARB Recommendation
{recommendations["arb_recommendation"]}
""",
    )
    written["decision_ecology_report"] = str(report_md)

    profiles_md = out_dir / "PARTICIPANT_DECISION_PROFILES.md"
    blocks = []
    for _pid, profile in profiles.items():
        blocks.append(
            f"""### {profile['label']}
- **Information Sources:** {", ".join(profile['information_sources'])}
- **Belief Update Process:** {profile['belief_update_process']}
- **Reaction Speed:** {profile['reaction_speed']}
- **Decision Objectives:** {profile['decision_objectives']}
- **Decision Constraints:** {profile['decision_constraints']}
- **Historical Examples:** {profile['historical_examples']}
- **Failure Modes:** {profile['failure_modes']}
- **Confidence:** {profile['confidence']}
"""
        )
    write_markdown(profiles_md, "# Participant Decision Profiles\n## Discovery Cycle 2 Program B Phase 2\n\n" + "\n".join(blocks))
    written["participant_decision_profiles"] = str(profiles_md)

    cascade_md = out_dir / "DECISION_CASCADE_ATLAS.md"
    cascade_rows: list[list[object]] = [
        [item["initiator"], ", ".join(item["stage_2"]), ", ".join(item["stage_3"]), item["cascade_strength"]]
        for item in cascades
    ]
    write_markdown(
        cascade_md,
        f"""# Decision Cascade Atlas
## Discovery Cycle 2 Program B Phase 2

{markdown_table(["Initiator", "Stage 2", "Stage 3", "Cascade Strength"], cascade_rows)}
""",
    )
    written["decision_cascade_atlas"] = str(cascade_md)

    strategic_md = out_dir / "STRATEGIC_INTERACTION_MATRIX.md"
    participants = list(profiles.keys())
    strategic_rows: list[list[object]] = [
        [source, *[strategic["matrix"][source][target] for target in participants]]
        for source in participants
    ]
    write_markdown(
        strategic_md,
        f"""# Strategic Interaction Matrix
## Discovery Cycle 2 Program B Phase 2

{markdown_table(["Participant", *participants], strategic_rows)}
""",
    )
    written["strategic_interaction_matrix"] = str(strategic_md)

    belief_md = out_dir / "BELIEF_UPDATE_REPORT.md"
    belief_rows: list[list[object]] = [
        [edge["source"], edge["target"], edge["update_strength"], edge["information_asymmetry"], edge["channel"]]
        for edge in belief["edges"][:30]
    ]
    write_markdown(
        belief_md,
        f"""# Belief Update Report
## Discovery Cycle 2 Program B Phase 2

{markdown_table(["Source", "Target", "Update Strength", "Information Asymmetry", "Channel"], belief_rows)}
""",
    )
    written["belief_update_report"] = str(belief_md)

    hierarchy_md = out_dir / "REACTION_HIERARCHY.md"
    hierarchy_rows: list[list[object]] = [
        [item["rank"], item["participant"], item["reaction_speed"], item["reaction_score"], item["belief_update_process"]]
        for item in hierarchy
    ]
    write_markdown(
        hierarchy_md,
        f"""# Reaction Hierarchy
## Discovery Cycle 2 Program B Phase 2

{markdown_table(["Rank", "Participant", "Reaction Speed", "Reaction Score", "Belief Update"], hierarchy_rows)}
""",
    )
    written["reaction_hierarchy"] = str(hierarchy_md)

    failure_md = out_dir / "DECISION_FAILURE_CATALOGUE.md"
    failure_rows: list[list[object]] = [
        [item["participant"], item["failure_category"], item["failure_mode"], item["confidence"]]
        for item in failures
    ]
    write_markdown(
        failure_md,
        f"""# Decision Failure Catalogue
## Discovery Cycle 2 Program B Phase 2

{markdown_table(["Participant", "Failure Category", "Failure Mode", "Confidence"], failure_rows)}
""",
    )
    written["decision_failure_catalogue"] = str(failure_md)

    rec_md = out_dir / "INSTITUTIONAL_RECOMMENDATIONS.md"
    asymmetry_lines = "\n".join(f"- {item['participant']}" for item in asymmetry[:5])
    cascade_lines = "\n".join(f"- {item}" for item in recommendations["dominant_cascade_initiators"])
    write_markdown(
        rec_md,
        f"""# Institutional Recommendations
## Discovery Cycle 2 Program B Phase 2

### Fastest Decision Makers
{chr(10).join(f"- {item}" for item in recommendations["fastest_decision_makers"])}

### Highest Information Asymmetry
{asymmetry_lines}

### Dominant Cascade Initiators
{cascade_lines}

### ARB Recommendation
{recommendations["arb_recommendation"]}
""",
    )
    written["institutional_recommendations"] = str(rec_md)

    write_json(out_dir / "decision_graph.json", analysis["decision_graph"])
    write_json(out_dir / "decision_profiles.json", profiles)
    write_json(out_dir / "belief_update_network.json", belief)
    write_json(out_dir / "reaction_hierarchy.json", hierarchy)
    write_json(out_dir / "strategic_dependency_network.json", strategic)
    write_json(out_dir / "decision_cascades.json", cascades)
    write_json(out_dir / "regime_decision_matrix.json", analysis["regime_decision_matrix"])
    write_json(out_dir / "decision_failure_catalogue.json", failures)
    write_json(out_dir / "institutional_recommendations.json", recommendations)

    written["decision_graph_json"] = str(out_dir / "decision_graph.json")
    written["decision_profiles_json"] = str(out_dir / "decision_profiles.json")
    written["belief_update_network_json"] = str(out_dir / "belief_update_network.json")
    written["reaction_hierarchy_json"] = str(out_dir / "reaction_hierarchy.json")
    written["strategic_dependency_network_json"] = str(out_dir / "strategic_dependency_network.json")
    written["decision_cascades_json"] = str(out_dir / "decision_cascades.json")
    written["regime_decision_matrix_json"] = str(out_dir / "regime_decision_matrix.json")
    written["decision_failure_catalogue_json"] = str(out_dir / "decision_failure_catalogue.json")
    written["institutional_recommendations_json"] = str(out_dir / "institutional_recommendations.json")

    return written
