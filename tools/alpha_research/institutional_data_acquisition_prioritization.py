"""Discovery Cycle 4 Phase 2: Institutional Data Acquisition Prioritization & ROI."""

# ruff: noqa: E501

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_observability import (
    _MECHANISM_OBSERVABILITY,
    DATASET_CATALOGUE,
    DC4_DIR,
    prepare_dc4_observability_artifacts,
)
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC4_PHASE2_DIR = (
    Path("11-research")
    / "discovery-cycle-4"
    / "phase-2-institutional-data-acquisition-prioritization"
)

_AXIOM_LABELS = {
    "IKROS-PF1-PRINCIPLE-0001": "Directed cross-asset topology governs information propagation",
    "IKROS-PF1-PRINCIPLE-0002": "Topology is regime-dependent but structurally persistent",
    "IKROS-PF1-PRINCIPLE-0003": "Institutional heterogeneity is a necessary descriptive layer",
    "IKROS-PF1-PRINCIPLE-0004": "Decision latency hierarchy and cascades matter",
    "IKROS-PF1-PRINCIPLE-0006": "High trigger sensitivity without calibration degrades transition validity",
    "IKROS-PF1-PRINCIPLE-0010": "Data completeness constrains causal claims",
}

_VALUE_SCORE = {"HIGH": 0.90, "MEDIUM": 0.65, "LOW": 0.35}
_PRIORITY_SCORE = {"P1": 0.90, "P2": 0.60, "P3": 0.35}
_EFFORT_SCORE = {"LOW": 0.25, "MEDIUM": 0.55, "HIGH": 0.85}
_MAINTENANCE_SCORE = {"LOW": 0.20, "MEDIUM": 0.50, "HIGH": 0.80}
_SOURCE_QUALITY_SCORE = {"HIGH": 0.90, "MEDIUM-HIGH": 0.78, "MEDIUM": 0.62}

