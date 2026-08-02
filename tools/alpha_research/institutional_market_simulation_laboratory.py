"""Program 6 — Institutional Market Simulation and Paper Trading Laboratory."""

# ruff: noqa: E501

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from tools.alpha_research.institutional_alpha_portfolio_intelligence import (
    PORTFOLIO_DECISIONS,
    prepare_program5_artifacts,
)
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown
from tools.paper_trading.monitoring import compute_performance
from tools.paper_trading.portfolio import VirtualPortfolio
from tools.paper_trading.risk import RiskMonitor, alerts_to_dict
from tools.paper_trading.shadow_execution import (
    ExecutionConfig,
    OrderRequest,
    ShadowExecutionEngine,
)

PROGRAM6_DIR = Path("11-research") / "program-6-institutional-market-simulation-paper-trading-laboratory"
PROGRAM6_SCHEMA_DIR = Path("schemas") / "institutional-market-simulation"

_DECISION_SCORE: dict[str, float] = {
    "BUY": 1.0,
    "INCREASE": 0.6,
    "HOLD": 0.0,
    "REDUCE": -0.5,
    "SELL": -1.0,
    "NO POSITION": -0.2,
}

_REPLAY_MODES: list[str] = [
    "historical_replay",
    "walk_forward_replay",
    "rolling_replay",
    "multi_year_replay",
    "regime_replay",
    "event_replay",
    "shock_replay",
    "session_replay",
]

_REPLAY_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "replay_mode": "historical_replay",
        "timestamp": "2021-01-04T00:00:00Z",
        "regime": "BULL_TREND",
        "event": "post-pandemic growth rebound",
        "market_return": 0.0100,
        "volatility": 0.0120,
        "shock": 0.0100,
    },
    {
        "replay_mode": "walk_forward_replay",
        "timestamp": "2021-03-15T00:00:00Z",
        "regime": "RISK_ON",
        "event": "ETF accumulation continuation",
        "market_return": 0.0060,
        "volatility": 0.0110,
        "shock": 0.0080,
    },
    {
        "replay_mode": "rolling_replay",
        "timestamp": "2021-06-21T00:00:00Z",
        "regime": "MACRO_TRANSITION",
        "event": "hawkish central-bank repricing",
        "market_return": -0.0040,
        "volatility": 0.0150,
        "shock": 0.0140,
    },
    {
        "replay_mode": "multi_year_replay",
        "timestamp": "2021-09-30T00:00:00Z",
        "regime": "BEAR_TREND",
        "event": "real-yield normalization",
        "market_return": -0.0070,
        "volatility": 0.0160,
        "shock": 0.0150,
    },
    {
        "replay_mode": "regime_replay",
        "timestamp": "2021-12-20T00:00:00Z",
        "regime": "RISK_OFF",
        "event": "growth scare and safe-haven bid",
        "market_return": 0.0120,
        "volatility": 0.0200,
        "shock": 0.0250,
    },
    {
        "replay_mode": "event_replay",
        "timestamp": "2022-03-14T00:00:00Z",
        "regime": "LIQUIDITY_CRISIS",
        "event": "geopolitical shock",
        "market_return": 0.0180,
        "volatility": 0.0280,
        "shock": 0.0400,
    },
    {
        "replay_mode": "shock_replay",
        "timestamp": "2022-06-13T00:00:00Z",
        "regime": "MACRO_TRANSITION",
        "event": "inflation surprise and forced repricing",
        "market_return": -0.0090,
        "volatility": 0.0300,
        "shock": 0.0450,
    },
    {
        "replay_mode": "session_replay",
        "timestamp": "2022-09-27T00:00:00Z",
        "regime": "RISK_OFF",
        "event": "USD funding stress session",
        "market_return": 0.0110,
        "volatility": 0.0210,
        "shock": 0.0310,
    },
    {
        "replay_mode": "historical_replay",
        "timestamp": "2023-01-17T00:00:00Z",
        "regime": "BULL_TREND",
        "event": "commodity complex divergence",
        "market_return": 0.0070,
        "volatility": 0.0130,
        "shock": 0.0090,
    },
    {
        "replay_mode": "walk_forward_replay",
        "timestamp": "2023-04-24T00:00:00Z",
        "regime": "MACRO_TRANSITION",
        "event": "policy path uncertainty",
        "market_return": 0.0050,
        "volatility": 0.0140,
        "shock": 0.0120,
    },
    {
        "replay_mode": "rolling_replay",
        "timestamp": "2023-07-10T00:00:00Z",
        "regime": "RISK_ON",
        "event": "ETF persistence with benign growth",
        "market_return": 0.0080,
        "volatility": 0.0100,
        "shock": 0.0060,
    },
    {
        "replay_mode": "multi_year_replay",
        "timestamp": "2023-10-02T00:00:00Z",
        "regime": "BEAR_TREND",
        "event": "rates shock",
        "market_return": -0.0100,
        "volatility": 0.0220,
        "shock": 0.0300,
    },
    {
        "replay_mode": "regime_replay",
        "timestamp": "2024-01-29T00:00:00Z",
        "regime": "RISK_OFF",
        "event": "policy credibility stress",
        "market_return": 0.0090,
        "volatility": 0.0180,
        "shock": 0.0220,
    },
    {
        "replay_mode": "event_replay",
        "timestamp": "2024-04-15T00:00:00Z",
        "regime": "LIQUIDITY_CRISIS",
        "event": "cross-asset de-risking event",
        "market_return": 0.0140,
        "volatility": 0.0260,
        "shock": 0.0380,
    },
    {
        "replay_mode": "shock_replay",
        "timestamp": "2024-07-22T00:00:00Z",
        "regime": "MACRO_TRANSITION",
        "event": "real-rate overshoot",
        "market_return": 0.0040,
        "volatility": 0.0170,
        "shock": 0.0180,
    },
    {
        "replay_mode": "session_replay",
        "timestamp": "2024-10-07T00:00:00Z",
        "regime": "RISK_ON",
        "event": "session transition accumulation",
        "market_return": 0.0060,
        "volatility": 0.0120,
        "shock": 0.0070,
    },
]


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, round(value, 4)))


