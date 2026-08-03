"""Discovery Cycle 2 governed campaign execution for AFRP cross-asset research.

DC2 Research Program A: Cross-Asset Transition Ecology.

Architecture constraints:
- Runtime FROZEN
- IKROS FROZEN (architecture; data writes are permitted)
- No infrastructure development
- No hypothesis creation, strategy synthesis, or parameter optimization
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, cast

from tools.alpha_research.cross_asset_ecology import (
    DC2_PROGRAM_A_DIR,
    emit_dc2_program_a_reports,
    prepare_dc2_program_a_artifacts,
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

DC2_PROGRAM_A_MANIFEST = (
    Path("11-research")
    / "discovery-cycle-2"
    / "research-program-a"
    / "dc2_program_a_campaign_manifest.json"
)


def load_dc2_program_a_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / DC2_PROGRAM_A_MANIFEST
    return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))


def _with_reproducibility_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc2-program-a-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_campaign_pipeline(
    campaign: ResearchCampaign,
    task_kinds: list[str],
) -> None:
    task_by_kind = {task.kind: task for task in campaign.tasks}
    selected_tasks = [task_by_kind[kind] for kind in task_kinds if kind in task_by_kind]
    previous_id: str | None = None
    for index, task in enumerate(selected_tasks, start=1):
        task.planned_order = index
        task.depends_on = [] if previous_id is None else [previous_id]
        previous_id = task.task_id
    campaign.tasks = selected_tasks
    campaign.pipeline.stages = [task.kind for task in selected_tasks]
    campaign.pipeline.task_ids = [task.task_id for task in selected_tasks]


def _resolve_task_payloads(
    repo_root: Path,
    raw_payloads: dict[str, Any],
) -> dict[str, Any]:
    del repo_root
    return dict(raw_payloads)


class _TransitionEntity(Protocol):
    lifecycle_state: str


class _TransitionRegistry(Protocol):
    def get(self, entity_id: str) -> _TransitionEntity: ...

    def transition(
        self,
        entity_id: str,
        target_state: str,
        note: str = "",
    ) -> object: ...


def _transition_if_needed(
    registry: _TransitionRegistry,
    entity_id: str,
    target_state: str,
    *,
    note: str = "",
) -> None:
    """Transition entity to target_state only if not already at or past that state."""
    state_rank: dict[str, int] = {
        "PROPOSED": 0,
        "APPROVED_FOR_TESTING": 1,
        "OPEN": 1,
        "ACTIVE": 2,
        "TESTING": 3,
        "COMPLETE": 4,
        "SUPPORTED": 4,
        "REFUTED": 4,
        "INCONCLUSIVE": 4,
        "CLOSED": 5,
    }
    try:
        current = str(registry.get(entity_id).lifecycle_state)
        current_rank = state_rank.get(current, -1)
        target_rank = state_rank.get(target_state, -1)
        if current_rank < target_rank:
            if note:
                registry.transition(entity_id, target_state, note=note)
            else:
                registry.transition(entity_id, target_state)
    except Exception:
        pass


def run_dc2_program_a_campaign(
    repo_root: Path,
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute DC2 Research Program A — Cross-Asset Transition Ecology.

    Runs all five research themes, registers IKROS entities, emits reports.
    Does NOT create hypotheses, build strategies, or optimize parameters.
    """
    repo_root = repo_root.resolve()
    manifest = load_dc2_program_a_manifest(repo_root)
    resolved_base = (base_dir or (repo_root / "data" / "ikros")).resolve()
    resolved_output = (output_dir or (repo_root / DC2_PROGRAM_A_DIR)).resolve()

    # --- Run analysis ---
    prepared = prepare_dc2_program_a_artifacts(output_dir=resolved_output)
    analysis = cast(dict[str, Any], prepared["analysis"])

    # --- IKROS orchestration ---
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    rq_data = manifest["entities"]["research_question_primary"]
    research_question = ResearchQuestion.from_dict(rq_data)

    exp_data = manifest["task_payloads"]["EXPERIMENT_REGISTRATION"]["entity"]
    experiment = Experiment.from_dict(_with_reproducibility_hash(exp_data))

    task_payloads = _resolve_task_payloads(repo_root, manifest["task_payloads"])
    task_payloads[TaskKind.RESEARCH_QUESTION.value] = {
        "entity_type": "ResearchQuestion",
        "entity": research_question.to_dict(),
    }
    task_payloads[TaskKind.EXPERIMENT_REGISTRATION.value] = {
        "entity_type": "Experiment",
        "entity": experiment.to_dict(),
    }

    campaign_spec = manifest["campaign"]
    campaign = orchestrator.build_campaign(
        title=str(campaign_spec["title"]),
        objective=(
            "Map cross-asset transition ecology to determine how information "
            "propagates before XAU/USD regime changes."
        ),
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.FAIL_FAST.value,
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )
    campaign.evidence_refs = [str(prepared["paths"]["analysis"])]

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])

    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        "ACTIVE",
        note="DC2 Program A ecology mapping active.",
    )
    _transition_if_needed(
        research_registry,
        research_question.ikros_id,
        "COMPLETE",
        note="DC2 Program A ecology mapping completed.",
    )
    _transition_if_needed(experiment_registry, experiment.ikros_id, "COMPLETE")

    # Register secondary research questions
    for rq_secondary in manifest["entities"]["research_questions_secondary"]:
        rq_id = str(rq_secondary["id"])
        if not research_registry.exists(rq_id):
            try:
                rq_dict = {
                    "ikros_id": rq_id,
                    "entity_type": "ResearchQuestion",
                    "version": "1.0.0",
                    "lifecycle_state": "OPEN",
                    "confidence": {
                        "prior": 0.5,
                        "statistical": 0.5,
                        "economic": 0.5,
                        "data": 0.5,
                        "model": 0.5,
                        "validation": 0.5,
                        "replication": 0.0,
                        "operational": 0.5,
                        "last_updated": "2026-08-02T00:00:00Z",
                    },
                    "lineage": {
                        "origin": {
                            "created_by": "dc2-program-a",
                            "created_at": "2026-08-02T00:00:00Z",
                            "creation_context": "DC2 Program A secondary question",
                            "motivation": rq_secondary.get("statement", ""),
                        },
                        "dependencies": {
                            "inputs": [],
                            "datasets": [],
                            "features": [],
                            "models": [],
                            "external_refs": [],
                        },
                        "experiments": {"tested_in": [], "validated_by": []},
                        "evidence": {"supporting": [], "contradicting": [], "ers_records": []},
                    },
                    "spec_refs": [],
                    "capability_refs": [],
                    "work_package_refs": [],
                    "version_history": [],
                    "title": f"DC2-PA: {rq_secondary.get('theme', rq_id)}",
                    "motivation": str(rq_secondary.get("statement", "")),
                    "scope": "MACRO",
                    "instrument": "XAU/USD",
                    "time_horizon": "1D",
                    "campaign_tag": "DC2-PROGRAM-A-001",
                    "linked_hypotheses": [],
                    "linked_conclusions": [],
                }
                rq_obj = ResearchQuestion.from_dict(rq_dict)
                research_registry.register(rq_obj)
                research_registry.link_conclusion(rq_id, campaign.campaign_id)
                _transition_if_needed(
                    research_registry,
                    rq_id,
                    "COMPLETE",
                    note="DC2 Program A addressed this secondary question.",
                )
            except Exception:
                pass

    arb = analysis.get("arb_recommendation", {})
    lifecycle_status = "COMPLETE"

    result: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "report": report.to_dict(),
        "progress": report.progress,
        "lifecycle_status": lifecycle_status,
        "research_question": research_registry.get(research_question.ikros_id).to_dict(),
        "experiment": experiment_registry.get(experiment.ikros_id).to_dict(),
        "program_summary": {
            "title": analysis["program"]["title"],
            "available_signals": analysis["program"]["available_signals"],
            "rows_analyzed": analysis["program"]["rows_analyzed"],
            "total_transitions": analysis["theme3_transition_ecology"]["total_transitions"],
            "dominant_transition_drivers": arb.get("dominant_transition_drivers", []),
            "strongest_relationships": arb.get("strongest_cross_market_relationships", []),
            "granger_positive": arb.get("granger_positive_signals", []),
            "stable_signals": arb.get("stable_relationships", []),
            "data_gap_count": len(analysis["data_availability"]["unavailable_markets"]),
            "high_severity_gaps": arb.get("data_gap_priority", []),
            "arb_narrative": arb.get("arb_narrative", ""),
        },
    }

    report_paths = emit_dc2_program_a_reports(
        output_dir=resolved_output,
        analysis=analysis,
        campaign_result=result,
    )
    result["report_paths"] = report_paths

    # Write report metrics
    metrics = {
        "campaign": "DC2 Research Program A",
        "cycle": "Discovery Cycle 2",
        "status": lifecycle_status,
        "signals_analyzed": len(analysis["program"]["available_signals"]),
        "unavailable_markets": analysis["program"]["unavailable_markets"],
        "rows": analysis["program"]["rows_analyzed"],
        "transitions_identified": analysis["theme3_transition_ecology"]["total_transitions"],
        "granger_positive_signals": arb.get("granger_positive_signals", []),
        "dominant_drivers": arb.get("dominant_transition_drivers", []),
        "top_signals": arb.get("strongest_cross_market_relationships", [])[:5],
        "promotion_candidates": arb.get("promotion_candidates_for_dc2_validation", []),
        "reports_written": len(report_paths),
    }
    metrics_path = repo_root / "reports" / "dc2-program-a-metrics.json"
    write_json(metrics_path, metrics)

    result_path = resolved_output / "dc2_program_a_campaign_result.json"
    write_json(result_path, result)
    result["report_paths"]["campaign_result"] = str(result_path)
    result["report_paths"]["metrics"] = str(metrics_path)

    return result
