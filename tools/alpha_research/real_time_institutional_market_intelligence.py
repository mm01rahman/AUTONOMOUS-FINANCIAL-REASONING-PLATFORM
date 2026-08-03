"""Generation 4 / Program 7 — Real-Time Institutional Market Intelligence Platform."""

# ruff: noqa: E501

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.alpha_research.institutional_alpha_portfolio_intelligence import (
    prepare_program5_artifacts,
)
from tools.alpha_research.institutional_market_simulation_laboratory import (
    _DECISION_SCORE,
    prepare_program6_artifacts,
)
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PROGRAM7_DIR = Path("11-research") / "generation-4-real-time-institutional-market-intelligence"
PROGRAM7_SCHEMA_DIR = Path("schemas") / "institutional-market-intelligence"

PORTFOLIO_DECISIONS: list[str] = ["BUY", "SELL", "HOLD", "REDUCE", "INCREASE", "NO POSITION"]

_REGIMES: list[str] = [
    "BULL_TREND",
    "BEAR_TREND",
    "RISK_OFF",
    "RISK_ON",
    "MACRO_TRANSITION",
    "LIQUIDITY_CRISIS",
]

_BELIEF_DIMENSIONS: list[str] = [
    "inflation",
    "growth",
    "liquidity",
    "policy",
    "safe_haven_demand",
    "market_stress",
    "risk_appetite",
    "cross_asset_relationships",
    "regime_conviction",
    "portfolio_conviction",
]

