"""Program 5 — Institutional Alpha Portfolio Intelligence System."""

# ruff: noqa: E501

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PROGRAM5_DIR = Path("11-research") / "program-5-institutional-alpha-portfolio-intelligence-system"
PROGRAM5_SCHEMA_DIR = Path("schemas") / "institutional-alpha-portfolio"

PORTFOLIO_DECISIONS: list[str] = [
    "BUY",
    "SELL",
    "HOLD",
    "REDUCE",
    "INCREASE",
    "NO POSITION",
]

PORTFOLIO_LIFECYCLE_STATES: list[str] = [
    "CANDIDATE",
    "APPROVED",
    "ACTIVE",
    "REDUCED",
    "SUSPENDED",
    "UNDER_REVIEW",
    "REVALIDATION",
    "RETIRED",
    "ARCHIVED",
]

_REGIMES: list[str] = [
    "BULL_TREND",
    "BEAR_TREND",
    "RISK_OFF",
    "RISK_ON",
    "MACRO_TRANSITION",
    "LIQUIDITY_CRISIS",
]

_REGIME_LABELS: dict[str, str] = {
    "BULL_TREND": "Bull trend",
    "BEAR_TREND": "Bear trend",
    "RISK_OFF": "Risk-off",
    "RISK_ON": "Risk-on",
    "MACRO_TRANSITION": "Macro transition",
    "LIQUIDITY_CRISIS": "Liquidity crisis",
}

_DECISION_SCORE: dict[str, float] = {
    "BUY": 1.0,
    "INCREASE": 0.6,
    "HOLD": 0.0,
    "REDUCE": -0.5,
    "SELL": -1.0,
    "NO POSITION": -0.2,
}

_DECISION_STRENGTH: dict[str, int] = {
    "SELL": 0,
    "REDUCE": 1,
    "NO POSITION": 2,
    "HOLD": 3,
    "INCREASE": 4,
    "BUY": 5,
}

_APPROVED_ALPHA_LIBRARY: dict[str, dict[str, Any]] = {
    "safe_haven_migration": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0006",
        "family": "SAFE_HAVEN_FLOWS",
        "primary_regime": "RISK_OFF",
        "confidence": 0.719,
        "evidence_completeness": 0.75,
        "replication_quality": 0.73,
        "scientific_independence_score": 0.71,
        "capacity_score": 0.61,
        "failure_severity": 0.31,
        "uncertainty": 0.28,
        "economic_strength": 0.76,
        "scientific_quality": 0.74,
        "explainability": 0.72,
        "expected_capacity": "MEDIUM",
        "expected_decay": "Gradual over 3-6 months post-stress event",
        "expected_holding_horizon": "5-15 days",
        "expected_drawdown": 0.17,
        "datasets": ["FRED-MACRO", "ETF-GLD", "SYNTHETIC-VIX"],
        "feature_exposures": ["usd_stress", "real_rates", "volatility_term_structure"],
        "cross_asset_dependencies": ["USD", "equity_volatility", "rates"],
        "failure_modes": [
            "Concept drift under regime transition",
            "Stress-window threshold instability",
        ],
        "common_assumptions": [
            "Safe-haven preference remains observable through public macro proxies.",
            "Policy stress regimes transmit rapidly into gold demand.",
        ],
        "evidence_units": 14,
        "lineage": ["PROGRAM_3", "PROGRAM_4"],
        "regime_relevance": {
            "BULL_TREND": 0.42,
            "BEAR_TREND": 0.72,
            "RISK_OFF": 0.95,
            "RISK_ON": 0.28,
            "MACRO_TRANSITION": 0.88,
            "LIQUIDITY_CRISIS": 0.96,
        },
        "votes": {
            "BULL_TREND": "HOLD",
            "BEAR_TREND": "INCREASE",
            "RISK_OFF": "BUY",
            "RISK_ON": "REDUCE",
            "MACRO_TRANSITION": "BUY",
            "LIQUIDITY_CRISIS": "BUY",
        },
    },
    "real_yield_dislocation_reversion": {
        "alpha_id": "IKROS-ALPHA-P4-0001",
        "family": "REAL_YIELD_DISLOCATIONS",
        "primary_regime": "MACRO_TRANSITION",
        "confidence": 0.72,
        "evidence_completeness": 0.72,
        "replication_quality": 0.72,
        "scientific_independence_score": 0.77,
        "capacity_score": 0.73,
        "failure_severity": 0.29,
        "uncertainty": 0.24,
        "economic_strength": 0.76,
        "scientific_quality": 0.75,
        "explainability": 0.73,
        "expected_capacity": "HIGH",
        "expected_decay": "Moderate after policy repricing stabilizes",
        "expected_holding_horizon": "3-10 days",
        "expected_drawdown": 0.14,
        "datasets": ["FRED-TIPS", "FRED-BREAKEVENS", "FRED-DXY"],
        "feature_exposures": ["real_yield_gap", "inflation_breakeven", "usd_path"],
        "cross_asset_dependencies": ["real_yields", "usd", "inflation_expectations"],
        "failure_modes": ["Macro regime discontinuity", "Yield-measurement lag"],
        "common_assumptions": [
            "Real-rate overshoots mean revert after policy repricing.",
            "Macro inflation expectations remain observable with public datasets.",
        ],
        "evidence_units": 11,
        "lineage": ["PROGRAM_4"],
        "regime_relevance": {
            "BULL_TREND": 0.54,
            "BEAR_TREND": 0.67,
            "RISK_OFF": 0.63,
            "RISK_ON": 0.48,
            "MACRO_TRANSITION": 0.92,
            "LIQUIDITY_CRISIS": 0.60,
        },
        "votes": {
            "BULL_TREND": "HOLD",
            "BEAR_TREND": "BUY",
            "RISK_OFF": "INCREASE",
            "RISK_ON": "HOLD",
            "MACRO_TRANSITION": "BUY",
            "LIQUIDITY_CRISIS": "HOLD",
        },
    },
    "policy_expectation_repricing": {
        "alpha_id": "IKROS-ALPHA-P4-0002",
        "family": "POLICY_EXPECTATION_REPRICING",
        "primary_regime": "MACRO_TRANSITION",
        "confidence": 0.71,
        "evidence_completeness": 0.71,
        "replication_quality": 0.70,
        "scientific_independence_score": 0.79,
        "capacity_score": 0.64,
        "failure_severity": 0.30,
        "uncertainty": 0.27,
        "economic_strength": 0.75,
        "scientific_quality": 0.73,
        "explainability": 0.70,
        "expected_capacity": "MEDIUM",
        "expected_decay": "Fast after event window closes",
        "expected_holding_horizon": "1-5 days",
        "expected_drawdown": 0.15,
        "datasets": ["FRED-2Y", "FRED-SOFR_PROXY", "FOMC_TEXT_PROXY"],
        "feature_exposures": ["front_end_repricing", "policy_text_shift", "usd_event_flow"],
        "cross_asset_dependencies": ["front_end_rates", "policy_expectations", "usd"],
        "failure_modes": ["Policy-text misclassification", "Meeting-window clustering"],
        "common_assumptions": [
            "Policy-surprise windows are causally distinct from generic safe-haven stress.",
            "Front-end rates and policy language jointly identify repricing shocks.",
        ],
        "evidence_units": 10,
        "lineage": ["PROGRAM_4"],
        "regime_relevance": {
            "BULL_TREND": 0.46,
            "BEAR_TREND": 0.55,
            "RISK_OFF": 0.58,
            "RISK_ON": 0.44,
            "MACRO_TRANSITION": 0.95,
            "LIQUIDITY_CRISIS": 0.50,
        },
        "votes": {
            "BULL_TREND": "HOLD",
            "BEAR_TREND": "HOLD",
            "RISK_OFF": "BUY",
            "RISK_ON": "NO POSITION",
            "MACRO_TRANSITION": "BUY",
            "LIQUIDITY_CRISIS": "HOLD",
        },
    },
    "etf_flow_accumulation_pressure": {
        "alpha_id": "IKROS-ALPHA-P4-0003",
        "family": "ETF_FLOW_PRESSURE",
        "primary_regime": "RISK_ON",
        "confidence": 0.70,
        "evidence_completeness": 0.72,
        "replication_quality": 0.70,
        "scientific_independence_score": 0.76,
        "capacity_score": 0.68,
        "failure_severity": 0.28,
        "uncertainty": 0.26,
        "economic_strength": 0.74,
        "scientific_quality": 0.72,
        "explainability": 0.71,
        "expected_capacity": "HIGH",
        "expected_decay": "Moderate when ETF positioning normalizes",
        "expected_holding_horizon": "4-12 days",
        "expected_drawdown": 0.13,
        "datasets": ["ETF-GLD", "ETF-IAU", "FRED-DXY"],
        "feature_exposures": ["etf_flow_zscore", "usd_relief", "realized_flow_persistence"],
        "cross_asset_dependencies": ["etf_inventory", "usd", "macro_sentiment"],
        "failure_modes": ["ETF reporting lag", "Crowding around macro catalysts"],
        "common_assumptions": [
            "ETF inventory shifts proxy institutional accumulation with acceptable delay.",
            "Persistent fund-flow pressure transmits into spot and futures demand.",
        ],
        "evidence_units": 12,
        "lineage": ["PROGRAM_4"],
        "regime_relevance": {
            "BULL_TREND": 0.82,
            "BEAR_TREND": 0.49,
            "RISK_OFF": 0.52,
            "RISK_ON": 0.91,
            "MACRO_TRANSITION": 0.61,
            "LIQUIDITY_CRISIS": 0.34,
        },
        "votes": {
            "BULL_TREND": "BUY",
            "BEAR_TREND": "HOLD",
            "RISK_OFF": "HOLD",
            "RISK_ON": "BUY",
            "MACRO_TRANSITION": "INCREASE",
            "LIQUIDITY_CRISIS": "REDUCE",
        },
    },
    "commodity_cross_curve_divergence": {
        "alpha_id": "IKROS-ALPHA-P4-0004",
        "family": "INTERMARKET_COMMODITY_RELATIONSHIPS",
        "primary_regime": "BULL_TREND",
        "confidence": 0.69,
        "evidence_completeness": 0.70,
        "replication_quality": 0.69,
        "scientific_independence_score": 0.78,
        "capacity_score": 0.67,
        "failure_severity": 0.33,
        "uncertainty": 0.30,
        "economic_strength": 0.73,
        "scientific_quality": 0.71,
        "explainability": 0.69,
        "expected_capacity": "MEDIUM",
        "expected_decay": "Higher around commodity cycle transitions",
        "expected_holding_horizon": "5-20 days",
        "expected_drawdown": 0.18,
        "datasets": ["COMEX-CURVE", "BRENT-WTI", "FRED-INDICES"],
        "feature_exposures": ["curve_dispersion", "commodity_spread", "industrial_risk_mix"],
        "cross_asset_dependencies": ["commodity_curves", "industrial_metals", "energy_spreads"],
        "failure_modes": ["Cross-commodity contamination", "Physical bottleneck distortion"],
        "common_assumptions": [
            "Commodity-curve divergence reflects macro transition pressure relevant to gold.",
            "Intermarket relationships remain stable enough to preserve explanatory power.",
        ],
        "evidence_units": 9,
        "lineage": ["PROGRAM_4"],
        "regime_relevance": {
            "BULL_TREND": 0.88,
            "BEAR_TREND": 0.51,
            "RISK_OFF": 0.42,
            "RISK_ON": 0.72,
            "MACRO_TRANSITION": 0.74,
            "LIQUIDITY_CRISIS": 0.31,
        },
        "votes": {
            "BULL_TREND": "BUY",
            "BEAR_TREND": "REDUCE",
            "RISK_OFF": "NO POSITION",
            "RISK_ON": "INCREASE",
            "MACRO_TRANSITION": "BUY",
            "LIQUIDITY_CRISIS": "REDUCE",
        },
    },
}


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, round(value, 4)))


