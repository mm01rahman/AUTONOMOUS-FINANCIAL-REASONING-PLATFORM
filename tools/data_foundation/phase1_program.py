"""Governed runner for Data Foundation V2 Phase 1."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import write_json, write_markdown
from tools.data_foundation import DATA_FOUNDATION_REPORT_DIR, build_data_foundation_v2_tier1
from tools.ikros.graph import EdgeType, GraphNode, NodeType, YAMLGraphRepository
from tools.ikros.graph.models import GraphEdge
from tools.ikros.identifiers import compute_reproducibility_hash
from tools.ikros.memory import MemoryRecord, MemoryTier, ResearchMemoryManager, YAMLMemoryRepository
from tools.ikros.models import Experiment, ResearchQuestion
from tools.ikros.orchestrator import FailurePolicy, ResearchCampaign, ResearchOrchestrator, TaskKind
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.research import ResearchRegistry


def _with_hash(entity: dict[str, Any]) -> dict[str, Any]:
    result = dict(entity)
    if "reproducibility_hash" not in result or result["reproducibility_hash"] == "df2-phase1-v1":
        result["reproducibility_hash"] = compute_reproducibility_hash(result)
    return result


def _select_pipeline(campaign: ResearchCampaign, task_kinds: list[str]) -> ResearchCampaign:
    allowed = set(task_kinds)
    selected = [task for task in campaign.tasks if task.kind in allowed]
    ordered = sorted(selected, key=lambda task: task_kinds.index(task.kind) if task.kind in task_kinds else 999)
    for idx, task in enumerate(ordered):
        task.depends_on = [ordered[idx - 1].task_id] if idx > 0 else []
    campaign.tasks = ordered
    campaign.pipeline.task_ids = [task.task_id for task in ordered]
    campaign.pipeline.stages = [task.kind for task in ordered]
    return campaign


def _campaign_spec() -> dict[str, Any]:
    return {
        "title": "Data Foundation V2 Phase 1 Institutional Market Data Infrastructure",
        "research_question_primary": {
            "ikros_id": "IKROS-RQ-20260802-9901",
            "title": "Data Foundation V2 Tier 1 Observation Question",
            "question": "How should AFRP implement deterministic historical market-data infrastructure for approved Tier 1 institutional datasets without Runtime changes, broker connectivity, or commercial feeds?",
            "category": "DATA_INFRASTRUCTURE",
            "priority": "HIGH",
            "lifecycle_state": "OPEN",
            "instrument": "XAU/USD",
            "confidence": {
                "prior": 0.75,
                "statistical": 0.0,
                "economic": 0.78,
                "data": 0.72,
                "model": 0.72,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "data-foundation-v2-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Data Foundation V2 Phase 1 primary question",
                    "motivation": "Implement permanent institutional-grade observation capability for approved free Tier 1 datasets.",
                }
            },
            "reproducibility_hash": "df2-phase1-v1",
        },
        "experiment": {
            "ikros_id": "IKROS-EXP-20260802-9901",
            "title": "Data Foundation V2 Tier 1 Infrastructure Execution",
            "experiment_type": "DATASET_VALIDATION",
            "hypothesis_under_test": "IKROS-HYP-20260802-0703",
            "dataset_refs": ["DS-001", "DS-003", "DS-007", "DS-008", "DS-009", "DS-010", "DS-011", "DS-012", "DS-014", "DS-017", "DS-018", "DS-019", "DS-PUB-021"],
            "methodology": "deterministic_historical_ingestion_validation_storage_and_registry_publication",
            "lifecycle_state": "DESIGNED",
            "confidence": {
                "prior": 0.75,
                "statistical": 0.0,
                "economic": 0.78,
                "data": 0.72,
                "model": 0.72,
                "validation": 0.0,
                "replication": 0.0,
                "operational": 0.0,
                "last_updated": "2026-08-02T00:00:00Z",
            },
            "lineage": {
                "origin": {
                    "created_by": "data-foundation-v2-phase1",
                    "created_at": "2026-08-02T00:00:00Z",
                    "creation_context": "Data Foundation V2 Phase 1 execution",
                    "motivation": "Create the provider library, dataset registry, quality dashboards, manifests, checksums, and IKROS updates for Tier 1 institutional market data.",
                }
            },
            "reproducibility_hash": "df2-phase1-v1",
        },
    }


def _upsert_graph(repo_root: Path, summary: dict[str, Any], campaign_id: str) -> dict[str, int]:
    graph_repo = YAMLGraphRepository((repo_root / "data" / "ikros" / "graph").resolve())
    graph = graph_repo.load()
    created_nodes = 0
    created_edges = 0
    conclusion_id = "IKROS-DF2-CONCLUSION-20260802-0001"

    conclusion = GraphNode(
        node_id=conclusion_id,
        node_type=NodeType.RESEARCH_CONCLUSION.value,
        ikros_id=conclusion_id,
        label="Data Foundation V2 Phase 1 conclusion",
        confidence=0.81,
        spec_refs=["SPEC-060"],
        wp_refs=["WP-IMP-0048"],
        attributes={
            "dataset_count": int(summary["dataset_count"]),
            "covered_variable_count": int(summary["covered_variable_count"]),
            "proxy_dependence_reduction": int(summary["proxy_dependence_reduction"]),
        },
    )
    if not graph.has_node(conclusion.node_id):
        graph.add_node(conclusion)
        created_nodes += 1

    existing = {(edge.source_id, edge.target_id, edge.edge_type) for edge in graph.edges()}

    def add_edge(source: str, target: str, edge_type: str, confidence: float, evidence_ref: str) -> None:
        nonlocal created_edges
        key = (source, target, edge_type)
        if key in existing or not graph.has_node(source) or not graph.has_node(target):
            return
        graph.add_edge(
            GraphEdge(
                edge_id=graph.next_edge_id(),
                source_id=source,
                target_id=target,
                edge_type=edge_type,
                confidence=confidence,
                evidence_ref=evidence_ref,
                spec_ref="SPEC-060",
                wp_ref="WP-IMP-0048",
                attributes={},
            )
        )
        existing.add(key)
        created_edges += 1

    for item in cast(list[dict[str, Any]], summary["dataset_registry"]):
        dataset_id = str(item["dataset_id"])
        version_id = str(item["version_id"])
        dataset_node_id = f"IKROS-DF2-DATASET-{dataset_id.replace('-', '')}"
        version_node_id = f"IKROS-DF2-DSETVER-{version_id.replace('-', '')}"
        dataset_node = GraphNode(
            node_id=dataset_node_id,
            node_type=NodeType.DATASET.value,
            ikros_id=dataset_node_id,
            label=f"{dataset_id} {item['name']}",
            confidence=float(item["confidence_score"]),
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={
                "provider": item["provider"],
                "domain": item["domain"],
                "covered_variables": item["covered_variables"],
            },
        )
        version_node = GraphNode(
            node_id=version_node_id,
            node_type=NodeType.DATASET_VERSION.value,
            ikros_id=version_node_id,
            label=f"{dataset_id} version {version_id}",
            confidence=float(item["quality_score"]),
            spec_refs=["SPEC-060"],
            wp_refs=["WP-IMP-0048"],
            attributes={"storage_path": item["storage_path"], "manifest_path": item["manifest_path"]},
        )
        if not graph.has_node(dataset_node.node_id):
            graph.add_node(dataset_node)
            created_nodes += 1
        if not graph.has_node(version_node.node_id):
            graph.add_node(version_node)
            created_nodes += 1
        evidence = str(DATA_FOUNDATION_REPORT_DIR / "DATASET_REGISTRY.md")
        add_edge(version_node_id, dataset_node_id, EdgeType.DERIVED_FROM.value, 0.92, evidence)
        add_edge(dataset_node_id, conclusion_id, EdgeType.SUPPORTED_BY.value, float(item["confidence_score"]), evidence)

    campaign_node_id = campaign_id
    if graph.has_node(conclusion_id) and graph.has_node(campaign_node_id):
        add_edge(conclusion_id, campaign_node_id, EdgeType.DERIVED_FROM.value, 0.80, str(DATA_FOUNDATION_REPORT_DIR / "ARB_RECOMMENDATION_DATA_FOUNDATION_V2_PHASE1.md"))
    graph_repo.save(graph)
    return {"created_nodes": created_nodes, "created_edges": created_edges}


def _store_memory(repo_root: Path, summary: dict[str, Any]) -> list[str]:
    memory = ResearchMemoryManager(
        repository=YAMLMemoryRepository((repo_root / "data" / "ikros" / "memory").resolve())
    )
    stored: list[str] = []

    def store_or_reuse(record: MemoryRecord) -> str:
        fingerprint = record.fingerprint()
        for existing in memory.list_all():
            if existing.fingerprint() == fingerprint:
                return existing.memory_id
        return memory.store(record)

    summary_record = MemoryRecord(
        memory_id=memory.next_id(MemoryTier.INSTITUTIONAL),
        tier=MemoryTier.INSTITUTIONAL,
        entity_type="DataFoundationSummary",
        title="Data Foundation V2 Phase 1 institutional summary",
        summary="Tier 1 historical market data infrastructure implemented with deterministic ingestion, storage, registries, and dashboards.",
        source_ids=[str(item) for item in cast(list[str], summary["supported_datasets"])],
        evidence_refs=[str(DATA_FOUNDATION_REPORT_DIR / "ARB_RECOMMENDATION_DATA_FOUNDATION_V2_PHASE1.md")],
        spec_refs=["SPEC-060"],
        capability_refs=["IKROS-ORCHESTRATOR", "IKROS-GRAPH", "IKROS-MEMORY"],
        work_package_refs=["WP-IMP-0048"],
        tags=["data-foundation", "tier1", "institutional-data"],
        payload={
            "dataset_count": summary["dataset_count"],
            "covered_variable_count": summary["covered_variable_count"],
            "proxy_dependence_reduction": summary["proxy_dependence_reduction"],
            "remaining_blocked_families": summary["remaining_blocked_families"],
        },
        confidence=0.81,
    )
    stored.append(store_or_reuse(summary_record))

    for item in cast(list[dict[str, Any]], summary["dataset_registry"])[:5]:
        record = MemoryRecord(
            memory_id=memory.next_id(MemoryTier.EPISODIC),
            tier=MemoryTier.EPISODIC,
            entity_type="DatasetQualitySnapshot",
            title=f"Dataset quality snapshot {item['dataset_id']}",
            summary=f"{item['dataset_id']} quality {item['quality_score']:.2f}, confidence {item['confidence_score']:.2f}.",
            source_ids=[str(item["dataset_id"])],
            evidence_refs=[str(DATA_FOUNDATION_REPORT_DIR / "QUALITY_DASHBOARD.md")],
            spec_refs=["SPEC-060"],
            capability_refs=["IKROS-MEMORY"],
            work_package_refs=["WP-IMP-0048"],
            tags=["dataset-quality", str(item["dataset_id"]).lower()],
            payload=item,
            confidence=float(item["confidence_score"]),
        )
        stored.append(store_or_reuse(record))
    return stored


def _emit_final_report(repo_root: Path, summary: dict[str, Any], metrics: dict[str, Any]) -> str:
    report_path = repo_root / DATA_FOUNDATION_REPORT_DIR / "FINAL_REPORT.md"
    supported = "\n".join(f"- {item}" for item in cast(list[str], summary["supported_datasets"]))
    ready = "\n".join(f"- {item}" for item in cast(list[str], summary["ready_mechanisms_after_tier1"]))
    blocked = "\n".join(f"- {item}" for item in cast(list[str], summary["remaining_blocked_families"]))
    commercial = "\n".join(f"- {item}" for item in cast(list[str], summary["remaining_commercial_only_gaps"]))
    write_markdown(
        report_path,
        f"""# Final Report — Data Foundation V2 Phase 1