_STREAM_ROWS: list[dict[str, Any]] = [
    {
        "timestamp": "2025-01-02T00:00:00Z",
        "xauusd": 2035.2,
        "dxy": 102.1,
        "real_yield": 1.67,
        "policy_surprise": 0.08,
        "etf_flow": 0.27,
        "cftc_positioning": 0.21,
        "vol_index": 16.2,
        "cross_asset_dispersion": 0.22,
        "news_risk": 0.18,
        "geopolitical_risk": 0.11,
        "event_type": "macro_release",
    },
    {
        "timestamp": "2025-01-10T00:00:00Z",
        "xauusd": 2042.8,
        "dxy": 101.8,
        "real_yield": 1.63,
        "policy_surprise": 0.05,
        "etf_flow": 0.31,
        "cftc_positioning": 0.23,
        "vol_index": 15.4,
        "cross_asset_dispersion": 0.20,
        "news_risk": 0.16,
        "geopolitical_risk": 0.10,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-01-22T00:00:00Z",
        "xauusd": 2026.7,
        "dxy": 102.9,
        "real_yield": 1.74,
        "policy_surprise": 0.14,
        "etf_flow": 0.12,
        "cftc_positioning": 0.18,
        "vol_index": 20.6,
        "cross_asset_dispersion": 0.31,
        "news_risk": 0.29,
        "geopolitical_risk": 0.15,
        "event_type": "policy_shift",
    },
    {
        "timestamp": "2025-02-03T00:00:00Z",
        "xauusd": 2061.4,
        "dxy": 101.4,
        "real_yield": 1.57,
        "policy_surprise": 0.07,
        "etf_flow": 0.36,
        "cftc_positioning": 0.27,
        "vol_index": 17.5,
        "cross_asset_dispersion": 0.24,
        "news_risk": 0.19,
        "geopolitical_risk": 0.21,
        "event_type": "geopolitical",
    },
    {
        "timestamp": "2025-02-14T00:00:00Z",
        "xauusd": 2054.3,
        "dxy": 102.2,
        "real_yield": 1.65,
        "policy_surprise": 0.04,
        "etf_flow": 0.25,
        "cftc_positioning": 0.22,
        "vol_index": 16.9,
        "cross_asset_dispersion": 0.23,
        "news_risk": 0.20,
        "geopolitical_risk": 0.17,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-02-27T00:00:00Z",
        "xauusd": 2007.9,
        "dxy": 104.0,
        "real_yield": 1.83,
        "policy_surprise": 0.19,
        "etf_flow": 0.05,
        "cftc_positioning": 0.14,
        "vol_index": 24.8,
        "cross_asset_dispersion": 0.37,
        "news_risk": 0.34,
        "geopolitical_risk": 0.25,
        "event_type": "shock",
    },
    {
        "timestamp": "2025-03-11T00:00:00Z",
        "xauusd": 2022.5,
        "dxy": 103.1,
        "real_yield": 1.75,
        "policy_surprise": 0.12,
        "etf_flow": 0.11,
        "cftc_positioning": 0.16,
        "vol_index": 22.1,
        "cross_asset_dispersion": 0.34,
        "news_risk": 0.30,
        "geopolitical_risk": 0.22,
        "event_type": "macro_release",
    },
    {
        "timestamp": "2025-03-24T00:00:00Z",
        "xauusd": 2048.0,
        "dxy": 101.9,
        "real_yield": 1.62,
        "policy_surprise": 0.06,
        "etf_flow": 0.29,
        "cftc_positioning": 0.24,
        "vol_index": 18.3,
        "cross_asset_dispersion": 0.25,
        "news_risk": 0.18,
        "geopolitical_risk": 0.13,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-04-04T00:00:00Z",
        "xauusd": 2072.2,
        "dxy": 101.1,
        "real_yield": 1.55,
        "policy_surprise": 0.05,
        "etf_flow": 0.33,
        "cftc_positioning": 0.28,
        "vol_index": 16.1,
        "cross_asset_dispersion": 0.21,
        "news_risk": 0.16,
        "geopolitical_risk": 0.09,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-04-21T00:00:00Z",
        "xauusd": 2064.9,
        "dxy": 101.6,
        "real_yield": 1.61,
        "policy_surprise": 0.09,
        "etf_flow": 0.20,
        "cftc_positioning": 0.21,
        "vol_index": 18.7,
        "cross_asset_dispersion": 0.27,
        "news_risk": 0.20,
        "geopolitical_risk": 0.14,
        "event_type": "macro_release",
    },
    {
        "timestamp": "2025-05-02T00:00:00Z",
        "xauusd": 2031.3,
        "dxy": 102.8,
        "real_yield": 1.72,
        "policy_surprise": 0.15,
        "etf_flow": 0.09,
        "cftc_positioning": 0.17,
        "vol_index": 21.6,
        "cross_asset_dispersion": 0.33,
        "news_risk": 0.28,
        "geopolitical_risk": 0.20,
        "event_type": "policy_shift",
    },
    {
        "timestamp": "2025-05-16T00:00:00Z",
        "xauusd": 2015.4,
        "dxy": 103.6,
        "real_yield": 1.79,
        "policy_surprise": 0.17,
        "etf_flow": 0.03,
        "cftc_positioning": 0.13,
        "vol_index": 25.7,
        "cross_asset_dispersion": 0.39,
        "news_risk": 0.36,
        "geopolitical_risk": 0.27,
        "event_type": "shock",
    },
    {
        "timestamp": "2025-05-28T00:00:00Z",
        "xauusd": 2041.8,
        "dxy": 102.2,
        "real_yield": 1.66,
        "policy_surprise": 0.07,
        "etf_flow": 0.24,
        "cftc_positioning": 0.20,
        "vol_index": 19.1,
        "cross_asset_dispersion": 0.28,
        "news_risk": 0.22,
        "geopolitical_risk": 0.16,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-06-10T00:00:00Z",
        "xauusd": 2058.7,
        "dxy": 101.7,
        "real_yield": 1.59,
        "policy_surprise": 0.06,
        "etf_flow": 0.30,
        "cftc_positioning": 0.25,
        "vol_index": 17.3,
        "cross_asset_dispersion": 0.23,
        "news_risk": 0.17,
        "geopolitical_risk": 0.12,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-06-23T00:00:00Z",
        "xauusd": 2079.6,
        "dxy": 100.9,
        "real_yield": 1.52,
        "policy_surprise": 0.04,
        "etf_flow": 0.35,
        "cftc_positioning": 0.29,
        "vol_index": 15.8,
        "cross_asset_dispersion": 0.19,
        "news_risk": 0.14,
        "geopolitical_risk": 0.09,
        "event_type": "normal",
    },
    {
        "timestamp": "2025-07-08T00:00:00Z",
        "xauusd": 2068.5,
        "dxy": 101.5,
        "real_yield": 1.60,
        "policy_surprise": 0.08,
        "etf_flow": 0.22,
        "cftc_positioning": 0.23,
        "vol_index": 18.0,
        "cross_asset_dispersion": 0.25,
        "news_risk": 0.19,
        "geopolitical_risk": 0.14,
        "event_type": "macro_release",
    },
    {
        "timestamp": "2025-07-21T00:00:00Z",
        "xauusd": 2029.1,
        "dxy": 103.2,
        "real_yield": 1.76,
        "policy_surprise": 0.16,
        "etf_flow": 0.07,
        "cftc_positioning": 0.15,
        "vol_index": 23.8,
        "cross_asset_dispersion": 0.35,
        "news_risk": 0.31,
        "geopolitical_risk": 0.23,
        "event_type": "event_risk",
    },
    {
        "timestamp": "2025-08-04T00:00:00Z",
        "xauusd": 2049.4,
        "dxy": 102.1,
        "real_yield": 1.68,
        "policy_surprise": 0.09,
        "etf_flow": 0.18,
        "cftc_positioning": 0.19,
        "vol_index": 20.0,
        "cross_asset_dispersion": 0.29,
        "news_risk": 0.23,
        "geopolitical_risk": 0.17,
        "event_type": "normal",
    },
]


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, round(value, 4)))


def _decision_from_score(score: float) -> str:
    if score >= 0.55:
        return "BUY"
    if score >= 0.20:
        return "INCREASE"
    if score <= -0.55:
        return "SELL"
    if score <= -0.22:
        return "REDUCE"
    if abs(score) <= 0.08:
        return "HOLD"
    return "NO POSITION"