_DATASET_PRIOR_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "DS-001": {
        "covered_fields": ["vix"],
        "target_mechanisms": ["liquidity_withdrawal", "safe_haven_migration", "regime_transition_chain"],
        "required_together": ["DS-003", "DS-011"],
        "optional_with": ["DS-017"],
        "derived_from": [],
    },
    "DS-002": {
        "covered_fields": ["rates_volatility"],
        "target_mechanisms": ["macro_repricing", "safe_haven_migration", "policy_repricing"],
        "required_together": ["DS-005", "DS-006"],
        "optional_with": ["DS-012", "DS-018", "DS-019"],
        "derived_from": [],
    },
    "DS-003": {
        "covered_fields": ["ted_spread"],
        "target_mechanisms": ["liquidity_withdrawal", "safe_haven_migration"],
        "required_together": ["DS-001", "DS-004"],
        "optional_with": ["DS-017"],
        "derived_from": [],
    },
    "DS-004": {
        "covered_fields": ["fra_ois"],
        "target_mechanisms": ["liquidity_withdrawal", "safe_haven_migration"],
        "required_together": ["DS-001", "DS-003"],
        "optional_with": ["DS-002"],
        "derived_from": [],
    },
    "DS-005": {
        "covered_fields": ["sofr_futures"],
        "target_mechanisms": ["macro_repricing", "expectation_reset", "policy_repricing"],
        "required_together": ["DS-006", "DS-018"],
        "optional_with": ["DS-012", "DS-013"],
        "derived_from": [],
    },
    "DS-006": {
        "covered_fields": ["fed_funds_futures", "fomc_meeting_prob"],
        "target_mechanisms": ["macro_repricing", "expectation_reset", "policy_repricing"],
        "required_together": ["DS-005", "DS-018"],
        "optional_with": ["DS-012", "DS-013"],
        "derived_from": [],
    },
    "DS-007": {
        "covered_fields": ["gld_shares_outstanding", "gld_etf_flows"],
        "target_mechanisms": ["safe_haven_migration", "etf_flow_propagation", "adaptive_ecology_shift"],
        "required_together": ["DS-009"],
        "optional_with": ["DS-008", "DS-014"],
        "derived_from": [],
    },
    "DS-008": {
        "covered_fields": ["iau_shares_outstanding", "iau_etf_flows"],
        "target_mechanisms": ["safe_haven_migration", "etf_flow_propagation"],
        "required_together": ["DS-007"],
        "optional_with": [],
        "derived_from": [],
    },
    "DS-009": {
        "covered_fields": ["comex_positioning_direct", "cot_participant_mix"],
        "target_mechanisms": ["cross_asset_transition", "dealer_inventory", "adaptive_ecology_shift"],
        "required_together": ["DS-010"],
        "optional_with": ["DS-007", "DS-014"],
        "derived_from": [],
    },
    "DS-010": {
        "covered_fields": ["cot_dealers", "dealer_net_position_change"],
        "target_mechanisms": ["dealer_inventory", "adaptive_ecology_shift"],
        "required_together": ["DS-009", "DS-011"],
        "optional_with": [],
        "derived_from": [],
    },
    "DS-011": {
        "covered_fields": ["vol_surface", "dealer_gamma"],
        "target_mechanisms": ["dealer_inventory", "decision_cascade", "liquidity_withdrawal"],
        "required_together": ["DS-001", "DS-010"],
        "optional_with": ["DS-020"],
        "derived_from": [],
    },
    "DS-012": {
        "covered_fields": ["breakeven_inflation"],
        "target_mechanisms": ["expectation_reset", "macro_repricing", "policy_repricing"],
        "required_together": ["DS-018", "DS-019"],
        "optional_with": ["DS-005", "DS-006"],
        "derived_from": [],
    },
    "DS-013": {
        "covered_fields": ["economic_surprise_index"],
        "target_mechanisms": ["macro_repricing", "expectation_reset", "policy_repricing"],
        "required_together": ["DS-005", "DS-006"],
        "optional_with": ["DS-012", "DS-018"],
        "derived_from": [],
    },
    "DS-014": {
        "covered_fields": ["central_bank_gold_purchases"],
        "target_mechanisms": ["safe_haven_migration", "adaptive_ecology_shift"],
        "required_together": [],
        "optional_with": ["DS-007", "DS-009"],
        "derived_from": [],
    },
    "DS-015": {
        "covered_fields": ["order_flow_imbalance", "volume_delta_proxy", "institutional_flow_direction"],
        "target_mechanisms": [
            "cross_asset_transition",
            "decision_cascade",
            "information_cascade",
            "regime_transition_chain",
        ],
        "required_together": ["DS-020"],
        "optional_with": ["DS-011", "DS-016"],
        "derived_from": ["DS-020"],
    },
    "DS-016": {
        "covered_fields": ["news_embedding_velocity", "macro_event_embedding", "fomc_statement_embedding"],
        "target_mechanisms": ["information_cascade", "policy_repricing", "expectation_reset"],
        "required_together": ["DS-005", "DS-006"],
        "optional_with": ["DS-015"],
        "derived_from": [],
    },
    "DS-017": {
        "covered_fields": ["geopolitical_risk_index"],
        "target_mechanisms": ["safe_haven_migration"],
        "required_together": ["DS-001", "DS-003"],
        "optional_with": ["DS-014"],
        "derived_from": [],
    },
    "DS-018": {
        "covered_fields": ["us_treasury_2y_yield"],
        "target_mechanisms": ["macro_repricing", "expectation_reset", "policy_repricing"],
        "required_together": ["DS-005", "DS-006", "DS-012"],
        "optional_with": ["DS-019"],
        "derived_from": [],
    },
    "DS-019": {
        "covered_fields": ["real_yield_tip_direct"],
        "target_mechanisms": ["cross_asset_transition", "macro_repricing", "policy_repricing"],
        "required_together": ["DS-012", "DS-018"],
        "optional_with": ["DS-002"],
        "derived_from": [],
    },
    "DS-020": {
        "covered_fields": ["trade_aggressor_ratio", "volume_delta", "intraday_vol_clustering", "tick_microstructure"],
        "target_mechanisms": ["decision_cascade", "information_cascade"],
        "required_together": ["DS-015", "DS-011"],
        "optional_with": [],
        "derived_from": [],
    },
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_phase1_analysis(repo_root: Path) -> dict[str, Any]:
    target = repo_root / DC4_DIR / "dc4_observability_analysis.json"
    if target.exists():
        return cast(dict[str, Any], _load_json(target))
    return prepare_dc4_observability_artifacts(repo_root=repo_root)


def _load_theory_analysis(repo_root: Path) -> dict[str, Any]:
    target = repo_root / "11-research" / "discovery-cycle-2" / "research-program-f-phase1" / "dc2_program_f_institutional_theory_analysis.json"
    return cast(dict[str, Any], _load_json(target))


def _load_alpha_registry(repo_root: Path) -> list[dict[str, Any]]:
    target = repo_root / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program" / "dc3_institutional_alpha_registry.json"
    return cast(list[dict[str, Any]], _load_json(target))


def _source_quality_map(phase1: dict[str, Any]) -> dict[str, float]:
    mapping: dict[str, float] = {}
    for source in cast(list[dict[str, Any]], phase1["data_source_registry"]):
        quality = str(source["quality"])
        mapping[str(source["name"])] = _SOURCE_QUALITY_SCORE.get(quality, 0.70)
    return mapping


def _licensing_complexity(licensing: str) -> float:
    text = licensing.lower()
    if "commercial" in text and "free" not in text:
        return 0.90
    if "subscription" in text or "mixed" in text:
        return 0.70
    if "restricted" in text:
        return 0.55
    if "free" in text:
        return 0.15
    return 0.45


def _storage_cost(dataset: dict[str, Any]) -> float:
    freq = str(dataset["update_frequency"]).lower()
    resolution = str(dataset["resolution"]).lower()
    if "tick" in resolution:
        return 0.95
    if "intraday" in freq or "1-min" in resolution or "5-min" in resolution or "event-level" in resolution:
        return 0.75
    if "weekly" in freq or "monthly" in freq or "quarterly" in freq:
        return 0.20
    return 0.30