## Implemented Tier 1 Work Packages
- DF2-WP-001
- DF2-WP-002
- DF2-WP-003
- DF2-WP-004

## Supported Datasets
{supported}

## Coverage Improvements
- Covered variables: {summary['covered_variable_count']}
- Proxy dependence reduction: {summary['proxy_dependence_reduction']}

## Observability Improvements
- Ready mechanisms after Tier 1:
{ready}

## Remaining Blocked Alpha Families
{blocked}

## Remaining Commercial-Only Gaps
{commercial}

## Repository Engineering Summary
- Dataset count: {summary['dataset_count']}
- Graph nodes created: {metrics['graph_nodes_created']}
- Graph edges created: {metrics['graph_edges_created']}
- No Runtime changes: {summary['no_runtime_changes']}
- No broker connectivity: {summary['no_broker_connectivity']}
- No alpha validation: {summary['no_alpha_validation']}
""",
    )
    return str(report_path.relative_to(repo_root))


def run_data_foundation_v2_phase1(repo_root: Path) -> dict[str, Any]:
    orchestrator = ResearchOrchestrator(base_dir=(repo_root / "data" / "ikros").resolve())
    spec = _campaign_spec()
    research_question = ResearchQuestion.from_dict(_with_hash(spec["research_question_primary"]))
    experiment = Experiment.from_dict(_with_hash(spec["experiment"]))
    task_payloads: dict[str, Any] = {
        TaskKind.RESEARCH_QUESTION.value: {"entity_type": "ResearchQuestion", "entity": research_question.to_dict()},
        TaskKind.EXPERIMENT_REGISTRATION.value: {"entity_type": "Experiment", "entity": experiment.to_dict()},
    }
    campaign = orchestrator.build_campaign(
        title=str(spec["title"]),
        objective="Implement deterministic Tier 1 institutional market data ingestion, storage, registries, manifests, checksums, dashboards, and IKROS integration for approved free/public datasets.",
        campaign_type="RESEARCH_AUDIT",
        task_payloads=task_payloads,
        failure_policy=FailurePolicy.CONTINUE.value,
    )
    _select_pipeline(campaign, [TaskKind.RESEARCH_QUESTION.value, TaskKind.EXPERIMENT_REGISTRATION.value, TaskKind.FINAL_REPORT.value])

    research_registry = cast(ResearchRegistry, orchestrator._registries["ResearchQuestion"])
    experiment_registry = cast(ExperimentRegistry, orchestrator._registries["Experiment"])
    if not research_registry.exists(research_question.ikros_id):
        research_registry.register(research_question)
    if not experiment_registry.exists(experiment.ikros_id):
        experiment_registry.register(experiment)

    orchestrator.register_campaign(campaign)
    report = orchestrator.run_campaign(campaign.campaign_id)
    summary = build_data_foundation_v2_tier1(repo_root)
    graph_metrics = _upsert_graph(repo_root, summary, campaign.campaign_id)
    memory_ids = _store_memory(repo_root, summary)

    metrics: dict[str, Any] = {
        "campaign_id": campaign.campaign_id,
        "dataset_count": int(summary["dataset_count"]),
        "covered_variable_count": int(summary["covered_variable_count"]),
        "proxy_dependence_reduction": int(summary["proxy_dependence_reduction"]),
        "ready_mechanisms_after_tier1": summary["ready_mechanisms_after_tier1"],
        "remaining_blocked_families": summary["remaining_blocked_families"],
        "remaining_commercial_only_gaps": summary["remaining_commercial_only_gaps"],
        "graph_nodes_created": graph_metrics["created_nodes"],
        "graph_edges_created": graph_metrics["created_edges"],
        "memory_records_created": memory_ids,
        "no_runtime_changes": True,
        "no_broker_connectivity": True,
        "no_alpha_validation": True,
        "report_paths": summary["report_paths"],
    }
    metrics["final_report"] = _emit_final_report(repo_root, summary, metrics)
    write_json(repo_root / DATA_FOUNDATION_REPORT_DIR / "data_foundation_v2_phase1_metrics.json", metrics)
    write_json(repo_root / DATA_FOUNDATION_REPORT_DIR / "data_foundation_v2_phase1_campaign_result.json", report.to_dict())
    return metrics


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = run_data_foundation_v2_phase1(root)
    print(
        "DF2 Phase 1 complete - "
        f"datasets: {result['dataset_count']}, "
        f"covered_variables: {result['covered_variable_count']}, "
        f"proxy_reduction: {result['proxy_dependence_reduction']}, "
        f"ready_mechanisms: {len(cast(list[str], result['ready_mechanisms_after_tier1']))}"
    )
