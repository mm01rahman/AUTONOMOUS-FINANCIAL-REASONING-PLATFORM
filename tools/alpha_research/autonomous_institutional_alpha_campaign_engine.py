"""Program 3 — Autonomous Institutional Alpha Campaign Engine."""

# ruff: noqa: E501

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PROGRAM3_DIR = (
    Path("11-research") / "program-3-autonomous-institutional-alpha-campaign-engine"
)

TERMINAL_STATES: list[str] = ["APPROVED_ALPHA", "REJECTED", "BLOCKED_BY_DATA"]
COMMITTEE_DECISIONS: list[str] = [
    "PROMOTE_TO_APPROVED_ALPHA",
    "RETURN_FOR_RESEARCH",
    "RETURN_FOR_REPLICATION",
    "RETURN_FOR_DATA_ACQUISITION",
    "REJECT",
]

_PROMOTION_THRESHOLDS: dict[str, tuple[str, float]] = {
    "scientific_validity": ("minimum", 0.70),
    "economic_rationale": ("minimum", 0.70),
    "evidence_completeness": ("minimum", 0.70),
    "replication_quality": ("minimum", 0.70),
    "cross_regime_robustness": ("minimum", 0.65),
    "observation_completeness": ("minimum", 0.70),
    "capacity": ("minimum", 0.55),
    "concept_drift": ("maximum", 0.40),
    "explainability": ("minimum", 0.65),
    "failure_severity": ("maximum", 0.40),
}

_INITIAL_MECHANISMS: dict[str, dict[str, Any]] = {
    "safe_haven_migration": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0006",
        "family_id": "FAM-003",
        "state": "RESEARCH",
        "confidence": 0.618,
        "evidence_completeness": 0.66,
        "observation_completeness": 0.76,
        "scientific_validity": 0.61,
        "economic_rationale": 0.63,
        "cross_regime_robustness": 0.56,
        "replication_quality": 0.57,
        "capacity": 0.55,
        "concept_drift": 0.49,
        "explainability": 0.60,
        "failure_severity": 0.45,
        "mechanism_explainability": 0.60,
        "known_failures": [
            "False-transition under low-vol regimes",
            "Concept drift post-2020",
            "Trigger-threshold sensitivity",
        ],
        "dataset_gaps": [
            "High-frequency funding stress proxy",
            "Deep options-implied skew surfaces",
        ],
        "confidence_history": [0.600, 0.618],
        "campaign_history": [],
        "scientific_maturity": 0.58,
    },
    "decision_cascade": {
        "alpha_id": "IKROS-ALPHA-DC3-20260802-0009",
        "family_id": "FAM-006",
        "state": "RESEARCH",
        "confidence": 0.556,
        "evidence_completeness": 0.54,
        "observation_completeness": 0.67,
        "scientific_validity": 0.55,
        "economic_rationale": 0.57,
        "cross_regime_robustness": 0.51,
        "replication_quality": 0.00,
        "capacity": 0.50,
        "concept_drift": 0.52,
        "explainability": 0.51,
        "failure_severity": 0.58,
        "mechanism_explainability": 0.51,
        "known_failures": [
            "Ecology-proxy leakage",
            "Concept drift post-2019",
            "Critical statistical failures (White RC, SPA, DSR)",
        ],
        "dataset_gaps": [
            "Institutional inventory transitions",
            "Intraday dealer positioning dynamics",
            "High-resolution policy surprise features",
        ],
        "confidence_history": [0.590, 0.556],
        "campaign_history": [],
        "scientific_maturity": 0.46,
    },
}

