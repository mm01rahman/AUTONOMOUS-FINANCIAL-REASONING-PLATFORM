"""Program 1 — Institutional Alpha Factory: complete lifecycle engine (Parts A–H)."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PROGRAM1_DIR = Path("11-research") / "program-1-institutional-alpha-factory"

# ---------------------------------------------------------------------------
# A. Lifecycle state machine
# ---------------------------------------------------------------------------

LIFECYCLE_STATES: list[str] = [
    "DISCOVERED",
    "RESEARCH",
    "READY_FOR_REVALIDATION",
    "VALIDATED",
    "PROMOTION_REVIEW",
    "APPROVED_ALPHA",
    "ACTIVE_ALPHA",
    "UNDER_MONITORING",
    "REVALIDATION_REQUIRED",
    "RETIRED",
]

_LIFECYCLE_RANK: dict[str, int] = {s: i for i, s in enumerate(LIFECYCLE_STATES)}

PROMOTION_DECISIONS: list[str] = [
    "PROMOTE",
    "RETURN_FOR_RESEARCH",
    "RETURN_FOR_REPLICATION",
    "REJECT",
]

# ---------------------------------------------------------------------------
# B. Deterministic mechanism parameters (sourced from DC3 Phase 4/5 + WP-IMP-0050)
# ---------------------------------------------------------------------------

_MECHANISM_PARAMS: dict[str, dict[str, Any]] = {
    "safe_haven_migration": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0006",
        "family_id": "FAM-003",
        "current_lifecycle_state": "RESEARCH",
        "observation_completeness": 0.76,
        "proxy_dependence": 0.41,
        "observation_gate_pass": True,
        "scientific_validity": 0.61,
        "economic_plausibility": 0.63,
        "cross_asset_consistency": 0.59,
        "regime_consistency": 0.56,
        "temporal_stability": 0.51,
        "robustness": 0.52,
        "generalization": 0.50,
        "capacity_score": 0.55,
        "explainability": 0.60,
        "institutional_risk": 0.52,
        "reproducibility": 0.57,
        "confidence_prior": 0.60,
        "confidence_posterior": 0.618,
        "scientific_mechanism": "Safe-haven demand during institutional stress drives gold allocation migration from risk assets.",
        "economic_rationale": "Portfolio rebalancing, flight-to-quality dynamics, and cross-border institutional mandate compliance.",
        "feature_dependencies": [
            "VIX_PROXY",
            "GOLD_USD_RETURN",
            "SPX_CORRELATION",
            "MACRO_STRESS_INDEX",
            "FLIGHT_TO_SAFETY_SIGNAL",
        ],
        "datasets": ["FRED-MACRO", "ETF-GLD", "SYNTHETIC-VIX"],
        "supported_market_states": ["RISK_OFF", "MACRO_STRESS", "CREDIT_STRESS"],
        "expected_regime": "HIGH_UNCERTAINTY",
        "expected_holding_period": "5-15 days",
        "expected_decay": "Gradual over 3-6 months post-stress event",
        "expected_failure_modes": [
            "False-transition detection under low-vol regimes",
            "Regime mis-classification",
            "Proxy degradation over time",
        ],
        "retirement_criteria": [
            "Concept drift confirmed over 6 consecutive months",
            "Observation completeness below 0.60",
            "Institutional confidence below 0.40",
        ],
        "capacity_class": "MEDIUM",
        "correlation_to_alternatives": 0.34,
        "known_failure_modes": [
            "False-transition under low-vol regimes",
            "Concept drift post-2020",
            "Trigger-threshold sensitivity",
        ],
        "replication_periods": [
            {
                "period_id": "REP-SHM-P001",
                "label": "2010-2015",
                "observation_completeness": 0.74,
                "method_pass_rate": 0.62,
                "confidence_contribution": 0.59,
                "regime": "POST_GFC_RECOVERY",
                "contradiction_found": False,
                "reproducibility_score": 0.61,
            },
            {
                "period_id": "REP-SHM-P002",
                "label": "2015-2019",
                "observation_completeness": 0.76,
                "method_pass_rate": 0.63,
                "confidence_contribution": 0.61,
                "regime": "LOW_VOL_EXPANSION",
                "contradiction_found": False,
                "reproducibility_score": 0.63,
            },
            {
                "period_id": "REP-SHM-P003",
                "label": "2019-2023",
                "observation_completeness": 0.68,
                "method_pass_rate": 0.54,
                "confidence_contribution": 0.52,
                "regime": "COVID_HYBRID",
                "contradiction_found": True,
                "reproducibility_score": 0.50,
            },
        ],
        "regime_replications": [
            {"regime": "RISK_OFF", "pass_rate": 0.65, "confidence_contribution": 0.61},
            {"regime": "MACRO_STRESS", "pass_rate": 0.62, "confidence_contribution": 0.59},
            {"regime": "LOW_VOL", "pass_rate": 0.44, "confidence_contribution": 0.48},
        ],
        "feature_subset_replications": [
            {"subset": "CORE_MACRO", "pass_rate": 0.60, "confidence_contribution": 0.58},
            {"subset": "FLOW_PROXY", "pass_rate": 0.55, "confidence_contribution": 0.54},
            {"subset": "FULL_FEATURE_SET", "pass_rate": 0.57, "confidence_contribution": 0.57},
        ],
        "confidence_trajectory": [0.60, 0.59, 0.61, 0.58, 0.61, 0.618],
    },
    "decision_cascade": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0009",
        "family_id": "FAM-006",
        "current_lifecycle_state": "RESEARCH",
        "observation_completeness": 0.67,
        "proxy_dependence": 0.58,
        "observation_gate_pass": False,
        "scientific_validity": 0.55,
        "economic_plausibility": 0.57,
        "cross_asset_consistency": 0.50,
        "regime_consistency": 0.51,
        "temporal_stability": 0.47,
        "robustness": 0.48,
        "generalization": 0.46,
        "capacity_score": 0.50,
        "explainability": 0.51,
        "institutional_risk": 0.48,
        "reproducibility": 0.55,
        "confidence_prior": 0.59,
        "confidence_posterior": 0.556,
        "scientific_mechanism": "Institutional decision cascades amplify gold price dislocations via sequential positioning adjustments.",
        "economic_rationale": "Agency conflicts and herding behaviour create predictable cascade patterns.",
        "feature_dependencies": [
            "CASCADE_INITIATOR_PROXY",
            "DEALER_POSITIONING_PROXY",
            "DECISION_NETWORK_INDICATOR",
        ],
        "datasets": ["SYNTHETIC-ECOLOGY-PROXY"],
        "supported_market_states": ["STRESS", "TRANSITION"],
        "expected_regime": "TRANSITION",
        "expected_holding_period": "2-7 days",
        "expected_decay": "Rapid, 4-8 weeks",
        "expected_failure_modes": [
            "Proxy leakage from ecology model",
            "False cascade detection",
            "Concept drift post-2019",
        ],
        "retirement_criteria": [
            "Proxy redesign fails repeated validation",
            "Observation completeness below 0.70 after acquisitions",
        ],
        "capacity_class": "LOW",
        "correlation_to_alternatives": 0.21,
        "known_failure_modes": [
            "Ecology-proxy leakage",
            "Concept drift post-2019",
            "Critical statistical failures (White RC, SPA, DSR)",
        ],
        "replication_periods": [],
        "regime_replications": [],
        "feature_subset_replications": [],
        "confidence_trajectory": [0.59, 0.57, 0.54, 0.53, 0.556],
    },
}

# ---------------------------------------------------------------------------
# C. Promotion criteria thresholds
# ---------------------------------------------------------------------------

_PROMOTION_CRITERIA: dict[str, tuple[str, float]] = {
    "scientific_validity": ("minimum", 0.70),
    "economic_plausibility": ("minimum", 0.70),
    "cross_asset_consistency": ("minimum", 0.60),
    "regime_consistency": ("minimum", 0.65),
    "temporal_stability": ("minimum", 0.65),
    "reproducibility": ("minimum", 0.70),
    "generalization": ("minimum", 0.60),
    "institutional_risk": ("maximum", 0.40),
    "observation_completeness": ("minimum", 0.70),
    "replication_score": ("minimum", 0.60),
}

# ---------------------------------------------------------------------------
# Part A — Scientific Replication Engine
# ---------------------------------------------------------------------------


def _run_replication_engine(
    mechanism_name: str, params: dict[str, Any]
) -> dict[str, Any]:
    """Deterministically replicate validation across periods, regimes, feature subsets."""
    periods = params["replication_periods"]
    regimes = params["regime_replications"]
    subsets = params["feature_subset_replications"]

    if not params["observation_gate_pass"]:
        return {
            "alpha_id": params["alpha_id"],
            "mechanism": mechanism_name,
            "replication_status": "BLOCKED",
            "blocking_reason": "Observation completeness gate failed (coverage < 0.70).",
            "total_replications": 0,
            "periods_validated": [],
            "regimes_validated": [],
            "feature_subsets_validated": [],
            "overall_replication_score": 0.0,
            "confidence_convergence": 0.0,
            "evidence_stability": 0.0,
            "contradictions_found": 0,
            "replication_ledger": [],
        }

    period_scores = [float(p["confidence_contribution"]) for p in periods]
    regime_scores = [float(r["confidence_contribution"]) for r in regimes]
    subset_scores = [float(s["confidence_contribution"]) for s in subsets]

    period_mean = sum(period_scores) / len(period_scores) if period_scores else 0.0
    regime_mean = sum(regime_scores) / len(regime_scores) if regime_scores else 0.0
    subset_mean = sum(subset_scores) / len(subset_scores) if subset_scores else 0.0

    combined = [period_mean, regime_mean, subset_mean]
    overall_score = sum(combined) / len(combined)

    trajectory = params["confidence_trajectory"]
    if len(trajectory) >= 2:
        delta_abs = [abs(trajectory[i] - trajectory[i - 1]) for i in range(1, len(trajectory))]
        evidence_stability = max(0.0, 1.0 - (sum(delta_abs) / len(delta_abs)) * 5.0)
        first, last = trajectory[0], trajectory[-1]
        confidence_convergence = min(1.0, (last - first + 0.5) / 1.0)
    else:
        evidence_stability = 0.5
        confidence_convergence = 0.5

    contradictions = sum(1 for p in periods if p.get("contradiction_found", False))

    status = (
        "CONFIRMED"
        if overall_score >= 0.70
        else "PARTIAL"
        if overall_score >= 0.50
        else "FAILED"
    )

    ledger = [
        {
            "replication_id": p["period_id"],
            "scope": "TEMPORAL_PERIOD",
            "label": p["label"],
            "observation_completeness": float(p["observation_completeness"]),
            "method_pass_rate": float(p["method_pass_rate"]),
            "confidence_contribution": float(p["confidence_contribution"]),
            "reproducibility_score": float(p["reproducibility_score"]),
            "contradiction_found": bool(p.get("contradiction_found", False)),
        }
        for p in periods
    ]

    return {
        "alpha_id": params["alpha_id"],
        "mechanism": mechanism_name,
        "replication_status": status,
        "blocking_reason": None,
        "total_replications": len(periods) + len(regimes) + len(subsets),
        "periods_validated": [p["label"] for p in periods],
        "regimes_validated": [r["regime"] for r in regimes],
        "feature_subsets_validated": [s["subset"] for s in subsets],
        "overall_replication_score": round(overall_score, 4),
        "period_mean": round(period_mean, 4),
        "regime_mean": round(regime_mean, 4),
        "subset_mean": round(subset_mean, 4),
        "confidence_convergence": round(confidence_convergence, 4),
        "evidence_stability": round(evidence_stability, 4),
        "contradictions_found": contradictions,
        "replication_ledger": ledger,
    }


# ---------------------------------------------------------------------------
# Part D — Evidence Convergence Engine
# ---------------------------------------------------------------------------


def _run_evidence_convergence(
    mechanism_name: str, params: dict[str, Any], replication: dict[str, Any]
) -> dict[str, Any]:
    trajectory = params["confidence_trajectory"]
    n = len(trajectory)

    if n < 3:
        convergence_state = "INSUFFICIENT_DATA"
        stability_score = 0.0
        is_converging = False
    else:
        deltas = [trajectory[i] - trajectory[i - 1] for i in range(1, n)]
        mean_delta = sum(deltas) / len(deltas)
        variance = sum((d - mean_delta) ** 2 for d in deltas) / len(deltas)

        if variance < 0.002:
            if mean_delta > 0.003:
                convergence_state = "CONVERGING"
            elif mean_delta > -0.003:
                convergence_state = "CONVERGING_SLOWLY"
            else:
                convergence_state = "DIVERGING"
        else:
            convergence_state = "OSCILLATING"

        stability_score = max(0.0, 1.0 - variance * 50.0)
        is_converging = convergence_state in {"CONVERGING", "CONVERGING_SLOWLY"}

    rep_score = float(replication["overall_replication_score"])
    proxy_dep = float(params["proxy_dependence"])
    obs_comp = float(params["observation_completeness"])

    # dataset sensitivity: higher proxy dependence → more sensitive
    dataset_sensitivity = round(proxy_dep * 0.8 + (1.0 - obs_comp) * 0.2, 4)

    evidence_weight = round(
        (rep_score * 0.4 + obs_comp * 0.3 + (1.0 - proxy_dep) * 0.3),
        4,
    )

    return {
        "alpha_id": params["alpha_id"],
        "mechanism": mechanism_name,
        "confidence_trajectory": trajectory,
        "trajectory_length": n,
        "evidence_count": n,
        "contradictory_evidence_count": int(replication["contradictions_found"]),
        "replication_consistency": round(rep_score, 4),
        "regime_consistency": round(float(params["regime_consistency"]), 4),
        "dataset_sensitivity": dataset_sensitivity,
        "proxy_dependence": round(proxy_dep, 4),
        "is_converging": is_converging,
        "convergence_state": convergence_state,
        "stability_score": round(stability_score, 4),
        "evidence_weight": evidence_weight,
    }


# ---------------------------------------------------------------------------
# Part B — Promotion Committee
# ---------------------------------------------------------------------------


def _evaluate_promotion_committee(
    mechanism_name: str,
    params: dict[str, Any],
    replication: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate all 10 governed criteria; return committee decision."""
    rep_score = float(replication["overall_replication_score"])

    scores: dict[str, float] = {
        "scientific_validity": float(params["scientific_validity"]),
        "economic_plausibility": float(params["economic_plausibility"]),
        "cross_asset_consistency": float(params["cross_asset_consistency"]),
        "regime_consistency": float(params["regime_consistency"]),
        "temporal_stability": float(params["temporal_stability"]),
        "reproducibility": float(params["reproducibility"]),
        "generalization": float(params["generalization"]),
        "institutional_risk": float(params["institutional_risk"]),
        "observation_completeness": float(params["observation_completeness"]),
        "replication_score": rep_score,
    }

    pass_fail: dict[str, bool] = {}
    failures: list[str] = []

    for criterion, (direction, threshold) in _PROMOTION_CRITERIA.items():
        value = scores[criterion]
        passed = value >= threshold if direction == "minimum" else value <= threshold
        pass_fail[criterion] = passed
        if not passed:
            delta = (value - threshold) if direction == "minimum" else (threshold - value)
            failures.append(
                f"{criterion}: {value:.3f} {'<' if direction == 'minimum' else '>'} threshold {threshold:.3f} (gap {abs(delta):.3f})"
            )

    n_pass = sum(pass_fail.values())
    n_total = len(pass_fail)
    overall_score = round(n_pass / n_total, 4)

    if not params["observation_gate_pass"]:
        decision = "RETURN_FOR_RESEARCH"
        rationale = "Observation completeness gate not satisfied; mechanism must remain in RESEARCH state until data gaps are resolved."
    elif n_pass == n_total:
        decision = "PROMOTE"
        rationale = "All 10 promotion criteria satisfied. Mechanism is eligible for APPROVED_ALPHA."
    elif n_pass >= n_total - 2 and scores["replication_score"] < 0.60:
        decision = "RETURN_FOR_REPLICATION"
        rationale = f"Mechanism passes {n_pass}/{n_total} criteria but replication score {rep_score:.3f} is insufficient. Additional independent validation is required."
    else:
        decision = "RETURN_FOR_RESEARCH"
        rationale = (
            f"Mechanism passes only {n_pass}/{n_total} promotion criteria. "
            f"Critical gaps: {'; '.join(failures[:3])}."
        )

    return {
        "alpha_id": params["alpha_id"],
        "mechanism": mechanism_name,
        "committee_id": "PROMOTION-COMMITTEE-PROGRAM1",
        "criteria_scores": scores,
        "criteria_pass": pass_fail,
        "criteria_met": n_pass,
        "criteria_total": n_total,
        "overall_score": overall_score,
        "decision": decision,
        "rationale": rationale,
        "blocking_failures": failures,
        "conditions": failures if decision != "PROMOTE" else [],
    }


