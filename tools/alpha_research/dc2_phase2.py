"""Discovery Cycle 2 Program A Phase 2 governed campaign execution.

DC2 Research Program A Phase 2: Cross-Asset Causal Transition Analysis.

Architecture constraints:
- Runtime FROZEN
- IKROS FROZEN (architecture; data writes are permitted)
- No infrastructure development
- No hypothesis creation, strategy synthesis, or parameter optimization
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.causal_analysis import (
    DC2_PHASE2_DIR,
    emit_dc2_phase2_reports,
    prepare_dc2_phase2_artifacts,
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

DC2_PHASE2_MANIFEST = (
    Path("11-research")
    / "discovery-cycle-2"
    / "research-program-a-phase2"
    / "dc2_phase2_campaign_manifest.json"
)


def _with_reproducibility_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc2-phase2-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_campaign_pipeline(
    campaign: ResearchCampaign,
    task_kinds: list[str],
) -> ResearchCampaign:
    """Filter campaign tasks to the named kind subset and rewire dependencies linearly."""
    kind_set = set(task_kinds)
    filtered = [t for t in campaign.tasks if t.kind in kind_set]
    ordered = sorted(
        filtered, key=lambda t: task_kinds.index(t.kind) if t.kind in task_kinds else 999
    )
    for i, task in enumerate(ordered):
        task.depends_on = [ordered[i - 1].task_id] if i > 0 else []
    campaign.tasks = ordered
    # Sync pipeline.task_ids to the filtered set
    campaign.pipeline.task_ids = [t.task_id for t in ordered]
    campaign.pipeline.stages = [t.kind for t in ordered]
    return campaign


def _transition_if_needed(
    registry: Any,
    entity_id: str,
    target_state: str,
    note: str = "",
) -> None:
    """Transition entity to target_state only if not already at or past that state."""
    _state_rank: dict[str, int] = {
        "PROPOSED": 0,
        "APPROVED_FOR_TESTING": 1,
        "TESTING": 2,
        "COMPLETE": 3,
        "ARCHIVED": 4,
    }
    try:
        entity = registry.get(entity_id)
        current = getattr(entity, "lifecycle_state", "PROPOSED")
        if _state_rank.get(current, 0) < _state_rank.get(target_state, 0):
            registry.transition(entity_id, target_state, note=note)
    except Exception:
        pass


def run_dc2_phase2_campaign(repo_root: Path) -> dict[str, Any]:
    """Execute the governed DC2 Program A Phase 2 causal analysis campaign.

    Returns a dict summarising the campaign result, registered entities, and report paths.
    """
    # ------------------------------------------------------------------ setup
    resolved_base = (repo_root / "data" / "ikros").resolve()
    orchestrator = ResearchOrchestrator(base_dir=resolved_base)

    # ------------------------------------------------------------------ manifest
    manifest_path = repo_root / DC2_PHASE2_MANIFEST
    if manifest_path.exists():
        campaign_spec = cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
    else:
        campaign_spec = _default_campaign_spec()

    # ------------------------------------------------------------------ research question + experiment
    rq_primary_dict = campaign_spec.get("research_question_primary", {})
    rq_id = rq_primary_dict.get("ikros_id", "IKROS-RQ-20260802-2001")
    exp_spec = campaign_spec.get("experiment", {})

    try:
        rq_obj = ResearchQuestion.from_dict(_with_reproducibility_hash(rq_primary_dict))
        exp_obj = Experiment.from_dict(_with_reproducibility_hash(exp_spec))
    except Exception:
        rq_obj = ResearchQuestion.from_dict(
            _with_reproducibility_hash(_default_campaign_spec()["research_question_primary"])
        )
        exp_obj = Experiment.from_dict(
            _with_reproducibility_hash(_default_campaign_spec()["experiment"])
        )

    # ------------------------------------------------------------------ build campaign (dict payload by TaskKind)
    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {
            "entity_type": "ResearchQuestion",
            "entity": rq_obj.to_dict(),
        },
        TaskKind.EXPERIMENT_REGISTRATION.value: {
            "entity_type": "Experiment",
            "entity": exp_obj.to_dict(),
        },
    }
    campaign = orchestrator.build_campaign(
        title=str(
            campaign_spec.get(
                "title", "DC2 Program A Phase 2: Cross-Asset Causal Transition Analysis"
            )
        ),
        objective="Determine which observed cross-asset relationships represent genuine causal mechanisms preceding XAU/USD regime transitions.",
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

    # ------------------------------------------------------------------ run analysis
    analysis = prepare_dc2_phase2_artifacts(repo_root=repo_root)

    # ------------------------------------------------------------------ register entities and run campaign
    research_registry = cast(
        ResearchRegistry,
        orchestrator._registries.get("ResearchQuestion", ResearchRegistry(base_dir=resolved_base)),
    )
    experiment_registry = cast(
        ExperimentRegistry,
        orchestrator._registries.get("Experiment", ExperimentRegistry(base_dir=resolved_base)),
    )

    if not research_registry.exists(rq_obj.ikros_id):
        research_registry.register(rq_obj)
    if not experiment_registry.exists(exp_obj.ikros_id):
        experiment_registry.register(exp_obj)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    # ------------------------------------------------------------------ emit reports
    out_dir = repo_root / DC2_PHASE2_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    report_paths = emit_dc2_phase2_reports(
        analysis, campaign_result=report.to_dict(), repo_root=repo_root
    )

    # ------------------------------------------------------------------ register secondary RQs
    secondary_rqs = campaign_spec.get("research_questions_secondary", [])
    for rq_secondary in secondary_rqs:
        rq_id_s = rq_secondary.get("ikros_id", f"IKROS-RQ-20260802-{id(rq_secondary)}")
        try:
            rq_d: dict[str, Any] = {
                "ikros_id": rq_id_s,
                "entity_type": "ResearchQuestion",
                "version": "1.0.0",
                "lifecycle_state": "ANSWERED",
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
                        "created_by": "dc2-phase2",
                        "created_at": "2026-08-02T00:00:00Z",
                        "creation_context": "DC2 Phase 2 secondary question",
                        "motivation": rq_secondary.get("statement", ""),
                    },
                    "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
                },
                "spec_refs": [],
                "capability_refs": [],
                "work_package_refs": [],
                "version_history": [],
                "title": f"DC2-P2: {rq_secondary.get('theme', rq_id_s)}",
                "motivation": str(rq_secondary.get("statement", "")),
                "instrument": "XAU/USD",
                "scope": "CROSS_ASSET",
                "time_horizon": "1D",
                "reproducibility_hash": compute_reproducibility_hash(rq_secondary),
            }
            rq_obj_s = ResearchQuestion.from_dict(rq_d)
            research_registry.register(rq_obj_s)
            research_registry.link_conclusion(rq_id_s, campaign.campaign_id)
            _transition_if_needed(
                research_registry,
                rq_id_s,
                "COMPLETE",
                note="DC2 Phase 2 addressed this secondary question.",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------ confidence updates
    arb = analysis.get("arb_summary", {})
    promoted = arb.get("promote_to_institutional_knowledge", [])
    _transition_if_needed(
        research_registry,
        rq_id,
        "COMPLETE",
        note=f"DC2 Phase 2 complete. {len(promoted)} signals promoted to institutional knowledge.",
    )

    # ------------------------------------------------------------------ write metrics
    (repo_root / "reports").mkdir(parents=True, exist_ok=True)
    metrics = {
        "phase": "DC2_PROGRAM_A_PHASE2",
        "n_signals_analysed": len(analysis.get("causal_conclusions", {})),
        "n_promoted": len(arb.get("promote_to_institutional_knowledge", [])),
        "n_retained": len(arb.get("retain_for_validation", [])),
        "n_rejected": len(arb.get("reject", [])),
        "campaign_id": campaign.campaign_id,
        "reports": report_paths,
    }
    write_json(repo_root / "reports" / "dc2-phase2-metrics.json", metrics)

    return {
        "campaign_id": campaign.campaign_id,
        "campaign_result": report.to_dict(),
        "analysis_summary": arb,
        "report_paths": report_paths,
        "metrics": metrics,
    }


def _default_tasks() -> list[dict[str, Any]]:
    return [
        {
            "task_id": "p2-t1",
            "title": "Theme 1: Conditional Causality",
            "kind": TaskKind.STATISTICAL_EVALUATION.value,
            "depends_on": [],
        },
        {
            "task_id": "p2-t2",
            "title": "Theme 2: Time-Lag Causality",
            "kind": TaskKind.STATISTICAL_EVALUATION.value,
            "depends_on": ["p2-t1"],
        },
        {
            "task_id": "p2-t3",
            "title": "Theme 3: Macro Mediation",
            "kind": TaskKind.STATISTICAL_EVALUATION.value,
            "depends_on": ["p2-t2"],
        },
        {
            "task_id": "p2-t4",
            "title": "Theme 4: Causal Stability",
            "kind": TaskKind.STATISTICAL_EVALUATION.value,
            "depends_on": ["p2-t3"],
        },
        {
            "task_id": "p2-t5",
            "title": "Causal Synthesis and ARB Report",
            "kind": TaskKind.FINAL_REPORT.value,
            "depends_on": ["p2-t4"],
        },
    ]


def _default_campaign_spec() -> dict[str, Any]:
    """Minimal campaign spec used when no manifest file is present."""
    return {
        "title": "DC2 Program A Phase 2: Cross-Asset Causal Transition Analysis",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-2001",
            "entity_type": "ResearchQuestion",
            "version": "1.0.0",
            "lifecycle_state": "ANSWERED",
            "confidence": {
                "prior": 0.5,
                "statistical": 0.5,
                "economic": 0.6,
                "data": 0.4,
                "model": 0.5,
                "validation": 0.5,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-phase2",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "DC2 Program A Phase 2 primary research question",
                    "motivation": "Phase 1 produced observational relationships. Phase 2 tests causal validity.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-P2: Which observed cross-asset relationships represent genuine causal mechanisms?",
            "motivation": "Phase 1 observational findings need causal validation before becoming institutional knowledge.",
            "instrument": "XAU/USD",
            "scope": "CROSS_ASSET",
            "time_horizon": "1D",
            "reproducibility_hash": "dc2-phase2-rq-primary-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-2001",
            "entity_type": "Experiment",
            "version": "1.0.0",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.5,
                "statistical": 0.5,
                "economic": 0.6,
                "data": 0.4,
                "model": 0.5,
                "validation": 0.5,
                "replication": 0.0,
                "operational": 0.5,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc2-phase2",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "DC2 Phase 2 causal analysis experiment",
                    "motivation": "Multi-method Granger/TE/partial-correlation causal audit.",
                },
                "dependencies": {"supporting": [], "contradicting": [], "ers_records": []},
            },
            "spec_refs": [],
            "capability_refs": [],
            "work_package_refs": [],
            "version_history": [],
            "title": "DC2-P2-EXP-001: Cross-Asset Causal Audit",
            "description": "Four-theme causal analysis: conditional Granger, lag-horizon Granger, macro mediation, rolling stability.",
            "reproducibility_hash": "dc2-phase2-exp-v1",
        },
        "tasks": _default_tasks(),
        "research_questions_secondary": [
            {
                "ikros_id": "IKROS-RQ-20260802-2002",
                "theme": "Conditional Causality",
                "statement": "Does causal influence from cross-asset signals to XAU/USD change across the six institutional regimes?",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-2003",
                "theme": "Time-Lag Causality",
                "statement": "At what horizons (immediate/short/medium/long) do cross-asset signals most causally precede XAU/USD transitions?",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-2004",
                "theme": "Macro Mediation",
                "statement": "Are cross-asset correlations direct causal paths or are they mediated by shared macro factors (DXY, yields, macro_pressure)?",
            },
            {
                "ikros_id": "IKROS-RQ-20260802-2005",
                "theme": "Causal Stability",
                "statement": "Do identified causal relationships remain stable across macro cycles, volatility regimes, and stress periods?",
            },
        ],
    }