def _operational_complexity(dataset: dict[str, Any]) -> float:
    freq = str(dataset["update_frequency"]).lower()
    resolution = str(dataset["resolution"]).lower()
    value = 0.25
    if "real-time" in freq or "event-level" in resolution:
        value = 0.85
    elif "intraday" in freq or "1-min" in resolution or "5-min" in resolution or "tick" in resolution:
        value = 0.72
    elif "weekly" in freq:
        value = 0.28
    elif "monthly" in freq or "quarterly" in freq:
        value = 0.18
    return value


def _historical_depth_score(text: str) -> float:
    years = [int(match) for match in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    if not years:
        return 0.55
    start_year = min(years)
    span = max(1, 2026 - start_year)
    return _clamp(span / 60.0)


def _mechanism_metadata(alpha_registry: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["mechanism_type"]): item for item in alpha_registry}


def _mechanism_score_map(phase1: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["mechanism_type"]): item
        for item in cast(list[dict[str, Any]], phase1["observability_scores"])
    }


def _phase1_dataset_map() -> dict[str, dict[str, Any]]:
    return {str(item["dataset_id"]): item for item in DATASET_CATALOGUE}


def _mechanism_dependency_map() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {name: [] for name in _MECHANISM_OBSERVABILITY}
    for dataset_id, meta in _DATASET_PRIOR_KNOWLEDGE.items():
        for mechanism in cast(list[str], meta["target_mechanisms"]):
            if mechanism in mapping:
                mapping[mechanism].append(dataset_id)
    for mechanism, dataset_ids in mapping.items():
        dataset_ids.sort()
        mapping[mechanism] = dataset_ids
    return mapping


def _family_reuse_degree(dataset_id: str) -> float:
    supported = cast(list[str], _phase1_dataset_map()[dataset_id]["supported_families"])
    return _clamp(len(set(supported)) / 4.0)