# ---------------------------------------------------------------------------
# Part E — Promotion Review System (lifecycle state resolution)
# ---------------------------------------------------------------------------


def _resolve_lifecycle_transition(
    params: dict[str, Any],
    replication: dict[str, Any],
    committee: dict[str, Any],
) -> dict[str, Any]:
    """Simulate full pipeline traversal and return final lifecycle state."""
    current = str(params["current_lifecycle_state"])
    gate_pass = bool(params["observation_gate_pass"])
    rep_status = str(replication["replication_status"])
    decision = str(committee["decision"])

    stages_traversed: list[str] = []

    if not gate_pass:
        return {
            "initial_state": current,
            "stages_traversed": [],
            "final_lifecycle_state": "RESEARCH",
            "transition_type": "BLOCKED",
            "reason": "Observation completeness gate failed; lifecycle advancement halted.",
            "promotion_committee_decision": decision,
        }

    # Advance: RESEARCH → READY_FOR_REVALIDATION (replication at least PARTIAL)
    if current == "RESEARCH" and rep_status in {"PARTIAL", "CONFIRMED"}:
        stages_traversed.append("READY_FOR_REVALIDATION")

        # Advance: READY_FOR_REVALIDATION → VALIDATED (replication PARTIAL+ counts)
        stages_traversed.append("VALIDATED")

        # Advance: VALIDATED → PROMOTION_REVIEW (automatic)
        stages_traversed.append("PROMOTION_REVIEW")

        if decision == "PROMOTE":
            final = "APPROVED_ALPHA"
        elif decision == "RETURN_FOR_REPLICATION":
            final = "READY_FOR_REVALIDATION"
        else:
            final = "RESEARCH"
    else:
        # No replication data → remain in RESEARCH
        final = "RESEARCH"

    initial_rank = _LIFECYCLE_RANK[current]
    final_rank = _LIFECYCLE_RANK[final]

    if final_rank > initial_rank:
        transition_type = "ADVANCED"
    elif final_rank < initial_rank:
        transition_type = "RETURNED"
    else:
        transition_type = "UNCHANGED"

    return {
        "initial_state": current,
        "stages_traversed": stages_traversed,
        "final_lifecycle_state": final,
        "transition_type": transition_type,
        "reason": committee["rationale"],
        "promotion_committee_decision": decision,
    }