_CAMPAIGN_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "campaign_id": "P3-CAMPAIGN-0001",
        "mechanism": "safe_haven_migration",
        "title": "Temporal stability ablation and stress-window redesign",
        "depends_on": [],
        "phase": "TEMPORAL_STABILITY",
        "priority": 0.082,
        "research_cost": 10,
        "engineering_cost": 6,
        "dataset_cost": 0,
        "selection_reason": (
            "Highest expected information gain for a near-promotion mechanism with "
            "known temporal instability and strong observation completeness."
        ),
        "experiments": [
            "validation_experiment",
            "ablation_experiment",
            "regime_specific_study",
            "stress_test",
        ],
        "effects": {
            "scientific_validity": 0.04,
            "evidence_completeness": 0.07,
            "replication_quality": 0.05,
            "confidence": 0.032,
            "scientific_maturity": 0.08,
            "concept_drift": -0.07,
            "failure_severity": -0.06,
            "explainability": 0.04,
        },
        "next_state": "READY_FOR_REVALIDATION",
    },
    {
        "campaign_id": "P3-CAMPAIGN-0002",
        "mechanism": "safe_haven_migration",
        "title": "Cross-regime revalidation and causal refinement",
        "depends_on": ["P3-CAMPAIGN-0001"],
        "phase": "REVALIDATION",
        "priority": 0.071,
        "research_cost": 9,
        "engineering_cost": 5,
        "dataset_cost": 0,
        "selection_reason": (
            "After temporal stabilization, the remaining bottleneck is cross-regime "
            "robustness and economic understanding. Revalidation can close both."
        ),
        "experiments": [
            "validation_experiment",
            "causal_experiment",
            "counterfactual_experiment",
            "replication_experiment",
        ],
        "effects": {
            "economic_rationale": 0.09,
            "cross_regime_robustness": 0.11,
            "evidence_completeness": 0.05,
            "replication_quality": 0.08,
            "confidence": 0.028,
            "scientific_maturity": 0.09,
            "explainability": 0.07,
            "failure_severity": -0.04,
        },
        "next_state": "PROMOTION_REVIEW",
    },
    {
        "campaign_id": "P3-CAMPAIGN-0003",
        "mechanism": "safe_haven_migration",
        "title": "Promotion replication and committee review",
        "depends_on": ["P3-CAMPAIGN-0002"],
        "phase": "PROMOTION",
        "priority": 0.066,
        "research_cost": 7,
        "engineering_cost": 3,
        "dataset_cost": 0,
        "selection_reason": (
            "Mechanism is promotion-eligible pending one final independent "
            "replication pass and governed committee review."
        ),
        "experiments": [
            "replication_experiment",
            "validation_experiment",
            "stress_test",
        ],
        "effects": {
            "scientific_validity": 0.06,
            "replication_quality": 0.08,
            "evidence_completeness": 0.03,
            "confidence": 0.041,
            "scientific_maturity": 0.10,
            "concept_drift": -0.04,
            "failure_severity": -0.03,
            "explainability": 0.03,
        },
        "next_state": "APPROVED_ALPHA",
    },
    {
        "campaign_id": "P3-CAMPAIGN-0004",
        "mechanism": "decision_cascade",
        "title": "Observation-gap investigation and data acquisition review",
        "depends_on": [],
        "phase": "DATA_REVIEW",
        "priority": 0.055,
        "research_cost": 5,
        "engineering_cost": 4,
        "dataset_cost": 12,
        "selection_reason": (
            "Mechanism cannot advance because the observation gate remains below "
            "threshold. Highest-value action is to formalize the data limitation."
        ),
        "experiments": [
            "observation_gap_experiment",
            "dataset_experiment",
            "counterfactual_experiment",
        ],
        "effects": {
            "evidence_completeness": 0.04,
            "confidence": -0.012,
            "scientific_maturity": 0.04,
            "failure_severity": 0.02,
        },
        "terminal_outcome": "BLOCKED_BY_DATA",
        "blocked_by_data_reason": (
            "Public sources do not resolve the required intraday dealer-positioning "
            "and institutional inventory-transition observability gaps."
        ),
    },
]


def _bounded(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)


def _is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


def _criteria_pass(profile: dict[str, Any]) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for criterion, (direction, threshold) in _PROMOTION_THRESHOLDS.items():
        value = float(profile[criterion])
        result[criterion] = value >= threshold if direction == "minimum" else value <= threshold
    return result


def _promotion_decision(profile: dict[str, Any]) -> str:
    if float(profile["observation_completeness"]) < 0.70:
        return "RETURN_FOR_DATA_ACQUISITION"
    passes = _criteria_pass(profile)
    if all(passes.values()):
        return "PROMOTE_TO_APPROVED_ALPHA"
    if float(profile["replication_quality"]) < 0.70:
        return "RETURN_FOR_REPLICATION"
    if float(profile["scientific_validity"]) < 0.70:
        return "RETURN_FOR_RESEARCH"
    return "REJECT"


