"""Discovery Cycle 3 Phase 3: Institutional Alpha Taxonomy & Consolidation Program."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC3_PHASE3_DIR = (
    Path("11-research") / "discovery-cycle-3" / "phase-3-institutional-alpha-taxonomy"
)
DC3_PHASE3_ANALYSIS = DC3_PHASE3_DIR / "dc3_phase3_institutional_alpha_taxonomy.json"


# ---------------------------------------------------------------------------
# Taxonomy family definitions
# ---------------------------------------------------------------------------

ALPHA_FAMILIES: list[dict[str, Any]] = [
    {
        "family_id": "FAM-001",
        "name": "Macro Repricing",
        "definition": "Mechanisms driven by macro-economic signal repricing transmitted through cross-asset relay channels.",
        "economic_rationale": "Macro shocks alter the real interest-rate and real-yield anchors that institutional actors use to price gold relative to alternatives.",
        "typical_regimes": ["macro_transition", "bear_unwind", "bull_trend"],
        "typical_failures": ["Relay disruption without macro confirmation", "False trigger on noise spikes"],
        "expected_persistence": "MEDIUM",
        "capacity_expectation": "HIGH",
        "known_risks": ["Policy reversal", "DXY regime change", "Yield-curve regime break"],
        "confidence": 0.63,
    },
    {
        "family_id": "FAM-002",
        "name": "Liquidity Transition",
        "definition": "Mechanisms driven by institutional liquidity withdrawal, inventory constraint, or flow-absorption collapse.",
        "economic_rationale": "Liquidity stress compresses bid-offer depth, forces inventory redistribution, and amplifies directional information flow.",
        "typical_regimes": ["crisis_dislocation", "bear_unwind", "range_compression"],
        "typical_failures": ["False liquidity alarm without depth data", "Missed recovery phase"],
        "expected_persistence": "LOW",
        "capacity_expectation": "MEDIUM",
        "known_risks": ["Rapid liquidity restoration", "Central-bank backstop"],
        "confidence": 0.60,
    },
    {
        "family_id": "FAM-003",
        "name": "Safe Haven Migration",
        "definition": "Mechanisms driven by capital migration toward gold as institutional safe-haven allocation rises.",
        "economic_rationale": "Geopolitical and systemic stress activates safe-haven mandates across institutional cohorts, generating correlated directional flows.",
        "typical_regimes": ["crisis_dislocation", "bull_trend"],
        "typical_failures": ["Overstay past safe-haven normalization", "Misidentification of stress type"],
        "expected_persistence": "MEDIUM",
        "capacity_expectation": "HIGH",
        "known_risks": ["Rapid de-risking reversal", "Competing safe-haven assets"],
        "confidence": 0.61,
    },
    {
        "family_id": "FAM-004",
        "name": "Cross-Asset Information Propagation",
        "definition": "Mechanisms driven by information flow through a directed cross-asset network topology.",
        "economic_rationale": "Directed source→relay→sink structure propagates institutional repricing with regime-dependent intensity.",
        "typical_regimes": ["macro_transition", "bull_trend", "range_compression"],
        "typical_failures": ["Topology disruption", "Relay bottleneck collapse"],
        "expected_persistence": "MEDIUM",
        "capacity_expectation": "MEDIUM",
        "known_risks": ["Data-gap limitations in current dataset", "Topology instability under rare events"],
        "confidence": 0.65,
    },
    {
        "family_id": "FAM-005",
        "name": "Expectation & Policy Reset",
        "definition": "Mechanisms driven by expectation updates, policy surprises, and belief cascade formation.",
        "economic_rationale": "Policy signals cause rapid expectation recalibration that propagates through fast-participant decision networks before slow-anchor actors reprice.",
        "typical_regimes": ["macro_transition", "bear_unwind", "calm_carry"],
        "typical_failures": ["Expectation reversal", "Policy surprise classification error"],
        "expected_persistence": "LOW",
        "capacity_expectation": "MEDIUM",
        "known_risks": ["Fed communication volatility", "Expectation anchoring by central banks"],
        "confidence": 0.58,
    },
    {
        "family_id": "FAM-006",
        "name": "Institutional Decision Cascade",
        "definition": "Mechanisms driven by structured participant decision cascades through strategic dependency networks.",
        "economic_rationale": "Fast institutional actors initiate decision chains that force constrained adjustments by slower actors.",
        "typical_regimes": ["macro_transition", "crisis_dislocation", "bull_trend"],
        "typical_failures": ["Cascade abort", "Strategic independence breakdown"],
        "expected_persistence": "LOW",
        "capacity_expectation": "MEDIUM",
        "known_risks": ["Macro-ecology model unresolved evidence per Program E"],
        "confidence": 0.57,
    },
    {
        "family_id": "FAM-007",
        "name": "Regime Transition & Adaptive Ecology",
        "definition": "Mechanisms driven by fundamental regime-state transitions and adaptive changes in market ecology.",
        "economic_rationale": "Regime transitions encode multi-channel institutional causal structures; ecology shifts redistribute flow-competition and cooperation.",
        "typical_regimes": ["macro_transition", "calm_carry", "crisis_dislocation"],
        "typical_failures": ["Transition timing mis-specification", "Ecology shift proxy weakness"],
        "expected_persistence": "MEDIUM",
        "capacity_expectation": "MEDIUM",
        "known_risks": ["Transition Engine v1 rejected", "Component redesign required per Program E"],
        "confidence": 0.56,
    },
]


# ---------------------------------------------------------------------------
# Feature and economic dimension descriptors (per mechanism type)
# ---------------------------------------------------------------------------

_MECHANISM_META: dict[str, dict[str, Any]] = {
    "cross_asset_transition":  {"family_id": "FAM-004", "core_driver": "cross_asset_relay", "primary_mechanism": "relay_pressure", "secondary_mechanism": "topology_reconfiguration", "feature_families": ["dxy_features", "yield_features", "macro_features"], "required_participants": ["dealers", "macro_hedge_funds", "market_makers"], "required_regime": ["macro_transition", "crisis_dislocation"], "info_source": "cross_asset_network", "causal_pathway": "source→relay→sink"},
    "macro_repricing":         {"family_id": "FAM-001", "core_driver": "macro_signal", "primary_mechanism": "relay_transmission", "secondary_mechanism": "rate_repricing", "feature_families": ["macro_features", "dxy_features", "yield_features"], "required_participants": ["macro_hedge_funds", "central_banks", "dealers"], "required_regime": ["macro_transition", "bear_unwind"], "info_source": "macro_announcements", "causal_pathway": "macro_shock→relay→xau"},
    "liquidity_withdrawal":    {"family_id": "FAM-002", "core_driver": "liquidity_stress", "primary_mechanism": "inventory_constraint", "secondary_mechanism": "forced_redistribution", "feature_families": ["vol_features", "price_features"], "required_participants": ["market_makers", "dealers", "commercial_hedgers"], "required_regime": ["crisis_dislocation", "bear_unwind"], "info_source": "volatility_signals", "causal_pathway": "liquidity_shock→inventory→price_impact"},
    "dealer_inventory":        {"family_id": "FAM-002", "core_driver": "dealer_constraint", "primary_mechanism": "inventory_redistribution", "secondary_mechanism": "hedger_offset", "feature_families": ["price_features", "vol_features", "yield_features"], "required_participants": ["dealers", "bullion_banks", "commercial_hedgers"], "required_regime": ["calm_carry", "bear_unwind"], "info_source": "positioning_proxies", "causal_pathway": "constraint_signal→redistribution→price"},
    "expectation_reset":       {"family_id": "FAM-005", "core_driver": "expectation_shift", "primary_mechanism": "belief_cascade", "secondary_mechanism": "anchor_repricing", "feature_families": ["macro_features", "dxy_features"], "required_participants": ["macro_hedge_funds", "market_makers", "etf_investors"], "required_regime": ["macro_transition", "range_compression"], "info_source": "forward_rates", "causal_pathway": "expectation_shock→fast_cascade→anchor_reprice"},
    "safe_haven_migration":    {"family_id": "FAM-003", "core_driver": "risk_off_stress", "primary_mechanism": "safe_haven_allocation", "secondary_mechanism": "topology_rewiring", "feature_families": ["macro_features", "dxy_features"], "required_participants": ["safe_haven_capital", "etf_investors", "central_banks"], "required_regime": ["crisis_dislocation", "bull_trend"], "info_source": "stress_topology", "causal_pathway": "stress_event→safe_haven_demand→price"},
    "etf_flow_propagation":    {"family_id": "FAM-004", "core_driver": "etf_flow", "primary_mechanism": "relay_amplification", "secondary_mechanism": "positioning_pressure", "feature_families": ["dxy_features", "price_features", "vol_features"], "required_participants": ["etf_investors", "market_makers", "dealers"], "required_regime": ["bull_trend", "range_compression"], "info_source": "flow_proxies", "causal_pathway": "etf_impulse→relay→positioning"},
    "policy_repricing":        {"family_id": "FAM-005", "core_driver": "policy_surprise", "primary_mechanism": "rate_shock", "secondary_mechanism": "fx_transmission", "feature_families": ["macro_features", "yield_features"], "required_participants": ["central_banks", "macro_hedge_funds", "dealers"], "required_regime": ["macro_transition", "bear_unwind"], "info_source": "fed_announcements", "causal_pathway": "policy_surprise→rate_shock→gold_reprice"},
    "decision_cascade":        {"family_id": "FAM-006", "core_driver": "cascade_initiator", "primary_mechanism": "strategic_dependency", "secondary_mechanism": "order_flow_impact", "feature_families": ["macro_features", "dxy_features"], "required_participants": ["macro_hedge_funds", "market_makers", "etf_investors"], "required_regime": ["macro_transition", "crisis_dislocation"], "info_source": "decision_ecology", "causal_pathway": "initiator_trigger→cascade→constrained_adjustment"},
    "information_cascade":     {"family_id": "FAM-004", "core_driver": "information_flow", "primary_mechanism": "directed_propagation", "secondary_mechanism": "regime_amplification", "feature_families": ["dxy_features", "macro_features"], "required_participants": ["macro_hedge_funds", "dealers", "market_makers"], "required_regime": ["macro_transition", "range_compression"], "info_source": "cross_asset_network", "causal_pathway": "source_signal→directed_edge→sink_reprice"},
    "adaptive_ecology_shift":  {"family_id": "FAM-007", "core_driver": "ecology_state", "primary_mechanism": "participant_role_rotation", "secondary_mechanism": "flow_path_rewiring", "feature_families": ["vol_features", "dxy_features", "yield_features"], "required_participants": ["dealers", "macro_hedge_funds", "commercial_hedgers"], "required_regime": ["calm_carry", "macro_transition"], "info_source": "ecology_model", "causal_pathway": "ecology_shift→flow_rewire→price_impact"},
    "regime_transition_chain": {"family_id": "FAM-007", "core_driver": "regime_state", "primary_mechanism": "transition_activation", "secondary_mechanism": "multi_channel_cascade", "feature_families": ["price_features", "macro_features", "dxy_features", "vol_features"], "required_participants": ["macro_hedge_funds", "central_banks", "dealers"], "required_regime": ["macro_transition"], "info_source": "regime_taxonomy", "causal_pathway": "trigger→participant→liquidity→activation"},
}


def _similarity_score(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    ma, mb = _MECHANISM_META[str(a["mechanism_type"])], _MECHANISM_META[str(b["mechanism_type"])]

    def _overlap(l1: list[str], l2: list[str]) -> float:
        s1, s2 = set(l1), set(l2)
        return len(s1 & s2) / max(1, len(s1 | s2))

    economic = 1.0 if ma["family_id"] == mb["family_id"] else 0.3 if ma["core_driver"] == mb["core_driver"] else 0.1
    feature = _overlap(cast(list[str], ma["feature_families"]), cast(list[str], mb["feature_families"]))
    regime = _overlap(cast(list[str], ma["required_regime"]), cast(list[str], mb["required_regime"]))
    cross_asset = 1.0 if ma["info_source"] == mb["info_source"] else 0.4 if ma["family_id"] == mb["family_id"] else 0.1
    participant = _overlap(cast(list[str], ma["required_participants"]), cast(list[str], mb["required_participants"]))
    failure = _overlap(cast(list[str], a["expected_failure_modes"]), cast(list[str], b["expected_failure_modes"]))
    lineage = _overlap(cast(list[str], a["institutional_lineage"]), cast(list[str], b["institutional_lineage"]))
    overall = round(0.20 * economic + 0.15 * feature + 0.15 * regime + 0.15 * cross_asset + 0.15 * participant + 0.10 * failure + 0.10 * lineage, 4)
    return {
        "economic_similarity": round(economic, 4),
        "feature_overlap": round(feature, 4),
        "regime_overlap": round(regime, 4),
        "cross_asset_overlap": round(cross_asset, 4),
        "participant_overlap": round(participant, 4),
        "failure_overlap": round(failure, 4),
        "lineage_overlap": round(lineage, 4),
        "overall_similarity": overall,
    }


def _similarity_matrix(mechanisms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ids = [str(m["alpha_id"]) for m in mechanisms]
    for i, a in enumerate(mechanisms):
        for j, b in enumerate(mechanisms):
            if j <= i:
                continue
            scores = _similarity_score(a, b)
            rows.append(
                {
                    "alpha_id_a": ids[i],
                    "alpha_id_b": ids[j],
                    "mechanism_a": a["mechanism_type"],
                    "mechanism_b": b["mechanism_type"],
                    **scores,
                }
            )
    return rows


def _cluster_mechanisms(mechanisms: list[dict[str, Any]]) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = {}
    for m in mechanisms:
        fam = str(_MECHANISM_META[str(m["mechanism_type"])]["family_id"])
        clusters.setdefault(fam, []).append(str(m["alpha_id"]))
    return clusters


def _redundancy_analysis(similarity_matrix: list[dict[str, Any]], mechanisms: list[dict[str, Any]]) -> dict[str, Any]:
    id_to_name = {str(m["alpha_id"]): str(m["name"]) for m in mechanisms}
    id_to_type = {str(m["alpha_id"]): str(m["mechanism_type"]) for m in mechanisms}

    near_duplicates: list[dict[str, Any]] = []
    specializations: list[dict[str, Any]] = []
    redundant: list[dict[str, Any]] = []

    for row in similarity_matrix:
        overall = float(row["overall_similarity"])
        economic = float(row["economic_similarity"])
        if overall >= 0.75:
            near_duplicates.append({
                "alpha_id_a": row["alpha_id_a"], "alpha_id_b": row["alpha_id_b"],
                "name_a": id_to_name[str(row["alpha_id_a"])], "name_b": id_to_name[str(row["alpha_id_b"])],
                "overall_similarity": overall, "verdict": "NEAR_DUPLICATE",
            })
            redundant.append(row)
        elif economic >= 0.9 and overall >= 0.55:
            specializations.append({
                "alpha_id_a": row["alpha_id_a"], "alpha_id_b": row["alpha_id_b"],
                "type_a": id_to_type[str(row["alpha_id_a"])], "type_b": id_to_type[str(row["alpha_id_b"])],
                "verdict": "SPECIALIZATION",
            })

    # merge candidates: same family, overall >= 0.6
    merge_candidates: list[dict[str, Any]] = []
    for row in similarity_matrix:
        ma = _MECHANISM_META[id_to_type[str(row["alpha_id_a"])]]
        mb = _MECHANISM_META[id_to_type[str(row["alpha_id_b"])]]
        if ma["family_id"] == mb["family_id"] and float(row["overall_similarity"]) >= 0.6:
            merge_candidates.append({
                "alpha_id_a": row["alpha_id_a"],
                "alpha_id_b": row["alpha_id_b"],
                "family_id": str(ma["family_id"]),
                "overall_similarity": row["overall_similarity"],
                "recommendation": "CONSIDER_MERGE",
            })

    return {
        "near_duplicates": near_duplicates,
        "specializations": specializations,
        "merge_candidates": merge_candidates,
        "redundant_pairs_count": len(redundant),
        "merge_candidate_count": len(merge_candidates),
        "independent_count": len(mechanisms) - len({p["alpha_id_a"] for p in near_duplicates}),
    }


def _research_priority_matrix(clusters: dict[str, list[str]], mechanisms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    id_to_m = {str(m["alpha_id"]): m for m in mechanisms}
    family_metrics: list[dict[str, Any]] = []
    fam_id_to_def = {f["family_id"]: f for f in ALPHA_FAMILIES}

    for fam_id, alpha_ids in clusters.items():
        fam_mechs = [id_to_m[aid] for aid in alpha_ids if aid in id_to_m]
        if not fam_mechs:
            continue
        fam = fam_id_to_def.get(fam_id, {"name": fam_id, "confidence": 0.5, "known_risks": []})
        avg_confidence = sum(float(m["confidence_prior"]) for m in fam_mechs) / len(fam_mechs)
        avg_novelty = sum(float(m["novelty_score"]) for m in fam_mechs) / len(fam_mechs)
        avg_info_gain = sum(float(m["expected_information_gain"]) for m in fam_mechs) / len(fam_mechs)
        avg_robustness = sum(float(m["expected_robustness"]) for m in fam_mechs) / len(fam_mechs)
        avg_cost = sum(float(m["research_cost"]) for m in fam_mechs) / len(fam_mechs)
        avg_failure = sum(float(m["failure_risk"]) for m in fam_mechs) / len(fam_mechs)
        avg_value = sum(float(m["expected_institutional_value"]) for m in fam_mechs) / len(fam_mechs)
        priority = round(
            0.20 * avg_confidence + 0.18 * avg_info_gain + 0.15 * avg_robustness
            + 0.12 * avg_novelty + 0.10 * avg_value - 0.08 * avg_cost - 0.07 * avg_failure,
            4,
        )
        family_metrics.append({
            "family_id": fam_id,
            "family_name": str(fam.get("name", fam_id)),
            "mechanism_count": len(fam_mechs),
            "avg_confidence": round(avg_confidence, 4),
            "avg_novelty": round(avg_novelty, 4),
            "avg_information_gain": round(avg_info_gain, 4),
            "avg_robustness": round(avg_robustness, 4),
            "avg_research_cost": round(avg_cost, 4),
            "avg_failure_risk": round(avg_failure, 4),
            "avg_institutional_value": round(avg_value, 4),
            "research_priority_score": priority,
            "alpha_ids": alpha_ids,
        })

    family_metrics.sort(key=lambda r: float(r["research_priority_score"]), reverse=True)
    for idx, row in enumerate(family_metrics, start=1):
        row["rank"] = idx
        row["priority_band"] = "P1" if idx <= 2 else "P2" if idx <= 4 else "P3"
    return family_metrics


def _validation_batch_plan(priority_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Design 3 balanced batches covering all families
    batches: list[dict[str, Any]] = []
    # Batch 1: P1 families — highest priority, independent mechanisms
    batch1_families = [r for r in priority_matrix if r["priority_band"] == "P1"]
    batch1_ids: list[str] = []
    for fam in batch1_families:
        batch1_ids.extend(cast(list[str], fam["alpha_ids"])[:1])  # one representative per family
    batches.append({
        "batch_id": "BATCH-001",
        "families": [r["family_id"] for r in batch1_families],
        "alpha_ids": batch1_ids,
        "rationale": "Highest-priority families; independent mechanism representatives.",
        "estimated_cycles": 4,
        "balanced_regimes": True,
        "representative_coverage": True,
    })
    # Batch 2: P2 families
    batch2_families = [r for r in priority_matrix if r["priority_band"] == "P2"]
    batch2_ids = []
    for fam in batch2_families:
        batch2_ids.extend(cast(list[str], fam["alpha_ids"])[:1])
    batches.append({
        "batch_id": "BATCH-002",
        "families": [r["family_id"] for r in batch2_families],
        "alpha_ids": batch2_ids,
        "rationale": "Medium-priority families; balanced regime/participant coverage.",
        "estimated_cycles": 4,
        "balanced_regimes": True,
        "representative_coverage": True,
    })
    # Batch 3: P3 families + remaining
    batch3_families = [r for r in priority_matrix if r["priority_band"] == "P3"]
    batch3_ids = []
    for fam in batch3_families:
        batch3_ids.extend(cast(list[str], fam["alpha_ids"]))
    batches.append({
        "batch_id": "BATCH-003",
        "families": [r["family_id"] for r in batch3_families],
        "alpha_ids": batch3_ids,
        "rationale": "Lower-priority families; secondary mechanisms and specializations.",
        "estimated_cycles": 3,
        "balanced_regimes": True,
        "representative_coverage": False,
    })
    return batches


def _graph_payload(clusters: dict[str, list[str]], taxonomy: list[dict[str, Any]]) -> dict[str, Any]:
    family_nodes = [
        {
            "node_id": f"IKROS-DC3P3-FAMILY-{fam['family_id'].replace('-', '')}",
            "label": str(fam["name"]),
            "node_type": "KNOWLEDGE_OBJECT",
            "confidence": float(fam["confidence"]),
        }
        for fam in taxonomy
    ]
    conclusion_node = {
        "node_id": "IKROS-DC3P3-CONCLUSION-20260802-0001",
        "label": "DC3 Phase 3 Institutional Alpha Taxonomy Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "confidence": 0.72,
    }
    edges: list[dict[str, Any]] = []
    fam_id_to_node: dict[str, str] = {}
    for fam, node in zip(taxonomy, family_nodes, strict=True):
        fam_id_to_node[str(fam["family_id"])] = str(node["node_id"])

    for fam_id, alpha_ids in clusters.items():
        fam_node_id = fam_id_to_node.get(fam_id, "")
        if fam_node_id:
            for aid in alpha_ids:
                edges.append({"source": aid, "target": fam_node_id, "relation": "RELATED_TO", "confidence": 0.65})
            edges.append({"source": fam_node_id, "target": conclusion_node["node_id"], "relation": "SUPPORTED_BY", "confidence": 0.70})

    return {
        "family_nodes": family_nodes,
        "conclusion_node": conclusion_node,
        "edges": edges,
    }


def prepare_dc3_phase3_taxonomy_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(".")
    registry_path = root / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program" / "dc3_institutional_alpha_registry.json"
    if not registry_path.exists():
        registry_path = Path(".") / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program" / "dc3_institutional_alpha_registry.json"

    import json  # noqa: PLC0415
    mechanisms = cast(list[dict[str, Any]], json.loads(registry_path.read_text(encoding="utf-8")))

    # Phase A: decomposition
    decomposition = [
        {
            "alpha_id": m["alpha_id"],
            "name": m["name"],
            "mechanism_type": m["mechanism_type"],
            **{k: v for k, v in _MECHANISM_META[str(m["mechanism_type"])].items()},
        }
        for m in mechanisms
    ]

    # Phase B: similarity matrix
    sim_matrix = _similarity_matrix(mechanisms)

    # Phase C: clustering
    clusters = _cluster_mechanisms(mechanisms)

    # Phase D: redundancy analysis
    redundancy = _redundancy_analysis(sim_matrix, mechanisms)

    # Phase E: taxonomy
    taxonomy = ALPHA_FAMILIES[:]

    # Phase F: research prioritization
    priority_matrix = _research_priority_matrix(clusters, mechanisms)

    # Phase G: validation batch plan
    batch_plan = _validation_batch_plan(priority_matrix)

    # Graph payload
    payload = _graph_payload(clusters, taxonomy)

    analysis: dict[str, Any] = {
        "phase": "DISCOVERY_CYCLE_3_PHASE_3",
        "title": "Institutional Alpha Taxonomy & Consolidation Program",
        "primary_question": "How many genuinely distinct economic alpha mechanisms exist among the discovered candidates?",
        "mechanism_count": len(mechanisms),
        "family_count": len(taxonomy),
        "mechanism_decomposition": decomposition,
        "similarity_matrix": sim_matrix,
        "mechanism_clusters": clusters,
        "redundancy_analysis": redundancy,
        "institutional_alpha_taxonomy": taxonomy,
        "alpha_family_registry": {fam["family_id"]: fam for fam in taxonomy},
        "research_priority_matrix": priority_matrix,
        "validation_batch_plan": batch_plan,
        "arb_recommendation": {
            "distinct_families": len(taxonomy),
            "independent_mechanisms": int(redundancy["independent_count"]),
            "redundant_pairs": int(redundancy["redundant_pairs_count"]),
            "merge_candidates": int(redundancy["merge_candidate_count"]),
            "validation_batches": len(batch_plan),
            "validate_now": False,
            "promote_now": False,
            "recommended_next_action": "Await ARB approval before Phase 4 Institutional Alpha Validation Execution.",
            "top_priority_families": [r["family_name"] for r in priority_matrix[:3]],
        },
        "ecology_knowledge_graph": payload,
    }

    out_dir = root / DC3_PHASE3_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc3_phase3_institutional_alpha_taxonomy.json", analysis)
    return analysis


def emit_dc3_phase3_taxonomy_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC3_PHASE3_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    taxonomy = cast(list[dict[str, Any]], analysis["institutional_alpha_taxonomy"])
    priority = cast(list[dict[str, Any]], analysis["research_priority_matrix"])
    sim_matrix = cast(list[dict[str, Any]], analysis["similarity_matrix"])
    redundancy = cast(dict[str, Any], analysis["redundancy_analysis"])
    batches = cast(list[dict[str, Any]], analysis["validation_batch_plan"])
    decomp = cast(list[dict[str, Any]], analysis["mechanism_decomposition"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])

    # Taxonomy
    tax_md = out_dir / "INSTITUTIONAL_ALPHA_TAXONOMY.md"
    tax_rows = [[f["family_id"], f["name"], f["expected_persistence"], f["confidence"]] for f in taxonomy]
    write_markdown(tax_md, f"# Institutional Alpha Taxonomy\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Family ID', 'Name', 'Persistence', 'Confidence'], tax_rows)}\n")
    written["institutional_alpha_taxonomy"] = str(tax_md)

    # Alpha Family Atlas
    atlas_md = out_dir / "ALPHA_FAMILY_ATLAS.md"
    atlas_rows = [[f["family_id"], f["name"], f["economic_rationale"], ", ".join(cast(list[str], f["typical_regimes"]))] for f in taxonomy]
    write_markdown(atlas_md, f"# Alpha Family Atlas\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Family ID', 'Name', 'Economic Rationale', 'Typical Regimes'], atlas_rows)}\n")
    written["alpha_family_atlas"] = str(atlas_md)

    # Mechanism Decomposition
    decomp_md = out_dir / "MECHANISM_DECOMPOSITION.md"
    decomp_rows = [[d["alpha_id"], d["name"], d["family_id"], d["core_driver"], d["primary_mechanism"]] for d in decomp]
    write_markdown(decomp_md, f"# Mechanism Decomposition\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Alpha ID', 'Name', 'Family', 'Core Driver', 'Primary Mechanism'], decomp_rows)}\n")
    written["mechanism_decomposition"] = str(decomp_md)

    # Similarity Matrix (top pairs)
    sim_md = out_dir / "MECHANISM_SIMILARITY_MATRIX.md"
    sorted_sim = sorted(sim_matrix, key=lambda r: float(r["overall_similarity"]), reverse=True)[:15]
    sim_rows = [[r["mechanism_a"], r["mechanism_b"], r["overall_similarity"], r["economic_similarity"], r["feature_overlap"]] for r in sorted_sim]
    write_markdown(sim_md, f"# Mechanism Similarity Matrix\n## Discovery Cycle 3 Phase 3 (top 15 pairs)\n\n{markdown_table(['Mechanism A', 'Mechanism B', 'Overall', 'Economic', 'Feature Overlap'], sim_rows)}\n")
    written["mechanism_similarity_matrix"] = str(sim_md)

    # Cluster Report
    cluster_md = out_dir / "MECHANISM_CLUSTER_REPORT.md"
    cluster_rows = [[fam_id, len(ids), ", ".join(ids)] for fam_id, ids in cast(dict[str, list[str]], analysis["mechanism_clusters"]).items()]
    write_markdown(cluster_md, f"# Mechanism Cluster Report\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Family ID', 'Count', 'Alpha IDs'], cluster_rows)}\n")
    written["mechanism_cluster_report"] = str(cluster_md)

    # Redundancy Analysis
    red_md = out_dir / "REDUNDANCY_ANALYSIS.md"
    write_markdown(
        red_md,
        f"""# Redundancy Analysis