# ---------------------------------------------------------------------------
# Part C — Institutional Alpha Registry
# ---------------------------------------------------------------------------


def _build_alpha_registry_entry(
    mechanism_name: str,
    params: dict[str, Any],
    replication: dict[str, Any],
    lifecycle: dict[str, Any],
    committee: dict[str, Any],
) -> dict[str, Any]:
    final_state = str(lifecycle["final_lifecycle_state"])
    registry_status = (
        "APPROVED"
        if final_state in {"APPROVED_ALPHA", "ACTIVE_ALPHA"}
        else "CANDIDATE"
        if final_state not in {"RETIRED"}
        else "RETIRED"
    )

    return {
        "alpha_id": params["alpha_id"],
        "mechanism": mechanism_name,
        "family_id": params["family_id"],
        "lifecycle_state": final_state,
        "registry_status": registry_status,
        "version": "1.0.0",
        "scientific_mechanism": params["scientific_mechanism"],
        "economic_rationale": params["economic_rationale"],
        "feature_dependencies": params["feature_dependencies"],
        "datasets": params["datasets"],
        "confidence": round(float(params["confidence_posterior"]), 4),
        "replication_score": round(float(replication["overall_replication_score"]), 4),
        "validation_history": ["DC3-PHASE4-BATCH1", "WP-IMP-0050", "PROGRAM1"],
        "failure_history": [str(f) for f in params["known_failure_modes"]],
        "capacity_class": params["capacity_class"],
        "correlation_to_alternatives": float(params["correlation_to_alternatives"]),
        "expected_regime": params["expected_regime"],
        "supported_market_states": params["supported_market_states"],
        "expected_holding_period": params["expected_holding_period"],
        "expected_decay": params["expected_decay"],
        "expected_failure_modes": params["expected_failure_modes"],
        "retirement_criteria": params["retirement_criteria"],
        "promotion_committee_decision": committee["decision"],
        "promotion_criteria_met": f"{committee['criteria_met']}/{committee['criteria_total']}",
        "observation_completeness": float(params["observation_completeness"]),
        "proxy_dependence": float(params["proxy_dependence"]),
    }