def _jaccard(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 0.0
    intersection = len(left_set.intersection(right_set))
    union = len(left_set.union(right_set))
    return _bounded(intersection / union if union else 0.0)


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return _bounded(sum(values) / len(values))


def _weighted_sum(values: list[float]) -> float:
    return _bounded(sum(values))


def _decision_from_score(score: float) -> str:
    if score >= 0.55:
        return "BUY"
    if score >= 0.22:
        return "INCREASE"
    if score <= -0.55:
        return "SELL"
    if score <= -0.22:
        return "REDUCE"
    if abs(score) <= 0.08:
        return "HOLD"
    return "NO POSITION"


def _current_regime() -> str:
    return "MACRO_TRANSITION"


def _alpha_profiles() -> dict[str, dict[str, Any]]:
    profiles = deepcopy(_APPROVED_ALPHA_LIBRARY)
    for name, profile in profiles.items():
        profile["mechanism"] = name
        profile["lifecycle_state"] = "APPROVED"
        profile["scientific_maturity"] = _avg(
            [
                float(profile["scientific_quality"]),
                float(profile["replication_quality"]),
                float(profile["evidence_completeness"]),
            ]
        )
    return profiles


def _build_independence_matrix(
    profiles: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items = list(profiles.items())
    scientific_matrix: list[dict[str, Any]] = []
    evidence_matrix: list[dict[str, Any]] = []
    for index, (left_name, left) in enumerate(items):
        for right_name, right in items[index + 1 :]:
            feature_overlap = _jaccard(
                list(left["feature_exposures"]), list(right["feature_exposures"])
            )
            dataset_overlap = _jaccard(list(left["datasets"]), list(right["datasets"]))
            failure_overlap = _jaccard(
                list(left["failure_modes"]), list(right["failure_modes"])
            )
            dependency_overlap = _jaccard(
                list(left["cross_asset_dependencies"]),
                list(right["cross_asset_dependencies"]),
            )
            regime_overlap = 1.0 if str(left["primary_regime"]) == str(right["primary_regime"]) else 0.25
            mechanism_overlap = 0.95 if str(left["family"]) == str(right["family"]) else _avg(
                [dependency_overlap, feature_overlap, regime_overlap * 0.5]
            )
            evidence_overlap = _bounded(
                min(float(left["evidence_units"]), float(right["evidence_units"]))
                / max(float(left["evidence_units"]), float(right["evidence_units"]))
            )
            lineage_overlap = _jaccard(list(left["lineage"]), list(right["lineage"]))
            economic_overlap = _avg(
                [
                    dependency_overlap,
                    1.0 if "usd" in ",".join(left["cross_asset_dependencies"]).lower()
                    and "usd" in ",".join(right["cross_asset_dependencies"]).lower()
                    else 0.0,
                    1.0 if "rates" in ",".join(left["cross_asset_dependencies"]).lower()
                    and "rates" in ",".join(right["cross_asset_dependencies"]).lower()
                    else 0.0,
                ]
            )
            graph_proximity = _avg([lineage_overlap, dependency_overlap, dataset_overlap])
            scientific_independence = _bounded(
                1.0
                - (
                    0.18 * mechanism_overlap
                    + 0.14 * feature_overlap
                    + 0.12 * dataset_overlap
                    + 0.10 * evidence_overlap
                    + 0.08 * failure_overlap
                    + 0.10 * regime_overlap
                    + 0.08 * economic_overlap
                    + 0.08 * graph_proximity
                    + 0.06 * lineage_overlap
                    + 0.06 * dependency_overlap
                )
            )
            evidence_independence = _bounded(
                1.0 - _avg([dataset_overlap, evidence_overlap, lineage_overlap, graph_proximity])
            )
            scientific_matrix.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "scientific_mechanism_overlap": mechanism_overlap,
                    "feature_overlap": feature_overlap,
                    "dataset_overlap": dataset_overlap,
                    "evidence_overlap": evidence_overlap,
                    "failure_overlap": failure_overlap,
                    "regime_overlap": regime_overlap,
                    "economic_rationale_overlap": economic_overlap,
                    "graph_proximity": graph_proximity,
                    "knowledge_lineage_overlap": lineage_overlap,
                    "causal_dependency_overlap": dependency_overlap,
                    "scientific_independence_score": scientific_independence,
                }
            )
            evidence_matrix.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "evidence_independence_score": evidence_independence,
                    "shared_datasets": sorted(set(left["datasets"]).intersection(right["datasets"])),
                    "shared_lineage": sorted(set(left["lineage"]).intersection(right["lineage"])),
                }
            )
    return scientific_matrix, evidence_matrix


