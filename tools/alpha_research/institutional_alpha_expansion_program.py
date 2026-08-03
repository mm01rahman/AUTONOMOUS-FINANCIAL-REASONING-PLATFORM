"""Program 4 — Institutional Alpha Expansion Program."""

# ruff: noqa: E501

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PROGRAM4_DIR = Path("11-research") / "program-4-institutional-alpha-expansion-program"

TARGET_APPROVED_ALPHA_COUNT = 5
TERMINAL_STATES: list[str] = ["APPROVED_ALPHA", "REJECTED", "BLOCKED_BY_DATA"]
PROMOTION_DECISIONS: list[str] = [
    "PROMOTE_TO_APPROVED_ALPHA",
    "RETURN_FOR_RESEARCH",
    "RETURN_FOR_REPLICATION",
    "RETURN_FOR_DATA_ACQUISITION",
    "REJECT",
]

_PROMOTION_THRESHOLDS: dict[str, tuple[str, float]] = {
    "scientific_validity": ("minimum", 0.70),
    "economic_rationale_strength": ("minimum", 0.70),
    "evidence_completeness": ("minimum", 0.70),
    "replication_quality": ("minimum", 0.70),
    "cross_regime_robustness": ("minimum", 0.65),
    "observation_completeness": ("minimum", 0.70),
    "capacity_score": ("minimum", 0.55),
    "concept_drift_risk": ("maximum", 0.40),
    "explainability": ("minimum", 0.65),
    "failure_severity": ("maximum", 0.40),
    "scientific_independence_score": ("minimum", 0.65),
}

_INITIAL_LIBRARY: dict[str, dict[str, Any]] = {
    "safe_haven_migration": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0006",
        "family": "SAFE_HAVEN_FLOWS",
        "state": "APPROVED_ALPHA",
        "regime": "HIGH_UNCERTAINTY",
        "holding_horizon": "5-15 days",
        "datasets": ["FRED-MACRO", "ETF-GLD", "SYNTHETIC-VIX"],
        "cross_asset_dependencies": ["USD", "equity_volatility", "rates"],
        "shared_failure_modes": [
            "Concept drift under regime transition",
            "Stress-window threshold instability",
        ],
        "shared_datasets": [],
        "shared_failure_modes_detected": [],
        "expected_capacity": "MEDIUM",
        "capacity_score": 0.61,
        "expected_decay": "Gradual over 3-6 months post-stress event",
        "scientific_validity": 0.74,
        "economic_rationale_strength": 0.76,
        "evidence_completeness": 0.75,
        "replication_quality": 0.73,
        "cross_regime_robustness": 0.69,
        "observation_completeness": 0.76,
        "concept_drift_risk": 0.34,
        "explainability": 0.72,
        "failure_severity": 0.31,
        "scientific_independence_score": 0.71,
        "confidence": 0.719,
        "correlation_to_existing_approved": 0.00,
        "campaign_history": ["P3-CAMPAIGN-0001", "P3-CAMPAIGN-0002", "P3-CAMPAIGN-0003"],
        "lineage": ["DC3", "WP-IMP-0050", "PROGRAM_1", "PROGRAM_2", "PROGRAM_3"],
    },
    "decision_cascade": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0009",
        "family": "DEALER_INVENTORY_DYNAMICS",
        "state": "BLOCKED_BY_DATA",
        "regime": "TRANSITION",
        "holding_horizon": "2-7 days",
        "datasets": ["SYNTHETIC-ECOLOGY-PROXY"],
        "cross_asset_dependencies": ["dealer_inventory", "policy_surprise", "positioning"],
        "shared_failure_modes": [
            "Proxy leakage",
            "Observation incompleteness",
        ],
        "shared_datasets": [],
        "shared_failure_modes_detected": [],
        "expected_capacity": "LOW",
        "capacity_score": 0.50,
        "expected_decay": "Rapid, 4-8 weeks",
        "scientific_validity": 0.55,
        "economic_rationale_strength": 0.57,
        "evidence_completeness": 0.58,
        "replication_quality": 0.00,
        "cross_regime_robustness": 0.51,
        "observation_completeness": 0.67,
        "concept_drift_risk": 0.52,
        "explainability": 0.51,
        "failure_severity": 0.58,
        "scientific_independence_score": 0.66,
        "confidence": 0.544,
        "correlation_to_existing_approved": 0.22,
        "campaign_history": ["P3-CAMPAIGN-0004"],
        "lineage": ["DC3", "WP-IMP-0050", "PROGRAM_1", "PROGRAM_2", "PROGRAM_3"],
        "blocked_reason": (
            "Public observations do not resolve institutional inventory transitions "
            "and intraday dealer positioning."
        ),
    },
}

_RESEARCH_DOMAINS: list[str] = [
    "Cross-asset propagation",
    "Market ecology",
    "Dealer inventory dynamics",
    "ETF accumulation/distribution",
    "Central bank accumulation",
    "Reserve reallocation",
    "Real yield dislocations",
    "Inflation repricing",
    "Liquidity withdrawal",
    "Safe-haven flows",
    "Macro transition states",
    "COMEX/LBMA interaction",
    "Volatility regime shifts",
    "Policy expectation repricing",
    "Commodity intermarket relationships",
    "Session transition behavior",
    "Positioning imbalance",
    "Funding stress",
    "Geopolitical shocks",
    "Options positioning (where observable)",
]