def _weighted_sum(values: list[float]) -> float:
    return round(sum(values), 4)


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


def _mean(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def _load_portfolio_foundation() -> dict[str, Any]:
    return prepare_program5_artifacts()


def _build_replay_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    price = 1875.0
    for index, row in enumerate(_REPLAY_BLUEPRINTS):
        price = round(price * (1.0 + float(row["market_return"])), 4)
        rows.append(
            {
                "sequence": index,
                "timestamp": row["timestamp"],
                "replay_mode": row["replay_mode"],
                "regime": row["regime"],
                "event": row["event"],
                "market_return": row["market_return"],
                "volatility": row["volatility"],
                "shock": row["shock"],
                "xauusd_price": price,
            }
        )
    return rows


def _initialize_alpha_state(portfolio_analysis: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return deepcopy(portfolio_analysis["approved_alpha_library"])


def _decay_action(confidence: float, drift: float, pnl_share: float) -> str:
    if confidence < 0.58 or drift > 0.28:
        return "retire"
    if confidence < 0.64 or drift > 0.22:
        return "suspend"
    if pnl_share < -0.03:
        return "revalidate"
    return "retain"


def _recompute_alpha_state(
    alpha_state: dict[str, dict[str, Any]],
    regime: str,
    market_return: float,
    volatility: float,
    shock: float,
    step_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    activity: list[dict[str, Any]] = []
    decay: list[dict[str, Any]] = []
    drift: list[dict[str, Any]] = []
    for mechanism, profile in alpha_state.items():
        base_confidence = float(profile["confidence"])
        regime_fit = float(profile["regime_relevance"][regime])
        direction = _DECISION_SCORE[str(profile["votes"][regime])]
        drift_score = _bounded(
            abs(float(shock) - regime_fit * 0.02) * 8.0
            + max(0.0, float(volatility) - 0.0180) * 5.0
            + step_index * 0.0020
        )
        confidence_drift = _bounded(abs(base_confidence - regime_fit))
        observation_drift = _bounded(float(volatility) * 10.0)
        knowledge_drift = _bounded(abs(direction * float(market_return)) * 4.0 + drift_score * 0.5)
        decay_score = _bounded(
            0.4 * drift_score
            + 0.3 * confidence_drift
            + 0.2 * max(0.0, float(profile["failure_severity"]) - 0.20)
            + 0.1 * max(0.0, 0.02 - direction * float(market_return))
        )
        updated_confidence = _bounded(base_confidence - 0.18 * drift_score + 0.05 * regime_fit)
        evidence_degradation = _bounded(drift_score * 0.7)
        activation_score = _bounded(
            0.45 * updated_confidence
            + 0.25 * regime_fit
            + 0.15 * float(profile["scientific_independence_score"])
            + 0.15 * float(profile["replication_quality"])
            - 0.20 * decay_score
        )
        status = (
            "active"
            if activation_score >= 0.66
            else "reduced"
            if activation_score >= 0.52
            else "suspended"
        )

        profile["confidence"] = updated_confidence
        profile["activation_score"] = activation_score
        profile["decay_score"] = decay_score
        profile["drift_score"] = drift_score
        profile["status"] = status

        activity.append(
            {
                "mechanism": mechanism,
                "regime": regime,
                "activation_score": activation_score,
                "confidence": updated_confidence,
                "status": status,
                "portfolio_vote": profile["votes"][regime],
            }
        )
        decay.append(
            {
                "mechanism": mechanism,
                "performance_degradation": _bounded(max(0.0, -direction * market_return * 8.0)),
                "confidence_degradation": _bounded(base_confidence - updated_confidence),
                "evidence_degradation": evidence_degradation,
                "concept_drift": drift_score,
                "capacity_decay": _bounded(max(0.0, float(volatility) - 0.0150) * 6.0),
                "regime_instability": _bounded(abs(regime_fit - 0.70)),
            }
        )
        drift.append(
            {
                "mechanism": mechanism,
                "feature_drift": _bounded(drift_score * 0.9),
                "distribution_drift": _bounded(abs(market_return) * 10.0),
                "regime_drift": _bounded(abs(regime_fit - 0.75)),
                "confidence_drift": confidence_drift,
                "market_drift": _bounded(abs(shock) * 8.0),
                "knowledge_drift": knowledge_drift,
                "observation_drift": observation_drift,
                "dataset_drift": _bounded(float(volatility) * 9.0),
            }
        )
    return activity, decay, drift


def _build_allocation(activity: list[dict[str, Any]], alpha_state: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    raw_scores = {
        row["mechanism"]: max(
            0.01,
            float(row["activation_score"]) * float(alpha_state[row["mechanism"]]["capacity_score"]),
        )
        for row in activity
    }
    total = sum(raw_scores.values())
    allocation = []
    for mechanism, score in sorted(raw_scores.items(), key=lambda item: item[1], reverse=True):
        weight = round(score / total, 4) if total else 0.0
        allocation.append(
            {
                "mechanism": mechanism,
                "allocation_weight": weight,
                "status": alpha_state[mechanism]["status"],
                "confidence": alpha_state[mechanism]["confidence"],
            }
        )
    if allocation:
        drift = round(1.0 - sum(float(item["allocation_weight"]) for item in allocation), 4)
        allocation[0]["allocation_weight"] = round(float(allocation[0]["allocation_weight"]) + drift, 4)
    return allocation


def _build_portfolio_decision(activity: list[dict[str, Any]], regime: str) -> dict[str, Any]:
    contributions: list[dict[str, Any]] = []
    scores: list[float] = []
    for row in activity:
        weight = _bounded(
            0.35 * float(row["confidence"]) + 0.35 * float(row["activation_score"]) + 0.30
        )
        vote = str(row["portfolio_vote"])
        weighted_score = round(weight * _DECISION_SCORE[vote], 4)
        scores.append(weighted_score)
        contributions.append(
            {
                "mechanism": row["mechanism"],
                "vote": vote,
                "vote_weight": weight,
                "weighted_score": weighted_score,
            }
        )
    mean_score = sum(scores) / max(len(scores), 1)
    return {
        "regime": regime,
        "decision": _decision_from_score(mean_score),
        "weighted_score": _bounded((mean_score + 1.0) / 2.0),
        "contributions": contributions,
    }


def _target_position_units(
    decision: str, equity: float, price: float, confidence: float
) -> float:
    base_units = max(1.0, round((equity * 0.08 / max(price, 1.0)), 4))
    scale = max(0.4, confidence)
    if decision == "BUY":
        return round(base_units * 1.20 * scale, 4)
    if decision == "INCREASE":
        return round(base_units * 0.70 * scale, 4)
    if decision == "SELL":
        return round(-base_units * 1.15 * scale, 4)
    if decision == "REDUCE":
        return round(-base_units * 0.60 * scale, 4)
    if decision == "NO POSITION":
        return 0.0
    return round(base_units * 0.15 * scale, 4)


def _rebalance_portfolio(
    portfolio: VirtualPortfolio,
    execution: ShadowExecutionEngine,
    timestamp: datetime,
    price: float,
    decision: dict[str, Any],
) -> dict[str, Any]:
    state = portfolio.state()
    current_position = portfolio.positions.get("XAUUSD")
    current_qty = current_position.quantity if current_position is not None else 0.0
    target_qty = _target_position_units(
        str(decision["decision"]),
        float(state["equity"]),
        price,
        float(decision["weighted_score"]),
    )
    delta = round(target_qty - float(current_qty), 4)
    if abs(delta) < 0.0001:
        portfolio.update_market_price("XAUUSD", price)
        return {"status": "skipped", "reason": "at_target", "fills": []}

    side = "buy" if delta > 0 else "sell"
    order = OrderRequest(
        order_id=f"P6-ORD-{timestamp.strftime('%Y%m%d%H%M%S')}",
        symbol="XAUUSD",
        side=side,
        quantity=abs(delta),
        decision_confidence=float(decision["weighted_score"]),
    )
    result = execution.execute(order=order, mid_price=price, now=timestamp)
    for fill in result.fills:
        portfolio.apply_fill(fill)
    portfolio.update_market_price("XAUUSD", price)
    return {
        "status": result.status,
        "reason": result.reason,
        "simulated_only": result.simulated_only,
        "fills": [
            {
                "fill_id": fill.fill_id,
                "side": fill.side,
                "quantity": fill.quantity,
                "price": fill.price,
                "status": fill.status,
            }
            for fill in result.fills
        ],
    }


def _rolling_var(returns: list[float], level: float = 0.95) -> float:
    if not returns:
        return 0.0
    ordered = sorted(returns)
    index = max(0, min(len(ordered) - 1, int((1.0 - level) * len(ordered))))
    return round(abs(ordered[index]), 4)


def _expected_shortfall(returns: list[float], level: float = 0.95) -> float:
    if not returns:
        return 0.0
    ordered = sorted(returns)
    threshold_index = max(1, int((1.0 - level) * len(ordered)))
    tail = ordered[:threshold_index]
    return round(abs(sum(tail) / len(tail)), 4) if tail else 0.0


def _performance_attribution(
    allocation: list[dict[str, Any]],
    activity: list[dict[str, Any]],
    alpha_state: dict[str, dict[str, Any]],
    market_return: float,
    price: float,
    decision: dict[str, Any],
) -> list[dict[str, Any]]:
    activity_index = {row["mechanism"]: row for row in activity}
    attribution: list[dict[str, Any]] = []
    for row in allocation:
        mechanism = str(row["mechanism"])
        profile = alpha_state[mechanism]
        activity_row = activity_index[mechanism]
        decision_direction = _DECISION_SCORE[str(activity_row["portfolio_vote"])]
        alpha_contribution = round(float(row["allocation_weight"]) * decision_direction * market_return * price, 4)
        attribution.append(
            {
                "mechanism": mechanism,
                "alpha_contribution": alpha_contribution,
                "regime_contribution": round(float(profile["regime_relevance"][decision["regime"]]) * float(row["allocation_weight"]), 4),
                "feature_contribution": round(float(profile["activation_score"]) * 0.35, 4),
                "evidence_contribution": round(float(profile["evidence_completeness"]) * 0.35, 4),
                "confidence_contribution": round(float(profile["confidence"]) * 0.35, 4),
                "risk_contribution": round(float(profile["failure_severity"]) * float(row["allocation_weight"]), 4),
                "dataset_contribution": round(len(profile["datasets"]) / 10.0, 4),
            }
        )
    return attribution


def _build_research_feedback(
    timestamp: str,
    decay: list[dict[str, Any]],
    drift: list[dict[str, Any]],
    risk: dict[str, Any],
) -> list[dict[str, Any]]:
    feedback: list[dict[str, Any]] = []
    for decay_row, drift_row in zip(decay, drift, strict=False):
        decay_score = max(
            float(decay_row["confidence_degradation"]),
            float(decay_row["concept_drift"]),
            float(drift_row["knowledge_drift"]),
        )
        if decay_score < 0.18:
            continue
        mechanism = str(decay_row["mechanism"])
        feedback.append(
            {
                "feedback_id": f"IKROS-RF-{timestamp.replace(':', '').replace('-', '')}-{mechanism[:6]}",
                "timestamp": timestamp,
                "mechanism": mechanism,
                "trigger": "persistent_degradation" if decay_score >= 0.24 else "drift",
                "recommended_action": (
                    "research_campaign" if decay_score >= 0.24 else "revalidation_request"
                ),
                "expected_information_gain": _bounded(decay_score + float(risk["tail_exposure"]) * 0.25),
                "ikros_update": f"Open Program 6 follow-up investigation for {mechanism}.",
            }
        )
    if float(risk["confidence_adjusted_drawdown"]) > 0.10:
        feedback.append(
            {
                "feedback_id": f"IKROS-RF-{timestamp.replace(':', '').replace('-', '')}-portfolio",
                "timestamp": timestamp,
                "mechanism": "portfolio",
                "trigger": "confidence_collapse",
                "recommended_action": "data_request",
                "expected_information_gain": _bounded(float(risk["confidence_adjusted_drawdown"]) + 0.10),
                "ikros_update": "Create governed portfolio degradation investigation and associated data request.",
            }
        )
    return feedback


def _risk_summary(
    timestamp: datetime,
    portfolio: VirtualPortfolio,
    confidence_history: list[float],
    market_return_history: list[float],
    volatility: float,
    alerts: list[dict[str, Any]],
    regime: str,
    allocation: list[dict[str, Any]],
    alpha_state: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    state = portfolio.state()
    var_95 = _rolling_var(market_return_history[-10:])
    es_95 = _expected_shortfall(market_return_history[-10:])
    concentration = max(float(item["allocation_weight"]) for item in allocation) if allocation else 0.0
    shared_failures = sorted(
        {
            failure
            for profile in alpha_state.values()
            for failure in profile["failure_modes"]
            if sum(failure in other["failure_modes"] for other in alpha_state.values()) > 1
        }
    )
    return {
        "timestamp": timestamp.isoformat(),
        "portfolio_var": var_95,
        "expected_shortfall": es_95,
        "confidence_adjusted_drawdown": _bounded(float(state["drawdown"]) * (1.0 + (1.0 - confidence_history[-1]))),
        "tail_exposure": _bounded(es_95 + volatility * 2.0),
        "concentration": round(concentration, 4),
        "regime_concentration": regime,
        "shared_failure_exposure": shared_failures,
        "alerts": alerts,
    }


def _simulation_schemas() -> dict[str, dict[str, Any]]:
    return {
        "paper-trade.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Paper Trade Record",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "decision", "execution", "portfolio_state"],
            "properties": {
                "timestamp": {"type": "string"},
                "decision": {"type": "string", "enum": PORTFOLIO_DECISIONS},
                "execution": {"type": "object"},
                "portfolio_state": {"type": "object"},
            },
        },
        "portfolio-history.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Portfolio History Entry",
            "type": "object",
            "additionalProperties": False,
            "required": ["timestamp", "equity", "cash", "allocation", "decision"],
            "properties": {
                "timestamp": {"type": "string"},
                "equity": {"type": "number"},
                "cash": {"type": "number"},
                "allocation": {"type": "array"},
                "decision": {"type": "string", "enum": PORTFOLIO_DECISIONS},
            },
        },
        "performance.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Simulation Performance Summary",
            "type": "object",
            "additionalProperties": False,
            "required": ["total_return", "sharpe", "sortino", "max_drawdown", "win_rate"],
            "properties": {
                "total_return": {"type": "number"},
                "sharpe": {"type": "number"},
                "sortino": {"type": "number"},
                "max_drawdown": {"type": "number"},
                "win_rate": {"type": "number"},
            },
        },
        "attribution.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Attribution Entry",
            "type": "object",
            "additionalProperties": False,
            "required": ["mechanism", "alpha_contribution", "regime_contribution", "confidence_contribution"],
            "properties": {
                "mechanism": {"type": "string"},
                "alpha_contribution": {"type": "number"},
                "regime_contribution": {"type": "number"},
                "feature_contribution": {"type": "number"},
                "evidence_contribution": {"type": "number"},
                "confidence_contribution": {"type": "number"},
                "risk_contribution": {"type": "number"},
                "dataset_contribution": {"type": "number"},
            },
        },
        "drift.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Drift Entry",
            "type": "object",
            "additionalProperties": False,
            "required": ["mechanism", "feature_drift", "distribution_drift", "regime_drift", "knowledge_drift"],
            "properties": {
                "mechanism": {"type": "string"},
                "feature_drift": {"type": "number"},
                "distribution_drift": {"type": "number"},
                "regime_drift": {"type": "number"},
                "confidence_drift": {"type": "number"},
                "market_drift": {"type": "number"},
                "knowledge_drift": {"type": "number"},
                "observation_drift": {"type": "number"},
                "dataset_drift": {"type": "number"},
            },
        },
        "decay.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Alpha Decay Entry",
            "type": "object",
            "additionalProperties": False,
            "required": ["mechanism", "performance_degradation", "confidence_degradation", "concept_drift", "regime_instability"],
            "properties": {
                "mechanism": {"type": "string"},
                "performance_degradation": {"type": "number"},
                "confidence_degradation": {"type": "number"},
                "evidence_degradation": {"type": "number"},
                "concept_drift": {"type": "number"},
                "capacity_decay": {"type": "number"},
                "regime_instability": {"type": "number"},
            },
        },
        "research-feedback.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Research Feedback Entry",
            "type": "object",
            "additionalProperties": False,
            "required": ["feedback_id", "timestamp", "trigger", "recommended_action", "expected_information_gain"],
            "properties": {
                "feedback_id": {"type": "string"},
                "timestamp": {"type": "string"},
                "mechanism": {"type": "string"},
                "trigger": {"type": "string"},
                "recommended_action": {"type": "string"},
                "expected_information_gain": {"type": "number"},
                "ikros_update": {"type": "string"},
            },
        },
    }