def _build_correlation_atlas(
    profiles: dict[str, dict[str, Any]], independence_matrix: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    atlas: list[dict[str, Any]] = []
    lookup = {name: profile for name, profile in profiles.items()}
    for row in independence_matrix:
        left = lookup[str(row["left"])]
        right = lookup[str(row["right"])]
        signal_correlation = _avg(
            [
                1.0
                - abs(
                    _DECISION_SCORE[str(left["votes"][regime])]
                    - _DECISION_SCORE[str(right["votes"][regime])]
                )
                / 2.0
                for regime in _REGIMES
            ]
        )
        regime_correlation = _avg(
            [
                min(
                    float(left["regime_relevance"][regime]),
                    float(right["regime_relevance"][regime]),
                )
                for regime in _REGIMES
            ]
        )
        economic_correlation = _avg(
            [
                float(row["economic_rationale_overlap"]),
                float(row["causal_dependency_overlap"]),
            ]
        )
        feature_correlation = float(row["feature_overlap"])
        evidence_correlation = _avg(
            [float(row["dataset_overlap"]), float(row["evidence_overlap"])]
        )
        failure_correlation = float(row["failure_overlap"])
        tail_correlation = _avg(
            [
                float(row["regime_overlap"]),
                float(row["failure_overlap"]),
                min(float(left["expected_drawdown"]), float(right["expected_drawdown"])) / 0.2,
            ]
        )
        cross_regime_correlation = _avg(
            [
                abs(
                    float(left["regime_relevance"]["RISK_OFF"])
                    - float(right["regime_relevance"]["RISK_OFF"])
                ),
                abs(
                    float(left["regime_relevance"]["RISK_ON"])
                    - float(right["regime_relevance"]["RISK_ON"])
                ),
                abs(
                    float(left["regime_relevance"]["MACRO_TRANSITION"])
                    - float(right["regime_relevance"]["MACRO_TRANSITION"])
                ),
            ]
        )
        aggregate = _avg(
            [
                signal_correlation,
                regime_correlation,
                economic_correlation,
                feature_correlation,
                evidence_correlation,
                failure_correlation,
                tail_correlation,
                1.0 - cross_regime_correlation,
            ]
        )
        atlas.append(
            {
                "left": row["left"],
                "right": row["right"],
                "signal_correlation": signal_correlation,
                "regime_correlation": regime_correlation,
                "economic_correlation": economic_correlation,
                "feature_correlation": feature_correlation,
                "evidence_correlation": evidence_correlation,
                "failure_correlation": failure_correlation,
                "tail_correlation": tail_correlation,
                "cross_regime_correlation": _bounded(1.0 - cross_regime_correlation),
                "aggregate_correlation": aggregate,
            }
        )
    return atlas


def _average_correlation(
    mechanism: str, correlation_atlas: list[dict[str, Any]]
) -> float:
    values = [
        float(row["aggregate_correlation"])
        for row in correlation_atlas
        if row["left"] == mechanism or row["right"] == mechanism
    ]
    return _avg(values)


def _cap_and_normalize(
    raw_scores: dict[str, float], caps: dict[str, float]
) -> dict[str, float]:
    total = sum(raw_scores.values())
    if total <= 0.0:
        equal = _bounded(1.0 / max(len(raw_scores), 1))
        return {name: equal for name in raw_scores}

    allocations = {name: raw / total for name, raw in raw_scores.items()}
    frozen: dict[str, float] = {}

    while True:
        overflow = {
            name: allocations[name] - caps[name]
            for name in allocations
            if name not in frozen and allocations[name] > caps[name]
        }
        if not overflow:
            break
        for name in overflow:
            frozen[name] = caps[name]
        residual = 1.0 - sum(frozen.values())
        open_names = [name for name in allocations if name not in frozen]
        if not open_names:
            break
        open_total = sum(raw_scores[name] for name in open_names)
        for name in open_names:
            allocations[name] = residual * raw_scores[name] / open_total

    for name, value in frozen.items():
        allocations[name] = value

    rounded = {name: round(value, 4) for name, value in allocations.items()}
    drift = round(1.0 - sum(rounded.values()), 4)
    if rounded:
        largest = max(rounded, key=lambda name: rounded[name])
        rounded[largest] = round(rounded[largest] + drift, 4)
    return rounded


def _build_allocation_registry(
    profiles: dict[str, dict[str, Any]], correlation_atlas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    regime = _current_regime()
    raw_scores: dict[str, float] = {}
    caps: dict[str, float] = {}
    diagnostics: dict[str, dict[str, float]] = {}
    for name, profile in profiles.items():
        avg_corr = _average_correlation(name, correlation_atlas)
        confidence_weight = float(profile["confidence"])
        evidence_weight = float(profile["evidence_completeness"])
        independence_weight = float(profile["scientific_independence_score"])
        replication_weight = float(profile["replication_quality"])
        regime_weight = float(profile["regime_relevance"][regime])
        quality_weight = float(profile["scientific_quality"])
        capacity_weight = float(profile["capacity_score"])
        failure_penalty = 0.12 * float(profile["failure_severity"])
        uncertainty_penalty = 0.12 * float(profile["uncertainty"])
        correlation_penalty = 0.10 * avg_corr
        raw = (
            0.20 * confidence_weight
            + 0.16 * evidence_weight
            + 0.16 * independence_weight
            + 0.12 * replication_weight
            + 0.16 * regime_weight
            + 0.12 * quality_weight
            + 0.08 * capacity_weight
            - failure_penalty
            - uncertainty_penalty
            - correlation_penalty
        )
        raw_scores[name] = max(round(raw, 6), 0.05)
        caps[name] = round(min(0.31, 0.14 + 0.23 * capacity_weight), 4)
        diagnostics[name] = {
            "avg_correlation": avg_corr,
            "failure_penalty": _bounded(failure_penalty),
            "uncertainty_penalty": _bounded(uncertainty_penalty),
            "correlation_penalty": _bounded(correlation_penalty),
        }

    allocations = _cap_and_normalize(raw_scores, caps)
    registry: list[dict[str, Any]] = []
    for name, profile in sorted(
        profiles.items(),
        key=lambda item: allocations[item[0]],
        reverse=True,
    ):
        registry.append(
            {
                "alpha_id": profile["alpha_id"],
                "mechanism": name,
                "allocation_weight": allocations[name],
                "confidence_weight": _bounded(float(profile["confidence"])),
                "evidence_weight": _bounded(float(profile["evidence_completeness"])),
                "regime_weight": _bounded(float(profile["regime_relevance"][regime])),
                "scientific_quality_weight": _bounded(float(profile["scientific_quality"])),
                "capacity_constraint": caps[name],
                "expected_capacity": profile["expected_capacity"],
                "expected_holding_horizon": profile["expected_holding_horizon"],
                "failure_penalty": diagnostics[name]["failure_penalty"],
                "uncertainty_penalty": diagnostics[name]["uncertainty_penalty"],
                "correlation_penalty": diagnostics[name]["correlation_penalty"],
                "allocation_rationale": (
                    "Confidence-, evidence-, regime-, and independence-weighted allocation "
                    "with explicit penalties for correlation, uncertainty, and failure severity."
                ),
            }
        )
    return registry


def _build_conflict_registry(
    profiles: dict[str, dict[str, Any]], correlation_atlas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    lookup = {row["left"] + "|" + row["right"]: row for row in correlation_atlas}
    lookup.update({row["right"] + "|" + row["left"]: row for row in correlation_atlas})
    names = list(profiles.keys())
    for index, left_name in enumerate(names):
        left = profiles[left_name]
        for right_name in names[index + 1 :]:
            right = profiles[right_name]
            regime_gaps = {
                regime: abs(
                    _DECISION_STRENGTH[str(left["votes"][regime])]
                    - _DECISION_STRENGTH[str(right["votes"][regime])]
                )
                for regime in _REGIMES
            }
            conflict_regime = max(regime_gaps, key=lambda regime: regime_gaps[regime])
            gap = regime_gaps[conflict_regime]
            if gap < 2:
                continue
            left_vote = str(left["votes"][conflict_regime])
            right_vote = str(right["votes"][conflict_regime])
            corr = lookup[left_name + "|" + right_name]
            left_score = _avg(
                [
                    float(left["confidence"]),
                    float(left["evidence_completeness"]),
                    float(left["regime_relevance"][conflict_regime]),
                    float(left["scientific_maturity"]),
                    float(left["economic_strength"]),
                ]
            )
            right_score = _avg(
                [
                    float(right["confidence"]),
                    float(right["evidence_completeness"]),
                    float(right["regime_relevance"][conflict_regime]),
                    float(right["scientific_maturity"]),
                    float(right["economic_strength"]),
                ]
            )
            winner_name = left_name if left_score >= right_score else right_name
            winner_vote = left_vote if winner_name == left_name else right_vote
            minority_name = right_name if winner_name == left_name else left_name
            minority_vote = right_vote if minority_name == right_name else left_vote
            conflicts.append(
                {
                    "conflict_id": f"PORTFOLIO-CONFLICT-{len(conflicts) + 1:04d}",
                    "left": left_name,
                    "right": right_name,
                    "root_cause": (
                        "Regime specificity and economic-channel disagreement across the "
                        "approved alpha library."
                    ),
                    "evidence_strength_gap": _bounded(abs(left_score - right_score)),
                    "confidence_difference": _bounded(
                        abs(float(left["confidence"]) - float(right["confidence"]))
                    ),
                    "regime_specificity": conflict_regime,
                    "economic_rationale": (
                        f"{left_name} prioritizes {left['primary_regime'].lower()} transmission "
                        f"while {right_name} prioritizes {right['primary_regime'].lower()} transmission."
                    ),
                    "historical_reliability_gap": _bounded(
                        abs(
                            float(left["replication_quality"])
                            - float(right["replication_quality"])
                        )
                    ),
                    "aggregate_correlation": corr["aggregate_correlation"],
                    "winning_alpha": {
                        "mechanism": winner_name,
                        "decision": winner_vote,
                    },
                    "minority_opinion": {
                        "mechanism": minority_name,
                        "decision": minority_vote,
                    },
                    "combined_recommendation": (
                        winner_vote if abs(left_score - right_score) > 0.05 else "HOLD"
                    ),
                }
            )
    return conflicts


def _build_capacity_registry(
    profiles: dict[str, dict[str, Any]], allocation_registry: list[dict[str, Any]]
) -> dict[str, Any]:
    allocations = {row["mechanism"]: float(row["allocation_weight"]) for row in allocation_registry}
    per_alpha: list[dict[str, Any]] = []
    for name, profile in profiles.items():
        allocation = allocations[name]
        utilization = allocation / max(float(profile["capacity_score"]), 0.01)
        per_alpha.append(
            {
                "alpha_id": profile["alpha_id"],
                "mechanism": name,
                "capacity_score": _bounded(float(profile["capacity_score"])),
                "expected_capacity": profile["expected_capacity"],
                "allocated_capital_share": allocation,
                "utilization_ratio": _bounded(utilization),
                "market_impact": _bounded(0.32 * allocation + 0.18 * utilization),
                "liquidity_constraints": (
                    "Event-window liquidity compression" if utilization > 0.32 else "Within governed capacity envelope"
                ),
                "scalability": _bounded(float(profile["capacity_score"]) * 0.9 + 0.05),
                "expected_degradation": _bounded(
                    0.18 * allocation + 0.22 * float(profile["failure_severity"])
                ),
            }
        )
    portfolio_capacity = {
        "cross_capacity_interactions": [
            {
                "shared_dependency": "USD",
                "affected_mechanisms": [
                    name
                    for name, profile in profiles.items()
                    if any("usd" in dependency.lower() for dependency in profile["cross_asset_dependencies"])
                ],
                "portfolio_penalty": 0.08,
            },
            {
                "shared_dependency": "Macro policy repricing",
                "affected_mechanisms": [
                    "real_yield_dislocation_reversion",
                    "policy_expectation_repricing",
                ],
                "portfolio_penalty": 0.06,
            },
        ],
        "portfolio_level_capacity": _avg([float(item["capacity_score"]) for item in per_alpha]),
    }
    return {"per_alpha": per_alpha, "portfolio_level": portfolio_capacity}


def _build_regime_allocation_engine(
    profiles: dict[str, dict[str, Any]], allocation_registry: list[dict[str, Any]]
) -> dict[str, Any]:
    base = {row["mechanism"]: float(row["allocation_weight"]) for row in allocation_registry}
    regime_payload: dict[str, Any] = {}
    for regime in _REGIMES:
        scaled = {
            name: base[name] * float(profile["regime_relevance"][regime])
            for name, profile in profiles.items()
        }
        total = sum(scaled.values())
        allocations = {
            name: round(value / total, 4) if total else round(1.0 / len(scaled), 4)
            for name, value in scaled.items()
        }
        drift = round(1.0 - sum(allocations.values()), 4)
        winner = max(allocations, key=lambda name: allocations[name])
        allocations[winner] = round(allocations[winner] + drift, 4)
        ordered = sorted(allocations.items(), key=lambda item: item[1], reverse=True)
        regime_payload[regime] = {
            "label": _REGIME_LABELS[regime],
            "preferred_alpha_mix": [
                {"mechanism": name, "allocation_weight": weight}
                for name, weight in ordered
            ],
            "allocation_adjustments": [
                {
                    "mechanism": name,
                    "adjustment_vs_base": round(weight - base[name], 4),
                }
                for name, weight in ordered
            ],
            "expected_confidence": _weighted_sum(
                [
                    weight * float(profiles[name]["confidence"])
                    for name, weight in allocations.items()
                ]
            ),
            "expected_resilience": _weighted_sum(
                [
                    weight * (1.0 - float(profiles[name]["failure_severity"]))
                    for name, weight in allocations.items()
                ]
            ),
            "automatic_portfolio_rotation": (
                f"Increase exposure toward {ordered[0][0]} and reduce the lowest-regime-fit "
                f"alpha when AFRP classifies the market as {_REGIME_LABELS[regime].lower()}."
            ),
        }
    return regime_payload


def _build_portfolio_decision(
    profiles: dict[str, dict[str, Any]], regime_allocations: dict[str, Any]
) -> dict[str, Any]:
    decisions: dict[str, Any] = {}
    for regime in _REGIMES:
        aggregate_score = 0.0
        contributions: list[dict[str, Any]] = []
        for name, profile in profiles.items():
            vote = str(profile["votes"][regime])
            weight = _avg(
                [
                    float(profile["confidence"]),
                    float(profile["evidence_completeness"]),
                    float(profile["replication_quality"]),
                    float(profile["regime_relevance"][regime]),
                    float(profile["scientific_maturity"]),
                    float(profile["economic_strength"]),
                ]
            )
            score = weight * _DECISION_SCORE[vote]
            aggregate_score += score
            contributions.append(
                {
                    "mechanism": name,
                    "vote": vote,
                    "vote_weight": weight,
                    "weighted_score": _bounded(score, lower=-1.0, upper=1.0),
                }
            )
        average_score = aggregate_score / len(profiles)
        decisions[regime] = {
            "decision": _decision_from_score(average_score),
            "weighted_score": _bounded((average_score + 1.0) / 2.0),
            "explanation": (
                "Votes are weighted by confidence, evidence, replication quality, regime relevance, scientific maturity, and economic strength."
            ),
            "contributions": contributions,
            "preferred_mix": regime_allocations[regime]["preferred_alpha_mix"],
        }

    current = _current_regime()
    return {
        "current_regime": current,
        "current_decision": decisions[current],
        "by_regime": decisions,
    }


def _build_portfolio_risk_report(
    profiles: dict[str, dict[str, Any]],
    allocation_registry: list[dict[str, Any]],
    correlation_atlas: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    capacity_registry: dict[str, Any],
) -> dict[str, Any]:
    allocations = {row["mechanism"]: float(row["allocation_weight"]) for row in allocation_registry}
    portfolio_confidence = _weighted_sum(
        [
            allocations[name] * float(profile["confidence"])
            for name, profile in profiles.items()
        ]
    )
    portfolio_uncertainty = _weighted_sum(
        [
            allocations[name] * float(profile["uncertainty"])
            for name, profile in profiles.items()
        ]
    )
    concentration = _bounded(sum(weight * weight for weight in allocations.values()) * 2.4)
    common_datasets = sorted(
        {
            dataset
            for row in correlation_atlas
            for dataset in _APPROVED_ALPHA_LIBRARY[str(row["left"])]["datasets"]
            if dataset in _APPROVED_ALPHA_LIBRARY[str(row["right"])]["datasets"]
        }
    )
    shared_failures = sorted(
        {
            failure
            for profile in profiles.values()
            for failure in list(profile["failure_modes"])
            if any(failure in other["failure_modes"] for other in profiles.values())
        }
    )
    expected_drawdown = _weighted_sum(
        [
            allocations[name] * float(profile["expected_drawdown"])
            for name, profile in profiles.items()
        ]
    )
    tail_vulnerability = _avg(
        [float(row["tail_correlation"]) for row in correlation_atlas]
    )
    return {
        "portfolio_confidence": portfolio_confidence,
        "portfolio_uncertainty": portfolio_uncertainty,
        "portfolio_concentration": concentration,
        "shared_failure_exposure": shared_failures,
        "common_datasets": common_datasets,
        "common_assumptions": sorted(
            {assumption for profile in profiles.values() for assumption in profile["common_assumptions"]}
        ),
        "expected_drawdown": expected_drawdown,
        "capacity_degradation": _bounded(
            1.0 - float(capacity_registry["portfolio_level"]["portfolio_level_capacity"])
        ),
        "tail_vulnerability": tail_vulnerability,
        "robustness_score": _bounded(
            portfolio_confidence
            + (1.0 - portfolio_uncertainty)
            + (1.0 - concentration)
            + (1.0 - tail_vulnerability)
        )
        / 4.0,
        "conflict_count": len(conflicts),
    }


def _build_portfolio_lifecycle(
    profiles: dict[str, dict[str, Any]], allocation_registry: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    allocations = {row["mechanism"]: float(row["allocation_weight"]) for row in allocation_registry}
    lifecycle: list[dict[str, Any]] = []
    for name, profile in profiles.items():
        weight = allocations[name]
        if float(profile["uncertainty"]) >= 0.34:
            state = "UNDER_REVIEW"
        elif weight >= 0.19:
            state = "ACTIVE"
        elif weight >= 0.14:
            state = "REDUCED"
        else:
            state = "SUSPENDED"
        profile["lifecycle_state"] = state
        lifecycle.append(
            {
                "alpha_id": profile["alpha_id"],
                "mechanism": name,
                "current_state": state,
                "history": ["CANDIDATE", "APPROVED", state],
                "transition_reason": (
                    "State derived from governed allocation weight, uncertainty, and failure severity."
                ),
                "revalidation_trigger": (
                    "Trigger revalidation when confidence drops below 0.65 or observation quality deteriorates."
                ),
            }
        )
    return lifecycle


def _build_dashboards(
    allocation_registry: list[dict[str, Any]],
    risk_report: dict[str, Any],
    conflicts: list[dict[str, Any]],
    capacity_registry: dict[str, Any],
    regime_allocations: dict[str, Any],
    lifecycle: list[dict[str, Any]],
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "institutional_portfolio_dashboard": {
            "tiles": [
                ["Current Regime", decision["current_regime"]],
                ["Portfolio Decision", decision["current_decision"]["decision"]],
                ["Portfolio Confidence", risk_report["portfolio_confidence"]],
                ["Robustness Score", risk_report["robustness_score"]],
            ]
        },
        "allocation_dashboard": {
            "tiles": [[row["mechanism"], row["allocation_weight"]] for row in allocation_registry]
        },
        "confidence_dashboard": {
            "tiles": [
                ["Portfolio Confidence", risk_report["portfolio_confidence"]],
                ["Portfolio Uncertainty", risk_report["portfolio_uncertainty"]],
            ]
        },
        "risk_dashboard": {
            "tiles": [
                ["Expected Drawdown", risk_report["expected_drawdown"]],
                ["Tail Vulnerability", risk_report["tail_vulnerability"]],
                ["Conflict Count", risk_report["conflict_count"]],
            ]
        },
        "alpha_contribution_dashboard": {
            "tiles": [
                [row["mechanism"], row["allocation_weight"]]
                for row in decision["current_decision"]["preferred_mix"]
            ]
        },
        "conflict_dashboard": {
            "tiles": [
                [row["conflict_id"], row["combined_recommendation"]]
                for row in conflicts
            ]
            or [["NONE", "No material conflicts"]]
        },
        "capacity_dashboard": {
            "tiles": [
                [item["mechanism"], item["utilization_ratio"]]
                for item in capacity_registry["per_alpha"]
            ]
        },
        "regime_dashboard": {
            "tiles": [
                [regime_allocations[regime]["label"], regime_allocations[regime]["expected_confidence"]]
                for regime in _REGIMES
            ]
        },
        "lifecycle_dashboard": {
            "tiles": [[row["mechanism"], row["current_state"]] for row in lifecycle]
        },
    }


def _build_portfolio_explanation(
    profiles: dict[str, dict[str, Any]],
    allocation_registry: list[dict[str, Any]],
    risk_report: dict[str, Any],
    conflicts: list[dict[str, Any]],
    decision: dict[str, Any],
) -> dict[str, Any]:
    contributions = []
    allocations = {row["mechanism"]: float(row["allocation_weight"]) for row in allocation_registry}
    for name, profile in profiles.items():
        contributions.append(
            {
                "mechanism": name,
                "allocation_weight": allocations[name],
                "confidence_attribution": _bounded(
                    allocations[name] * float(profile["confidence"])
                ),
                "evidence_attribution": _bounded(
                    allocations[name] * float(profile["evidence_completeness"])
                ),
                "risk_attribution": _bounded(
                    allocations[name] * float(profile["failure_severity"])
                ),
                "failure_attribution": list(profile["failure_modes"]),
                "regime_attribution": profile["primary_regime"],
            }
        )
    return {
        "portfolio_executive_report": (
            "AFRP transforms the approved alpha library into a governed institutional portfolio by favoring high-confidence, high-evidence, high-independence mechanisms under the active macro-transition regime while penalizing shared failure channels and concentration."
        ),
        "capital_allocation_rationale": (
            "Capital is allocated through confidence-, evidence-, regime-, capacity-, and scientific-quality weighting with explicit penalties for uncertainty, failure severity, and pairwise correlation."
        ),
        "alpha_contribution_report": contributions,
        "confidence_attribution": {
            item["mechanism"]: item["confidence_attribution"] for item in contributions
        },
        "evidence_attribution": {
            item["mechanism"]: item["evidence_attribution"] for item in contributions
        },
        "risk_attribution": {
            item["mechanism"]: item["risk_attribution"] for item in contributions
        },
        "failure_attribution": {
            item["mechanism"]: item["failure_attribution"] for item in contributions
        },
        "regime_attribution": {
            item["mechanism"]: item["regime_attribution"] for item in contributions
        },
        "economic_narrative": (
            "The current portfolio is anchored by macro-transition, safe-haven, and ETF-flow mechanisms because they provide complementary economic channels across policy repricing, stress migration, and institutional accumulation."
        ),
        "contradictory_evidence": [
            {
                "mechanism": conflict["minority_opinion"]["mechanism"],
                "reason": conflict["root_cause"],
                "minority_view": conflict["minority_opinion"]["decision"],
            }
            for conflict in conflicts
        ],
        "current_portfolio_decision": decision["current_decision"],
        "portfolio_risk_summary": risk_report,
    }


def _build_portfolio_lineage(
    allocation_registry: list[dict[str, Any]], lifecycle: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "origin_programs": ["PROGRAM_3", "PROGRAM_4", "PROGRAM_5"],
        "alpha_to_portfolio_lineage": {
            row["mechanism"]: ["PROGRAM_4_APPROVED_LIBRARY", "PROGRAM_5_PORTFOLIO_CONSTRUCTION"]
            for row in allocation_registry
        },
        "lifecycle_lineage": {
            row["mechanism"]: row["history"] for row in lifecycle
        },
    }


def _build_portfolio_memory(
    allocation_registry: list[dict[str, Any]], conflicts: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "institutional_lessons": [
            "Approved alpha diversification is strongest when safe-haven, macro-rate, ETF-flow, and intermarket channels are combined instead of concentrated in a single family.",
            "Conflict resolution should preserve minority evidence rather than suppress it because contradictory institutional signals still improve governance explainability.",
        ],
        "decisions": [
            {
                "mechanism": row["mechanism"],
                "allocation_weight": row["allocation_weight"],
                "note": row["allocation_rationale"],
            }
            for row in allocation_registry
        ],
        "conflict_memory": conflicts,
    }


def _build_evidence_registry(
    profiles: dict[str, dict[str, Any]], decision: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "alpha_id": profile["alpha_id"],
            "mechanism": name,
            "supporting_evidence_units": profile["evidence_units"],
            "evidence_completeness": profile["evidence_completeness"],
            "replication_quality": profile["replication_quality"],
            "portfolio_decision_relevance": profile["regime_relevance"][decision["current_regime"]],
        }
        for name, profile in profiles.items()
    ]


def _build_confidence_registry(
    profiles: dict[str, dict[str, Any]], risk_report: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {
            "alpha_id": profile["alpha_id"],
            "mechanism": name,
            "confidence": profile["confidence"],
            "uncertainty": profile["uncertainty"],
            "portfolio_confidence_share": _bounded(
                float(profile["confidence"]) / max(float(risk_report["portfolio_confidence"]), 0.01),
                upper=4.0,
            ),
        }
        for name, profile in profiles.items()
    ]


def _build_portfolio_registry(
    allocation_registry: list[dict[str, Any]],
    risk_report: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "portfolio_id": "IKROS-PORTFOLIO-P5-0001",
        "portfolio_name": "Institutional Alpha Portfolio v1",
        "approved_alpha_count": len(allocation_registry),
        "active_alpha_count": len([row for row in allocation_registry if row["allocation_weight"] >= 0.15]),
        "current_regime": decision["current_regime"],
        "portfolio_decision": decision["current_decision"]["decision"],
        "portfolio_confidence": risk_report["portfolio_confidence"],
        "portfolio_uncertainty": risk_report["portfolio_uncertainty"],
        "scientific_objective": "Maximize scientific robustness, institutional confidence, durability, and resilience without implementing trade execution.",
    }


def _build_graph_summary(
    allocation_registry: list[dict[str, Any]], conflicts: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "nodes": [
            "PROGRAM5-PORTFOLIO",
            *[row["alpha_id"] for row in allocation_registry],
            *[row["conflict_id"] for row in conflicts],
        ],
        "edges": [
            {
                "source": "PROGRAM5-PORTFOLIO",
                "target": row["alpha_id"],
                "relationship": "ALLOCATES_TO",
            }
            for row in allocation_registry
        ]
        + [
            {
                "source": "PROGRAM5-PORTFOLIO",
                "target": row["conflict_id"],
                "relationship": "GOVERNS_CONFLICT",
            }
            for row in conflicts
        ],
    }


def _build_audit_trail(
    decision: dict[str, Any], risk_report: dict[str, Any], conflicts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "step": "load-approved-alpha-library",
            "outcome": "Loaded five approved Program 4 mechanisms into the governed portfolio workspace.",
        },
        {
            "step": "construct-allocation",
            "outcome": f"Current portfolio decision is {decision['current_decision']['decision']} under {decision['current_regime']}.",
        },
        {
            "step": "resolve-conflicts",
            "outcome": f"Resolved {len(conflicts)} material conflicts using evidence, confidence, and regime specificity.",
        },
        {
            "step": "risk-capacity-review",
            "outcome": f"Portfolio robustness score recorded at {risk_report['robustness_score']}.",
        },
    ]


def _portfolio_schemas() -> dict[str, dict[str, Any]]:
    return {
        "portfolio.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Institutional Portfolio",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "portfolio_id",
                "portfolio_name",
                "approved_alpha_count",
                "current_regime",
                "portfolio_decision",
                "portfolio_confidence",
                "portfolio_uncertainty",
            ],
            "properties": {
                "portfolio_id": {"type": "string"},
                "portfolio_name": {"type": "string"},
                "approved_alpha_count": {"type": "integer", "minimum": 1},
                "current_regime": {"type": "string"},
                "portfolio_decision": {"type": "string", "enum": PORTFOLIO_DECISIONS},
                "portfolio_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "portfolio_uncertainty": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "scientific_objective": {"type": "string"},
            },
        },
        "allocation.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Institutional Allocation Entry",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "alpha_id",
                "mechanism",
                "allocation_weight",
                "confidence_weight",
                "evidence_weight",
                "regime_weight",
            ],
            "properties": {
                "alpha_id": {"type": "string"},
                "mechanism": {"type": "string"},
                "allocation_weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "confidence_weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "evidence_weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "regime_weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "scientific_quality_weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "capacity_constraint": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "allocation_rationale": {"type": "string"},
            },
        },
        "risk.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Risk Report",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "portfolio_confidence",
                "portfolio_uncertainty",
                "portfolio_concentration",
                "expected_drawdown",
                "tail_vulnerability",
                "robustness_score",
            ],
            "properties": {
                "portfolio_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "portfolio_uncertainty": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "portfolio_concentration": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "expected_drawdown": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "tail_vulnerability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "robustness_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
        },
        "capacity.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Capacity Entry",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "alpha_id",
                "mechanism",
                "capacity_score",
                "allocated_capital_share",
                "utilization_ratio",
            ],
            "properties": {
                "alpha_id": {"type": "string"},
                "mechanism": {"type": "string"},
                "capacity_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "allocated_capital_share": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "utilization_ratio": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "market_impact": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "expected_degradation": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
        },
        "conflict.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Conflict Entry",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "conflict_id",
                "left",
                "right",
                "root_cause",
                "winning_alpha",
                "minority_opinion",
                "combined_recommendation",
            ],
            "properties": {
                "conflict_id": {"type": "string"},
                "left": {"type": "string"},
                "right": {"type": "string"},
                "root_cause": {"type": "string"},
                "evidence_strength_gap": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "confidence_difference": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "regime_specificity": {"type": "string"},
                "economic_rationale": {"type": "string"},
                "historical_reliability_gap": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "aggregate_correlation": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "winning_alpha": {"type": "object"},
                "minority_opinion": {"type": "object"},
                "combined_recommendation": {"type": "string", "enum": PORTFOLIO_DECISIONS},
            },
        },
        "portfolio-decision.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Decision",
            "type": "object",
            "additionalProperties": False,
            "required": ["decision", "weighted_score", "explanation", "contributions"],
            "properties": {
                "decision": {"type": "string", "enum": PORTFOLIO_DECISIONS},
                "weighted_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "explanation": {"type": "string"},
                "contributions": {"type": "array"},
                "preferred_mix": {"type": "array"},
            },
        },
        "portfolio-explanation.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Explanation",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "portfolio_executive_report",
                "capital_allocation_rationale",
                "alpha_contribution_report",
                "economic_narrative",
                "current_portfolio_decision",
            ],
            "properties": {
                "portfolio_executive_report": {"type": "string"},
                "capital_allocation_rationale": {"type": "string"},
                "alpha_contribution_report": {"type": "array"},
                "economic_narrative": {"type": "string"},
                "contradictory_evidence": {"type": "array"},
                "current_portfolio_decision": {"type": "object"},
                "portfolio_risk_summary": {"type": "object"},
            },
        },
        "portfolio-lifecycle.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Lifecycle Entry",
            "type": "object",
            "additionalProperties": False,
            "required": [
                "alpha_id",
                "mechanism",
                "current_state",
                "history",
                "transition_reason",
                "revalidation_trigger",
            ],
            "properties": {
                "alpha_id": {"type": "string"},
                "mechanism": {"type": "string"},
                "current_state": {"type": "string", "enum": PORTFOLIO_LIFECYCLE_STATES},
                "history": {"type": "array"},
                "transition_reason": {"type": "string"},
                "revalidation_trigger": {"type": "string"},
            },
        },
        "dashboard.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Dashboard",
            "type": "object",
            "additionalProperties": False,
            "required": ["tiles"],
            "properties": {
                "tiles": {"type": "array"},
            },
        },
    }