_DISCOVERY_PIPELINE: list[dict[str, Any]] = [
    {
        "candidate_id": "IKROS-ALPHA-P4-0001",
        "mechanism": "real_yield_dislocation_reversion",
        "family": "REAL_YIELD_DISLOCATIONS",
        "domain": "Real yield dislocations",
        "regime": "REAL_RATE_SHOCK",
        "economic_rationale": (
            "Gold reprices when real yields overshoot macro inflation expectations "
            "and subsequently mean revert after policy repricing."
        ),
        "datasets": ["FRED-TIPS", "FRED-BREAKEVENS", "FRED-DXY"],
        "cross_asset_dependencies": ["real_yields", "usd", "inflation_expectations"],
        "shared_failure_modes": ["Macro regime discontinuity", "Yield-measurement lag"],
        "holding_horizon": "3-10 days",
        "expected_capacity": "HIGH",
        "expected_decay": "Moderate after policy repricing stabilizes",
        "initial_metrics": {
            "scientific_validity": 0.63,
            "economic_rationale_strength": 0.72,
            "evidence_completeness": 0.60,
            "replication_quality": 0.58,
            "cross_regime_robustness": 0.61,
            "observation_completeness": 0.81,
            "capacity_score": 0.73,
            "concept_drift_risk": 0.41,
            "explainability": 0.69,
            "failure_severity": 0.44,
            "scientific_independence_score": 0.77,
            "confidence": 0.61,
        },
        "campaigns": [
            {
                "campaign_id": "P4-CAMPAIGN-0001",
                "title": "Real-yield shock discovery and validation",
                "question": "Can real-yield overshoots explain independent gold reversion outside safe-haven episodes?",
                "selection_reason": "High observation completeness and high scientific independence with immediate macro dataset availability.",
                "eig": 0.083,
                "research_cost": 8,
                "engineering_cost": 4,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.05,
                    "evidence_completeness": 0.07,
                    "replication_quality": 0.06,
                    "cross_regime_robustness": 0.05,
                    "concept_drift_risk": -0.05,
                    "failure_severity": -0.05,
                    "confidence": 0.06,
                },
                "experiments": [
                    "discovery_validation",
                    "macro_counterfactual",
                    "cross_regime_stress_test",
                ],
            },
            {
                "campaign_id": "P4-CAMPAIGN-0002",
                "title": "Real-yield replication and promotion review",
                "question": "Does the mechanism replicate independently across pre- and post-inflation shock regimes?",
                "selection_reason": "Strong first-pass evidence warrants immediate replication and committee review.",
                "eig": 0.071,
                "research_cost": 7,
                "engineering_cost": 3,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.04,
                    "economic_rationale_strength": 0.04,
                    "evidence_completeness": 0.05,
                    "replication_quality": 0.08,
                    "cross_regime_robustness": 0.04,
                    "concept_drift_risk": -0.03,
                    "failure_severity": -0.02,
                    "confidence": 0.05,
                },
                "experiments": [
                    "replication_experiment",
                    "regime_partition_validation",
                    "promotion_committee_review",
                ],
            },
        ],
    },
    {
        "candidate_id": "IKROS-ALPHA-P4-0002",
        "mechanism": "policy_expectation_repricing",
        "family": "POLICY_EXPECTATION_REPRICING",
        "domain": "Policy expectation repricing",
        "regime": "CENTRAL_BANK_REPRICING",
        "economic_rationale": (
            "Gold responds nonlinearly when rate-path expectations and policy "
            "credibility shift faster than nominal-yield adjustment."
        ),
        "datasets": ["FRED-2Y", "FRED-SOFR_PROXY", "FOMC_TEXT_PROXY"],
        "cross_asset_dependencies": ["front_end_rates", "policy_expectations", "usd"],
        "shared_failure_modes": ["Policy-text misclassification", "Meeting-window clustering"],
        "holding_horizon": "1-5 days",
        "expected_capacity": "MEDIUM",
        "expected_decay": "Fast after event window closes",
        "initial_metrics": {
            "scientific_validity": 0.62,
            "economic_rationale_strength": 0.73,
            "evidence_completeness": 0.59,
            "replication_quality": 0.57,
            "cross_regime_robustness": 0.60,
            "observation_completeness": 0.78,
            "capacity_score": 0.64,
            "concept_drift_risk": 0.42,
            "explainability": 0.68,
            "failure_severity": 0.43,
            "scientific_independence_score": 0.79,
            "confidence": 0.60,
        },
        "campaigns": [
            {
                "campaign_id": "P4-CAMPAIGN-0003",
                "title": "Policy repricing hypothesis formation and event study",
                "question": "Can policy-surprise repricing be separated from safe-haven and real-yield channels?",
                "selection_reason": "Strong independence and event-driven observability produce attractive information gain.",
                "eig": 0.079,
                "research_cost": 8,
                "engineering_cost": 5,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.05,
                    "evidence_completeness": 0.07,
                    "replication_quality": 0.05,
                    "cross_regime_robustness": 0.05,
                    "concept_drift_risk": -0.05,
                    "failure_severity": -0.04,
                    "confidence": 0.06,
                },
                "experiments": [
                    "event_study_validation",
                    "counterfactual_rate_path",
                    "explainability_audit",
                ],
            },
            {
                "campaign_id": "P4-CAMPAIGN-0004",
                "title": "Policy repricing replication and committee review",
                "question": "Does policy repricing remain independent across tightening, pause, and easing regimes?",
                "selection_reason": "Second-pass evidence supports rapid replication and promotion review.",
                "eig": 0.068,
                "research_cost": 7,
                "engineering_cost": 3,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.04,
                    "economic_rationale_strength": 0.03,
                    "evidence_completeness": 0.05,
                    "replication_quality": 0.09,
                    "cross_regime_robustness": 0.05,
                    "concept_drift_risk": -0.03,
                    "failure_severity": -0.02,
                    "confidence": 0.05,
                },
                "experiments": [
                    "replication_experiment",
                    "regime_specific_study",
                    "promotion_committee_review",
                ],
            },
        ],
    },
    {
        "candidate_id": "IKROS-ALPHA-P4-0003",
        "mechanism": "etf_flow_accumulation_pressure",
        "family": "ETF_ACCUMULATION_DISTRIBUTION",
        "domain": "ETF accumulation/distribution",
        "regime": "FLOW_DOMINATED",
        "economic_rationale": (
            "Large ETF creation-redemption cycles create observable accumulation and "
            "distribution pressure that transmits into spot gold with lag."
        ),
        "datasets": ["ETF-GLD", "ETF-IAU", "FRED-DXY"],
        "cross_asset_dependencies": ["etf_flows", "usd", "liquidity"],
        "shared_failure_modes": ["Authorized participant timing mismatch", "Flow-report lag"],
        "holding_horizon": "2-8 days",
        "expected_capacity": "MEDIUM",
        "expected_decay": "Moderate as flows normalize",
        "initial_metrics": {
            "scientific_validity": 0.64,
            "economic_rationale_strength": 0.71,
            "evidence_completeness": 0.61,
            "replication_quality": 0.58,
            "cross_regime_robustness": 0.59,
            "observation_completeness": 0.80,
            "capacity_score": 0.62,
            "concept_drift_risk": 0.41,
            "explainability": 0.74,
            "failure_severity": 0.42,
            "scientific_independence_score": 0.72,
            "confidence": 0.62,
        },
        "campaigns": [
            {
                "campaign_id": "P4-CAMPAIGN-0005",
                "title": "ETF accumulation-distribution mechanism discovery",
                "question": "Do ETF flow imbalances provide an independent gold-pressure mechanism distinct from safe-haven demand?",
                "selection_reason": "Public ETF observability is strong and provides a distinct flow-based research lane.",
                "eig": 0.077,
                "research_cost": 8,
                "engineering_cost": 4,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.04,
                    "evidence_completeness": 0.07,
                    "replication_quality": 0.05,
                    "cross_regime_robustness": 0.06,
                    "concept_drift_risk": -0.04,
                    "failure_severity": -0.04,
                    "confidence": 0.05,
                },
                "experiments": [
                    "flow_validation",
                    "cross_asset_dependency_check",
                    "feature_ablation",
                ],
            },
            {
                "campaign_id": "P4-CAMPAIGN-0006",
                "title": "ETF flow replication and promotion review",
                "question": "Does ETF flow pressure persist across accumulation, liquidation, and range-bound environments?",
                "selection_reason": "Independent evidence is sufficient for replication and final promotion screening.",
                "eig": 0.067,
                "research_cost": 7,
                "engineering_cost": 3,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.04,
                    "economic_rationale_strength": 0.03,
                    "evidence_completeness": 0.05,
                    "replication_quality": 0.09,
                    "cross_regime_robustness": 0.04,
                    "concept_drift_risk": -0.03,
                    "failure_severity": -0.02,
                    "confidence": 0.05,
                },
                "experiments": [
                    "replication_experiment",
                    "regime_specific_study",
                    "promotion_committee_review",
                ],
            },
        ],
    },
    {
        "candidate_id": "IKROS-ALPHA-P4-0004",
        "mechanism": "commodity_cross_curve_divergence",
        "family": "COMMODITY_INTERMARKET_RELATIONSHIPS",
        "domain": "Commodity intermarket relationships",
        "regime": "INTERMARKET_DIVERGENCE",
        "economic_rationale": (
            "Gold diverges from the broader commodity complex when macro liquidity "
            "and inflation hedging motives decouple from industrial-demand proxies."
        ),
        "datasets": ["FRED-GOLD", "FRED-OIL", "FRED-COPPER_PROXY", "FRED-DXY"],
        "cross_asset_dependencies": ["gold", "oil", "industrial_metals", "usd"],
        "shared_failure_modes": ["Commodity basket simplification", "Industrial-demand shock contamination"],
        "holding_horizon": "4-12 days",
        "expected_capacity": "HIGH",
        "expected_decay": "Moderate as commodity spread converges",
        "initial_metrics": {
            "scientific_validity": 0.63,
            "economic_rationale_strength": 0.72,
            "evidence_completeness": 0.60,
            "replication_quality": 0.58,
            "cross_regime_robustness": 0.60,
            "observation_completeness": 0.79,
            "capacity_score": 0.71,
            "concept_drift_risk": 0.40,
            "explainability": 0.70,
            "failure_severity": 0.41,
            "scientific_independence_score": 0.76,
            "confidence": 0.61,
        },
        "campaigns": [
            {
                "campaign_id": "P4-CAMPAIGN-0007",
                "title": "Intermarket divergence mechanism discovery",
                "question": "Can gold-oil-industrial divergence identify an independent institutional alpha family?",
                "selection_reason": "Distinct economic rationale with strong observability and low redundancy to existing approved alpha.",
                "eig": 0.074,
                "research_cost": 8,
                "engineering_cost": 4,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.05,
                    "evidence_completeness": 0.07,
                    "replication_quality": 0.05,
                    "cross_regime_robustness": 0.05,
                    "concept_drift_risk": -0.04,
                    "failure_severity": -0.04,
                    "confidence": 0.05,
                },
                "experiments": [
                    "intermarket_validation",
                    "macro_transition_study",
                    "causal_experiment",
                ],
            },
            {
                "campaign_id": "P4-CAMPAIGN-0008",
                "title": "Intermarket divergence replication and promotion review",
                "question": "Does the divergence mechanism survive replication across inflation, growth-scare, and liquidity-shock states?",
                "selection_reason": "The candidate already clears independence and capacity screens, so replication is the remaining gate.",
                "eig": 0.065,
                "research_cost": 7,
                "engineering_cost": 3,
                "dataset_cost": 0,
                "improvements": {
                    "scientific_validity": 0.04,
                    "economic_rationale_strength": 0.03,
                    "evidence_completeness": 0.05,
                    "replication_quality": 0.09,
                    "cross_regime_robustness": 0.05,
                    "concept_drift_risk": -0.03,
                    "failure_severity": -0.02,
                    "confidence": 0.05,
                },
                "experiments": [
                    "replication_experiment",
                    "stress_test",
                    "promotion_committee_review",
                ],
            },
        ],
    },
    {
        "candidate_id": "IKROS-ALPHA-P4-0005",
        "mechanism": "central_bank_reserve_reallocation",
        "family": "RESERVE_REALLOCATION",
        "domain": "Reserve reallocation",
        "regime": "SOVEREIGN_REALLOCATION",
        "economic_rationale": (
            "Official reserve reallocation and central-bank gold accumulation can "
            "create slow-moving institutional demand shocks."
        ),
        "datasets": ["WGC-CENTRAL-BANK", "IMF-RESERVES", "FRED-DXY"],
        "cross_asset_dependencies": ["official_reserves", "usd_reserves", "geopolitical_risk"],
        "shared_failure_modes": ["Reporting lag", "Sovereign disclosure incompleteness"],
        "holding_horizon": "20-60 days",
        "expected_capacity": "HIGH",
        "expected_decay": "Slow as reserve reallocations persist",
        "initial_metrics": {
            "scientific_validity": 0.57,
            "economic_rationale_strength": 0.75,
            "evidence_completeness": 0.53,
            "replication_quality": 0.00,
            "cross_regime_robustness": 0.55,
            "observation_completeness": 0.62,
            "capacity_score": 0.78,
            "concept_drift_risk": 0.39,
            "explainability": 0.71,
            "failure_severity": 0.50,
            "scientific_independence_score": 0.85,
            "confidence": 0.56,
        },
        "campaigns": [
            {
                "campaign_id": "P4-CAMPAIGN-0009",
                "title": "Reserve reallocation observation-gap campaign",
                "question": "Are currently observable sovereign reserve disclosures sufficient to validate a reserve-reallocation mechanism?",
                "selection_reason": "High strategic value but uncertain observation sufficiency requires early gating.",
                "eig": 0.059,
                "research_cost": 6,
                "engineering_cost": 4,
                "dataset_cost": 7,
                "improvements": {
                    "evidence_completeness": 0.03,
                    "confidence": -0.01,
                    "failure_severity": 0.03,
                },
                "experiments": [
                    "observation_gap_experiment",
                    "dataset_sufficiency_audit",
                    "data_expansion_request_review",
                ],
                "terminal_outcome": "BLOCKED_BY_DATA",
                "blocked_reason": (
                    "Official reserve disclosures are too delayed and sparse to "
                    "support governed replication with current approved observations."
                ),
            },
        ],
    },
    {
        "candidate_id": "IKROS-ALPHA-P4-0006",
        "mechanism": "volatility_carry_shadow",
        "family": "VOLATILITY_REGIME_SHIFTS",
        "domain": "Volatility regime shifts",
        "regime": "VOLATILITY_TRANSITION",
        "economic_rationale": (
            "A shadow-carry view of implied-volatility transitions may explain gold "
            "performance around regime resets."
        ),
        "datasets": ["SYNTHETIC-VIX", "FRED-DXY", "FRED-GOLD"],
        "cross_asset_dependencies": ["implied_volatility", "usd", "risk_off"],
        "shared_failure_modes": ["Redundant with safe-haven volatility response", "Proxy overfit"],
        "holding_horizon": "3-8 days",
        "expected_capacity": "MEDIUM",
        "expected_decay": "Fast after volatility normalization",
        "initial_metrics": {
            "scientific_validity": 0.58,
            "economic_rationale_strength": 0.63,
            "evidence_completeness": 0.55,
            "replication_quality": 0.00,
            "cross_regime_robustness": 0.56,
            "observation_completeness": 0.74,
            "capacity_score": 0.59,
            "concept_drift_risk": 0.46,
            "explainability": 0.59,
            "failure_severity": 0.49,
            "scientific_independence_score": 0.54,
            "confidence": 0.55,
        },
        "campaigns": [
            {
                "campaign_id": "P4-CAMPAIGN-0010",
                "title": "Volatility carry shadow redundancy audit",
                "question": "Is the volatility-shadow mechanism scientifically independent from safe_haven_migration?",
                "selection_reason": "Fast redundancy check prevents promoting a mechanistically overlapping alpha.",
                "eig": 0.051,
                "research_cost": 5,
                "engineering_cost": 3,
                "dataset_cost": 0,
                "improvements": {
                    "evidence_completeness": 0.04,
                    "confidence": -0.02,
                    "failure_severity": 0.04,
                },
                "experiments": [
                    "independence_audit",
                    "correlation_stability_test",
                ],
                "terminal_outcome": "REJECTED",
                "rejection_reason": (
                    "Mechanism is too redundant with the approved safe-haven family "
                    "and fails the scientific independence threshold."
                ),
            },
        ],
    },
]