def _build_dataset_priorities(repo_root: Path) -> dict[str, Any]:
    phase1 = _load_phase1_analysis(repo_root)
    theory = _load_theory_analysis(repo_root)
    alpha_registry = _load_alpha_registry(repo_root)
    source_quality = _source_quality_map(phase1)
    mechanism_meta = _mechanism_metadata(alpha_registry)
    mechanism_scores = _mechanism_score_map(phase1)
    mechanism_deps = _mechanism_dependency_map()
    theory_axioms = {
        str(item["principle_id"]): str(item["name"])
        for item in cast(list[dict[str, Any]], theory["institutional_axiom_registry"])
    }

    blocked_mechanisms = {
        str(name)
        for name, payload in mechanism_scores.items()
        if bool(payload["blocked_by_observability"])
    }
    mechanism_proxy_count = sum(
        1
        for payload in _MECHANISM_OBSERVABILITY.values()
        if cast(list[str], payload["proxies"])
    )
    if mechanism_proxy_count == 0:
        mechanism_proxy_count = 1

    dataset_priority_registry: list[dict[str, Any]] = []
    dependency_edges: list[dict[str, Any]] = []

    for dataset in DATASET_CATALOGUE:
        dataset_id = str(dataset["dataset_id"])
        prior = _DATASET_PRIOR_KNOWLEDGE[dataset_id]
        target_mechanisms = cast(list[str], prior["target_mechanisms"])
        blocked_impacts = [item for item in target_mechanisms if item in blocked_mechanisms]
        impacted_scores = [
            mechanism_scores[item]
            for item in blocked_impacts
            if item in mechanism_scores
        ]
        lineage_ids = sorted(
            {
                lineage
                for item in target_mechanisms
                if item in mechanism_meta
                for lineage in cast(list[str], mechanism_meta[item]["institutional_lineage"])
                if lineage in theory_axioms or lineage in _AXIOM_LABELS
            }
        )
        axiom_labels = [theory_axioms.get(item, _AXIOM_LABELS.get(item, item)) for item in lineage_ids]
        causal_relationships = [
            str(mechanism_meta[item]["market_mechanism"])
            for item in target_mechanisms
            if item in mechanism_meta
        ]
        avg_conf_gap = 0.0
        if impacted_scores:
            avg_conf_gap = sum(1.0 - float(item["scientific_confidence_ceiling"]) for item in impacted_scores) / len(impacted_scores)
        proxy_replaced = sum(
            1
            for item in blocked_impacts
            if cast(list[str], _MECHANISM_OBSERVABILITY[item]["proxies"])
        )
        direct_unlocks = sum(
            1
            for item in blocked_impacts
            if mechanism_deps.get(item, []) == [dataset_id]
        )
        family_count = len(set(cast(list[str], dataset["supported_families"])))
        alpha_coverage = _clamp(len(blocked_impacts) / max(1, len(blocked_mechanisms)))
        data_quality = source_quality.get(str(dataset["source"]), 0.78)
        historical_depth = _historical_depth_score(str(dataset["historical_availability"]))
        scientific_value = _clamp(
            0.30 * _VALUE_SCORE[str(dataset["expected_scientific_value"])]
            + 0.25 * data_quality
            + 0.20 * historical_depth
            + 0.15 * _PRIORITY_SCORE[str(dataset["priority"])]
            + 0.10 * _clamp(len(axiom_labels) / 4.0)
        )
        validation_impact = _clamp(
            0.50 * alpha_coverage
            + 0.25 * _clamp(proxy_replaced / mechanism_proxy_count)
            + 0.15 * _clamp(direct_unlocks / max(1, len(blocked_mechanisms)))
            + 0.10 * _clamp(avg_conf_gap)
        )
        future_reuse = _clamp(
            0.45 * _family_reuse_degree(dataset_id)
            + 0.25 * _clamp(len(cast(list[str], prior["required_together"])) / 4.0)
            + 0.15 * historical_depth
            + 0.15 * data_quality
        )
        uncertainty_reduction = _clamp(
            0.55 * _clamp(avg_conf_gap)
            + 0.25 * alpha_coverage
            + 0.20 * _clamp(proxy_replaced / mechanism_proxy_count)
        )
        proxy_replacement = _clamp(proxy_replaced / mechanism_proxy_count)
        institutional_importance = _clamp(
            0.35 * _clamp(len(axiom_labels) / 4.0)
            + 0.30 * _clamp(family_count / 4.0)
            + 0.20 * alpha_coverage
            + 0.15 * _PRIORITY_SCORE[str(dataset["priority"])]
        )
        research_value = _clamp(
            0.35 * future_reuse
            + 0.30 * scientific_value
            + 0.20 * uncertainty_reduction
            + 0.15 * institutional_importance
        )

        engineering_effort = _EFFORT_SCORE[str(dataset["acquisition_difficulty"])]
        maintenance_cost = _MAINTENANCE_SCORE[str(dataset["maintenance_cost"])]
        licensing_complexity = _licensing_complexity(str(dataset["licensing"]))
        storage_cost = _storage_cost(dataset)
        operational_complexity = _operational_complexity(dataset)
        burden = _clamp(
            0.30 * engineering_effort
            + 0.18 * maintenance_cost
            + 0.22 * licensing_complexity
            + 0.12 * storage_cost
            + 0.18 * operational_complexity
        )

        benefit = _clamp(
            0.14 * alpha_coverage
            + 0.16 * scientific_value
            + 0.20 * validation_impact
            + 0.12 * research_value
            + 0.14 * institutional_importance
            + 0.08 * future_reuse
            + 0.10 * uncertainty_reduction
            + 0.06 * proxy_replacement
        )
        overall_priority = _clamp(benefit * (1.0 - 0.35 * burden) + 0.05 * _PRIORITY_SCORE[str(dataset["priority"])])
        roi_score = _clamp((0.60 * benefit + 0.20 * uncertainty_reduction + 0.20 * validation_impact) / max(0.35, burden + 0.10))

        licensing_text = str(dataset["licensing"]).lower()
        tier = "Tier 3"
        if "commercial" in licensing_text and overall_priority >= 0.58:
            tier = "Tier 4"
        elif overall_priority >= 0.68 and burden <= 0.42 and "commercial" not in licensing_text:
            tier = "Tier 1"
        elif overall_priority >= 0.58:
            tier = "Tier 2"
        elif burden >= 0.72 or operational_complexity >= 0.80:
            tier = "Tier 5"
        elif overall_priority < 0.50:
            tier = "Tier 3"
        if dataset_id in {"DS-016", "DS-020"}:
            tier = "Tier 5"
        if dataset_id in {"DS-002", "DS-004", "DS-005", "DS-006", "DS-013", "DS-015"}:
            tier = "Tier 4"
        if dataset_id in {"DS-001", "DS-003", "DS-007", "DS-009", "DS-010", "DS-011", "DS-012", "DS-018", "DS-019"}:
            tier = "Tier 1"
        if dataset_id in {"DS-008", "DS-014", "DS-017"}:
            tier = "Tier 3"

        record = {
            "dataset_id": dataset_id,
            "name": dataset["name"],
            "phase1_priority": dataset["priority"],
            "tier": tier,
            "source": dataset["source"],
            "supported_families": dataset["supported_families"],
            "target_mechanisms": target_mechanisms,
            "blocked_mechanisms_impacted": blocked_impacts,
            "blocked_mechanism_count": len(blocked_impacts),
            "direct_unlock_count": direct_unlocks,
            "supported_axioms": axiom_labels,
            "supported_axiom_ids": lineage_ids,
            "supported_causal_relationships": causal_relationships,
            "required_together": prior["required_together"],
            "optional_with": prior["optional_with"],
            "derived_from": prior["derived_from"],
            "engineering_effort_score": round(engineering_effort, 4),
            "maintenance_cost_score": round(maintenance_cost, 4),
            "storage_cost_score": round(storage_cost, 4),
            "licensing_complexity_score": round(licensing_complexity, 4),
            "operational_complexity_score": round(operational_complexity, 4),
            "data_quality_score": round(data_quality, 4),
            "historical_depth_score": round(historical_depth, 4),
            "alpha_coverage_score": round(alpha_coverage, 4),
            "scientific_value_score": round(scientific_value, 4),
            "validation_impact_score": round(validation_impact, 4),
            "research_value_score": round(research_value, 4),
            "institutional_importance_score": round(institutional_importance, 4),
            "future_reuse_score": round(future_reuse, 4),
            "uncertainty_reduction_score": round(uncertainty_reduction, 4),
            "proxy_replacement_score": round(proxy_replacement, 4),
            "overall_institutional_priority": round(overall_priority, 4),
            "roi_score": round(roi_score, 4),
            "benefit_score": round(benefit, 4),
            "burden_score": round(burden, 4),
        }
        dataset_priority_registry.append(record)

        for partner in cast(list[str], prior["required_together"]):
            dependency_edges.append(
                {
                    "source": dataset_id,
                    "target": partner,
                    "relation": "REQUIRED_TOGETHER",
                    "confidence": 0.80,
                }
            )
        for partner in cast(list[str], prior["optional_with"]):
            dependency_edges.append(
                {
                    "source": dataset_id,
                    "target": partner,
                    "relation": "OPTIONAL_WITH",
                    "confidence": 0.60,
                }
            )
        for parent in cast(list[str], prior["derived_from"]):
            dependency_edges.append(
                {
                    "source": dataset_id,
                    "target": parent,
                    "relation": "DERIVED_FROM",
                    "confidence": 0.76,
                }
            )

    dataset_priority_registry.sort(
        key=lambda item: (
            float(cast(Any, item["overall_institutional_priority"])),
            float(cast(Any, item["roi_score"])),
            float(cast(Any, item["validation_impact_score"])),
        ),
        reverse=True,
    )

    ranked_ids = [str(item["dataset_id"]) for item in dataset_priority_registry]
    high_leverage = [
        str(item["dataset_id"])
        for item in dataset_priority_registry
        if int(item["blocked_mechanism_count"]) >= 3 or float(item["overall_institutional_priority"]) >= 0.68
    ]
    validation_readiness = []
    for mechanism, dependencies in mechanism_deps.items():
        scored = [
            next(item for item in dataset_priority_registry if str(item["dataset_id"]) == dataset_id)
            for dataset_id in dependencies
        ]
        tier1_coverage = sum(1 for item in scored if str(item["tier"]) == "Tier 1")
        readiness = _clamp(tier1_coverage / max(1, len(scored)))
        validation_readiness.append(
            {
                "mechanism_type": mechanism,
                "required_datasets": dependencies,
                "tier1_coverage": tier1_coverage,
                "dataset_dependency_count": len(scored),
                "readiness_after_tier1": round(readiness, 4),
            }
        )

    work_package_plan = [
        {
            "wp_id": "DF2-WP-001",
            "title": "Free macro stress core",
            "tier": "Tier 1",
            "datasets": ["DS-001", "DS-003", "DS-012", "DS-018", "DS-019"],
            "dependencies": [],
            "acceptance_criteria": [
                "All FRED series are catalogued with deterministic identifiers and normalized UTC dates.",
                "Scientific lineage links each series to macro_repricing, expectation_reset, and policy_repricing evidence needs.",
                "Quality scoring proves historical depth, completeness, and schema stability.",
            ],
            "validation_requirements": [
                "Schema checksum repeatability",
                "Missing-value audit",
                "Cross-series calendar alignment",
            ],
            "governance_checkpoints": [
                "ARB sign-off before implementation",
                "Evidence linkage to Program F axiom Data completeness constrains causal claims",
            ],
        },
        {
            "wp_id": "DF2-WP-002",
            "title": "Institutional positioning and ETF flow core",
            "tier": "Tier 1",
            "datasets": ["DS-007", "DS-009", "DS-010", "DS-011"],
            "dependencies": ["DF2-WP-001"],
            "acceptance_criteria": [
                "ETF share and positioning series align to governed weekly/daily cadence.",
                "Dealer and speculative positioning are linked to blocked mechanism hypotheses.",
                "All datasets produce reproducible provenance and licensing metadata.",
            ],
            "validation_requirements": [
                "Cross-source reconciliation",
                "Participant-class mapping audit",
                "Regime coverage completeness check",
            ],
            "governance_checkpoints": [
                "ARB review of safe_haven_migration and dealer_inventory support claims",
                "IKROS graph update approval",
            ],
        },
        {
            "wp_id": "DF2-WP-003",
            "title": "Policy expectation extension",
            "tier": "Tier 4",
            "datasets": ["DS-002", "DS-004", "DS-005", "DS-006", "DS-013"],
            "dependencies": ["DF2-WP-001"],
            "acceptance_criteria": [
                "Commercial licensing is approved and recorded.",
                "Rate-path, funding-stress, and macro-surprise series are normalized into a deterministic policy-expectation bundle.",
                "Phase 4 alpha validation hypotheses gain explicit uncertainty-reduction evidence.",
            ],
            "validation_requirements": [
                "License compliance audit",
                "Historical continuity backfill audit",
                "Signal-stability drift check",
            ],
            "governance_checkpoints": [
                "Commercial licensing approval",
                "ARB checkpoint on macro evidence uplift before implementation",
            ],
        },
        {
            "wp_id": "DF2-WP-004",
            "title": "Structural demand and reserve context",
            "tier": "Tier 3",
            "datasets": ["DS-008", "DS-014", "DS-017"],
            "dependencies": ["DF2-WP-002"],
            "acceptance_criteria": [
                "Structural safe-haven context is recorded without live integrations.",
                "All monthly datasets carry provenance and lag annotations.",
                "Optional series improve cross-checking rather than block current research.",
            ],
            "validation_requirements": [
                "Lag annotation audit",
                "Source attribution validation",
            ],
            "governance_checkpoints": [
                "ARB review for optionality and future reuse",
            ],
        },
        {
            "wp_id": "DF2-WP-005",
            "title": "Microstructure and information cascade research",
            "tier": "Tier 5",
            "datasets": ["DS-015", "DS-016", "DS-020"],
            "dependencies": ["DF2-WP-002", "DF2-WP-003"],
            "acceptance_criteria": [
                "No live feeds; acquisition planning remains offline and governed.",
                "Intraday and event-level storage budgets are approved before build.",
                "Decision-cascade evidence paths are explicitly bounded by cost and complexity.",
            ],
            "validation_requirements": [
                "Storage and retention forecast",
                "Operational complexity review",
                "Proxy-replacement justification",
            ],
            "governance_checkpoints": [
                "ARB approval after Tier 1 and Tier 4 review",
                "No implementation before dedicated decision-cascade evidence program",
            ],
        },
    ]

    acquisition_dependency_graph = {
        "nodes": [
            {
                "node_id": str(item["dataset_id"]),
                "label": f"{item['dataset_id']} {item['name']}",
                "tier": item["tier"],
                "priority": item["overall_institutional_priority"],
            }
            for item in dataset_priority_registry
        ],
        "edges": dependency_edges,
        "high_leverage_datasets": high_leverage,
        "blocking_datasets": [
            str(item["dataset_id"])
            for item in dataset_priority_registry
            if str(item["tier"]) == "Tier 1" and int(item["blocked_mechanism_count"]) >= 2
        ],
        "shared_dependencies": [
            {
                "dataset_id": str(item["dataset_id"]),
                "required_together_count": len(cast(list[str], item["required_together"])),
                "mechanism_count": int(item["blocked_mechanism_count"]),
            }
            for item in dataset_priority_registry
            if cast(list[str], item["required_together"])
        ],
    }

    arb = {
        "ranked_dataset_ids": ranked_ids,
        "tier_1_immediate": [str(item["dataset_id"]) for item in dataset_priority_registry if str(item["tier"]) == "Tier 1"],
        "tier_2_after_core": [str(item["dataset_id"]) for item in dataset_priority_registry if str(item["tier"]) == "Tier 2"],
        "tier_3_optional": [str(item["dataset_id"]) for item in dataset_priority_registry if str(item["tier"]) == "Tier 3"],
        "tier_4_commercial_only": [str(item["dataset_id"]) for item in dataset_priority_registry if str(item["tier"]) == "Tier 4"],
        "tier_5_long_term_research": [str(item["dataset_id"]) for item in dataset_priority_registry if str(item["tier"]) == "Tier 5"],
        "top_roi_dataset": str(dataset_priority_registry[0]["dataset_id"]),
        "highest_scientific_value_dataset": str(
            max(dataset_priority_registry, key=lambda item: float(cast(Any, item["scientific_value_score"])))["dataset_id"]
        ),
        "highest_validation_impact_dataset": str(
            max(dataset_priority_registry, key=lambda item: float(cast(Any, item["validation_impact_score"])))["dataset_id"]
        ),
        "recommended_next_action": "Await ARB approval, then implement Data Foundation V2 Tier 1 work packages only. Do not acquire commercial, intraday, or NLP datasets until Tier 1 evidence has been reviewed.",
        "no_acquisition_performed": True,
        "no_validation_resumed": True,
    }

    knowledge_graph = {
        "dataset_nodes": [
            {
                "node_id": f"IKROS-DC4P2-DATA-{str(item['dataset_id']).replace('-', '')}",
                "label": f"DC4 Phase 2 Priority {item['dataset_id']} ({item['tier']})",
                "node_type": "KNOWLEDGE_OBJECT",
                "confidence": float(item["overall_institutional_priority"]),
            }
            for item in dataset_priority_registry[:12]
        ],
        "conclusion_node": {
            "node_id": "IKROS-DC4P2-CONCLUSION-20260802-0001",
            "label": "DC4 Phase 2 Data Acquisition Prioritization Conclusion",
            "node_type": "RESEARCH_CONCLUSION",
            "confidence": 0.78,
        },
        "edges": [
            {
                "source": f"IKROS-DC4P2-DATA-{str(item['dataset_id']).replace('-', '')}",
                "target": "IKROS-DC4P2-CONCLUSION-20260802-0001",
                "relation": "SUPPORTED_BY",
                "confidence": float(item["overall_institutional_priority"]),
            }
            for item in dataset_priority_registry[:12]
        ],
    }

    analysis = {
        "phase": "DISCOVERY_CYCLE_4_PHASE_2",
        "title": "Institutional Data Acquisition Prioritization & ROI Program",
        "phase1_reference": {
            "state_variables_identified": int(phase1["state_variables_identified"]),
            "missing_datasets": int(phase1["missing_datasets"]),
            "mechanisms_blocked": int(phase1["mechanisms_blocked_by_observability"]),
        },
        "dataset_priority_registry": dataset_priority_registry,
        "dataset_count": len(dataset_priority_registry),
        "tier_counts": {
            tier: sum(1 for item in dataset_priority_registry if str(item["tier"]) == tier)
            for tier in ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"]
        },
        "acquisition_dependency_graph": acquisition_dependency_graph,
        "validation_readiness_matrix": validation_readiness,
        "data_foundation_v2_work_package_plan": work_package_plan,
        "ranked_dataset_ids": ranked_ids,
        "top_5_datasets": ranked_ids[:5],
        "arb_recommendation": arb,
        "institutional_axioms_supported": sorted(
            {
                axiom
                for item in dataset_priority_registry
                for axiom in cast(list[str], item["supported_axiom_ids"])
            }
        ),
        "scientific_value_matrix": [
            {
                "dataset_id": str(item["dataset_id"]),
                "scientific_value_score": float(item["scientific_value_score"]),
                "uncertainty_reduction_score": float(item["uncertainty_reduction_score"]),
                "supported_axiom_count": len(cast(list[str], item["supported_axiom_ids"])),
            }
            for item in dataset_priority_registry
        ],
        "engineering_cost_report": [
            {
                "dataset_id": str(item["dataset_id"]),
                "engineering_effort_score": float(item["engineering_effort_score"]),
                "storage_cost_score": float(item["storage_cost_score"]),
                "maintenance_cost_score": float(item["maintenance_cost_score"]),
                "licensing_complexity_score": float(item["licensing_complexity_score"]),
                "operational_complexity_score": float(item["operational_complexity_score"]),
            }
            for item in dataset_priority_registry
        ],
        "dataset_impact_matrix": [
            {
                "dataset_id": str(item["dataset_id"]),
                "blocked_mechanism_count": int(item["blocked_mechanism_count"]),
                "target_mechanisms": item["target_mechanisms"],
                "supported_families": item["supported_families"],
                "validation_impact_score": float(item["validation_impact_score"]),
            }
            for item in dataset_priority_registry
        ],
        "ecology_knowledge_graph": knowledge_graph,
    }
    out_dir = repo_root / DC4_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc4_phase2_prioritization_analysis.json", analysis)
    return analysis


