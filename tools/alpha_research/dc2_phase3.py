"""Discovery Cycle 2 Program A Phase 3 governed campaign execution.

DC2 Research Program A Phase 3: Institutional Cross-Asset Information Network.

Architecture constraints:
- Runtime FROZEN
- IKROS FROZEN (architecture; data writes are permitted)
- No infrastructure development
- No hypothesis creation, strategy synthesis, or parameter optimization
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.information_network import (
    DC2_PHASE3_DIR,
    emit_dc2_phase3_reports,
    prepare_dc2_phase3_artifacts,
)
from tools.alpha_research.reporting import write_json
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import (
    FailurePolicy,
    ResearchCampaign,
    ResearchOrchestrator,
    TaskKind,
)
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.research import ResearchRegistry


def _with_reproducibility_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc2-phase3-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_campaign_pipeline(
    campaign: ResearchCampaign,
    task_kinds: list[str],
) -> ResearchCampaign:
    kind_set = set(task_kinds)
    filtered = [task for task in campaign.tasks if task.kind in kind_set]
    ordered = sorted(
        filtered, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999
    )
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _transition_if_needed(
    registry: Any,
    entity_id: str,
    target_state: str,
    note: str = "",
) -> None:
    state_rank: dict[str, int] = {
        "PROPOSED": 0,
        "OPEN": 0,
        "APPROVED_FOR_TESTING": 1,
        "ACTIVE": 1,
        "TESTING": 2,
        "ANSWERED": 3,
        "COMPLETE": 3,
        "ARCHIVED": 4,
        "RETIRED": 4,
    }
    try:
        current = str(registry.get(entity_id).lifecycle_state)
        if state_rank.get(current, 0) < state_rank.get(target_state, 0):
            if note:
                registry.transition(entity_id, target_state, note=note)
            else:
                registry.transition(entity_id, target_state)
    except Exception:
        pass


def run_dc2_phase3_campaign(repo_root: Path) -> dict[str, Any]:
    resolved_base = (repo_root / "data" / "ikros").resolve()
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    spec = _default_campaign_spec()
    research_question = ResearchQuestion.from_dict(
        _with_reproducibility_hash(spec["research_question_primary"])
    )
    experiment = Experiment.from_dict(_with_reproducibility_hash(spec["experiment"]))

    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {
            "entity_type": "ResearchQuestion",
            "entity": research_question.to_dict(),
        },
        TaskKind.EXPERIMENT_REGISTRATION.value: {
            "entity_type": "Experiment",
            "entity": experiment.to_dict(),
        },
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective="Construct the institutional cross-asset information network describing how information propagates through financial markets before XAU/USD transitions between regimes.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )

    analysis = prepare_dc2_phase3_artifacts(repo_root=repo_root)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    output_dir = repo_root / DC2_PHASE3_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    report_paths = emit_dc2_phase3_reports(
        analysis, campaign_result=report.to_dict(), repo_root=repo_root
    )

    for rq_secondary in spec["research_questions_secondary"]:
        rq_id = str(rq_secondary["ikros_id"])
        if not research_registry.exists(rq_id):
            try:
                rq_dict = {
                    "ikros_id": rq_id,
                    "entity_type": "ResearchQuestion",
                    "version": "1.0.0",
                    "lifecycle_state": "ANSWERED",
                    "confidence": {
                        "prior": 0.5,
                        "statistical": 0.55,
                        "economic": 0.55,
                        "data": 0.5,
                        "model": 0.5,
                        "validation": 0.5,
                        "replication": 0.0,
                        "operational": 0.5,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "dc2-phase3",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "DC2 Phase 3 secondary question",
                            "motivation": rq_secondary.get("statement", ""),
                        },
                        "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": [],
                    "capability_refs": [],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": f"DC2-P3: {rq_secondary.get('theme', rq_id)}",
                    "motivation": str(rq_secondary.get("statement", "")),
                    "instrument": "XAU/USD",
                    "scope": "CROSS_ASSET",
                    "time_horizon": "1D",
                    "reproducibility_hash": compute_reproducibility_hash(rq_secondary),
                }
                rq_obj = ResearchQuestion.from_dict(rq_dict)
                research_registry.register(rq_obj)
                research_registry.link_conclusion(rq_id, campaign.campaign_id)
                _transition_if_needed(
                    research_registry,
                    rq_id,
                    "ANSWERED",
                    note="DC2 Phase 3 addressed this network question.",
                )
            except Exception:
                pass

    arb = analysis["arb_recommendation"]
    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        "ANSWERED",
        note=f"DC2 Phase 3 completed. Governing model: {arb['governing_model']}.",
    )
    _transition_if_needed(experiment_registry, experiment.ikros_id, "COMPLETE")

    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    metrics = {
        "phase": "DC2_PROGRAM_A_PHASE3",
        "n_nodes": len(analysis["overall_network"]["nodes"]),
        "n_edges": len(analysis["overall_network"]["edges"]),
        "n_communities": len(analysis["community_detection"]["communities"]),
        "n_feedback_loops": len(analysis["community_detection"]["feedback_loops"]),
        "campaign_id": campaign.campaign_id,
        "reports": report_paths,
    }
    write_json(repo_root / "reports" / "dc2-phase3-metrics.json", metrics)

    return {
        "campaign_id": campaign.campaign_id,
        "campaign_result": report.to_dict(),
        "analysis_summary": arb,
        "report_paths": report_paths,
        "metrics": metrics,
    }


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC2 Program A Phase 3: Institutional Cross-Asset Information Network",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-3001",
            "entity_type": "ResearchQuestion",
            "version": "1.0.0",
            "lifecycle_state": "ANSWERED",
            "confidence": {
                "prior": 0.55,
                "statistical": 0.55,
                "economic": 0.60,
                "data": 0.50,
                "model": 0.50,
                "validation": 0.50,
                "replication": 0.0,
                "operational": 0.50,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-phase3",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "DC2 Program A Phase 3 primary research question",
                    "motivation": "Phase 2 established causal relationships. Phase 3 integrates them into the full institutional information network.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-P3: What is the governing institutional cross-asset information network preceding XAU/USD regime transitions?",
            "motivation": "The network must be modeled as a full system, not as independent pairwise relationships.",
            "instrument": "XAU/USD",
            "scope": "CROSS_ASSET",
            "time_horizon": "1D",
            "reproducibility_hash": "dc2-phase3-rq-primary-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-3001",
            "entity_type": "Experiment",
            "version": "1.0.0",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.55,
                "statistical": 0.55,
                "economic": 0.60,
                "data": 0.50,
                "model": 0.50,
                "validation": 0.50,
                "replication": 0.0,
                "operational": 0.50,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-phase3",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "DC2 Phase 3 network experiment",
                    "motivation": "Dynamic directed network, centrality, communities, hierarchy, and stability.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-P3-EXP-001: Institutional Cross-Asset Information Network",
            "description": "Construct the governed dynamic information network over the full causal market system.",
            "reproducibility_hash": "dc2-phase3-exp-v1",
        },
        "research_questions_secondary": [
            {
                "ikros_id": "IKROS-RQ-20260802-3002",
                "theme": "Source Markets",
                "statement": "Which markets act as persistent information sources prior to XAU/USD regime transitions?",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-3003",
                "theme": "Relay Markets",
                "statement": "Which markets relay or bottleneck information between macro shocks and XAU/USD?",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-3004",
                "theme": "Regime Topology",
                "statement": "How does network topology change across the six institutional regimes and stress periods?",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-3005",
                "theme": "Feedback Loops",
                "statement": "Which feedback loops are stable enough to be treated as institutional network structure?",
            },
        ],
    }