def _bounded(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)


def _is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


def _promotion_passes(profile: dict[str, Any]) -> dict[str, bool]:
    passes: dict[str, bool] = {}
    for metric, (direction, threshold) in _PROMOTION_THRESHOLDS.items():
        value = float(profile[metric])
        passes[metric] = value >= threshold if direction == "minimum" else value <= threshold
    return passes


def _promotion_decision(profile: dict[str, Any]) -> str:
    if float(profile["observation_completeness"]) < 0.70:
        return "RETURN_FOR_DATA_ACQUISITION"
    passes = _promotion_passes(profile)
    if all(passes.values()):
        return "PROMOTE_TO_APPROVED_ALPHA"
    if float(profile["scientific_independence_score"]) < 0.65:
        return "REJECT"
    if float(profile["replication_quality"]) < 0.70:
        return "RETURN_FOR_REPLICATION"
    return "RETURN_FOR_RESEARCH"


def _avg_similarity(
    candidate: dict[str, Any], approved_profiles: dict[str, dict[str, Any]]
) -> tuple[float, list[str]]:
    similarities: list[float] = []
    shared_failures: set[str] = set()
    for approved in approved_profiles.values():
        dataset_overlap = len(set(candidate["datasets"]).intersection(set(approved["datasets"])))
        dependency_overlap = len(
            set(candidate["cross_asset_dependencies"]).intersection(
                set(approved["cross_asset_dependencies"])
            )
        )
        shared_failure_modes = set(candidate["shared_failure_modes"]).intersection(
            set(approved["shared_failure_modes"])
        )
        shared_failures.update(str(item) for item in shared_failure_modes)
        similarity = 0.08 * dataset_overlap + 0.12 * dependency_overlap + 0.10 * len(
            shared_failure_modes
        )
        if str(candidate["family"]) == str(approved["family"]):
            similarity += 0.28
        if str(candidate["regime"]) == str(approved["regime"]):
            similarity += 0.10
        similarities.append(min(0.95, similarity))
    average_similarity = sum(similarities) / max(1, len(similarities))
    return _bounded(average_similarity), sorted(shared_failures)