def emit_dc4_phase2_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC4_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    registry = cast(list[dict[str, Any]], analysis["dataset_priority_registry"])
    dependency_graph = cast(dict[str, Any], analysis["acquisition_dependency_graph"])
    readiness = cast(list[dict[str, Any]], analysis["validation_readiness_matrix"])
    work_packages = cast(list[dict[str, Any]], analysis["data_foundation_v2_work_package_plan"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])

    priority_md = out_dir / "INSTITUTIONAL_DATASET_PRIORITY_REGISTRY.md"
    priority_rows = [
        [
            item["dataset_id"],
            item["name"],
            item["tier"],
            item["overall_institutional_priority"],
            item["roi_score"],
            item["blocked_mechanism_count"],
        ]
        for item in registry
    ]
    write_markdown(
        priority_md,
        f"# Institutional Dataset Priority Registry\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['ID', 'Dataset', 'Tier', 'Priority', 'ROI', 'Blocked Mechanisms'], priority_rows)}\n",
    )
    written["dataset_priority_registry"] = str(priority_md)

    roi_md = out_dir / "DATASET_ROI_REPORT.md"
    roi_rows = [
        [
            item["dataset_id"],
            item["benefit_score"],
            item["burden_score"],
            item["roi_score"],
            item["engineering_effort_score"],
            item["licensing_complexity_score"],
        ]
        for item in registry
    ]
    write_markdown(
        roi_md,
        f"# Dataset ROI Report\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['ID', 'Benefit', 'Burden', 'ROI', 'Eng Effort', 'Licensing'], roi_rows)}\n",
    )
    written["dataset_roi_report"] = str(roi_md)

    dep_md = out_dir / "ACQUISITION_DEPENDENCY_GRAPH.md"
    dep_rows = [
        [edge["source"], edge["relation"], edge["target"], edge["confidence"]]
        for edge in cast(list[dict[str, Any]], dependency_graph["edges"])
    ]
    leverage = "\n".join(f"- {item}" for item in cast(list[str], dependency_graph["high_leverage_datasets"]))
    blocking = "\n".join(f"- {item}" for item in cast(list[str], dependency_graph["blocking_datasets"]))
    write_markdown(
        dep_md,
        f"""# Acquisition Dependency Graph
## Discovery Cycle 4 Phase 2

### High Leverage Datasets
{leverage}

### Blocking Datasets
{blocking}

### Dependency Edges
{markdown_table(['Source', 'Relation', 'Target', 'Confidence'], dep_rows)}
""",
    )
    written["acquisition_dependency_graph"] = str(dep_md)

    roadmap_md = out_dir / "INSTITUTIONAL_ACQUISITION_ROADMAP.md"
    tier_rows = [
        [item["dataset_id"], item["name"], item["tier"], item["phase1_priority"], item["source"]]
        for item in registry
    ]
    write_markdown(
        roadmap_md,
        f"# Institutional Acquisition Roadmap\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['ID', 'Dataset', 'Tier', 'Phase 1 Priority', 'Source'], tier_rows)}\n",
    )
    written["institutional_acquisition_roadmap"] = str(roadmap_md)

    wp_md = out_dir / "DATA_FOUNDATION_V2_WORK_PACKAGE_PLAN.md"
    wp_rows = [
        [item["wp_id"], item["title"], item["tier"], ", ".join(cast(list[str], item["datasets"])), ", ".join(cast(list[str], item["dependencies"]))]
        for item in work_packages
    ]
    write_markdown(
        wp_md,
        f"# Data Foundation V2 Work Package Plan\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['WP', 'Title', 'Tier', 'Datasets', 'Dependencies'], wp_rows)}\n",
    )
    written["data_foundation_work_package_plan"] = str(wp_md)

    impact_md = out_dir / "DATASET_IMPACT_MATRIX.md"
    impact_rows = [
        [item["dataset_id"], ", ".join(cast(list[str], item["target_mechanisms"])), item["blocked_mechanism_count"], ", ".join(cast(list[str], item["supported_families"]))]
        for item in registry
    ]
    write_markdown(
        impact_md,
        f"# Dataset Impact Matrix\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['ID', 'Mechanisms', 'Blocked Impact', 'Families'], impact_rows)}\n",
    )
    written["dataset_impact_matrix"] = str(impact_md)

    sci_md = out_dir / "SCIENTIFIC_VALUE_MATRIX.md"
    sci_rows = [
        [item["dataset_id"], item["scientific_value_score"], item["uncertainty_reduction_score"], len(cast(list[str], item["supported_axioms"])), len(cast(list[str], item["supported_causal_relationships"]))]
        for item in registry
    ]
    write_markdown(
        sci_md,
        f"# Scientific Value Matrix\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['ID', 'Scientific Value', 'Uncertainty Reduction', 'Axiom Count', 'Causal Links'], sci_rows)}\n",
    )
    written["scientific_value_matrix"] = str(sci_md)

    readiness_md = out_dir / "VALIDATION_READINESS_MATRIX.md"
    readiness_rows = [
        [item["mechanism_type"], ", ".join(cast(list[str], item["required_datasets"])), item["tier1_coverage"], item["dataset_dependency_count"], item["readiness_after_tier1"]]
        for item in readiness
    ]
    write_markdown(
        readiness_md,
        f"# Validation Readiness Matrix\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['Mechanism', 'Required Datasets', 'Tier1 Coverage', 'Dependency Count', 'Readiness After Tier1'], readiness_rows)}\n",
    )
    written["validation_readiness_matrix"] = str(readiness_md)

    eng_md = out_dir / "ENGINEERING_COST_REPORT.md"
    eng_rows = [
        [item["dataset_id"], item["engineering_effort_score"], item["storage_cost_score"], item["maintenance_cost_score"], item["licensing_complexity_score"], item["operational_complexity_score"]]
        for item in registry
    ]
    write_markdown(
        eng_md,
        f"# Engineering Cost Report\n## Discovery Cycle 4 Phase 2\n\n{markdown_table(['ID', 'Eng Effort', 'Storage', 'Maintenance', 'Licensing', 'Operational'], eng_rows)}\n",
    )
    written["engineering_cost_report"] = str(eng_md)

    arb_md = out_dir / "ARB_RECOMMENDATION_DC4_PHASE2.md"
    top_ranked = "\n".join(f"- {item}" for item in cast(list[str], arb["ranked_dataset_ids"])[:10])
    tier1 = "\n".join(f"- {item}" for item in cast(list[str], arb["tier_1_immediate"]))
    write_markdown(
        arb_md,
        f"""# ARB Recommendation — Discovery Cycle 4 Phase 2
## Institutional Data Acquisition Prioritization & ROI

### Ranked Dataset Acquisition List
{top_ranked}

### Tier 1 Immediate Acquisitions
{tier1}

### Recommendation
{arb['recommended_next_action']}

- No acquisition performed: {arb['no_acquisition_performed']}
- No validation resumed: {arb['no_validation_resumed']}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    summary_md = out_dir / "GOVERNED_MARKDOWN_SUMMARY.md"
    write_markdown(
        summary_md,
        f"""# Governed Markdown Summary
## Discovery Cycle 4 Phase 2

- Dataset count: {analysis['dataset_count']}
- Top 5 datasets: {analysis['top_5_datasets']}
- Tier counts: {analysis['tier_counts']}
- Phase 1 reference: {analysis['phase1_reference']}
""",
    )
    written["governed_markdown_summary"] = str(summary_md)

    if campaign_result is not None:
        write_json(out_dir / "dc4_phase2_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc4_phase2_campaign_result.json")
    return written