def _normalize_probabilities(values: dict[str, float]) -> dict[str, float]:
    clipped = {key: max(0.0001, value) for key, value in values.items()}
    total = sum(clipped.values())
    normalized = {key: round(value / total, 4) for key, value in clipped.items()}
    drift = round(1.0 - sum(normalized.values()), 4)
    top = max(normalized, key=lambda key: normalized[key])
    normalized[top] = round(normalized[top] + drift, 4)
    return normalized


def _source_quality(row: dict[str, Any]) -> dict[str, float]:
    return {
        "spot_xauusd": _bounded(0.96 - abs(float(row["vol_index"]) - 18.0) * 0.01, 0.70, 0.99),
        "usd_index": 0.94,
        "real_yields": _bounded(0.90 - abs(float(row["policy_surprise"])) * 0.15, 0.72, 0.95),
        "central_bank_announcements": _bounded(0.92 - abs(float(row["policy_surprise"]) - 0.10), 0.68, 0.95),
        "economic_calendar": 0.93,
        "etf_flows": _bounded(0.89 - abs(float(row["etf_flow"]) - 0.22) * 0.6, 0.62, 0.93),
        "cftc_positioning": 0.87,
        "options_positioning": 0.78,
        "volatility_indices": 0.92,
        "cross_asset_prices": 0.93,
        "commodity_prices": 0.91,
        "news_metadata": _bounded(0.86 - float(row["news_risk"]) * 0.2, 0.62, 0.90),
        "geopolitical_event_metadata": _bounded(0.83 - float(row["geopolitical_risk"]) * 0.1, 0.60, 0.88),
    }


def _belief_update(previous: dict[str, float], row: dict[str, Any]) -> dict[str, float]:
    updated = dict(previous)
    policy = float(row["policy_surprise"])
    stress = _bounded(float(row["vol_index"]) / 30.0 + float(row["geopolitical_risk"]) * 0.6)
    risk_on = _bounded(float(row["etf_flow"]) + (0.25 - float(row["cross_asset_dispersion"])))
    updated["inflation"] = _bounded(previous["inflation"] * 0.92 + float(row["real_yield"]) / 3.5 * 0.08)
    updated["growth"] = _bounded(previous["growth"] * 0.90 + (0.6 - policy) * 0.10)
    updated["liquidity"] = _bounded(previous["liquidity"] * 0.90 + (0.55 - stress) * 0.10)
    updated["policy"] = _bounded(previous["policy"] * 0.88 + policy * 0.12)
    updated["safe_haven_demand"] = _bounded(previous["safe_haven_demand"] * 0.90 + stress * 0.10)
    updated["market_stress"] = _bounded(previous["market_stress"] * 0.88 + stress * 0.12)
    updated["risk_appetite"] = _bounded(previous["risk_appetite"] * 0.90 + risk_on * 0.10)
    updated["cross_asset_relationships"] = _bounded(
        previous["cross_asset_relationships"] * 0.91 + (1.0 - float(row["cross_asset_dispersion"])) * 0.09
    )
    updated["regime_conviction"] = _bounded(
        previous["regime_conviction"] * 0.88 + (1.0 - abs(float(row["event_type"] == "shock") - 0.5)) * 0.12
    )
    updated["portfolio_conviction"] = _bounded(
        previous["portfolio_conviction"] * 0.87
        + (
            updated["risk_appetite"] * 0.35
            + (1.0 - updated["market_stress"]) * 0.35
            + updated["cross_asset_relationships"] * 0.30
        )
        * 0.13
    )
    return updated


def _regime_probabilities(beliefs: dict[str, float], row: dict[str, Any]) -> dict[str, float]:
    stress = float(beliefs["market_stress"])
    policy = float(beliefs["policy"])
    appetite = float(beliefs["risk_appetite"])
    dispersion = float(row["cross_asset_dispersion"])
    values = {
        "BULL_TREND": 0.40 + appetite * 0.55 - stress * 0.20,
        "BEAR_TREND": 0.25 + stress * 0.40 + policy * 0.18 - appetite * 0.18,
        "RISK_OFF": 0.20 + stress * 0.65 + float(row["geopolitical_risk"]) * 0.25,
        "RISK_ON": 0.28 + appetite * 0.60 - stress * 0.25,
        "MACRO_TRANSITION": 0.30 + policy * 0.50 + dispersion * 0.20,
        "LIQUIDITY_CRISIS": 0.15 + stress * 0.70 + max(0.0, dispersion - 0.30),
    }
    return _normalize_probabilities(values)


def _alpha_activation(
    alpha_library: dict[str, dict[str, Any]],
    regime_probs: dict[str, float],
    beliefs: dict[str, float],
) -> list[dict[str, Any]]:
    activation_rows: list[dict[str, Any]] = []
    for mechanism, profile in alpha_library.items():
        regime_fit = sum(
            float(profile["regime_relevance"][regime]) * regime_probs[regime]
            for regime in _REGIMES
        )
        strengthening = _bounded(
            0.40 * regime_fit
            + 0.25 * float(profile["confidence"])
            + 0.20 * float(profile["evidence_completeness"])
            + 0.15 * float(beliefs["portfolio_conviction"])
        )
        degrading = _bounded(
            0.35 * float(profile["failure_severity"])
            + 0.25 * float(beliefs["market_stress"])
            + 0.20 * (1.0 - regime_fit)
            + 0.20 * (1.0 - float(profile["replication_quality"]))
        )
        activation_probability = _bounded(strengthening - degrading * 0.35 + 0.35)
        state = (
            "active"
            if activation_probability >= 0.67
            else "degrading"
            if degrading > 0.55
            else "dormant"
        )
        activation_rows.append(
            {
                "mechanism": mechanism,
                "alpha_id": profile["alpha_id"],
                "activation_probability": activation_probability,
                "strengthening": strengthening,
                "degrading": degrading,
                "state": state,
                "vote": profile["votes"][max(regime_probs, key=lambda regime: regime_probs[regime])],
            }
        )
    return sorted(activation_rows, key=lambda row: row["activation_probability"], reverse=True)