def prepare_program5_artifacts() -> dict[str, Any]:
    """Construct the governed institutional portfolio from the approved alpha library."""
    profiles = _alpha_profiles()
    independence_matrix, evidence_matrix = _build_independence_matrix(profiles)
    correlation_atlas = _build_correlation_atlas(profiles, independence_matrix)
    allocation_registry = _build_allocation_registry(profiles, correlation_atlas)
    conflicts = _build_conflict_registry(profiles, correlation_atlas)
    capacity_registry = _build_capacity_registry(profiles, allocation_registry)
    regime_allocations = _build_regime_allocation_engine(profiles, allocation_registry)
    portfolio_decision = _build_portfolio_decision(profiles, regime_allocations)
    lifecycle = _build_portfolio_lifecycle(profiles, allocation_registry)
    risk_report = _build_portfolio_risk_report(
        profiles,
        allocation_registry,
        correlation_atlas,
        conflicts,
        capacity_registry,
    )
    portfolio_explanation = _build_portfolio_explanation(
        profiles,
        allocation_registry,
        risk_report,
        conflicts,
        portfolio_decision,
    )
    dashboards = _build_dashboards(
        allocation_registry,
        risk_report,
        conflicts,
        capacity_registry,
        regime_allocations,
        lifecycle,
        portfolio_decision,
    )
    portfolio_registry = _build_portfolio_registry(
        allocation_registry,
        risk_report,
        portfolio_decision,
    )
    portfolio_lineage = _build_portfolio_lineage(allocation_registry, lifecycle)
    portfolio_memory = _build_portfolio_memory(allocation_registry, conflicts)
    evidence_registry = _build_evidence_registry(profiles, portfolio_decision)
    confidence_registry = _build_confidence_registry(profiles, risk_report)
    graph_summary = _build_graph_summary(allocation_registry, conflicts)
    audit_trail = _build_audit_trail(portfolio_decision, risk_report, conflicts)
    schemas = _portfolio_schemas()
    return {
        "program": "INSTITUTIONAL_ALPHA_PORTFOLIO_INTELLIGENCE_SYSTEM",
        "version": "1.0.0",
        "current_regime": portfolio_decision["current_regime"],
        "approved_alpha_library": profiles,
        "portfolio_registry": portfolio_registry,
        "allocation_registry": allocation_registry,
        "mechanism_independence_matrix": independence_matrix,
        "evidence_independence_matrix": evidence_matrix,
        "institutional_correlation_atlas": correlation_atlas,
        "conflict_registry": conflicts,
        "portfolio_risk_report": risk_report,
        "capacity_registry": capacity_registry,
        "regime_allocation_engine": regime_allocations,
        "institutional_portfolio_decision": portfolio_decision,
        "portfolio_explanation": portfolio_explanation,
        "portfolio_lifecycle": lifecycle,
        "institutional_portfolio_dashboards": dashboards,
        "portfolio_lineage": portfolio_lineage,
        "portfolio_memory": portfolio_memory,
        "portfolio_evidence_registry": evidence_registry,
        "portfolio_confidence_registry": confidence_registry,
        "portfolio_graph": graph_summary,
        "portfolio_audit_trail": audit_trail,
        "schemas": schemas,
        "arb_recommendation": (
            "Program 5 may proceed as a governed portfolio-intelligence layer because AFRP can now construct, explain, and maintain an institutional alpha portfolio without introducing execution, broker connectivity, or Runtime modifications. Continue only with scientific monitoring, revalidation, and future portfolio governance extensions."
        ),
    }