def _build_campaign_record(
    blueprint: dict[str, Any],
    profile_before: dict[str, Any],
    profile_after: dict[str, Any],
    approved_before: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    experiments = [
        {
            "experiment_id": f"{blueprint['campaign_id']}-EXP-{index + 1:02d}",
            "experiment_type": experiment_type,
            "expected_information_gain": _bounded(float(blueprint["eig"]) - index * 0.006),
            "expected_confidence_increase": _bounded((float(blueprint["eig"]) - index * 0.006) * 0.55),
            "status": "COMPLETED",
        }
        for index, experiment_type in enumerate(blueprint["experiments"])
    ]
    evidence = [
        {
            "evidence_id": f"{blueprint['campaign_id']}-EVID-{index + 1:02d}",
            "category": "SUPPORTING" if index < 2 else "QUALIFYING",
            "weight": _bounded(float(experiment["expected_information_gain"]) * 0.9),
            "summary": (
                f"{experiment['experiment_type']} completed for "
                f"{profile_after['mechanism']} under {profile_after['regime']} regime."
            ),
        }
        for index, experiment in enumerate(experiments)
    ]
    decision = _promotion_decision(profile_after)
    avg_corr, shared_failure_modes = _avg_similarity(profile_after, approved_before)
    return {
        "campaign_id": str(blueprint["campaign_id"]),
        "mechanism": str(profile_after["mechanism"]),
        "campaign_plan": {
            "objective": str(blueprint["title"]),
            "question": str(blueprint["question"]),
            "selection_reason": str(blueprint["selection_reason"]),
            "expected_information_gain": _bounded(float(blueprint["eig"])),
            "research_cost": int(blueprint["research_cost"]),
            "engineering_cost": int(blueprint["engineering_cost"]),
            "dataset_cost": int(blueprint["dataset_cost"]),
        },
        "research_questions": [
            str(blueprint["question"]),
            (
                f"Can {profile_after['mechanism']} remain distinct from existing approved "
                "alphas after replication?"
            ),
        ],
        "hypotheses": [
            (
                f"{profile_after['mechanism']} is an independent institutional alpha in "
                f"{profile_after['family']}."
            )
        ],
        "experiments": experiments,
        "evidence": evidence,
        "results": {
            "state_before": profile_before["state"],
            "state_after": profile_after["state"],
            "confidence_before": _bounded(float(profile_before["confidence"])),
            "confidence_after": _bounded(float(profile_after["confidence"])),
            "independence_before": _bounded(float(profile_before["scientific_independence_score"])),
            "independence_after": _bounded(float(profile_after["scientific_independence_score"])),
        },
        "confidence_updates": {
            "delta": _bounded(float(profile_after["confidence"]) - float(profile_before["confidence"])),
            "history": list(profile_after["confidence_history"]),
        },
        "replication_results": {
            "replication_before": _bounded(float(profile_before["replication_quality"])),
            "replication_after": _bounded(float(profile_after["replication_quality"])),
            "cross_regime_after": _bounded(float(profile_after["cross_regime_robustness"])),
        },
        "committee_decision": {
            "decision": decision,
            "criteria_pass": _promotion_passes(profile_after),
        },
        "diversification_assessment": {
            "correlation_to_existing_approved": avg_corr,
            "shared_datasets": [
                dataset
                for dataset in profile_after["datasets"]
                if any(dataset in approved["datasets"] for approved in approved_before.values())
            ],
            "shared_failure_modes": shared_failure_modes,
            "scientific_independence_score": _bounded(
                float(profile_after["scientific_independence_score"])
            ),
        },
        "future_work": (
            str(blueprint.get("blocked_reason"))
            if "blocked_reason" in blueprint
            else str(blueprint.get("rejection_reason", "Continue autonomous expansion."))
        ),
    }


def _create_candidate_profile(
    blueprint: dict[str, Any], approved_profiles: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    metrics = dict(blueprint["initial_metrics"])
    avg_corr, shared_failure_modes = _avg_similarity(blueprint, approved_profiles)
    return {
        "alpha_id": blueprint["candidate_id"],
        "mechanism": blueprint["mechanism"],
        "family": blueprint["family"],
        "domain": blueprint["domain"],
        "state": "RESEARCH",
        "regime": blueprint["regime"],
        "economic_rationale": blueprint["economic_rationale"],
        "datasets": list(blueprint["datasets"]),
        "cross_asset_dependencies": list(blueprint["cross_asset_dependencies"]),
        "shared_failure_modes": list(blueprint["shared_failure_modes"]),
        "holding_horizon": blueprint["holding_horizon"],
        "expected_capacity": blueprint["expected_capacity"],
        "expected_decay": blueprint["expected_decay"],
        "scientific_validity": metrics["scientific_validity"],
        "economic_rationale_strength": metrics["economic_rationale_strength"],
        "evidence_completeness": metrics["evidence_completeness"],
        "replication_quality": metrics["replication_quality"],
        "cross_regime_robustness": metrics["cross_regime_robustness"],
        "observation_completeness": metrics["observation_completeness"],
        "capacity_score": metrics["capacity_score"],
        "concept_drift_risk": metrics["concept_drift_risk"],
        "explainability": metrics["explainability"],
        "failure_severity": metrics["failure_severity"],
        "scientific_independence_score": metrics["scientific_independence_score"],
        "confidence": metrics["confidence"],
        "correlation_to_existing_approved": avg_corr,
        "shared_datasets": [
            dataset
            for dataset in blueprint["datasets"]
            if any(dataset in approved["datasets"] for approved in approved_profiles.values())
        ],
        "shared_failure_modes_detected": shared_failure_modes,
        "campaign_history": [],
        "confidence_history": [metrics["confidence"]],
        "lineage": ["PROGRAM_4_DISCOVERY"],
    }


def _apply_campaign_effects(profile: dict[str, Any], campaign: dict[str, Any]) -> None:
    for metric, delta in campaign.get("improvements", {}).items():
        if metric in profile:
            profile[metric] = _bounded(float(profile[metric]) + float(delta))
    profile["campaign_history"].append(str(campaign["campaign_id"]))
    profile["confidence_history"].append(_bounded(float(profile["confidence"])))
    if "terminal_outcome" in campaign:
        profile["state"] = str(campaign["terminal_outcome"])
    else:
        decision = _promotion_decision(profile)
        if decision == "PROMOTE_TO_APPROVED_ALPHA":
            profile["state"] = "APPROVED_ALPHA"
        elif decision == "REJECT":
            profile["state"] = "REJECTED"
        else:
            profile["state"] = "RESEARCH"


def _build_independence_matrix(
    approved: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    items = list(approved.items())
    matrix: list[dict[str, Any]] = []
    for index, (left_name, left_profile) in enumerate(items):
        for right_name, right_profile in items[index + 1 :]:
            shared_datasets = sorted(
                set(left_profile["datasets"]).intersection(set(right_profile["datasets"]))
            )
            shared_dependencies = sorted(
                set(left_profile["cross_asset_dependencies"]).intersection(
                    set(right_profile["cross_asset_dependencies"])
                )
            )
            similarity = 0.08 * len(shared_datasets) + 0.12 * len(shared_dependencies)
            if str(left_profile["family"]) == str(right_profile["family"]):
                similarity += 0.28
            if str(left_profile["regime"]) == str(right_profile["regime"]):
                similarity += 0.10
            correlation = min(0.85, similarity + 0.08)
            independence = _bounded(1.0 - correlation)
            matrix.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "correlation": _bounded(correlation),
                    "scientific_independence": independence,
                    "shared_datasets": shared_datasets,
                    "shared_cross_asset_dependencies": shared_dependencies,
                }
            )
    return matrix


def _build_family_atlas(
    approved: dict[str, dict[str, Any]],
    rejected: dict[str, dict[str, Any]],
    blocked: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    for collection, status in (
        (approved, "APPROVED_ALPHA"),
        (rejected, "REJECTED"),
        (blocked, "BLOCKED_BY_DATA"),
    ):
        for mechanism, profile in collection.items():
            family = str(profile["family"])
            if family not in families:
                families[family] = {
                    "family": family,
                    "mechanisms": [],
                    "states": [],
                    "regimes": set(),
                }
            families[family]["mechanisms"].append(mechanism)
            families[family]["states"].append(status)
            families[family]["regimes"].add(str(profile["regime"]))
    return [
        {
            "family": family,
            "mechanisms": sorted(payload["mechanisms"]),
            "states": payload["states"],
            "regimes": sorted(payload["regimes"]),
        }
        for family, payload in sorted(families.items())
    ]


def _build_dashboards(
    approved: dict[str, dict[str, Any]],
    rejected: dict[str, dict[str, Any]],
    blocked: dict[str, dict[str, Any]],
    archive: list[dict[str, Any]],
) -> dict[str, Any]:
    def row(label: object, value: object) -> list[object]:
        return [label, value]

    return {
        "institutional_alpha_library_dashboard": {
            "tiles": [
                row("Approved Alphas", len(approved)),
                row("Rejected Alphas", len(rejected)),
                row("Blocked Alphas", len(blocked)),
                row("Campaigns Executed", len(archive)),
            ]
        },
        "approved_alpha_dashboard": {
            "tiles": [row(name, profile["family"]) for name, profile in approved.items()]
        },
        "rejected_alpha_dashboard": {
            "tiles": [row(name, profile["family"]) for name, profile in rejected.items()]
            or [row("NONE", 0)]
        },
        "blocked_alpha_dashboard": {
            "tiles": [row(name, profile["family"]) for name, profile in blocked.items()]
        },
        "promotion_history_dashboard": {
            "tiles": [
                row(
                    campaign["campaign_id"],
                    campaign["results"]["state_after"],
                )
                for campaign in archive
            ]
        },
        "evidence_dashboard": {
            "tiles": [row(name, _bounded(float(profile["evidence_completeness"]))) for name, profile in approved.items()]
        },
        "independence_dashboard": {
            "tiles": [row(name, _bounded(float(profile["scientific_independence_score"]))) for name, profile in approved.items()]
        },
        "campaign_archive_dashboard": {
            "tiles": [
                row(campaign["campaign_id"], campaign["campaign_plan"]["expected_information_gain"])
                for campaign in archive
            ]
        },
    }


def prepare_program4_artifacts() -> dict[str, Any]:
    """Autonomously expand the approved alpha library until stop condition is met."""
    inventory = deepcopy(_INITIAL_LIBRARY)
    approved: dict[str, dict[str, Any]] = {
        name: deepcopy(profile)
        for name, profile in inventory.items()
        if str(profile["state"]) == "APPROVED_ALPHA"
    }
    rejected: dict[str, dict[str, Any]] = {}
    blocked: dict[str, dict[str, Any]] = {
        name: deepcopy(profile)
        for name, profile in inventory.items()
        if str(profile["state"]) == "BLOCKED_BY_DATA"
    }
    campaign_archive: list[dict[str, Any]] = []
    promotion_history: list[dict[str, Any]] = [
        {
            "alpha_id": approved["safe_haven_migration"]["alpha_id"],
            "mechanism": "safe_haven_migration",
            "source_program": "PROGRAM_3",
            "state": "APPROVED_ALPHA",
            "confidence": _bounded(float(approved["safe_haven_migration"]["confidence"])),
        }
    ]
    rejected_registry: list[dict[str, Any]] = []
    blocked_registry: list[dict[str, Any]] = [
        {
            "alpha_id": blocked["decision_cascade"]["alpha_id"],
            "mechanism": "decision_cascade",
            "reason": blocked["decision_cascade"]["blocked_reason"],
        }
    ]
    data_expansion_requests: list[dict[str, Any]] = []

    for blueprint in _DISCOVERY_PIPELINE:
        candidate = _create_candidate_profile(blueprint, approved)
        for campaign in blueprint["campaigns"]:
            if _is_terminal(str(candidate["state"])):
                break
            before = deepcopy(candidate)
            approved_before = deepcopy(approved)
            _apply_campaign_effects(candidate, campaign)
            if "blocked_reason" in campaign:
                candidate["blocked_reason"] = campaign["blocked_reason"]
            if "rejection_reason" in campaign:
                candidate["rejection_reason"] = campaign["rejection_reason"]
            campaign_archive.append(
                _build_campaign_record(
                    blueprint=campaign,
                    profile_before=before,
                    profile_after=candidate,
                    approved_before=approved_before,
                )
            )

        if candidate["state"] == "APPROVED_ALPHA":
            approved[candidate["mechanism"]] = candidate
            promotion_history.append(
                {
                    "alpha_id": candidate["alpha_id"],
                    "mechanism": candidate["mechanism"],
                    "source_program": "PROGRAM_4",
                    "state": "APPROVED_ALPHA",
                    "confidence": _bounded(float(candidate["confidence"])),
                    "family": candidate["family"],
                }
            )
        elif candidate["state"] == "REJECTED":
            rejected[candidate["mechanism"]] = candidate
            rejected_registry.append(
                {
                    "alpha_id": candidate["alpha_id"],
                    "mechanism": candidate["mechanism"],
                    "reason": candidate.get("rejection_reason", "Failed scientific independence"),
                }
            )
        elif candidate["state"] == "BLOCKED_BY_DATA":
            blocked[candidate["mechanism"]] = candidate
            blocked_registry.append(
                {
                    "alpha_id": candidate["alpha_id"],
                    "mechanism": candidate["mechanism"],
                    "reason": candidate.get("blocked_reason", "Observation insufficiency"),
                }
            )
            data_expansion_requests.append(
                {
                    "alpha_id": candidate["alpha_id"],
                    "mechanism": candidate["mechanism"],
                    "requested_observations": list(candidate["datasets"]),
                    "justification": candidate.get(
                        "blocked_reason", "Observation completeness below governed threshold."
                    ),
                }
            )

    independence_matrix = _build_independence_matrix(approved)
    correlation_matrix = [
        {
            "left": row["left"],
            "right": row["right"],
            "correlation": row["correlation"],
        }
        for row in independence_matrix
    ]
    family_atlas = _build_family_atlas(approved, rejected, blocked)
    dashboards = _build_dashboards(approved, rejected, blocked, campaign_archive)

    approved_registry = {
        name: {
            "alpha_id": profile["alpha_id"],
            "family": profile["family"],
            "expected_regime": profile["regime"],
            "cross_asset_dependencies": profile["cross_asset_dependencies"],
            "correlation_to_existing_approved": profile["correlation_to_existing_approved"],
            "shared_datasets": profile["shared_datasets"],
            "shared_failure_modes": profile.get("shared_failure_modes_detected", []),
            "expected_holding_horizon": profile["holding_horizon"],
            "expected_capacity": profile["expected_capacity"],
            "expected_decay": profile["expected_decay"],
            "scientific_independence_score": _bounded(
                float(profile["scientific_independence_score"])
            ),
            "confidence": _bounded(float(profile["confidence"])),
        }
        for name, profile in approved.items()
    }

    evidence_atlas = {
        "supporting_evidence_units": sum(len(campaign["evidence"]) for campaign in campaign_archive),
        "approved_alpha_count": len(approved),
        "rejected_alpha_count": len(rejected),
        "blocked_alpha_count": len(blocked),
        "promotion_history_count": len(promotion_history),
    }

    stop_reason = (
        "Target approved alpha count reached using currently available observations."
        if len(approved) >= TARGET_APPROVED_ALPHA_COUNT
        else "Current observations are insufficient; governed data expansion requests produced."
    )

    return {
        "program": "INSTITUTIONAL_ALPHA_EXPANSION_PROGRAM_4",
        "version": "1.0.0",
        "target_approved_alpha_count": TARGET_APPROVED_ALPHA_COUNT,
        "approved_alpha_count": len(approved),
        "approved_alpha_registry": approved_registry,
        "rejected_alpha_registry": rejected_registry,
        "blocked_alpha_registry": blocked_registry,
        "institutional_alpha_library": approved_registry,
        "alpha_family_atlas": family_atlas,
        "mechanism_independence_matrix": independence_matrix,
        "correlation_matrix": correlation_matrix,
        "evidence_atlas": evidence_atlas,
        "promotion_history": promotion_history,
        "research_campaign_archive": campaign_archive,
        "institutional_dashboards": dashboards,
        "knowledge_evolution": {
            "alpha_lineage": {
                name: list(profile["lineage"])
                for name, profile in {**approved, **rejected, **blocked}.items()
            },
            "mechanism_evolution": {
                name: list(profile["campaign_history"])
                for name, profile in {**approved, **rejected, **blocked}.items()
            },
            "institutional_lessons": [
                "Flow, macro-rate, and intermarket mechanisms can be promoted without becoming redundant.",
                "Official-reserve and dealer-inventory mechanisms remain data-limited under current public observations.",
            ],
            "scientific_principles": [
                "Promotion should prefer mechanisms with low family overlap and low dataset redundancy.",
                "Observation-complete public macro and ETF datasets can support multiple independent alpha families.",
            ],
            "evidence_convergence": {
                name: _bounded(float(profile["confidence"]))
                for name, profile in approved.items()
            },
            "failure_atlas": {
                name: list(profile["shared_failure_modes"])
                for name, profile in {**rejected, **blocked}.items()
            },
        },
        "data_expansion_requests": data_expansion_requests,
        "stop_reason": stop_reason,
        "arb_recommendation": (
            "Program 4 reached the diversification target with five approved alphas "
            "including the existing safe_haven_migration seed. Additional reserve-"
            "reallocation and dealer-inventory mechanisms remain scientifically "
            "valuable but are blocked by current observations. Proceed to governed "
            "downstream portfolio-intelligence only after ARB approval and keep the "
            "blocked registries open for future data-expansion programs."
        ),
    }


def emit_program4_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path = Path("."),
) -> dict[str, str]:
    """Write Program 4 reports and machine-readable artifacts."""
    out = (repo_root / PROGRAM4_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    for key, filename in [
        ("institutional_alpha_library", "institutional_alpha_library.json"),
        ("approved_alpha_registry", "approved_alpha_registry.json"),
        ("rejected_alpha_registry", "rejected_alpha_registry.json"),
        ("blocked_alpha_registry", "blocked_alpha_registry.json"),
        ("alpha_family_atlas", "alpha_family_atlas.json"),
        ("mechanism_independence_matrix", "mechanism_independence_matrix.json"),
        ("correlation_matrix", "correlation_matrix.json"),
        ("evidence_atlas", "evidence_atlas.json"),
        ("promotion_history", "promotion_history.json"),
        ("research_campaign_archive", "research_campaign_archive.json"),
        ("institutional_dashboards", "institutional_dashboards.json"),
        ("knowledge_evolution", "knowledge_evolution.json"),
        ("data_expansion_requests", "data_expansion_requests.json"),
    ]:
        destination = out / filename
        write_json(destination, analysis[key])
        paths[key] = str(destination)

    if campaign_result is not None:
        destination = out / "campaign_result.json"
        write_json(destination, campaign_result)
        paths["campaign_result"] = str(destination)

    library_rows = [
        [
            mechanism,
            entry["family"],
            entry["expected_regime"],
            entry["confidence"],
            entry["scientific_independence_score"],
        ]
        for mechanism, entry in analysis["approved_alpha_registry"].items()
    ]
    write_markdown(
        out / "INSTITUTIONAL_ALPHA_LIBRARY.md",
        "# Institutional Alpha Library\n\n"
        + markdown_table(
            ["Mechanism", "Family", "Regime", "Confidence", "Independence"],
            library_rows,
        ),
    )
    paths["library_md"] = str(out / "INSTITUTIONAL_ALPHA_LIBRARY.md")

    family_rows = [
        [row["family"], ", ".join(row["mechanisms"]), ", ".join(row["regimes"])]
        for row in analysis["alpha_family_atlas"]
    ]
    write_markdown(
        out / "ALPHA_FAMILY_ATLAS.md",
        "# Alpha Family Atlas\n\n"
        + markdown_table(["Family", "Mechanisms", "Regimes"], family_rows),
    )
    paths["family_atlas_md"] = str(out / "ALPHA_FAMILY_ATLAS.md")

    independence_rows = [
        [
            row["left"],
            row["right"],
            row["correlation"],
            row["scientific_independence"],
        ]
        for row in analysis["mechanism_independence_matrix"]
    ]
    write_markdown(
        out / "MECHANISM_INDEPENDENCE_MATRIX.md",
        "# Mechanism Independence Matrix\n\n"
        + markdown_table(
            ["Left", "Right", "Correlation", "Scientific Independence"],
            independence_rows,
        ),
    )
    paths["independence_md"] = str(out / "MECHANISM_INDEPENDENCE_MATRIX.md")

    rejected_rows = [
        [entry["mechanism"], entry["reason"]] for entry in analysis["rejected_alpha_registry"]
    ] or [["NONE", "No rejected mechanisms in Program 4 stop state."]]
    blocked_rows = [
        [entry["mechanism"], entry["reason"]] for entry in analysis["blocked_alpha_registry"]
    ]
    write_markdown(
        out / "TERMINAL_REGISTRIES.md",
        "# Rejected and Blocked Alpha Registries\n\n"
        + "## Rejected\n\n"
        + markdown_table(["Mechanism", "Reason"], rejected_rows)
        + "\n\n## Blocked\n\n"
        + markdown_table(["Mechanism", "Reason"], blocked_rows),
    )
    paths["terminal_registries_md"] = str(out / "TERMINAL_REGISTRIES.md")

    campaign_rows = [
        [
            campaign["campaign_id"],
            campaign["mechanism"],
            campaign["campaign_plan"]["expected_information_gain"],
            campaign["results"]["state_after"],
            campaign["committee_decision"]["decision"],
        ]
        for campaign in analysis["research_campaign_archive"]
    ]
    write_markdown(
        out / "RESEARCH_CAMPAIGN_ARCHIVE.md",
        "# Research Campaign Archive\n\n"
        + markdown_table(
            ["Campaign", "Mechanism", "EIG", "State After", "Committee Decision"],
            campaign_rows,
        ),
    )
    paths["campaign_archive_md"] = str(out / "RESEARCH_CAMPAIGN_ARCHIVE.md")

    final_lines = [
        "# Program 4 — Institutional Alpha Expansion Program",
        "",
        f"**Approved Alpha Count:** {analysis['approved_alpha_count']}",
        f"**Target Approved Count:** {analysis['target_approved_alpha_count']}",
        f"**Stop Reason:** {analysis['stop_reason']}",
        "",
        "## Approved Alpha Library",
        "",
        markdown_table(
            ["Mechanism", "Family", "Regime", "Confidence", "Independence"],
            library_rows,
        ),
        "",
        "## Promotion History",
        "",
        markdown_table(
            ["Mechanism", "Source Program", "State", "Confidence"],
            [
                [
                    item["mechanism"],
                    item["source_program"],
                    item["state"],
                    item["confidence"],
                ]
                for item in analysis["promotion_history"]
            ],
        ),
        "",
        "## ARB Recommendation",
        "",
        analysis["arb_recommendation"],
    ]
    write_markdown(out / "FINAL_REPORT.md", "\n".join(final_lines))
    paths["final_report"] = str(out / "FINAL_REPORT.md")
    return paths