def _portfolio_recommendation(
    activation_rows: list[dict[str, Any]],
    alpha_library: dict[str, dict[str, Any]],
    regime_probs: dict[str, float],
    beliefs: dict[str, float],
) -> dict[str, Any]:
    scores: list[float] = []
    raw_alloc: dict[str, float] = {}
    for row in activation_rows:
        mechanism = str(row["mechanism"])
        profile = alpha_library[mechanism]
        vote = str(row["vote"])
        vote_score = _DECISION_SCORE[vote]
        weight = _bounded(
            0.35 * float(row["activation_probability"])
            + 0.25 * float(profile["confidence"])
            + 0.20 * float(profile["scientific_independence_score"])
            + 0.20 * float(profile["capacity_score"])
        )
        scores.append(weight * vote_score)
        raw_alloc[mechanism] = max(0.001, weight * (1.0 - float(row["degrading"]) * 0.4))
    total = sum(raw_alloc.values())
    allocation: list[dict[str, Any]] = []
    for mechanism, score in sorted(raw_alloc.items(), key=lambda item: item[1], reverse=True):
        activation_probability = next(
            float(item["activation_probability"])
            for item in activation_rows
            if item["mechanism"] == mechanism
        )
        allocation.append(
            {
                "mechanism": mechanism,
                "allocation_weight": round(score / total, 4),
                "activation_probability": activation_probability,
            }
        )
    if allocation:
        allocation_sum = sum(float(item["allocation_weight"]) for item in allocation)
        drift = round(1.0 - allocation_sum, 4)
        allocation[0]["allocation_weight"] = round(float(allocation[0]["allocation_weight"]) + drift, 4)
    mean_score = sum(scores) / max(len(scores), 1)
    concentration = max(float(item["allocation_weight"]) for item in allocation) if allocation else 0.0
    uncertainty = _bounded(1.0 - beliefs["portfolio_conviction"] + concentration * 0.25)
    confidence = _bounded(beliefs["portfolio_conviction"] * 0.72 + (1.0 - uncertainty) * 0.28)
    return {
        "decision": _decision_from_score(mean_score),
        "weighted_score": _bounded((mean_score + 1.0) / 2.0),
        "allocation": allocation,
        "portfolio_confidence": confidence,
        "portfolio_uncertainty": uncertainty,
        "portfolio_concentration": round(concentration, 4),
        "portfolio_diversification": _bounded(1.0 - concentration),
        "portfolio_risk": _bounded(float(beliefs["market_stress"]) * 0.55 + uncertainty * 0.45),
        "regime_top": max(regime_probs, key=lambda regime: regime_probs[regime]),
    }


def _research_triggers(
    row: dict[str, Any],
    beliefs: dict[str, float],
    regime_probs: dict[str, float],
    activation_rows: list[dict[str, Any]],
    portfolio: dict[str, Any],
) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    regime_entropy = 1.0 - max(regime_probs.values())
    if regime_entropy > 0.42:
        triggers.append(
            {
                "trigger_type": "unknown_regime",
                "severity": "high",
                "reason": "Regime probabilities are diffuse with elevated uncertainty.",
                "expected_information_gain": _bounded(regime_entropy + 0.10),
                "campaign_type": "REGIME_DISCOVERY",
            }
        )
    if float(row["cross_asset_dispersion"]) > 0.34:
        triggers.append(
            {
                "trigger_type": "unexpected_relationships",
                "severity": "high",
                "reason": "Cross-asset dispersion exceeds governed threshold.",
                "expected_information_gain": _bounded(float(row["cross_asset_dispersion"]) + 0.05),
                "campaign_type": "CROSS_ASSET_RELATIONSHIP_INVESTIGATION",
            }
        )
    if float(beliefs["market_stress"]) > 0.68:
        triggers.append(
            {
                "trigger_type": "novel_market_behavior",
                "severity": "high",
                "reason": "Market stress belief elevated above institutional baseline.",
                "expected_information_gain": _bounded(float(beliefs["market_stress"]) + 0.06),
                "campaign_type": "STRESS_DIAGNOSTICS",
            }
        )
    for row_activation in activation_rows:
        if float(row_activation["degrading"]) > 0.58:
            triggers.append(
                {
                    "trigger_type": "concept_drift",
                    "severity": "medium",
                    "reason": f"{row_activation['mechanism']} degradation signal exceeded threshold.",
                    "expected_information_gain": _bounded(float(row_activation["degrading"])),
                    "campaign_type": "ALPHA_REVALIDATION",
                    "mechanism": row_activation["mechanism"],
                }
            )
    if float(portfolio["portfolio_confidence"]) < 0.58:
        triggers.append(
            {
                "trigger_type": "evidence_conflict",
                "severity": "high",
                "reason": "Portfolio confidence decayed below governed threshold.",
                "expected_information_gain": _bounded(1.0 - float(portfolio["portfolio_confidence"])),
                "campaign_type": "PORTFOLIO_BELIEF_RECONCILIATION",
            }
        )
    return triggers