def prepare_program6_artifacts() -> dict[str, Any]:
    """Construct the deterministic institutional simulation laboratory."""
    portfolio_analysis = _load_portfolio_foundation()
    alpha_state = _initialize_alpha_state(portfolio_analysis)
    replay_rows = _build_replay_rows()
    portfolio = VirtualPortfolio(initial_cash=1_000_000.0)
    execution = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.20, random_seed=42)
    )
    risk_monitor = RiskMonitor()

    paper_trade_registry: list[dict[str, Any]] = []
    portfolio_history: list[dict[str, Any]] = []
    confidence_history: list[float] = []
    risk_history: list[dict[str, Any]] = []
    performance_history: list[dict[str, Any]] = []
    attribution_history: list[dict[str, Any]] = []
    decay_registry: list[dict[str, Any]] = []
    drift_registry: list[dict[str, Any]] = []
    research_feedback_registry: list[dict[str, Any]] = []
    live_portfolio_dashboard: list[list[object]] = []
    market_return_history: list[float] = []
    trade_pnls: list[float] = []
    exposures: list[float] = []
    research_priorities: list[dict[str, Any]] = []

    last_price = replay_rows[0]["xauusd_price"]
    portfolio.update_market_price("XAUUSD", last_price)

    for step in replay_rows:
        timestamp = datetime.fromisoformat(str(step["timestamp"]).replace("Z", "+00:00"))
        regime = str(step["regime"])
        market_return = float(step["market_return"])
        volatility = float(step["volatility"])
        shock = float(step["shock"])
        market_return_history.append(market_return)

        activity, decay_rows, drift_rows = _recompute_alpha_state(
            alpha_state=alpha_state,
            regime=regime,
            market_return=market_return,
            volatility=volatility,
            shock=shock,
            step_index=int(step["sequence"]),
        )
        allocation = _build_allocation(activity, alpha_state)
        decision = _build_portfolio_decision(activity, regime)
        execution_result = _rebalance_portfolio(
            portfolio=portfolio,
            execution=execution,
            timestamp=timestamp,
            price=float(step["xauusd_price"]),
            decision=decision,
        )
        state_mark = portfolio.mark(timestamp)
        confidence_now = _mean([float(item["confidence"]) for item in activity])
        confidence_history.append(confidence_now)
        exposures.append(float(state_mark["gross_exposure"]))
        trade_pnls.append(float(state_mark["total_pnl"]))

        alerts = alerts_to_dict(
            risk_monitor.evaluate(
                when=timestamp,
                portfolio_state=portfolio.state(),
                position_notional=abs(float(portfolio.state()["net_exposure"])),
                confidence_values=confidence_history,
                volatility=volatility,
                position_notionals=[
                    abs(position.market_price * position.quantity)
                    for position in portfolio.positions.values()
                    if abs(position.quantity) > 1e-12
                ],
            )
        )
        risk_row = _risk_summary(
            timestamp=timestamp,
            portfolio=portfolio,
            confidence_history=confidence_history,
            market_return_history=market_return_history,
            volatility=volatility,
            alerts=alerts,
            regime=regime,
            allocation=allocation,
            alpha_state=alpha_state,
        )
        attribution_rows = _performance_attribution(
            allocation=allocation,
            activity=activity,
            alpha_state=alpha_state,
            market_return=market_return,
            price=float(step["xauusd_price"]),
            decision=decision,
        )
        feedback_rows = _build_research_feedback(
            timestamp=timestamp.isoformat(),
            decay=decay_rows,
            drift=drift_rows,
            risk=risk_row,
        )
        current_perf = compute_performance(
            equity=[float(point["equity"]) for point in portfolio_history[-10:]] + [float(state_mark["equity"])],
            trade_pnls=trade_pnls[-10:],
            exposures=exposures[-10:],
            risk_free_rate=0.01,
        )

        paper_trade_registry.append(
            {
                "timestamp": timestamp.isoformat(),
                "replay_mode": step["replay_mode"],
                "market_observation": step,
                "decision": decision["decision"],
                "execution": execution_result,
                "portfolio_state": portfolio.to_dict(),
                "confidence": confidence_now,
            }
        )
        portfolio_history.append(
            {
                "timestamp": timestamp.isoformat(),
                "equity": float(state_mark["equity"]),
                "cash": float(state_mark["cash"]),
                "allocation": allocation,
                "decision": decision["decision"],
                "regime": regime,
            }
        )
        risk_history.append(risk_row)
        performance_history.append(
            {
                "timestamp": timestamp.isoformat(),
                "replay_mode": step["replay_mode"],
                "total_return": round(current_perf.total_return, 4),
                "sharpe": round(current_perf.sharpe, 4),
                "sortino": round(current_perf.sortino, 4),
                "calmar": round(current_perf.calmar, 4),
                "max_drawdown": round(current_perf.max_drawdown, 4),
                "win_rate": round(current_perf.win_rate, 4),
            }
        )
        attribution_history.append(
            {
                "timestamp": timestamp.isoformat(),
                "decision": decision["decision"],
                "attribution": attribution_rows,
            }
        )
        decay_registry.append(
            {
                "timestamp": timestamp.isoformat(),
                "replay_mode": step["replay_mode"],
                "entries": [
                    {
                        **row,
                        "recommended_action": _decay_action(
                            confidence=float(alpha_state[row["mechanism"]]["confidence"]),
                            drift=float(alpha_state[row["mechanism"]]["drift_score"]),
                            pnl_share=float(state_mark["total_pnl"]) / 1_000_000.0,
                        ),
                    }
                    for row in decay_rows
                ],
            }
        )
        drift_registry.append(
            {
                "timestamp": timestamp.isoformat(),
                "replay_mode": step["replay_mode"],
                "entries": drift_rows,
            }
        )
        research_feedback_registry.extend(feedback_rows)
        research_priorities.append(
            {
                "timestamp": timestamp.isoformat(),
                "priority": "HIGH" if feedback_rows else "NORMAL",
                "feedback_count": len(feedback_rows),
                "focus": "portfolio_revalidation" if feedback_rows else "portfolio_monitoring",
            }
        )
        last_price = float(step["xauusd_price"])
        live_portfolio_dashboard = [
            ["Timestamp", timestamp.isoformat()],
            ["Regime", regime],
            ["Decision", decision["decision"]],
            ["Portfolio Confidence", confidence_now],
            ["Portfolio Equity", float(state_mark["equity"])],
        ]

    final_equity = float(portfolio_history[-1]["equity"])
    final_performance = compute_performance(
        equity=[float(point["equity"]) for point in portfolio_history],
        trade_pnls=trade_pnls,
        exposures=exposures,
        risk_free_rate=0.01,
    )
    continuous_performance_database = {
        "daily_portfolio": portfolio_history,
        "daily_alpha_activity": [
            {
                "timestamp": row["timestamp"],
                "activity": [
                    {
                        "mechanism": item["mechanism"],
                        "allocation_weight": item["allocation_weight"],
                        "status": item["status"],
                    }
                    for item in row["allocation"]
                ],
            }
            for row in portfolio_history
        ],
        "portfolio_decisions": [
            {"timestamp": row["timestamp"], "decision": row["decision"], "regime": row["regime"]}
            for row in portfolio_history
        ],
        "confidence_history": [
            {"timestamp": row["timestamp"], "confidence": round(confidence_history[index], 4)}
            for index, row in enumerate(portfolio_history)
        ],
        "risk_history": risk_history,
        "pnl_history": [
            {"timestamp": row["timestamp"], "total_pnl": round(float(row["equity"]) - 1_000_000.0, 4)}
            for row in portfolio_history
        ],
        "regime_history": [
            {"timestamp": row["timestamp"], "regime": row["regime"]} for row in portfolio_history
        ],
        "attribution_history": attribution_history,
    }
    portfolio_performance_registry = {
        "portfolio_id": portfolio_analysis["portfolio_registry"]["portfolio_id"],
        "simulation_steps": len(replay_rows),
        "final_equity": round(final_equity, 4),
        "total_return": round(final_performance.total_return, 4),
        "sharpe": round(final_performance.sharpe, 4),
        "sortino": round(final_performance.sortino, 4),
        "calmar": round(final_performance.calmar, 4),
        "max_drawdown": round(final_performance.max_drawdown, 4),
        "win_rate": round(final_performance.win_rate, 4),
        "profit_factor": round(final_performance.profit_factor, 4),
    }
    live_market_monitor = {
        "symbol": "XAU/USD",
        "current_price": last_price,
        "current_regime": portfolio_history[-1]["regime"],
        "portfolio_recommendation": portfolio_history[-1]["decision"],
        "confidence": round(confidence_history[-1], 4),
        "risk": risk_history[-1],
        "alpha_activation": portfolio_history[-1]["allocation"],
        "research_queue": research_priorities[-5:],
    }
    dashboards = {
        "live_portfolio_dashboard": {"tiles": live_portfolio_dashboard},
        "paper_trading_dashboard": {
            "tiles": [
                ["Trades Logged", len(paper_trade_registry)],
                ["Final Equity", round(final_equity, 4)],
                ["Decision", portfolio_history[-1]["decision"]],
            ]
        },
        "performance_dashboard": {
            "tiles": [
                ["Total Return", portfolio_performance_registry["total_return"]],
                ["Sharpe", portfolio_performance_registry["sharpe"]],
                ["Max Drawdown", portfolio_performance_registry["max_drawdown"]],
            ]
        },
        "attribution_dashboard": {
            "tiles": [
                [row["attribution"][0]["mechanism"], row["attribution"][0]["alpha_contribution"]]
                for row in attribution_history[-5:]
            ]
        },
        "alpha_activity_dashboard": {
            "tiles": [
                [item["mechanism"], item["status"]]
                for item in portfolio_history[-1]["allocation"]
            ]
        },
        "decay_dashboard": {
            "tiles": [
                [entry["mechanism"], entry["recommended_action"]]
                for entry in decay_registry[-1]["entries"]
            ]
        },
        "risk_dashboard": {
            "tiles": [
                ["VaR", risk_history[-1]["portfolio_var"]],
                ["Expected Shortfall", risk_history[-1]["expected_shortfall"]],
                ["Tail Exposure", risk_history[-1]["tail_exposure"]],
            ]
        },
        "research_feedback_dashboard": {
            "tiles": [
                [row["mechanism"], row["recommended_action"]]
                for row in research_feedback_registry[-5:]
            ]
            or [["portfolio", "monitor_only"]]
        },
    }

    return {
        "program": "INSTITUTIONAL_MARKET_SIMULATION_PAPER_TRADING_LABORATORY",
        "version": "1.0.0",
        "portfolio_registry": portfolio_analysis["portfolio_registry"],
        "market_replay_engine": {
            "supported_modes": _REPLAY_MODES,
            "replay_rows": replay_rows,
            "preserves_temporal_ordering": True,
        },
        "paper_trade_registry": paper_trade_registry,
        "portfolio_performance_registry": portfolio_performance_registry,
        "performance_attribution_registry": attribution_history,
        "portfolio_evolution_engine": portfolio_history,
        "alpha_decay_registry": decay_registry,
        "drift_registry": drift_registry,
        "risk_monitoring_registry": risk_history,
        "live_market_monitor": live_market_monitor,
        "continuous_performance_database": continuous_performance_database,
        "research_feedback_registry": research_feedback_registry,
        "institutional_dashboards": dashboards,
        "schemas": _simulation_schemas(),
        "arb_recommendation": (
            "Program 6 is ready as a governed non-executing simulation laboratory. AFRP can continuously replay markets, maintain a paper-trading portfolio, attribute performance, detect drift and decay, and feed governed research back into IKROS without any broker connectivity or live order flow."
        ),
    }


