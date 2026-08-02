"""Governed runner for WP-IMP-0050 Institutional Alpha Evidence & Validation Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_evidence_validation_engine import (
    WP0050_DIR,
    emit_wp_imp_0050_reports,
    prepare_wp_imp_0050_artifacts,
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


def _with_reproducibility_hash(entity: dict[str, Any]) -> dict[str, Any]:
    payload = dict(entity)
    if "reproducibility_hash" not in payload:
        payload["reproducibility_hash"] = compute_reproducibility_hash(payload)
    return payload


def _select_campaign_pipeline(
    campaign: ResearchCampaign, task_kinds: list[str]
) -> ResearchCampaign:
    allowed = set(task_kinds)
    selected = [task for task in campaign.tasks if task.kind in allowed]
    ordered = sorted(
        selected, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999
    )
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _upsert_graph_payload(
    repo_root: Path, analysis: dict[str, Any], campaign_id: str
) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = cast(dict[str, Any], analysis["ikros_graph_payload"])
    created_nodes = 0
    created_edges = 0

    for raw in cast(list[dict[str, Any]], payload["nodes"]):
        node = GraphNode(
            node_id=str(raw["node_id"]),
            node_type=(
                NodeType.VALIDATION.value
                if str(raw["node_type"]) == "VALIDATION"
                else NodeType.RESEARCH_CONCLUSION.value
            ),
            ikros_id=str(raw["node_id"]),
            label=str(raw["label"]),
            confidence=float(raw["confidence"]),
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0050"],
            attributes={},
        )
        if not graph.has_node(node.node_id):
            graph.add_node(node)
            created_nodes += 1

    relation_index = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(
        source_id: str,
        target_id: str,
        edge_type: str,
        confidence: float,
        evidence_ref: str,
    ) -> None:
        nonlocal created_edges
        key = (source_id, target_id, edge_type)
        if key in relation_index:
            return
        if not graph.has_node(source_id) or not graph.has_node(target_id):
            return
        edge = GraphEdge(
            edge_id=graph.next_edge_id(),
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            confidence=confidence,
            evidence_ref=evidence_ref,
            spec_ref="SPEC-060",
            wp_ref="WP-IMP-0050",
            attributes={},
        )
        graph.add_edge(edge)
        relation_index.add(key)
        created_edges += 1

    for raw_edge in cast(list[dict[str, Any]], payload["edges"]):
        relation = str(raw_edge["relation"])
        edge_type = (
            EdgeType.RELATED_TO.value
            if relation == "VALIDATED_BY"
            else EdgeType.SUPPORTED_BY.value
        )
        add_edge(
            str(raw_edge["source"]),
            str(raw_edge["target"]),
            edge_type,
            float(raw_edge["confidence"]),
            str(WP0050_DIR / "FINAL_REPORT.md"),
        )

    add_edge(
        str(payload["batch_node_id"]),
        campaign_id,
        EdgeType.DERIVED_FROM.value,
        0.78,
        str(WP0050_DIR / "FINAL_REPORT.md"),
    )

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Generation 2 WP-IMP-0050 Institutional Alpha Evidence Engine",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260803-0050",
            "title": "WP-IMP-0050 Primary Research Question",
            "question": (
                "Can AFRP maintain a permanent evidence-first institutional alpha "
                "validation system with hard observation gates and governed lineage?"
            ),
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.64,
                "statistical": 0.0,
                "economic": 0.62,
                "data": 0.59,
                "model": 0.60,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "wp-imp-0050-evidence-engine",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 evidence-engine bootstrap",
                    "motivation": "Institutionalize scientific validation as a permanent system.",
                }
            },
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260803-0050",
            "title": "WP-IMP-0050 Evidence Engine Integration",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260803-0050",
            "dataset_refs": [
                "dc3_phase4_batch1_validation.json",
                "dc3_phase5_revision_analysis.json",
            ],
            "methodology": "institutional_evidence_first_validation_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.63,
                "statistical": 0.0,
                "economic": 0.61,
                "data": 0.58,
                "model": 0.60,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-03T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "wp-imp-0050-evidence-engine",
                    "created_at": "2026-08-03T00:00:00Z",
                    "creation_context": "Generation 2 evidence-engine integration",
                    "motivation": "Establish evidence-led, reproducible mechanism validation.",
                }
            },
        },
    }


def run_wp_imp_0050_campaign(repo_root: Path) -> dict[str, Any]:
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _campaign_spec()
    rq = ResearchQuestion.from_dict(_with_reproducibility_hash(spec["research_question_primary"]))
    exp = Experiment.from_dict(_with_reproducibility_hash(spec["experiment"]))
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
            "Implement a permanent institutional evidence and validation engine with "
            "hard observation completeness gates, governed scorecards, failure dossiers, "
            "confidence updates, and IKROS lineage updates."
        ),
        campaign_type="HYPOTHESIS_VALIDATION",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.STATISTICAL_EVALUATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )

    analysis = prepare_wp_imp_0050_artifacts(repo_root=repo_root)

    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_wp_imp_0050_reports(
        analysis, campaign_result=report.to_dict(), repo_root=repo_root
    )
    graph_metrics = _upsert_graph_payload(repo_root, analysis, campaign.campaign_id)

    metrics = {
        "campaign_id": campaign.campaign_id,
        "engine_id": analysis["engine_architecture"]["engine_id"],
        "mechanisms_processed": len(analysis["mechanism_dossiers"]),
        "blocked_on_observation_completeness": analysis[
            "blocked_on_observation_completeness"
        ],
        "validated_mechanisms": analysis["validated_mechanisms"],
        "ready_for_revalidation": analysis["ready_for_revalidation"],
        "research_mechanisms": analysis["research_mechanisms"],
        "promote_any_alpha_now": False,
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
        "arb_recommendation": analysis["arb_recommendation"],
    }
    write_json(repo_root / WP0050_DIR / "wp_imp_0050_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_wp_imp_0050_campaign(root)
    print(
        "WP-IMP-0050 complete - "
        f"processed={result['mechanisms_processed']}, "
        f"blocked={len(result['blocked_on_observation_completeness'])}, "
        f"validated={len(result['validated_mechanisms'])}"
    )