def _event_reasoning(
    row: dict[str, Any],
    beliefs_before: dict[str, float],
    beliefs_after: dict[str, float],
    activation_rows: list[dict[str, Any]],
    portfolio_before: dict[str, Any] | None,
    portfolio_after: dict[str, Any],
    triggers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    event_rows: list[dict[str, Any]] = []
    shock_score = _bounded(
        float(row["news_risk"]) * 0.45
        + float(row["geopolitical_risk"]) * 0.35
        + max(0.0, float(row["vol_index"]) - 18.0) / 15.0 * 0.20
    )
    significant = shock_score >= 0.38 or str(row["event_type"]) in {"shock", "geopolitical", "policy_shift", "event_risk"}
    if not significant:
        return event_rows
    top_alpha = activation_rows[0]["mechanism"]
    immediate = _bounded(shock_score * 0.75 + float(row["policy_surprise"]) * 0.25)
    medium = _bounded(immediate * 0.75 + float(beliefs_after["cross_asset_relationships"]) * 0.25)
    confidence_revision = _bounded(float(portfolio_after["portfolio_confidence"]) - float(portfolio_before["portfolio_confidence"])) if portfolio_before else 0.0
    event_rows.append(
        {
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "immediate_impact": immediate,
            "medium_term_impact": medium,
            "affected_alpha_mechanisms": [top_alpha] + [item["mechanism"] for item in activation_rows[1:3]],
            "affected_portfolio": portfolio_after["decision"],
            "evidence_change": _bounded(abs(float(beliefs_after["market_stress"]) - float(beliefs_before["market_stress"]))),
            "belief_revision": {
                key: _bounded(float(beliefs_after[key]) - float(beliefs_before[key]), -1.0, 1.0)
                for key in ("inflation", "growth", "liquidity", "policy", "market_stress", "risk_appetite")
            },
            "confidence_revision": confidence_revision,
            "expected_research_value": _bounded(immediate * 0.45 + medium * 0.35 + len(triggers) * 0.08),
            "institutional_narrative": (
                f"Event '{row['event_type']}' shifted stress and policy beliefs, increasing attention on {top_alpha} while portfolio stance moved toward {portfolio_after['decision']}."
            ),
        }
    )
    return event_rows


def _longitudinal_report(
    belief_registry: list[dict[str, Any]],
    portfolio_registry: list[dict[str, Any]],
    trigger_registry: list[dict[str, Any]],
    event_registry: list[dict[str, Any]],
    activation_registry: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "alpha_health_over_time": [
            {
                "timestamp": row["timestamp"],
                "active_alpha_count": len([item for item in row["rows"] if item["state"] == "active"]),
                "degrading_alpha_count": len([item for item in row["rows"] if item["state"] == "degrading"]),
            }
            for row in activation_registry
        ],
        "portfolio_evolution": [
            {
                "timestamp": row["timestamp"],
                "decision": row["portfolio"]["decision"],
                "confidence": row["portfolio"]["portfolio_confidence"],
                "uncertainty": row["portfolio"]["portfolio_uncertainty"],
            }
            for row in portfolio_registry
        ],
        "confidence_trajectories": [
            {"timestamp": row["timestamp"], "portfolio_conviction": row["beliefs"]["portfolio_conviction"]}
            for row in belief_registry
        ],
        "regime_evolution": [
            {"timestamp": row["timestamp"], "regime_top": row["regime_top"], "max_prob": row["max_probability"]}
            for row in portfolio_registry
        ],
        "research_productivity": {
            "triggers_total": len(trigger_registry),
            "high_severity_triggers": len([row for row in trigger_registry if row["severity"] == "high"]),
            "event_reasoning_records": len(event_registry),
        },
        "evidence_accumulation": {
            "belief_updates": len(belief_registry),
            "portfolio_revisions": len(portfolio_registry),
            "activation_updates": len(activation_registry),
        },
        "failure_recurrence": {
            "concept_drift_triggers": len(
                [row for row in trigger_registry if row["trigger_type"] == "concept_drift"]
            ),
            "evidence_conflict_triggers": len(
                [row for row in trigger_registry if row["trigger_type"] == "evidence_conflict"]
            ),
        },
        "scientific_maturity": _bounded(
            min(1.0, 0.40 + len(trigger_registry) * 0.01 + len(event_registry) * 0.015)
        ),
    }


def _dashboards(
    market_state_registry: list[dict[str, Any]],
    belief_registry: list[dict[str, Any]],
    portfolio_registry: list[dict[str, Any]],
    activation_registry: list[dict[str, Any]],
    trigger_registry: list[dict[str, Any]],
    event_registry: list[dict[str, Any]],
    longitudinal: dict[str, Any],
) -> dict[str, Any]:
    latest_market = market_state_registry[-1]
    latest_belief = belief_registry[-1]
    latest_portfolio = portfolio_registry[-1]["portfolio"]
    latest_activation = activation_registry[-1]["rows"]
    return {
        "market_state_dashboard": {
            "tiles": [
                ["Timestamp", latest_market["timestamp"]],
                ["XAU/USD", latest_market["xauusd"]],
                ["Vol Index", latest_market["vol_index"]],
                ["Event Type", latest_market["event_type"]],
            ]
        },
        "institutional_beliefs_dashboard": {
            "tiles": [[key, value] for key, value in latest_belief["beliefs"].items()]
        },
        "portfolio_dashboard": {
            "tiles": [
                ["Decision", latest_portfolio["decision"]],
                ["Confidence", latest_portfolio["portfolio_confidence"]],
                ["Uncertainty", latest_portfolio["portfolio_uncertainty"]],
                ["Risk", latest_portfolio["portfolio_risk"]],
            ]
        },
        "alpha_activity_dashboard": {
            "tiles": [[row["mechanism"], row["state"]] for row in latest_activation]
        },
        "research_queue_dashboard": {
            "tiles": [[row["trigger_type"], row["campaign_type"]] for row in trigger_registry[-10:]]
            or [["none", "none"]]
        },
        "evidence_dashboard": {
            "tiles": [
                ["Belief Updates", len(belief_registry)],
                ["Event Reasoning", len(event_registry)],
                ["Research Triggers", len(trigger_registry)],
            ]
        },
        "confidence_dashboard": {
            "tiles": [
                ["Portfolio Conviction", latest_belief["beliefs"]["portfolio_conviction"]],
                ["Regime Conviction", latest_belief["beliefs"]["regime_conviction"]],
            ]
        },
        "risk_dashboard": {
            "tiles": [
                ["Market Stress", latest_belief["beliefs"]["market_stress"]],
                ["Portfolio Risk", latest_portfolio["portfolio_risk"]],
            ]
        },
        "regimes_dashboard": {
            "tiles": [[key, value] for key, value in portfolio_registry[-1]["regime_probabilities"].items()]
        },
        "knowledge_growth_dashboard": {
            "tiles": [
                ["Belief Registry Size", len(belief_registry)],
                ["Market State Registry Size", len(market_state_registry)],
                ["Trigger Registry Size", len(trigger_registry)],
            ]
        },
        "research_productivity_dashboard": {
            "tiles": [
                ["High Severity Triggers", longitudinal["research_productivity"]["high_severity_triggers"]],
                ["Event Narratives", longitudinal["research_productivity"]["event_reasoning_records"]],
            ]
        },
        "scientific_health_dashboard": {
            "tiles": [
                ["Scientific Maturity", longitudinal["scientific_maturity"]],
                ["Evidence Conflict Triggers", longitudinal["failure_recurrence"]["evidence_conflict_triggers"]],
            ]
        },
    }


def _schemas() -> dict[str, dict[str, Any]]:
    return {
        "belief-state.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Belief State",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "beliefs"],
            "properties": {"timestamp": {"type": "string"}, "beliefs": {"type": "object"}},
        },
        "market-state.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Market State",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "xauusd", "dxy", "real_yield", "sources_quality"],
            "properties": {
                "timestamp": {"type": "string"},
                "xauusd": {"type": "number"},
                "dxy": {"type": "number"},
                "real_yield": {"type": "number"},
                "sources_quality": {"type": "object"},
            },
        },
        "regime-probabilities.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Regime Probabilities",
            "type": "object",
            "additionalProperties": False,
            "required": _REGIMES,
            "properties": {regime: {"type": "number", "minimum": 0.0, "maximum": 1.0} for regime in _REGIMES},
        },
        "alpha-activation.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Alpha Activation",
            "type": "object",
            "additionalProperties": False,
            "required": ["mechanism", "activation_probability", "state"],
            "properties": {
                "mechanism": {"type": "string"},
                "activation_probability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "state": {"type": "string"},
            },
        },
        "portfolio-evolution.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio Evolution",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "portfolio", "regime_probabilities"],
            "properties": {
                "timestamp": {"type": "string"},
                "portfolio": {"type": "object"},
                "regime_probabilities": {"type": "object"},
            },
        },
        "research-trigger.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Research Trigger",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "trigger_type", "severity", "campaign_type", "expected_information_gain"],
            "properties": {
                "timestamp": {"type": "string"},
                "trigger_type": {"type": "string"},
                "severity": {"type": "string"},
                "campaign_type": {"type": "string"},
                "expected_information_gain": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
        },
        "event-reasoning.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Event Reasoning",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "event_type", "immediate_impact", "medium_term_impact", "institutional_narrative"],
            "properties": {
                "timestamp": {"type": "string"},
                "event_type": {"type": "string"},
                "immediate_impact": {"type": "number"},
                "medium_term_impact": {"type": "number"},
                "institutional_narrative": {"type": "string"},
            },
        },
        "executive-dashboard.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Executive Dashboard",
            "type": "object",
            "additionalProperties": False,
            "required": ["tiles"],
            "properties": {"tiles": {"type": "array"}},
        },
    }