def emit_program6_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path = Path("."),
) -> dict[str, str]:
    """Write Program 6 reports, artifacts, and schemas."""
    out = (repo_root / PROGRAM6_DIR).resolve()
    schema_dir = (repo_root / PROGRAM6_SCHEMA_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    for key, filename in [
        ("market_replay_engine", "market_replay_engine.json"),
        ("paper_trade_registry", "paper_trade_registry.json"),
        ("portfolio_performance_registry", "portfolio_performance_registry.json"),
        ("performance_attribution_registry", "performance_attribution_registry.json"),
        ("portfolio_evolution_engine", "portfolio_evolution_engine.json"),
        ("alpha_decay_registry", "alpha_decay_registry.json"),
        ("drift_registry", "drift_registry.json"),
        ("risk_monitoring_registry", "risk_monitoring_registry.json"),
        ("live_market_monitor", "live_market_monitor.json"),
        ("continuous_performance_database", "continuous_performance_database.json"),
        ("research_feedback_registry", "research_feedback_registry.json"),
        ("institutional_dashboards", "institutional_dashboards.json"),
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

    replay_rows = [
        [
            row["timestamp"],
            row["replay_mode"],
            row["regime"],
            row["market_return"],
            row["xauusd_price"],
        ]
        for row in analysis["market_replay_engine"]["replay_rows"]
    ]
    write_markdown(
        out / "MARKET_REPLAY_REPORT.md",
        "# Market Replay Engine\n\n"
        + markdown_table(
            ["Timestamp", "Replay Mode", "Regime", "Market Return", "Price"],
            replay_rows,
        ),
    )
    paths["market_replay_md"] = str(out / "MARKET_REPLAY_REPORT.md")

    trade_rows = [
        [
            row["timestamp"],
            row["replay_mode"],
            row["decision"],
            row["execution"]["status"],
            row["portfolio_state"]["state"]["equity"],
        ]
        for row in analysis["paper_trade_registry"]
    ]
    write_markdown(
        out / "PAPER_TRADING_REPORT.md",
        "# Paper Trading Report\n\n"
        + markdown_table(
            ["Timestamp", "Replay Mode", "Decision", "Execution", "Equity"],
            trade_rows,
        ),
    )
    paths["paper_trading_md"] = str(out / "PAPER_TRADING_REPORT.md")

    drift_rows = [
        [
            item["timestamp"],
            entry["mechanism"],
            entry["feature_drift"],
            entry["regime_drift"],
            entry["knowledge_drift"],
        ]
        for item in analysis["drift_registry"]
        for entry in item["entries"]
    ]
    write_markdown(
        out / "DRIFT_AND_DECAY_REPORT.md",
        "# Drift and Decay Report\n\n"
        + markdown_table(
            ["Timestamp", "Mechanism", "Feature Drift", "Regime Drift", "Knowledge Drift"],
            drift_rows,
        ),
    )
    paths["drift_decay_md"] = str(out / "DRIFT_AND_DECAY_REPORT.md")

    feedback_rows = [
        [
            row["timestamp"],
            row["mechanism"],
            row["trigger"],
            row["recommended_action"],
            row["expected_information_gain"],
        ]
        for row in analysis["research_feedback_registry"]
    ] or [["N/A", "portfolio", "none", "monitor_only", 0.0]]
    write_markdown(
        out / "RESEARCH_FEEDBACK_REPORT.md",
        "# Research Feedback Report\n\n"
        + markdown_table(
            ["Timestamp", "Mechanism", "Trigger", "Action", "Expected Information Gain"],
            feedback_rows,
        ),
    )
    paths["research_feedback_md"] = str(out / "RESEARCH_FEEDBACK_REPORT.md")

    final_lines = [
        "# Program 6 — Institutional Market Simulation & Paper Trading Laboratory",
        "",
        f"**Portfolio ID:** {analysis['portfolio_registry']['portfolio_id']}",
        f"**Simulation Steps:** {analysis['portfolio_performance_registry']['simulation_steps']}",
        f"**Final Equity:** {analysis['portfolio_performance_registry']['final_equity']}",
        f"**Total Return:** {analysis['portfolio_performance_registry']['total_return']}",
        f"**Sharpe:** {analysis['portfolio_performance_registry']['sharpe']}",
        "",
        "## Live Monitor",
        "",
        f"- Regime: {analysis['live_market_monitor']['current_regime']}",
        f"- Recommendation: {analysis['live_market_monitor']['portfolio_recommendation']}",
        f"- Confidence: {analysis['live_market_monitor']['confidence']}",
        "",
        "## ARB Recommendation",
        "",
        analysis["arb_recommendation"],
    ]
    write_markdown(out / "FINAL_REPORT.md", "\n".join(final_lines))
    paths["final_report"] = str(out / "FINAL_REPORT.md")
    return paths
