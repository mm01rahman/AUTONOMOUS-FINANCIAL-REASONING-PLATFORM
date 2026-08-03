"""Program 1 — Institutional Alpha Factory: governed IKROS campaign runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_factory import (
    PROGRAM1_DIR,
    emit_program1_reports,
    prepare_program1_artifacts,
)
from tools.alpha_research.reporting import write_json
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
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


def _with_hash(entity: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entity)
    if "reproducibility_hash" not in payload:
        payload["reproducibility_hash"] = compute_reproducibility_hash(payload)
    return payload


def _select_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    allowed = set(task_kinds)
    selected = [t for t in campaign.tasks if t.kind in allowed]
    ordered = sorted(
        selected, key=lambda t: task_kinds.index(t.kind) if t.kind in task_kinds else 999
    )
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [t.task_id for t in ordered]
    campaign.pipeline.stages = [t.kind for t in ordered]
    return campaign


def _upsert_graph(
    repo_root: Path, analysis: dict[str, Any], campaign_id: str
) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    created_nodes = 0
    created_edges = 0

    alpha_ids: list[str] = [
        str(r["alpha_id"]) for r in cast(list[dict[str, Any]], analysis["mechanism_results"])
    ]

    # Register each alpha as a RESEARCH_CONCLUSION node if not already present
    for alpha_id in alpha_ids:
        if not graph.has_node(alpha_id):
            node = GraphNode(
                node_id=alpha_id,
                node_type=NodeType.RESEARCH_CONCLUSION.value,
                ikros_id=alpha_id,
                label=f"Alpha {alpha_id}",
                confidence=0.60,
                spec_refs=["SPEC-060"],
                wp_refs=["WP-IMP-0051"],
                attributes={},
            )
            graph.add_node(node)
            created_nodes += 1

    # Add promotion committee node per mechanism
    relation_index = {(e.source_id, e.target_id, e.edge_type) for e in graph.edges()}

    def _add_edge(src: str, tgt: str, etype: str, conf: float, ref: str) -> None:
        nonlocal created_edges
        key = (src, tgt, etype)
        if key in relation_index:
            return
        if not graph.has_node(src) or not graph.has_node(tgt):
            return
        edge = GraphEdge(
            edge_id=graph.next_edge_id(),
            source_id=src,
            target_id=tgt,
            edge_type=etype,
            confidence=conf,
            evidence_ref=ref,
            spec_ref="SPEC-060",
            wp_ref="WP-IMP-0051",
            attributes={},
        )
        graph.add_edge(edge)
        relation_index.add(key)
        created_edges += 1

    # Link each alpha node to the campaign node if both exist
    for alpha_id in alpha_ids:
        _add_edge(
            alpha_id,
            campaign_id,
            EdgeType.DERIVED_FROM.value,
            0.65,
            str(PROGRAM1_DIR / "FINAL_REPORT.md"),
        )

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Program 1 — Institutional Alpha Factory: Complete Lifecycle Engine",
        "rq": {
            "ikros_id": "IKROS-RQ-20260803-0051",
            "title": "Program 1 Primary Research Question",
            "question": (
                "Does the Institutional Alpha Factory infrastructure successfully enforce "
                "governed promotion criteria and prevent premature alpha promotion?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.62,
                "statistical": 0.0,
                "economic": 0.60,
                "data": 0.58,
                "model": 0.60,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program1-alpha-factory",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 Program 1 bootstrap",
                    "motivation": "Establish permanent institutional alpha lifecycle governance.",
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0051",
            "title": "Program 1 Alpha Factory Integration Experiment",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0051",
            "dataset_refs": [
                "dc3_phase4_batch1_validation.json",
                "dc3_phase5_revision_analysis.json",
                "wp_imp_0050_evidence_validation_engine.json",
            ],
            "methodology": "institutional_alpha_factory_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.61,
                "statistical": 0.0,
                "economic": 0.59,
                "data": 0.57,
                "model": 0.60,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "program1-alpha-factory",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 Program 1 factory experiment",
                    "motivation": (
                        "Validate that governed promotion criteria block premature alpha."
                    ),
                }
            },
        },
    }


def run_program1_alpha_factory_campaign(repo_root: Path) -> dict[str, Any]:
    """Execute Program 1 Institutional Alpha Factory and persist all artifacts."""
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _campaign_spec()

    rq = ResearchQuestion.from_dict(_with_hash(spec["rq"]))
    exp = Experiment.from_dict(_with_hash(spec["experiment"]))

    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {
            "entity_type": "ResearchQuestion",
            "entity": rq.to_dict(),
        },
        TaskKind.EXPERIMENT_REGISTRATION.value: {
            "entity_type": "Experiment",
            "entity": exp.to_dict(),
        },
    }

    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective=(
            "Implement and execute the complete Institutional Alpha Factory lifecycle: "
            "replication engine, promotion committee, alpha registry, evidence convergence, "
            "promotion review system, institutional dossier, IKROS extensions, and dashboards. "
            "No alpha promotion may occur without satisfying all 10 governed criteria."
        ),
        campaign_type="HYPOTHESIS_VALIDATION",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )

    _select_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.STATISTICAL_EVALUATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )

    analysis = prepare_program1_artifacts()

    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)

    report_paths = emit_program1_reports(
        analysis, campaign_result=report.to_dict(), repo_root=repo_root
    )

    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "program": analysis["program"],
        "mechanisms_processed": analysis["mechanisms_processed"],
        "approved_alpha_count": analysis["approved_alpha_count"],
        "no_promotion_executed": analysis["no_promotion_executed"],
        "replication_statuses": {
            r["mechanism"]: r["replication_status"]
            for r in analysis["replication_registry"]
        },
        "committee_decisions": {
            r["mechanism"]: r["decision"]
            for r in analysis["promotion_reviews"]
        },
        "final_lifecycle_states": {
            r["mechanism"]: r["final_lifecycle_state"]
            for r in analysis["mechanism_results"]
        },
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
        "arb_recommendation": analysis["arb_recommendation"],
    }

    write_json(repo_root / PROGRAM1_DIR / "program1_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_program1_alpha_factory_campaign(root)
    print(
        f"Program 1 complete — "
        f"processed={result['mechanisms_processed']}, "
        f"approved={result['approved_alpha_count']}, "
        f"promotion_blocked={result['no_promotion_executed']}"
    )