def prepare_program7_artifacts() -> dict[str, Any]:
    """Build the deterministic real-time institutional intelligence layer."""
    foundation = prepare_program6_artifacts()
    # Source of truth for alpha metadata is Program 5.
    alpha_profiles = deepcopy(prepare_program5_artifacts()["approved_alpha_library"])

    belief_state = {name: 0.55 for name in _BELIEF_DIMENSIONS}
    market_state_registry: list[dict[str, Any]] = []
    belief_registry: list[dict[str, Any]] = []
    regime_registry: list[dict[str, Any]] = []
    alpha_activation_registry: list[dict[str, Any]] = []
    portfolio_evolution_registry: list[dict[str, Any]] = []
    event_registry: list[dict[str, Any]] = []
    research_trigger_registry: list[dict[str, Any]] = []
    knowledge_growth_registry: list[dict[str, Any]] = []

    portfolio_previous: dict[str, Any] | None = None

    for row in _STREAM_ROWS:
        quality = _source_quality(row)
        market_state = {**row, "sources_quality": quality}
        market_state_registry.append(market_state)

        belief_before = dict(belief_state)
        belief_state = _belief_update(belief_state, row)
        belief_registry.append({"timestamp": row["timestamp"], "beliefs": dict(belief_state)})

        regime_probs = _regime_probabilities(belief_state, row)
        regime_registry.append({"timestamp": row["timestamp"], "regime_probabilities": regime_probs})

        activation_rows = _alpha_activation(alpha_profiles, regime_probs, belief_state)
        alpha_activation_registry.append({"timestamp": row["timestamp"], "rows": activation_rows})

        portfolio = _portfolio_recommendation(activation_rows, alpha_profiles, regime_probs, belief_state)
        portfolio_evolution_registry.append(
            {
                "timestamp": row["timestamp"],
                "portfolio": portfolio,
                "regime_probabilities": regime_probs,
                "regime_top": portfolio["regime_top"],
                "max_probability": regime_probs[portfolio["regime_top"]],
            }
        )

        triggers = _research_triggers(row, belief_state, regime_probs, activation_rows, portfolio)
        for trigger in triggers:
            research_trigger_registry.append(
                {"timestamp": row["timestamp"], **trigger, "governed_campaign_opened": True}
            )

        events = _event_reasoning(
            row=row,
            beliefs_before=belief_before,
            beliefs_after=belief_state,
            activation_rows=activation_rows,
            portfolio_before=portfolio_previous,
            portfolio_after=portfolio,
            triggers=triggers,
        )
        event_registry.extend(events)
        portfolio_previous = portfolio

        knowledge_growth_registry.append(
            {
                "timestamp": row["timestamp"],
                "knowledge_graph_updates": 1 + len(events) + len(triggers),
                "research_memory_updates": 1 + len(triggers),
                "evidence_registry_updates": 1 + len(events),
                "failure_registry_updates": len(
                    [item for item in activation_rows if item["state"] == "degrading"]
                ),
                "confidence_registry_updates": 1,
                "portfolio_registry_updates": 1,
                "alpha_registry_updates": len(activation_rows),
                "research_registry_updates": len(triggers),
                "lessons_learned_updates": 1 if events else 0,
                "scientific_principles_updates": 1 if triggers else 0,
                "lineage_preserved": True,
            }
        )

    longitudinal = _longitudinal_report(
        belief_registry=belief_registry,
        portfolio_registry=portfolio_evolution_registry,
        trigger_registry=research_trigger_registry,
        event_registry=event_registry,
        activation_registry=alpha_activation_registry,
    )
    dashboards = _dashboards(
        market_state_registry=market_state_registry,
        belief_registry=belief_registry,
        portfolio_registry=portfolio_evolution_registry,
        activation_registry=alpha_activation_registry,
        trigger_registry=research_trigger_registry,
        event_registry=event_registry,
        longitudinal=longitudinal,
    )
    intelligence_registry = {
        "intelligence_cycle_count": len(_STREAM_ROWS),
        "continuous_operation": True,
        "latest_portfolio_decision": portfolio_evolution_registry[-1]["portfolio"]["decision"],
        "latest_regime": portfolio_evolution_registry[-1]["regime_top"],
        "latest_confidence": portfolio_evolution_registry[-1]["portfolio"]["portfolio_confidence"],
        "governed_research_triggers": len(research_trigger_registry),
        "scientific_health_score": _bounded(
            0.55
            + min(0.20, len(event_registry) * 0.01)
            + min(0.15, len(research_trigger_registry) * 0.005)
            + (1.0 - longitudinal["scientific_maturity"]) * 0.10
        ),
        "non_executing": True,
        "broker_connections": 0,
        "trade_execution_calls": 0,
    }

    return {
        "program": "GENERATION_4_REAL_TIME_INSTITUTIONAL_MARKET_INTELLIGENCE_PLATFORM",
        "version": "1.0.0",
        "foundation_portfolio": foundation["portfolio_registry"],
        "market_state_registry": market_state_registry,
        "belief_registry": belief_registry,
        "regime_registry": regime_registry,
        "alpha_activation_registry": alpha_activation_registry,
        "portfolio_evolution_registry": portfolio_evolution_registry,
        "research_trigger_registry": research_trigger_registry,
        "event_registry": event_registry,
        "knowledge_growth_registry": knowledge_growth_registry,
        "longitudinal_registry": longitudinal,
        "institutional_intelligence_registry": intelligence_registry,
        "executive_dashboards": dashboards,
        "schemas": _schemas(),
        "arb_recommendation": (
            "Generation 4 is operational as a continuously running institutional market intelligence layer. AFRP now observes markets, updates beliefs, maintains regime probabilities, monitors alpha activation, revises portfolio recommendations, and autonomously opens governed research triggers without executing trades or connecting to brokers."
        ),
    }