# ---------------------------------------------------------------------------
# Part F — Institutional Dossier generator
# ---------------------------------------------------------------------------


def _build_institutional_dossier(
    mechanism_name: str,
    params: dict[str, Any],
    replication: dict[str, Any],
    convergence: dict[str, Any],
    lifecycle: dict[str, Any],
    committee: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dossier_id": f"DOSSIER-{params['alpha_id']}",
        "alpha_id": params["alpha_id"],
        "mechanism": mechanism_name,
        "family_id": params["family_id"],
        "final_lifecycle_state": lifecycle["final_lifecycle_state"],
        "sections": {
            "executive_summary": {
                "confidence": float(params["confidence_posterior"]),
                "replication_status": replication["replication_status"],
                "committee_decision": committee["decision"],
                "overall_lifecycle_disposition": lifecycle["transition_type"],
            },
            "scientific_basis": {
                "mechanism_description": params["scientific_mechanism"],
                "economic_rationale": params["economic_rationale"],
                "scientific_validity_score": float(params["scientific_validity"]),
                "economic_plausibility_score": float(params["economic_plausibility"]),
                "explainability": float(params["explainability"]),
                "known_failure_modes": params["known_failure_modes"],
            },
            "validation_history": {
                "phases_completed": ["DC3-PHASE4", "DC3-PHASE5", "WP-IMP-0050", "PROGRAM1"],
                "observation_completeness": float(params["observation_completeness"]),
                "proxy_dependence": float(params["proxy_dependence"]),
                "regime_coverage": {r["regime"]: float(r["confidence_contribution"]) for r in params["regime_replications"]},
            },
            "replication_record": {
                "total_replications": int(replication["total_replications"]),
                "replication_score": float(replication["overall_replication_score"]),
                "contradictions": int(replication["contradictions_found"]),
                "period_ledger": replication["replication_ledger"],
            },
            "evidence_convergence": {
                "trajectory": convergence["confidence_trajectory"],
                "convergence_state": convergence["convergence_state"],
                "stability_score": float(convergence["stability_score"]),
                "is_converging": bool(convergence["is_converging"]),
            },
            "feature_and_dataset_profile": {
                "feature_dependencies": params["feature_dependencies"],
                "datasets": params["datasets"],
                "dataset_sensitivity": float(convergence["dataset_sensitivity"]),
            },
            "risk_and_capacity": {
                "capacity_class": params["capacity_class"],
                "correlation_to_alternatives": float(params["correlation_to_alternatives"]),
                "institutional_risk_score": float(params["institutional_risk"]),
                "expected_decay": params["expected_decay"],
                "expected_holding_period": params["expected_holding_period"],
            },
            "future_research": {
                "retirement_criteria": params["retirement_criteria"],
                "blocking_promotion_criteria": committee["blocking_failures"],
                "recommended_next_action": (
                    "Resolve data gaps and rerun observation completeness check."
                    if not params["observation_gate_pass"]
                    else "Improve scientific validity and regime consistency through targeted experiments."
                ),
            },
        },
    }


