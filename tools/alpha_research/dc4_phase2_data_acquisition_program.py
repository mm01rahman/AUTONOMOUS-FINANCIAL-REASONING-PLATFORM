"""Governed runner for Discovery Cycle 4 Phase 2 data acquisition prioritization."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_data_acquisition_prioritization import (
    DC4_PHASE2_DIR,
    _build_dataset_priorities,
    emit_dc4_phase2_reports,
)
from tools.alpha_research.reporting import write_json
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import FailurePolicy, ResearchCampaign, ResearchOrchestrator, TaskKind
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.research import ResearchRegistry


def _with_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "dc4-phase2-prioritization-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    kind_set = set(task_kinds)
    filtered = [task for task in campaign.tasks if task.kind in kind_set]
    ordered = sorted(filtered, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999)
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _upsert_graph(repo_root: Path, analysis: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = cast(dict[str, Any], analysis["ecology_knowledge_graph"])
    created_nodes = 0
    created_edges = 0

    for item in cast(list[dict[str, Any]], payload["dataset_nodes"]):
        node = GraphNode(
            node_id=str(item["node_id"]),
            node_type=NodeType.KNOWLEDGE_OBJECT.value,
            ikros_id=str(item["node_id"]),
            label=str(item["label"]),
            confidence=float(item["confidence"]),
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={},
        )
        if not graph.has_node(node.node_id):
            graph.add_node(node)
            created_nodes += 1

    conclusion = cast(dict[str, Any], payload["conclusion_node"])
    conclusion_node = GraphNode(
        node_id=str(conclusion["node_id"]),
        node_type=NodeType.RESEARCH_CONCLUSION.value,
        ikros_id=str(conclusion["node_id"]),
        label=str(conclusion["label"]),
        confidence=float(conclusion["confidence"]),
        spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0048"],
        attributes={},
    )
    if not graph.has_node(conclusion_node.node_id):
        graph.add_node(conclusion_node)
        created_nodes += 1

    relations = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(source: str, target: str, edge_type: str, confidence: float) -> None:
        nonlocal created_edges
        key = (source, target, edge_type)
        if key in relations or not graph.has_node(source) or not graph.has_node(target):
            return
        graph.add_edge(
            GraphEdge(
                edge_id=graph.next_edge_id(),
                source_id=source,
                target_id=target,
                edge_type=edge_type,
                confidence=confidence,
                evidence_ref=str(DC4_PHASE2_DIR / "ARB_RECOMMENDATION_DC4_PHASE2.md"),
                spec_ref="SPEC-060",
                wp_ref="WP-IMP-0048",
                attributes={},
            )
        )
        relations.add(key)
        created_edges += 1

    for edge in cast(list[dict[str, Any]], payload["edges"]):
        relation = str(edge["relation"])
        edge_type = EdgeType.SUPPORTED_BY.value if relation == "SUPPORTED_BY" else EdgeType.RELATED_TO.value
        add_edge(str(edge["source"]), str(edge["target"]), edge_type, float(edge["confidence"]))

    add_edge(str(conclusion["node_id"]), campaign_id, EdgeType.DERIVED_FROM.value, 0.80)
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC4 Phase 2 Institutional Data Acquisition Prioritization & ROI Program",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9801",
            "title": "DC4 Phase 2 Dataset Prioritization Primary Question",
            "question": "Which missing datasets should AFRP acquire first to maximize scientific value for institutional alpha research without resuming validation or building live integrations?",
            "category": "DATA_ACQUISITION_PRIORITIZATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.72,
                "statistical": 0.0,
                "economic": 0.74,
                "data": 0.62,
                "model": 0.68,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc4-phase2-data-acquisition-program",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "DC4 Phase 2 primary question",
                    "motivation": "Prioritize missing datasets by scientific value, validation impact, and governed implementation burden.",
                }
            },
            "reproducibility_hash": "dc4-phase2-prioritization-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9801",
            "title": "DC4 Phase 2 Dataset Prioritization Experiment",
            "experiment_type": "DATASET_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260802-0702",
            "dataset_refs": ["dc4_observability_analysis.json", "dc3_institutional_alpha_registry.json"],
            "methodology": "institutional_priority_scoring_and_roi_planning",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.72,
                "statistical": 0.0,
                "economic": 0.74,
                "data": 0.62,
                "model": 0.68,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "dc4-phase2-data-acquisition-program",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "DC4 Phase 2 prioritization experiment",
                    "motivation": "Produce a ranked acquisition plan, dependency graph, ROI report, and Data Foundation V2 work package roadmap without acquiring any datasets.",
                }
            },
            "reproducibility_hash": "dc4-phase2-prioritization-v1",
        },
    }


def run_dc4_phase2_campaign(repo_root: Path) -> dict[str, Any]:
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _campaign_spec()
    research_question = ResearchQuestion.from_dict(_with_hash(spec["research_question_primary"]))
    experiment = Experiment.from_dict(_with_hash(spec["experiment"]))
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
        objective="Rank missing datasets by scientific value, validation uplift, institutional reuse, and governed implementation burden; emit acquisition tiers, dependency graph, ROI analysis, and Data Foundation V2 work package plan.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_pipeline(
        campaign,
        [
            TaskKind.RESEARCH_QUESTION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
            TaskKind.FINAL_REPORT.value,
        ],
    )

    analysis = _build_dataset_priorities(repo_root=repo_root)

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc4_phase2_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph(repo_root, analysis, campaign.campaign_id)

    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "dataset_count": int(analysis["dataset_count"]),
        "tier_counts": analysis["tier_counts"],
        "top_5_datasets": analysis["top_5_datasets"],
        "tier_1_immediate": arb["tier_1_immediate"],
        "tier_4_commercial_only": arb["tier_4_commercial_only"],
        "top_roi_dataset": arb["top_roi_dataset"],
        "highest_scientific_value_dataset": arb["highest_scientific_value_dataset"],
        "highest_validation_impact_dataset": arb["highest_validation_impact_dataset"],
        "no_acquisition_performed": True,
        "no_validation_resumed": True,
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
    }
    write_json(repo_root / DC4_PHASE2_DIR / "dc4_phase2_metrics.json", metrics)
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_dc4_phase2_campaign(root)
    print(
        "DC4 Phase 2 complete - "
        f"datasets: {result['dataset_count']}, "
        f"top_roi: {result['top_roi_dataset']}, "
        f"tier1: {len(cast(list[str], result['tier_1_immediate']))}, "
        f"commercial_only: {len(cast(list[str], result['tier_4_commercial_only']))}"
    )