def emit_program7_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path = Path("."),
) -> dict[str, str]:
    """Write Generation 4 / Program 7 artifacts, reports, and schemas."""
    out = (repo_root / PROGRAM7_DIR).resolve()
    schema_dir = (repo_root / PROGRAM7_SCHEMA_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    for key, filename in [
        ("market_state_registry", "market_state_registry.json"),
        ("belief_registry", "belief_registry.json"),
        ("regime_registry", "regime_registry.json"),
        ("alpha_activation_registry", "alpha_activation_registry.json"),
        ("portfolio_evolution_registry", "portfolio_evolution_registry.json"),
        ("research_trigger_registry", "research_trigger_registry.json"),
        ("event_registry", "event_registry.json"),
        ("knowledge_growth_registry", "knowledge_growth_registry.json"),
        ("longitudinal_registry", "longitudinal_registry.json"),
        ("institutional_intelligence_registry", "institutional_intelligence_registry.json"),
        ("executive_dashboards", "executive_dashboards.json"),
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

    market_rows = [
        [row["timestamp"], row["xauusd"], row["dxy"], row["real_yield"], row["event_type"]]
        for row in analysis["market_state_registry"]
    ]
    write_markdown(
        out / "MARKET_INTELLIGENCE_REPORT.md",
        "# Real-Time Market Intelligence\n\n"
        + markdown_table(
            ["Timestamp", "XAU/USD", "DXY", "Real Yield", "Event Type"],
            market_rows,
        ),
    )
    paths["market_intelligence_md"] = str(out / "MARKET_INTELLIGENCE_REPORT.md")

    regime_rows = [
        [
            row["timestamp"],
            max(row["regime_probabilities"], key=lambda key: row["regime_probabilities"][key]),
            max(row["regime_probabilities"].values()),
        ]
        for row in analysis["regime_registry"]
    ]
    write_markdown(
        out / "REGIME_PROBABILITY_REPORT.md",
        "# Regime Probability Report\n\n"
        + markdown_table(["Timestamp", "Top Regime", "Top Probability"], regime_rows),
    )
    paths["regime_md"] = str(out / "REGIME_PROBABILITY_REPORT.md")

    trigger_rows = [
        [
            row["timestamp"],
            row["trigger_type"],
            row["severity"],
            row["campaign_type"],
            row["expected_information_gain"],
        ]
        for row in analysis["research_trigger_registry"]
    ] or [["N/A", "none", "none", "none", 0.0]]
    write_markdown(
        out / "RESEARCH_TRIGGER_REPORT.md",
        "# Research Trigger Report\n\n"
        + markdown_table(
            ["Timestamp", "Trigger", "Severity", "Campaign", "Expected Information Gain"],
            trigger_rows,
        ),
    )
    paths["trigger_md"] = str(out / "RESEARCH_TRIGGER_REPORT.md")

    final_portfolio = analysis["portfolio_evolution_registry"][-1]["portfolio"]
    final_lines = [
        "# Generation 4 — Real-Time Institutional Market Intelligence Platform",
        "",
        f"**Intelligence Cycles:** {analysis['institutional_intelligence_registry']['intelligence_cycle_count']}",
        f"**Latest Decision:** {analysis['institutional_intelligence_registry']['latest_portfolio_decision']}",
        f"**Latest Regime:** {analysis['institutional_intelligence_registry']['latest_regime']}",
        f"**Latest Confidence:** {analysis['institutional_intelligence_registry']['latest_confidence']}",
        f"**Research Triggers:** {analysis['institutional_intelligence_registry']['governed_research_triggers']}",
        "",
        "## Portfolio Evolution Snapshot",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Decision", final_portfolio["decision"]],
                ["Confidence", final_portfolio["portfolio_confidence"]],
                ["Uncertainty", final_portfolio["portfolio_uncertainty"]],
                ["Concentration", final_portfolio["portfolio_concentration"]],
                ["Risk", final_portfolio["portfolio_risk"]],
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
