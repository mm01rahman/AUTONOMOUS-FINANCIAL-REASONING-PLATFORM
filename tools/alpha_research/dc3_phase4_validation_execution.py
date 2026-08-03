"""Governed runner for Discovery Cycle 3 Phase 4 Adaptive Institutional Alpha Validation Program — Batch 1."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.institutional_alpha_validation_execution import (
    DC3_PHASE4_DIR,
    emit_dc3_phase4_validation_reports,
    prepare_dc3_phase4_validation_artifacts,
)
from tools.alpha_research.reporting import write_json
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import FailurePolicy, ResearchCampaign, ResearchOrchestrator, TaskKind
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.research import ResearchRegistry


def _with_reproducibility_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if (
        "reproducibility_hash" not in result
        or result["reproducibility_hash"] == "dc3-phase4-validation-execution-v1"
    ):
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_campaign_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    kind_set = set(task_kinds)
    filtered = [task for task in campaign.tasks if task.kind in kind_set]
    ordered = sorted(filtered, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999)
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _upsert_graph_payload(repo_root: Path, analysis: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    payload = cast(dict[str, Any], analysis["ecology_knowledge_graph"])
    created_nodes = 0
    created_edges = 0

    validation_nodes = cast(list[dict[str, Any]], payload["validation_nodes"])
    batch_node = cast(dict[str, Any], payload["batch_node"])

    for item in validation_nodes:
        node = GraphNode(
            node_id=str(item["node_id"]),
            node_type=NodeType.VALIDATION.value,
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

    bn = GraphNode(
        node_id=str(batch_node["node_id"]),
        node_type=NodeType.RESEARCH_CONCLUSION.value,
        ikros_id=str(batch_node["node_id"]),
        label=str(batch_node["label"]),
        confidence=float(batch_node["confidence"]),
        spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0048"],
        attributes={},
    )
    if not graph.has_node(bn.node_id):
        graph.add_node(bn)
        created_nodes += 1

    relation_index = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(source_id: str, target_id: str, edge_type: str, confidence: float, evidence_ref: str) -> None:
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
            wp_ref="WP-IMP-0048",
            attributes={},
        )
        graph.add_edge(edge)
        relation_index.add(key)
        created_edges += 1

    for edge in cast(list[dict[str, Any]], payload["edges"]):
        relation = str(edge["relation"])
        if relation == "VALIDATED_BY":
            edge_type = EdgeType.RELATED_TO.value
        elif relation == "SUPPORTED_BY":
            edge_type = EdgeType.SUPPORTED_BY.value
        else:
            edge_type = EdgeType.EXPLAINS.value
        add_edge(str(edge["source"]), str(edge["target"]), edge_type, float(edge["confidence"]), str(DC3_PHASE4_DIR / "BATCH1_VALIDATION_REPORT.md"))

    add_edge(str(batch_node["node_id"]), campaign_id, EdgeType.DERIVED_FROM.value, 0.80, str(DC3_PHASE4_DIR / "ARB_RECOMMENDATION_BATCH1.md"))

    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _default_campaign_spec() -> dict[str, Any]:
    return {
        "title": "DC3 Phase 4 Adaptive Institutional Alpha Validation — Batch 1",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9501",
            "title": "DC3 Phase 4 Batch 1 Primary Research Question",
            "question": "Which Batch 1 alpha mechanisms survive the full institutional validation framework, and what adaptive research priorities emerge from the results?",
            "category": "MECHANISM_VALIDATION",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "evidence_refs": ["dc3_phase4_batch1_validation.json"],
            "confidence": {"prior": 0.62, "statistical": 0.0, "economic": 0.62, "data": 0.58, "model": 0.58, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc3-phase4-validation-execution", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase4 batch1 primary question", "motivation": "Execute first adaptive institutional alpha validation."}},
            "reproducibility_hash": "dc3-phase4-validation-execution-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9501",
            "title": "DC3 Phase 4 Batch 1 Validation Execution",
            "experiment_type": "MECHANISM_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260802-0501",
            "dataset_refs": ["dc3_institutional_alpha_registry.json", "dc3_phase4_batch1_validation.json"],
            "methodology": "adaptive_institutional_alpha_validation_framework_v1",
            "lifecycle_state": "DESIGNED",
            "confidence": {"prior": 0.62, "statistical": 0.0, "economic": 0.62, "data": 0.58, "model": 0.58, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
            "lineage": {"origin": {"created_by": "dc3-phase4-validation-execution", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase4 batch1 validation experiment", "motivation": "Apply 17-method validation to BATCH-001 mechanisms and produce adaptive research queue."}},
            "reproducibility_hash": "dc3-phase4-validation-execution-v1",
        },
        "research_questions_secondary": [
            {
                "ikros_id": "IKROS-RQ-20260802-9502",
                "title": "DC3 Phase 4 Confidence Update Question",
                "question": "How do Batch 1 validation outcomes update mechanism confidence and family research priority?",
                "category": "CONFIDENCE_UPDATE",
                "priority": "HIGH",
                "lifecycle_state": "OPEN",
                "instrument": "XAU/USD",
                "confidence": {"prior": 0.60, "statistical": 0.0, "economic": 0.60, "data": 0.55, "model": 0.55, "validation": 0.0, "replication": 0.0, "operational": 0.0, "last_updated": "2026-08-02T00:00:00Z"},
                "lineage": {"origin": {"created_by": "dc3-phase4-validation-execution", "created_at": "2026-08-02T00:00:00Z", "creation_context": "DC3 phase4 secondary question", "motivation": ""}},
                "reproducibility_hash": "dc3-phase4-validation-execution-v1",
            },
        ],
    }


def run_dc3_phase4_validation_campaign(repo_root: Path) -> dict[str, Any]:
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _default_campaign_spec()
    rq = ResearchQuestion.from_dict(_with_reproducibility_hash(spec["research_question_primary"]))
    exp = Experiment.from_dict(_with_reproducibility_hash(spec["experiment"]))
    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {"entity_type": "ResearchQuestion", "entity": rq.to_dict()},
        TaskKind.EXPERIMENT_REGISTRATION.value: {"entity_type": "Experiment", "entity": exp.to_dict()},
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective="Execute adaptive institutional alpha validation for Batch 1 (FAM-003 safe_haven_migration, FAM-006 decision_cascade); produce validation results, adaptive research queue, family re-ranking, and ARB recommendation.",
        campaign_type="HYPOTHESIS_VALIDATION",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_campaign_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.STATISTICAL_EVALUATION.value, TaskKind.FINAL_REPORT.value])

    analysis = prepare_dc3_phase4_validation_artifacts(repo_root=repo_root)

    rq_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    exp_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not rq_registry.exists(rq.ikros_id):
        rq_registry.register(rq)
    if not exp_registry.exists(exp.ikros_id):
        exp_registry.register(exp)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    report_paths = emit_dc3_phase4_validation_reports(analysis, campaign_result=report.to_dict(), repo_root=repo_root)
    graph_metrics = _upsert_graph_payload(repo_root, analysis, campaign.campaign_id)

    for rq_secondary in spec["research_questions_secondary"]:
        rq_id = str(rq_secondary["ikros_id"])
        if not rq_registry.exists(rq_id):
            try:
                rq2 = ResearchQuestion.from_dict(_with_reproducibility_hash(rq_secondary))
                rq_registry.register(rq2)
            except Exception:
                pass

    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    dashboard = cast(dict[str, Any], analysis["validation_dashboard"])
    results = cast(list[dict[str, Any]], analysis["validation_results"])
    outcomes = {str(r["alpha_id"]): str(r["outcome"]["outcome"]) for r in results}

    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "batch": "BATCH-001",
        "mechanisms_validated": int(dashboard["mechanisms_validated"]),
        "mechanisms_pending": int(dashboard["mechanisms_pending"]),
        "outcomes": outcomes,
        "avg_confidence_delta": float(dashboard["avg_confidence_delta"]),
        "mechanisms_requiring_research": int(dashboard["mechanisms_requiring_research"]),
        "mechanisms_candidate_or_above": int(dashboard["mechanisms_candidate_or_above"]),
        "promotion_this_phase": False,
        "batch_2_requires_arb_approval": True,
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "report_paths": report_paths,
        "arb_reject": arb["mechanisms_to_reject"],
        "arb_research": arb["mechanisms_requiring_more_evidence"],
        "arb_candidates": arb["mechanisms_eligible_for_promotion_review"],
    }
    write_json((repo_root / DC3_PHASE4_DIR / "dc3_phase4_metrics.json"), metrics)
    return metrics


if __name__ == "__main__":
    import sys
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_dc3_phase4_validation_campaign(repo_root)
    for alpha_id, outcome in cast(dict[str, str], result["outcomes"]).items():
        print(f"  {alpha_id} -> {outcome}")
    print(f"DC3 Phase 4 Batch 1 complete — validated: {result['mechanisms_validated']}, pending: {result['mechanisms_pending']}")