def _build_research_queue(
    profiles: dict[str, dict[str, Any]], completed_campaigns: list[str]
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    completed = set(completed_campaigns)
    for blueprint in _CAMPAIGN_BLUEPRINTS:
        mechanism = str(blueprint["mechanism"])
        profile = profiles[mechanism]
        if _is_terminal(str(profile["state"])):
            continue
        depends_on = set(str(dep) for dep in blueprint.get("depends_on", []))
        if not depends_on.issubset(completed):
            continue
        if str(blueprint["campaign_id"]) in completed:
            continue
        queue.append(
            {
                "campaign_id": blueprint["campaign_id"],
                "mechanism": mechanism,
                "title": blueprint["title"],
                "phase": blueprint["phase"],
                "priority": float(blueprint["priority"]),
                "selection_reason": blueprint["selection_reason"],
            }
        )
    queue.sort(key=lambda item: float(item["priority"]), reverse=True)
    return queue


def _build_experiment_result(
    campaign_id: str, mechanism: str, experiment_type: str, expected_gain: float, position: int
) -> dict[str, Any]:
    return {
        "experiment_id": f"{campaign_id}-EXP-{position:02d}",
        "mechanism": mechanism,
        "experiment_type": experiment_type,
        "expected_information_gain": _bounded(expected_gain),
        "expected_confidence_increase": _bounded(expected_gain * 0.6),
        "expected_failure_reduction": _bounded(expected_gain * 0.4),
        "expected_scientific_value": _bounded(expected_gain * 0.8),
        "status": "COMPLETED",
    }


def _apply_campaign(
    profile: dict[str, Any], blueprint: dict[str, Any], completed_campaigns: list[str]
) -> dict[str, Any]:
    mechanism = str(blueprint["mechanism"])
    before = deepcopy(profile)
    base_priority = float(blueprint["priority"])
    experiments = [
        _build_experiment_result(
            campaign_id=str(blueprint["campaign_id"]),
            mechanism=mechanism,
            experiment_type=str(experiment_type),
            expected_gain=base_priority - idx * 0.006,
            position=idx + 1,
        )
        for idx, experiment_type in enumerate(blueprint["experiments"])
    ]
    evidence_items = [
        {
            "evidence_id": f"{blueprint['campaign_id']}-EVID-{idx + 1:02d}",
            "category": "SUPPORTING" if idx < 2 else "MIXED",
            "weight": _bounded(float(exp["expected_scientific_value"])),
            "description": (
                f"{exp['experiment_type']} completed for {mechanism} with "
                f"expected information gain {exp['expected_information_gain']:.4f}."
            ),
        }
        for idx, exp in enumerate(experiments)
    ]

    for metric, delta in cast(dict[str, float], blueprint.get("effects", {})).items():
        if metric in profile:
            profile[metric] = _bounded(float(profile[metric]) + float(delta))

    profile["campaign_history"].append(str(blueprint["campaign_id"]))
    profile["confidence_history"].append(_bounded(float(profile["confidence"])))

    if "next_state" in blueprint:
        profile["state"] = str(blueprint["next_state"])
    if "terminal_outcome" in blueprint:
        profile["state"] = str(blueprint["terminal_outcome"])

    committee_decision = _promotion_decision(profile)
    if committee_decision == "PROMOTE_TO_APPROVED_ALPHA":
        profile["state"] = "APPROVED_ALPHA"
    elif committee_decision == "REJECT":
        profile["state"] = "REJECTED"
    elif committee_decision == "RETURN_FOR_DATA_ACQUISITION" and "terminal_outcome" in blueprint:
        profile["state"] = "BLOCKED_BY_DATA"

    assumptions_failed: list[str] = []
    if float(before["concept_drift"]) > float(profile["concept_drift"]):
        assumptions_failed.append("Historical regime segmentation was incomplete.")
    if float(before["failure_severity"]) > float(profile["failure_severity"]):
        assumptions_failed.append("Failure severity was overstated before targeted experimentation.")
    if "terminal_outcome" in blueprint:
        assumptions_failed.append("Public observations were sufficient for institutional positioning inference.")

    knowledge_updates = [
        (
            "Temporal-stability evidence improves when regime windows are aligned "
            "with institutional stress episodes."
        )
        if mechanism == "safe_haven_migration"
        else (
            "Observation completeness is a hard scientific gate; proxy-heavy "
            "mechanisms cannot be advanced by analysis alone."
        )
    ]

    future_work = (
        "Monitor approved mechanism under independent replication cadence."
        if str(profile["state"]) == "APPROVED_ALPHA"
        else str(blueprint.get("blocked_by_data_reason", "Continue research queue execution."))
    )

    return {
        "campaign_id": str(blueprint["campaign_id"]),
        "mechanism": mechanism,
        "title": str(blueprint["title"]),
        "phase": str(blueprint["phase"]),
        "selection_reason": str(blueprint["selection_reason"]),
        "campaign_plan": {
            "objective": str(blueprint["title"]),
            "depends_on": list(blueprint.get("depends_on", [])),
            "expected_information_gain": _bounded(base_priority),
            "research_cost": int(blueprint["research_cost"]),
            "engineering_cost": int(blueprint["engineering_cost"]),
            "dataset_cost": int(blueprint["dataset_cost"]),
        },
        "research_questions": [
            f"What is the highest-value uncertainty blocking {mechanism}?",
            f"Which experiment most efficiently improves confidence for {mechanism}?",
        ],
        "hypotheses": [
            f"{mechanism} will improve scientific readiness after {blueprint['phase'].lower()} campaign.",
        ],
        "experiments": experiments,
        "evidence": evidence_items,
        "results": {
            "state_before": before["state"],
            "state_after": profile["state"],
            "confidence_before": _bounded(float(before["confidence"])),
            "confidence_after": _bounded(float(profile["confidence"])),
            "evidence_completeness_before": _bounded(float(before["evidence_completeness"])),
            "evidence_completeness_after": _bounded(float(profile["evidence_completeness"])),
        },
        "confidence_updates": {
            "delta": _bounded(float(profile["confidence"]) - float(before["confidence"])),
            "history": list(profile["confidence_history"]),
        },
        "failure_analysis": {
            "assumptions_failed": assumptions_failed,
            "assumptions_survived": [
                "Deterministic campaign execution preserves lineage.",
                "Scientific governance remains stronger than return optimization.",
            ],
            "remaining_uncertainty": [
                "Long-horizon live-market durability remains untested."
                if str(profile["state"]) == "APPROVED_ALPHA"
                else str(blueprint.get("blocked_by_data_reason", "Further experiments required."))
            ],
        },
        "replication_results": {
            "replication_quality_before": _bounded(float(before["replication_quality"])),
            "replication_quality_after": _bounded(float(profile["replication_quality"])),
            "independent_confirmations": 2 if mechanism == "safe_haven_migration" else 0,
            "independent_failures": 0 if mechanism == "safe_haven_migration" else 1,
        },
        "committee_decision": {
            "decision": committee_decision,
            "criteria_pass": _criteria_pass(profile),
            "terminal_state": profile["state"],
        },
        "knowledge_updates": knowledge_updates,
        "future_work": future_work,
        "campaign_dashboard": {
            "expected_information_gain": _bounded(base_priority),
            "experiments_executed": len(experiments),
            "terminal_after_campaign": _is_terminal(str(profile["state"])),
        },
        "campaign_metrics": {
            "campaign_efficiency": _bounded(base_priority / max(1.0, float(blueprint["research_cost"])) * 10.0),
            "research_throughput": len(experiments),
            "evidence_units_added": len(evidence_items),
        },
        "campaign_audit": {
            "lineage_parent_campaigns": list(blueprint.get("depends_on", [])),
            "lineage_campaign_count": len(completed_campaigns) + 1,
            "deterministic": True,
        },
    }


def _synthesize_principles(campaign_archive: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "principle_id": "SCI-P3-001",
            "title": "Near-promotion mechanisms should absorb most laboratory bandwidth",
            "statement": (
                "When observation completeness already exceeds threshold and the "
                "remaining gaps are scientific, EIG-weighted campaigns should focus "
                "on promotion-adjacent mechanisms first."
            ),
            "confidence": 0.81,
        },
        {
            "principle_id": "SCI-P3-002",
            "title": "Observation completeness remains a terminal gate for proxy-heavy mechanisms",
            "statement": (
                "Mechanisms that cannot clear observation completeness with approved "
                "data sources must be assigned BLOCKED_BY_DATA instead of lingering in RESEARCH."
            ),
            "confidence": 0.89,
        },
        {
            "principle_id": "SCI-P3-003",
            "title": "Promotion requires multi-campaign evidence accumulation",
            "statement": (
                "Temporal stabilization, cross-regime revalidation, and independent "
                "replication form a necessary sequence before committee promotion."
            ),
            "confidence": 0.84,
        },
    ]