## Discovery Cycle 3 Phase 3

- Near duplicates: {redundancy['redundant_pairs_count']}
- Merge candidates: {redundancy['merge_candidate_count']}
- Independent mechanisms: {redundancy['independent_count']}
""",
    )
    written["redundancy_analysis"] = str(red_md)

    # Consolidation Report
    cons_md = out_dir / "CONSOLIDATION_REPORT.md"
    merge_rows = [[r["alpha_id_a"], r["alpha_id_b"], r["family_id"], r["overall_similarity"], r["recommendation"]] for r in cast(list[dict[str, Any]], redundancy["merge_candidates"])]
    if merge_rows:
        write_markdown(cons_md, f"# Consolidation Report\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Alpha A', 'Alpha B', 'Family', 'Similarity', 'Recommendation'], merge_rows)}\n")
    else:
        write_markdown(cons_md, "# Consolidation Report\n## Discovery Cycle 3 Phase 3\n\nNo merge candidates identified; all mechanisms are sufficiently distinct at current evidence level.\n")
    written["consolidation_report"] = str(cons_md)

    # Validation Batch Plan
    batch_md = out_dir / "VALIDATION_BATCH_PLAN.md"
    batch_rows = [[b["batch_id"], ", ".join(cast(list[str], b["families"])), len(cast(list[str], b["alpha_ids"])), b["estimated_cycles"], b["rationale"]] for b in batches]
    write_markdown(batch_md, f"# Validation Batch Plan\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Batch ID', 'Families', 'Alpha Count', 'Est. Cycles', 'Rationale'], batch_rows)}\n")
    written["validation_batch_plan"] = str(batch_md)

    # Research Prioritization Matrix
    prio_md = out_dir / "RESEARCH_PRIORITIZATION_MATRIX.md"
    prio_rows = [[r["rank"], r["priority_band"], r["family_name"], r["research_priority_score"], r["avg_confidence"], r["avg_information_gain"]] for r in priority]
    write_markdown(prio_md, f"# Research Prioritization Matrix\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Rank', 'Band', 'Family', 'Priority Score', 'Avg Confidence', 'Avg Info Gain'], prio_rows)}\n")
    written["research_prioritization_matrix"] = str(prio_md)

    # Alpha Family Registry
    reg_md = out_dir / "INSTITUTIONAL_ALPHA_FAMILY_REGISTRY.md"
    reg_rows = [[f["family_id"], f["name"], f["capacity_expectation"], f["expected_persistence"], f["confidence"]] for f in taxonomy]
    write_markdown(reg_md, f"# Institutional Alpha Family Registry\n## Discovery Cycle 3 Phase 3\n\n{markdown_table(['Family ID', 'Name', 'Capacity', 'Persistence', 'Confidence'], reg_rows)}\n")
    written["institutional_alpha_family_registry"] = str(reg_md)

    # ARB Recommendation
    arb_md = out_dir / "ARB_RECOMMENDATION.md"
    gaps = "\n".join(f"- {g}" for g in [
        "Macro and decision-layer evidence remains conditional from Program E/F.",
        "External data gaps (VIX, S&P500, crude, FX pairs) remain structural constraints.",
        "Participant ecology layer proxies require redesign before Batch 2/3 validation.",
    ])
    top_fams = "\n".join(f"- {n}" for n in cast(list[str], arb["top_priority_families"]))
    write_markdown(
        arb_md,
        f"""# ARB Recommendation
## Discovery Cycle 3 Phase 3

- Distinct families: {arb['distinct_families']}
- Independent mechanisms: {arb['independent_mechanisms']}
- Redundant pairs: {arb['redundant_pairs']}
- Merge candidates: {arb['merge_candidates']}
- Validation batches designed: {arb['validation_batches']}
- Validate now: {arb['validate_now']}
- Promote now: {arb['promote_now']}

### Top Priority Families
{top_fams}

### Research Gaps
{gaps}

### Recommendation
{arb['recommended_next_action']}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    write_json(out_dir / "dc3_phase3_taxonomy_similarity_matrix.json", sim_matrix)
    written["similarity_json"] = str(out_dir / "dc3_phase3_taxonomy_similarity_matrix.json")
    write_json(out_dir / "dc3_phase3_alpha_family_registry.json", taxonomy)
    written["family_registry_json"] = str(out_dir / "dc3_phase3_alpha_family_registry.json")
    if campaign_result is not None:
        write_json(out_dir / "dc3_phase3_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc3_phase3_campaign_result.json")
    return written