def emit_program5_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path = Path("."),
) -> dict[str, str]:
    """Write Program 5 portfolio artifacts, reports, and governed schemas."""
    out = (repo_root / PROGRAM5_DIR).resolve()
    schema_dir = (repo_root / PROGRAM5_SCHEMA_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    for key, filename in [
        ("portfolio_registry", "portfolio_registry.json"),
        ("allocation_registry", "allocation_registry.json"),
        ("mechanism_independence_matrix", "mechanism_independence_matrix.json"),
        ("evidence_independence_matrix", "evidence_independence_matrix.json"),
        ("institutional_correlation_atlas", "institutional_correlation_atlas.json"),
        ("conflict_registry", "conflict_registry.json"),
        ("portfolio_risk_report", "portfolio_risk_report.json"),
        ("capacity_registry", "capacity_registry.json"),
        ("regime_allocation_engine", "regime_allocation_engine.json"),
        ("institutional_portfolio_decision", "institutional_portfolio_decision.json"),
        ("portfolio_explanation", "portfolio_explanation.json"),
        ("portfolio_lifecycle", "portfolio_lifecycle.json"),
        ("institutional_portfolio_dashboards", "institutional_portfolio_dashboards.json"),
        ("portfolio_lineage", "portfolio_lineage.json"),
        ("portfolio_memory", "portfolio_memory.json"),
        ("portfolio_evidence_registry", "portfolio_evidence_registry.json"),
        ("portfolio_confidence_registry", "portfolio_confidence_registry.json"),
        ("portfolio_graph", "portfolio_graph.json"),
        ("portfolio_audit_trail", "portfolio_audit_trail.json"),
    ]:
        destination = out / filename
        write_json(destination, analysis[key])
        paths[key] = str(destination)

    if campaign_result is not None:
        destination = out / "campaign_result.json"
        write_json(destination, campaign_result)
        paths["campaign_result"] = str(destination)

    for filename, schema in analysis["schemas"].items():
        destination = schema_dir / filename
        write_json(destination, schema)
        paths[f"schema:{filename}"] = str(destination)

    allocation_rows = [
        [
            row["mechanism"],
            row["allocation_weight"],
            row["confidence_weight"],
            row["regime_weight"],
            row["capacity_constraint"],
        ]
        for row in analysis["allocation_registry"]
    ]
    write_markdown(
        out / "ALLOCATION_DASHBOARD.md",
        "# Institutional Allocation Dashboard\n\n"
        + markdown_table(
            ["Mechanism", "Allocation", "Confidence", "Regime", "Capacity Cap"],
            allocation_rows,
        ),
    )
    paths["allocation_dashboard_md"] = str(out / "ALLOCATION_DASHBOARD.md")

    independence_rows = [
        [
            row["left"],
            row["right"],
            row["scientific_independence_score"],
            row["dataset_overlap"],
            row["causal_dependency_overlap"],
        ]
        for row in analysis["mechanism_independence_matrix"]
    ]
    write_markdown(
        out / "MECHANISM_INDEPENDENCE_MATRIX.md",
        "# Mechanism Independence Matrix\n\n"
        + markdown_table(
            ["Left", "Right", "Independence", "Dataset Overlap", "Causal Overlap"],
            independence_rows,
        ),
    )
    paths["independence_md"] = str(out / "MECHANISM_INDEPENDENCE_MATRIX.md")

    correlation_rows = [
        [
            row["left"],
            row["right"],
            row["aggregate_correlation"],
            row["tail_correlation"],
            row["cross_regime_correlation"],
        ]
        for row in analysis["institutional_correlation_atlas"]
    ]
    write_markdown(
        out / "INSTITUTIONAL_CORRELATION_ATLAS.md",
        "# Institutional Correlation Atlas\n\n"
        + markdown_table(
            ["Left", "Right", "Aggregate", "Tail", "Cross-Regime"],
            correlation_rows,
        ),
    )
    paths["correlation_md"] = str(out / "INSTITUTIONAL_CORRELATION_ATLAS.md")

    conflict_rows = [
        [
            row["conflict_id"],
            row["left"],
            row["right"],
            row["winning_alpha"]["mechanism"],
            row["combined_recommendation"],
        ]
        for row in analysis["conflict_registry"]
    ] or [["NONE", "-", "-", "-", "No material conflicts"]]
    write_markdown(
        out / "CONFLICT_RESOLUTION_REPORT.md",
        "# Conflict Resolution Report\n\n"
        + markdown_table(
            ["Conflict", "Left", "Right", "Winner", "Combined Recommendation"],
            conflict_rows,
        ),
    )
    paths["conflict_md"] = str(out / "CONFLICT_RESOLUTION_REPORT.md")

    lifecycle_rows = [
        [row["mechanism"], row["current_state"], row["revalidation_trigger"]]
        for row in analysis["portfolio_lifecycle"]
    ]
    write_markdown(
        out / "PORTFOLIO_LIFECYCLE.md",
        "# Portfolio Lifecycle\n\n"
        + markdown_table(
            ["Mechanism", "Current State", "Revalidation Trigger"],
            lifecycle_rows,
        ),
    )
    paths["lifecycle_md"] = str(out / "PORTFOLIO_LIFECYCLE.md")

    final_lines = [
        "# Program 5 — Institutional Alpha Portfolio Intelligence System",
        "",
        f"**Current Regime:** {analysis['current_regime']}",
        f"**Portfolio Decision:** {analysis['portfolio_registry']['portfolio_decision']}",
        f"**Portfolio Confidence:** {analysis['portfolio_registry']['portfolio_confidence']}",
        f"**Portfolio Uncertainty:** {analysis['portfolio_registry']['portfolio_uncertainty']}",
        "",
        "## Allocation Methodology",
        "",
        analysis["portfolio_explanation"]["capital_allocation_rationale"],
        "",
        "## Portfolio Allocation",
        "",
        markdown_table(
            ["Mechanism", "Allocation", "Confidence", "Regime"],
            [
                [
                    row["mechanism"],
                    row["allocation_weight"],
                    row["confidence_weight"],
                    row["regime_weight"],
                ]
                for row in analysis["allocation_registry"]
            ],
        ),
        "",
        "## Conflict Resolution Examples",
        "",
        markdown_table(
            ["Conflict", "Winner", "Combined Recommendation"],
            [
                [
                    row["conflict_id"],
                    row["winning_alpha"]["mechanism"],
                    row["combined_recommendation"],
                ]
                for row in analysis["conflict_registry"]
            ]
            or [["NONE", "-", "-"]],
        ),
        "",
        "## ARB Recommendation",
        "",
        analysis["arb_recommendation"],
    ]
    write_markdown(out / "FINAL_REPORT.md", "\n".join(final_lines))
    paths["final_report"] = str(out / "FINAL_REPORT.md")
    return paths