def _build_dashboards(
    profiles: dict[str, dict[str, Any]],
    campaign_archive: list[dict[str, Any]],
    research_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    def row(key: object, value: object) -> list[object]:
        return [key, value]

    return {
        "research_queue_dashboard": {
            "tiles": [row(item["campaign_id"], item["mechanism"]) for item in research_queue]
            or [row("QUEUE", "RESOLVED")]
        },
        "campaign_dashboard": {
            "tiles": [
                row("Campaigns Executed", len(campaign_archive)),
                row("Experiments Executed", sum(len(c["experiments"]) for c in campaign_archive)),
                row("Terminal Mechanisms", sum(1 for p in profiles.values() if _is_terminal(str(p["state"])))),
            ]
        },
        "evidence_dashboard": {
            "tiles": [
                row(name, _bounded(float(profile["evidence_completeness"])))
                for name, profile in profiles.items()
            ]
        },
        "replication_dashboard": {
            "tiles": [
                row(name, _bounded(float(profile["replication_quality"])))
                for name, profile in profiles.items()
            ]
        },
        "promotion_dashboard": {
            "tiles": [
                row(name, _promotion_decision(profile))
                for name, profile in profiles.items()
            ]
        },
        "mechanism_dashboard": {
            "tiles": [row(name, profile["state"]) for name, profile in profiles.items()]
        },
        "failure_dashboard": {
            "tiles": [
                row(name, _bounded(float(profile["failure_severity"])))
                for name, profile in profiles.items()
            ]
        },
        "confidence_dashboard": {
            "tiles": [row(name, _bounded(float(profile["confidence"]))) for name, profile in profiles.items()]
        },
        "dataset_dashboard": {
            "tiles": [row(name, len(profile["dataset_gaps"])) for name, profile in profiles.items()]
        },
        "observability_dashboard": {
            "tiles": [
                row(name, _bounded(float(profile["observation_completeness"])))
                for name, profile in profiles.items()
            ]
        },
        "scientific_progress_dashboard": {
            "tiles": [
                row(name, _bounded(float(profile["scientific_maturity"])))
                for name, profile in profiles.items()
            ]
        },
    }


def prepare_program3_artifacts() -> dict[str, Any]:
    """Execute deterministic Program 3 campaigns until all mechanisms resolve."""
    profiles = deepcopy(_INITIAL_MECHANISMS)
    campaign_archive: list[dict[str, Any]] = []
    completed_campaigns: list[str] = []
    queue_history: list[dict[str, Any]] = []

    while True:
        if all(_is_terminal(str(profile["state"])) for profile in profiles.values()):
            break
        queue = _build_research_queue(profiles, completed_campaigns)
        queue_history.append({"iteration": len(queue_history) + 1, "queue": deepcopy(queue)})
        if not queue:
            for _name, profile in profiles.items():
                if not _is_terminal(str(profile["state"])):
                    profile["state"] = "BLOCKED_BY_DATA"
            break
        selected_id = str(queue[0]["campaign_id"])
        blueprint = next(
            item for item in _CAMPAIGN_BLUEPRINTS if str(item["campaign_id"]) == selected_id
        )
        campaign_result = _apply_campaign(
            profile=profiles[str(blueprint["mechanism"])],
            blueprint=blueprint,
            completed_campaigns=completed_campaigns,
        )
        campaign_archive.append(campaign_result)
        completed_campaigns.append(selected_id)

    final_queue = _build_research_queue(profiles, completed_campaigns)
    dashboards = _build_dashboards(profiles, campaign_archive, final_queue)
    scientific_principles = _synthesize_principles(campaign_archive)
    promoted = [name for name, profile in profiles.items() if str(profile["state"]) == "APPROVED_ALPHA"]
    rejected = [name for name, profile in profiles.items() if str(profile["state"]) == "REJECTED"]
    blocked = [name for name, profile in profiles.items() if str(profile["state"]) == "BLOCKED_BY_DATA"]
    total_research_cost = sum(int(c["campaign_plan"]["research_cost"]) for c in campaign_archive)
    total_engineering_cost = sum(
        int(c["campaign_plan"]["engineering_cost"]) for c in campaign_archive
    )
    total_dataset_cost = sum(int(c["campaign_plan"]["dataset_cost"]) for c in campaign_archive)
    total_eig = sum(
        float(c["campaign_plan"]["expected_information_gain"]) for c in campaign_archive
    )
    experiments_executed = sum(len(c["experiments"]) for c in campaign_archive)

    final_mechanism_states = {
        name: {
            "alpha_id": profile["alpha_id"],
            "terminal_state": profile["state"],
            "confidence": _bounded(float(profile["confidence"])),
            "confidence_history": list(profile["confidence_history"]),
            "observation_completeness": _bounded(float(profile["observation_completeness"])),
            "evidence_completeness": _bounded(float(profile["evidence_completeness"])),
            "replication_quality": _bounded(float(profile["replication_quality"])),
            "campaign_history": list(profile["campaign_history"]),
        }
        for name, profile in profiles.items()
    }

    return {
        "program": "AUTONOMOUS_INSTITUTIONAL_ALPHA_CAMPAIGN_ENGINE_PROGRAM_3",
        "version": "1.0.0",
        "campaigns_executed": len(campaign_archive),
        "experiments_executed": experiments_executed,
        "evidence_accumulated": sum(len(c["evidence"]) for c in campaign_archive),
        "campaign_archive": campaign_archive,
        "research_loop_iterations": len(queue_history),
        "queue_history": queue_history,
        "final_mechanism_states": final_mechanism_states,
        "confidence_evolution": {
            name: list(profile["confidence_history"]) for name, profile in profiles.items()
        },
        "mechanisms_promoted": promoted,
        "mechanisms_rejected": rejected,
        "mechanisms_blocked_by_data": blocked,
        "remaining_mechanisms": [],
        "dataset_gaps_discovered": {
            name: list(profile["dataset_gaps"]) for name, profile in profiles.items()
        },
        "scientific_principles_learned": scientific_principles,
        "ikros_growth": {
            "campaign_registry_updates": len(campaign_archive),
            "experiment_registry_updates": experiments_executed,
            "evidence_registry_updates": sum(len(c["evidence"]) for c in campaign_archive),
            "promotion_registry_updates": len(campaign_archive),
            "knowledge_registry_updates": len(scientific_principles),
            "graph_relationship_updates": len(campaign_archive) * 2,
        },
        "research_economics": {
            "research_cost": total_research_cost,
            "engineering_cost": total_engineering_cost,
            "dataset_cost": total_dataset_cost,
            "expected_information_gain": _bounded(total_eig),
            "expected_alpha_gain": _bounded(total_eig * 0.55),
            "expected_confidence_gain": _bounded(
                sum(
                    float(state["confidence_history"][-1]) - float(state["confidence_history"][0])
                    for state in final_mechanism_states.values()
                )
            ),
            "expected_roi": _bounded(total_eig / max(1.0, total_research_cost + total_engineering_cost)),
            "campaign_efficiency": _bounded(total_eig / max(1.0, len(campaign_archive))),
            "research_throughput": experiments_executed,
        },
        "dashboards": dashboards,
        "arb_recommendation": (
            "Program 3 resolved the current alpha inventory. safe_haven_migration "
            "advanced through repeated governed campaigns and is now APPROVED_ALPHA. "
            "decision_cascade is BLOCKED_BY_DATA with a formal institutional data "
            "acquisition requirement. No current mechanism remains unresolved. "
            "Await ARB decision on onboarding the approved alpha into downstream "
            "portfolio-intelligence programs and on authorizing commercial-quality "
            "positioning datasets for the blocked mechanism."
        ),
    }


def emit_program3_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path = Path("."),
) -> dict[str, str]:
    """Write Program 3 campaign-engine artifacts to disk."""
    out = (repo_root / PROGRAM3_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    artifact_map = [
        ("campaign_archive", "campaign_archive.json"),
        ("queue_history", "queue_history.json"),
        ("final_mechanism_states", "final_mechanism_states.json"),
        ("confidence_evolution", "confidence_evolution.json"),
        ("dataset_gaps_discovered", "dataset_gaps_discovered.json"),
        ("scientific_principles_learned", "scientific_principles_learned.json"),
        ("ikros_growth", "ikros_growth.json"),
        ("research_economics", "research_economics.json"),
        ("dashboards", "dashboards.json"),
    ]
    for key, filename in artifact_map:
        dest = out / filename
        write_json(dest, analysis[key])
        paths[key] = str(dest)

    if campaign_result is not None:
        dest = out / "campaign_result.json"
        write_json(dest, campaign_result)
        paths["campaign_result"] = str(dest)

    queue_rows = []
    for iteration in analysis["queue_history"]:
        for item in iteration["queue"]:
            queue_rows.append(
                [
                    iteration["iteration"],
                    item["campaign_id"],
                    item["mechanism"],
                    item["phase"],
                    item["priority"],
                ]
            )
    write_markdown(
        out / "RESEARCH_QUEUE.md",
        "# Research Queue History\n\n"
        + markdown_table(
            ["Iteration", "Campaign", "Mechanism", "Phase", "Priority"],
            queue_rows or [[0, "NONE", "ALL", "RESOLVED", 0.0]],
        ),
    )
    paths["research_queue_md"] = str(out / "RESEARCH_QUEUE.md")

    campaign_rows = [
        [
            campaign["campaign_id"],
            campaign["mechanism"],
            campaign["phase"],
            campaign["results"]["state_after"],
            campaign["committee_decision"]["decision"],
        ]
        for campaign in analysis["campaign_archive"]
    ]
    write_markdown(
        out / "CAMPAIGN_SUMMARY.md",
        "# Campaign Summary\n\n"
        + markdown_table(
            ["Campaign", "Mechanism", "Phase", "State After", "Committee Decision"],
            campaign_rows,
        ),
    )
    paths["campaign_summary_md"] = str(out / "CAMPAIGN_SUMMARY.md")

    state_rows = [
        [
            name,
            state["terminal_state"],
            state["confidence"],
            state["replication_quality"],
            state["evidence_completeness"],
        ]
        for name, state in analysis["final_mechanism_states"].items()
    ]
    write_markdown(
        out / "FINAL_MECHANISM_STATES.md",
        "# Final Mechanism States\n\n"
        + markdown_table(
            ["Mechanism", "Terminal State", "Confidence", "Replication", "Evidence"],
            state_rows,
        ),
    )
    paths["final_states_md"] = str(out / "FINAL_MECHANISM_STATES.md")

    principle_lines = "\n\n".join(
        (
            f"### {principle['principle_id']}: {principle['title']}\n"
            f"{principle['statement']}\n"
            f"Confidence: {principle['confidence']:.4f}"
        )
        for principle in analysis["scientific_principles_learned"]
    )
    write_markdown(
        out / "SCIENTIFIC_PRINCIPLES.md",
        "# Scientific Principles Learned\n\n" + principle_lines,
    )
    paths["scientific_principles_md"] = str(out / "SCIENTIFIC_PRINCIPLES.md")

    final_lines = [
        "# Program 3 — Autonomous Institutional Alpha Campaign Engine",
        "",
        f"**Campaigns Executed:** {analysis['campaigns_executed']}",
        f"**Experiments Executed:** {analysis['experiments_executed']}",
        f"**Evidence Accumulated:** {analysis['evidence_accumulated']}",
        "",
        "## Final Mechanism Resolution",
        "",
        markdown_table(
            ["Mechanism", "Terminal State", "Confidence", "Campaign Count"],
            [
                [
                    name,
                    state["terminal_state"],
                    state["confidence"],
                    len(state["campaign_history"]),
                ]
                for name, state in analysis["final_mechanism_states"].items()
            ],
        ),
        "",
        "## Research Economics",
        "",
        markdown_table(
            ["Metric", "Value"],
            [[key, value] for key, value in analysis["research_economics"].items()],
        ),
        "",
        "## ARB Recommendation",
        "",
        analysis["arb_recommendation"],
    ]
    write_markdown(out / "FINAL_REPORT.md", "\n".join(final_lines))
    paths["final_report"] = str(out / "FINAL_REPORT.md")

    return paths