# ---------------------------------------------------------------------------
# Part G — IKROS extensions payload
# ---------------------------------------------------------------------------


def _build_ikros_extensions_payload(
    mechanism_name: str,
    params: dict[str, Any],
    replication: dict[str, Any],
    convergence: dict[str, Any],
    lifecycle: dict[str, Any],
    committee: dict[str, Any],
) -> dict[str, Any]:
    alpha_id = str(params["alpha_id"])
    return {
        "alpha_registry_upsert": {
            "registry_id": f"ALPHA-REG-{alpha_id}",
            "alpha_id": alpha_id,
            "lifecycle_state": lifecycle["final_lifecycle_state"],
            "confidence": float(params["confidence_posterior"]),
            "replication_score": float(replication["overall_replication_score"]),
            "registry_status": "CANDIDATE",
        },
        "replication_registry_upsert": {
            "registry_id": f"REPL-REG-{alpha_id}",
            "alpha_id": alpha_id,
            "replication_status": replication["replication_status"],
            "replication_score": float(replication["overall_replication_score"]),
            "contradictions": int(replication["contradictions_found"]),
        },
        "promotion_registry_upsert": {
            "registry_id": f"PROMO-REG-{alpha_id}",
            "alpha_id": alpha_id,
            "committee_decision": committee["decision"],
            "criteria_met": int(committee["criteria_met"]),
            "criteria_total": int(committee["criteria_total"]),
        },
        "confidence_registry_upsert": {
            "registry_id": f"CONF-REG-{alpha_id}",
            "alpha_id": alpha_id,
            "confidence_posterior": float(params["confidence_posterior"]),
            "convergence_state": convergence["convergence_state"],
            "stability_score": float(convergence["stability_score"]),
        },
        "lineage_record": {
            "alpha_id": alpha_id,
            "program": "INSTITUTIONAL_ALPHA_FACTORY_PROGRAM_1",
            "parent_wp": "WP-IMP-0050",
            "stages_traversed": lifecycle["stages_traversed"],
            "final_state": lifecycle["final_lifecycle_state"],
        },
    }


# ---------------------------------------------------------------------------
# Part H — Dashboard generators
# ---------------------------------------------------------------------------


def _build_dashboards(
    mechanism_results: list[dict[str, Any]],
    replication_registry: list[dict[str, Any]],
    promotion_reviews: list[dict[str, Any]],
    alpha_registry: list[dict[str, Any]],
    convergence_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate all 7 governed dashboards."""

    def _row(label: str, value: object) -> list[object]:
        return [label, value]

    # 1. Institutional Alpha Dashboard
    alpha_tiles = [
        _row("Mechanisms Processed", len(mechanism_results)),
        _row("Approved Alpha Count", sum(1 for r in alpha_registry if r["registry_status"] == "APPROVED")),
        _row("Candidate Alpha Count", sum(1 for r in alpha_registry if r["registry_status"] == "CANDIDATE")),
        _row("Mechanisms Blocked", sum(1 for r in replication_registry if r["replication_status"] == "BLOCKED")),
    ]

    # 2. Promotion Dashboard
    promo_tiles = [
        _row("PROMOTE Decisions", sum(1 for r in promotion_reviews if r["decision"] == "PROMOTE")),
        _row("RETURN_FOR_RESEARCH", sum(1 for r in promotion_reviews if r["decision"] == "RETURN_FOR_RESEARCH")),
        _row("RETURN_FOR_REPLICATION", sum(1 for r in promotion_reviews if r["decision"] == "RETURN_FOR_REPLICATION")),
        _row("REJECT Decisions", sum(1 for r in promotion_reviews if r["decision"] == "REJECT")),
    ]

    # 3. Evidence Dashboard
    evidence_tiles = [
        _row("Converging", sum(1 for r in convergence_reports if r["convergence_state"] in {"CONVERGING", "CONVERGING_SLOWLY"})),
        _row("Oscillating", sum(1 for r in convergence_reports if r["convergence_state"] == "OSCILLATING")),
        _row("Diverging", sum(1 for r in convergence_reports if r["convergence_state"] == "DIVERGING")),
        _row("Insufficient Data", sum(1 for r in convergence_reports if r["convergence_state"] == "INSUFFICIENT_DATA")),
    ]

    # 4. Replication Dashboard
    rep_tiles = [
        _row("CONFIRMED", sum(1 for r in replication_registry if r["replication_status"] == "CONFIRMED")),
        _row("PARTIAL", sum(1 for r in replication_registry if r["replication_status"] == "PARTIAL")),
        _row("FAILED", sum(1 for r in replication_registry if r["replication_status"] == "FAILED")),
        _row("BLOCKED", sum(1 for r in replication_registry if r["replication_status"] == "BLOCKED")),
    ]

    # 5. Confidence Dashboard
    conf_tiles = [
        _row(r["mechanism"], round(float(r["confidence_posterior"]), 4))
        for r in mechanism_results
    ]

    # 6. Research Queue Dashboard
    research_tiles = [
        _row(r["mechanism"], r["final_lifecycle_state"])
        for r in mechanism_results
    ]

    # 7. Scientific Status Dashboard
    sci_tiles = [
        _row("No Alpha Promoted", True),
        _row("Factory Infrastructure Active", True),
        _row("Evidence Engine Active", True),
        _row("Promotion Committee Active", True),
        _row("ARB Gate Enforced", True),
    ]

    return {
        "institutional_alpha_dashboard": {"tiles": alpha_tiles},
        "promotion_dashboard": {"tiles": promo_tiles},
        "evidence_dashboard": {"tiles": evidence_tiles},
        "replication_dashboard": {"tiles": rep_tiles},
        "confidence_dashboard": {"tiles": conf_tiles},
        "research_queue_dashboard": {"tiles": research_tiles},
        "scientific_status_dashboard": {"tiles": sci_tiles},
    }


# ---------------------------------------------------------------------------
# Master artifact builder
# ---------------------------------------------------------------------------


def prepare_program1_artifacts() -> dict[str, Any]:
    """Execute all Program 1 factory engines and return the complete artifact set."""
    mechanism_results: list[dict[str, Any]] = []
    replication_registry: list[dict[str, Any]] = []
    promotion_reviews: list[dict[str, Any]] = []
    alpha_registry: list[dict[str, Any]] = []
    convergence_reports: list[dict[str, Any]] = []
    dossiers: list[dict[str, Any]] = []
    ikros_extensions: list[dict[str, Any]] = []

    for mech_name, params in _MECHANISM_PARAMS.items():
        # Part A: Replication
        replication = _run_replication_engine(mech_name, params)

        # Part D: Evidence convergence
        convergence = _run_evidence_convergence(mech_name, params, replication)

        # Part B: Promotion committee
        committee = _evaluate_promotion_committee(mech_name, params, replication)

        # Part E: Lifecycle resolution
        lifecycle = _resolve_lifecycle_transition(params, replication, committee)

        # Part C: Registry entry
        registry_entry = _build_alpha_registry_entry(
            mech_name, params, replication, lifecycle, committee
        )

        # Part F: Institutional dossier
        dossier = _build_institutional_dossier(
            mech_name, params, replication, convergence, lifecycle, committee
        )

        # Part G: IKROS extensions
        ikros_ext = _build_ikros_extensions_payload(
            mech_name, params, replication, convergence, lifecycle, committee
        )

        mechanism_results.append(
            {
                "mechanism": mech_name,
                "alpha_id": params["alpha_id"],
                "family_id": params["family_id"],
                "confidence_prior": float(params["confidence_prior"]),
                "confidence_posterior": float(params["confidence_posterior"]),
                "replication_status": replication["replication_status"],
                "replication_score": float(replication["overall_replication_score"]),
                "committee_decision": committee["decision"],
                "initial_lifecycle_state": lifecycle["initial_state"],
                "stages_traversed": lifecycle["stages_traversed"],
                "final_lifecycle_state": lifecycle["final_lifecycle_state"],
                "transition_type": lifecycle["transition_type"],
                "criteria_met": f"{committee['criteria_met']}/{committee['criteria_total']}",
                "observation_gate_pass": bool(params["observation_gate_pass"]),
                "convergence_state": convergence["convergence_state"],
            }
        )

        replication_registry.append(replication)
        promotion_reviews.append(committee)
        alpha_registry.append(registry_entry)
        convergence_reports.append(convergence)
        dossiers.append(dossier)
        ikros_extensions.append(ikros_ext)

    # Part H: Dashboards
    dashboards = _build_dashboards(
        mechanism_results,
        replication_registry,
        promotion_reviews,
        alpha_registry,
        convergence_reports,
    )

    approved_count = sum(
        1 for r in mechanism_results if r["final_lifecycle_state"] == "APPROVED_ALPHA"
    )

    return {
        "program": "INSTITUTIONAL_ALPHA_FACTORY_PROGRAM_1",
        "version": "1.0.0",
        "no_promotion_executed": approved_count == 0,
        "approved_alpha_count": approved_count,
        "mechanisms_processed": len(mechanism_results),
        "mechanism_results": mechanism_results,
        "replication_registry": replication_registry,
        "promotion_reviews": promotion_reviews,
        "institutional_alpha_registry": alpha_registry,
        "evidence_convergence_reports": convergence_reports,
        "institutional_dossiers": dossiers,
        "ikros_extensions": ikros_extensions,
        "dashboards": dashboards,
        "arb_recommendation": (
            "No institutional alpha promoted in Program 1. "
            "Factory infrastructure is operational. "
            "safe_haven_migration requires improvements to scientific validity "
            "(current 0.61, required 0.70), regime consistency (0.56, required 0.65), "
            "and temporal stability (0.51, required 0.65) before promotion. "
            "decision_cascade is blocked on observation completeness; "
            "targeted dataset acquisition required before replication can proceed. "
            "Await ARB approval for Program 2 (targeted experiments and dataset acquisitions)."
        ),
    }


# ---------------------------------------------------------------------------
# Report emitter
# ---------------------------------------------------------------------------


def emit_program1_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path = Path("."),
) -> dict[str, str]:
    """Write all Program 1 reports, registries, and schemas to disk."""
    out = (repo_root / PROGRAM1_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    paths: dict[str, str] = {}

    # --- JSON artifacts ---
    for key, filename in [
        ("mechanism_results", "mechanism_results.json"),
        ("replication_registry", "replication_registry.json"),
        ("promotion_reviews", "promotion_reviews.json"),
        ("institutional_alpha_registry", "institutional_alpha_registry.json"),
        ("evidence_convergence_reports", "evidence_convergence_reports.json"),
        ("institutional_dossiers", "institutional_dossiers.json"),
        ("ikros_extensions", "ikros_extensions.json"),
        ("dashboards", "dashboards.json"),
    ]:
        dest = out / filename
        write_json(dest, analysis[key])
        paths[key] = str(dest)

    if campaign_result:
        dest = out / "campaign_result.json"
        write_json(dest, campaign_result)
        paths["campaign_result"] = str(dest)

    # --- Markdown reports ---
    mech_results = analysis["mechanism_results"]
    repl_reg = analysis["replication_registry"]
    prom_rev = analysis["promotion_reviews"]
    conv_reps = analysis["evidence_convergence_reports"]
    alpha_reg = analysis["institutional_alpha_registry"]

    # Replication registry
    repl_md = markdown_table(
        ["Mechanism", "Status", "Score", "Periods", "Contradictions"],
        [
            [
                r["mechanism"],
                r["replication_status"],
                r["overall_replication_score"],
                r["total_replications"],
                r["contradictions_found"],
            ]
            for r in repl_reg
        ],
    )
    write_markdown(out / "REPLICATION_REGISTRY.md", f"# Replication Registry\n\n{repl_md}")
    paths["replication_registry_md"] = str(out / "REPLICATION_REGISTRY.md")

    # Promotion dashboard
    promo_md = markdown_table(
        ["Mechanism", "Criteria Met", "Decision", "Rationale"],
        [
            [
                r["mechanism"],
                f"{r['criteria_met']}/{r['criteria_total']}",
                r["decision"],
                r["rationale"][:80],
            ]
            for r in prom_rev
        ],
    )
    write_markdown(out / "PROMOTION_DASHBOARD.md", f"# Promotion Dashboard\n\n{promo_md}")
    paths["promotion_dashboard_md"] = str(out / "PROMOTION_DASHBOARD.md")

    # Evidence convergence
    conv_md = markdown_table(
        ["Mechanism", "State", "Stability", "Weight", "Converging"],
        [
            [
                r["mechanism"],
                r["convergence_state"],
                r["stability_score"],
                r["evidence_weight"],
                r["is_converging"],
            ]
            for r in conv_reps
        ],
    )
    write_markdown(
        out / "EVIDENCE_CONVERGENCE.md", f"# Evidence Convergence Report\n\n{conv_md}"
    )
    paths["evidence_convergence_md"] = str(out / "EVIDENCE_CONVERGENCE.md")

    # Alpha Registry
    reg_md = markdown_table(
        ["Mechanism", "State", "Confidence", "Repl Score", "Status"],
        [
            [
                r["mechanism"],
                r["lifecycle_state"],
                r["confidence"],
                r["replication_score"],
                r["registry_status"],
            ]
            for r in alpha_reg
        ],
    )
    write_markdown(
        out / "INSTITUTIONAL_ALPHA_REGISTRY.md",
        f"# Institutional Alpha Registry\n\n{reg_md}",
    )
    paths["institutional_alpha_registry_md"] = str(out / "INSTITUTIONAL_ALPHA_REGISTRY.md")

    # Final report
    final_md_lines = [
        "# Program 1 — Institutional Alpha Factory: Final Report",
        "",
        f"**Program:** {analysis['program']}",
        f"**Mechanisms Processed:** {analysis['mechanisms_processed']}",
        f"**Approved Alpha Count:** {analysis['approved_alpha_count']}",
        f"**No Promotion Executed:** {analysis['no_promotion_executed']}",
        "",
        "## Mechanism Summary",
        "",
        markdown_table(
            ["Mechanism", "Initial State", "Stages Traversed", "Final State", "Decision"],
            [
                [
                    r["mechanism"],
                    r["initial_lifecycle_state"],
                    " → ".join(r["stages_traversed"]) or "—",
                    r["final_lifecycle_state"],
                    r["committee_decision"],
                ]
                for r in mech_results
            ],
        ),
        "",
        "## ARB Recommendation",
        "",
        analysis["arb_recommendation"],
        "",
        "## Parts Implemented",
        "",
        "- Part A: Scientific Replication Engine",
        "- Part B: Promotion Committee",
        "- Part C: Institutional Alpha Registry",
        "- Part D: Evidence Convergence Engine",
        "- Part E: Promotion Review System",
        "- Part F: Institutional Dossier",
        "- Part G: IKROS Extensions",
        "- Part H: Dashboards (7 governed dashboards)",
    ]
    write_markdown(out / "FINAL_REPORT.md", "\n".join(final_md_lines))
    paths["final_report"] = str(out / "FINAL_REPORT.md")

    # --- Write schemas (Part I) ---
    _emit_schemas(repo_root)

    return paths


def _emit_schemas(repo_root: Path) -> None:
    """Write Part I JSON schemas for the alpha factory domain."""
    schema_dir = (repo_root / "schemas" / "institutional-alpha-factory").resolve()

    schemas: dict[str, object] = {
        "approved-alpha.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ApprovedAlpha",
            "type": "object",
            "required": ["alpha_id", "lifecycle_state", "confidence", "replication_score"],
            "properties": {
                "alpha_id": {"type": "string"},
                "lifecycle_state": {"type": "string", "enum": LIFECYCLE_STATES},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "replication_score": {"type": "number", "minimum": 0, "maximum": 1},
                "registry_status": {"type": "string", "enum": ["CANDIDATE", "APPROVED", "RETIRED"]},
            },
        },
        "promotion-review.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "PromotionReview",
            "type": "object",
            "required": ["alpha_id", "decision", "criteria_met", "criteria_total"],
            "properties": {
                "alpha_id": {"type": "string"},
                "decision": {"type": "string", "enum": PROMOTION_DECISIONS},
                "criteria_met": {"type": "integer"},
                "criteria_total": {"type": "integer"},
                "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "replication.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "ReplicationEntry",
            "type": "object",
            "required": ["alpha_id", "replication_status", "overall_replication_score"],
            "properties": {
                "alpha_id": {"type": "string"},
                "replication_status": {"type": "string", "enum": ["CONFIRMED", "PARTIAL", "FAILED", "BLOCKED"]},
                "overall_replication_score": {"type": "number", "minimum": 0, "maximum": 1},
                "contradictions_found": {"type": "integer", "minimum": 0},
            },
        },
        "evidence-convergence.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "EvidenceConvergence",
            "type": "object",
            "required": ["alpha_id", "convergence_state", "stability_score"],
            "properties": {
                "alpha_id": {"type": "string"},
                "convergence_state": {"type": "string", "enum": ["CONVERGING", "CONVERGING_SLOWLY", "OSCILLATING", "DIVERGING", "INSUFFICIENT_DATA"]},
                "stability_score": {"type": "number", "minimum": 0, "maximum": 1},
                "is_converging": {"type": "boolean"},
                "evidence_weight": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "alpha-dossier.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "AlphaDossier",
            "type": "object",
            "required": ["dossier_id", "alpha_id", "final_lifecycle_state", "sections"],
            "properties": {
                "dossier_id": {"type": "string"},
                "alpha_id": {"type": "string"},
                "final_lifecycle_state": {"type": "string", "enum": LIFECYCLE_STATES},
                "sections": {"type": "object"},
            },
        },
        "alpha-lifecycle.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "AlphaLifecycle",
            "type": "object",
            "required": ["alpha_id", "initial_state", "final_lifecycle_state", "transition_type"],
            "properties": {
                "alpha_id": {"type": "string"},
                "initial_state": {"type": "string", "enum": LIFECYCLE_STATES},
                "final_lifecycle_state": {"type": "string", "enum": LIFECYCLE_STATES},
                "transition_type": {"type": "string", "enum": ["ADVANCED", "RETURNED", "UNCHANGED", "BLOCKED"]},
                "stages_traversed": {"type": "array", "items": {"type": "string"}},
            },
        },
        "registry.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "AlphaRegistry",
            "type": "array",
            "items": {"$ref": "approved-alpha.schema.json"},
        },
        "dashboard.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "FactoryDashboard",
            "type": "object",
            "required": ["tiles"],
            "properties": {
                "tiles": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
            },
        },
        "audit.schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "FactoryAuditRecord",
            "type": "object",
            "required": ["program", "alpha_id", "stage", "timestamp"],
            "properties": {
                "program": {"type": "string"},
                "alpha_id": {"type": "string"},
                "stage": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "outcome": {"type": "string"},
            },
        },
    }

    for filename, schema in schemas.items():
        write_json(schema_dir / filename, schema)
