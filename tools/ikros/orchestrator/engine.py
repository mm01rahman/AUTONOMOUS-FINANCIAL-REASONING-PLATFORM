"""IKROS Institutional Research Orchestrator."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from tools.ikros.confidence import (
    ConfidenceEvidence,
    ResearchConfidenceEngine,
)
from tools.ikros.graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    KnowledgeGraphRepository,
    NodeType,
    YAMLGraphRepository,
)
from tools.ikros.ingestion import ResearchIngestionEngine, SourceDocument
from tools.ikros.memory import MemoryRecord, MemoryTier, ResearchMemoryManager, YAMLMemoryRepository
from tools.ikros.models import (
    Alpha,
    AlphaCandidate,
    Experiment,
    Feature,
    FeatureFamily,
    Hypothesis,
    IKROSEntity,
    ResearchQuestion,
)
from tools.ikros.orchestrator.models import (
    CampaignAuditEntry,
    CampaignAuditEvent,
    CampaignCompletionReport,
    CampaignLifecycleState,
    CampaignType,
    FailurePolicy,
    ResearchCampaign,
    ResearchPipeline,
    ResearchTask,
    ResearchTaskResult,
    TaskKind,
    TaskStatus,
)
from tools.ikros.orchestrator.persistence import (
    CampaignAuditLog,
    OrchestratorRepository,
    YAMLOrchestratorRepository,
)
from tools.ikros.orchestrator.validation import (
    assert_valid_audit_entry,
    assert_valid_campaign,
)
from tools.ikros.query import QueryEngine
from tools.ikros.query.audit import QueryAuditLog
from tools.ikros.registries.alpha import AlphaRegistry
from tools.ikros.registries.base import BaseRegistry
from tools.ikros.registries.experiment import ExperimentRegistry
from tools.ikros.registries.feature import FeatureRegistry
from tools.ikros.registries.hypothesis import HypothesisRegistry
from tools.ikros.registries.research import ResearchRegistry


class OrchestratorError(RuntimeError):
    """Raised when orchestrator execution fails."""


class ResearchOrchestrator:
    """Deterministic orchestration layer for governed institutional research campaigns."""

    def __init__(
        self,
        registries: dict[str, BaseRegistry[IKROSEntity]] | None = None,
        graph: KnowledgeGraph | None = None,
        graph_repository: KnowledgeGraphRepository | None = None,
        memory: ResearchMemoryManager | None = None,
        repository: OrchestratorRepository | None = None,
        audit_log: CampaignAuditLog | None = None,
        base_dir: Path | None = None,
    ) -> None:
        resolved_base = base_dir or Path("data") / "ikros"
        self._base_dir = resolved_base
        self._registries = registries or self._default_registries(resolved_base / "registries")
        self._graph_repository = graph_repository or YAMLGraphRepository(resolved_base / "graph")
        self._graph = graph or self._graph_repository.load()
        memory_repository = YAMLMemoryRepository(resolved_base / "memory")
        self._memory = memory or ResearchMemoryManager(memory_repository, self._graph)
        self._repository = repository or YAMLOrchestratorRepository(resolved_base / "orchestrator")
        self._audit_log = audit_log or CampaignAuditLog(resolved_base / "orchestrator" / "audit")
        self._ingestion_engine = ResearchIngestionEngine(
            registries=self._registries,
            graph=self._graph,
            graph_repository=self._graph_repository,
            memory=self._memory,
            base_dir=resolved_base,
        )
        self._confidence_engine = ResearchConfidenceEngine(
            registries=self._registries,
            graph=self._graph,
            graph_repository=self._graph_repository,
            memory=self._memory,
            base_dir=resolved_base,
        )

    def build_campaign(
        self,
        *,
        title: str,
        objective: str,
        campaign_type: str,
        task_payloads: dict[str, dict[str, Any]] | None = None,
        failure_policy: str = FailurePolicy.FAIL_FAST.value,
        research_question_id: str | None = None,
    ) -> ResearchCampaign:
        task_payloads = task_payloads or {}
        first_task_id = self._repository.next_task_id()
        tasks = []
        for planned_order, (kind, stage_title, depends_on) in enumerate(
            _default_pipeline_template(campaign_type),
            start=1,
        ):
            task_id = _derived_id(first_task_id, planned_order - 1)
            tasks.append(
                ResearchTask(
                    task_id=task_id,
                    kind=kind,
                    title=stage_title,
                    payload=deepcopy(task_payloads.get(kind, {})),
                    depends_on=list(depends_on),
                    planned_order=planned_order,
                    max_attempts=2 if failure_policy == FailurePolicy.RETRY_ONCE.value else 1,
                )
            )
        task_ids = [task.task_id for task in tasks]
        dependency_map = {
            task.kind: task_id
            for task, task_id in zip(tasks, task_ids, strict=False)
        }
        for task in tasks:
            task.depends_on = [dependency_map.get(dep, dep) for dep in task.depends_on]
        pipeline = ResearchPipeline(
            pipeline_id=self._repository.next_pipeline_id(),
            name=f"{campaign_type} pipeline",
            stages=[task.kind for task in tasks],
            task_ids=[task.task_id for task in tasks],
        )
        campaign = ResearchCampaign(
            campaign_id=self._repository.next_campaign_id(),
            campaign_type=campaign_type,
            title=title,
            objective=objective,
            pipeline=pipeline,
            tasks=tasks,
            lifecycle_state=CampaignLifecycleState.READY.value,
            failure_policy=failure_policy,
            research_question_id=research_question_id,
        )
        return campaign

    def register_campaign(self, campaign: ResearchCampaign) -> str:
        assert_valid_campaign(campaign)
        campaign.updated_at = _now_iso()
        self._repository.save_campaign(campaign)
        self._ensure_campaign_graph_node(campaign)
        self._write_audit(
            campaign=campaign,
            event_type=CampaignAuditEvent.CAMPAIGN_REGISTERED,
            detail="Campaign registered",
        )
        self._graph_repository.save(self._graph)
        self._repository.save_campaign(campaign)
        return campaign.campaign_id

    def get_campaign(self, campaign_id: str) -> ResearchCampaign:
        return self._repository.get_campaign(campaign_id)

    def list_campaigns(self) -> list[ResearchCampaign]:
        return self._repository.list_campaigns()

    def run_campaign(self, campaign_id: str) -> CampaignCompletionReport:
        campaign = self.get_campaign(campaign_id)
        if campaign.lifecycle_state == CampaignLifecycleState.DRAFT.value:
            raise OrchestratorError("campaign must be READY before execution")
        if campaign.lifecycle_state in {
            CampaignLifecycleState.COMPLETED.value,
            CampaignLifecycleState.CANCELLED.value,
        }:
            if campaign.completion_report_id is None:
                raise OrchestratorError("completed campaign is missing its completion report")
            reports = {report.report_id: report for report in self._repository.list_reports()}
            return reports[campaign.completion_report_id]
        if campaign.started_at is None:
            campaign.started_at = _now_iso()
        previous_state = campaign.lifecycle_state
        campaign.lifecycle_state = CampaignLifecycleState.RUNNING.value
        self._write_audit(
            campaign=campaign,
            event_type=CampaignAuditEvent.CAMPAIGN_STARTED,
            detail="Campaign execution started",
            previous_state=previous_state,
            new_state=campaign.lifecycle_state,
        )
        while True:
            self._mark_blocked_tasks(campaign)
            ready = self._ready_tasks(campaign)
            if not ready:
                break
            for task in ready:
                self._execute_task(campaign, task)
                if (
                    task.status == TaskStatus.FAILED.value
                    and campaign.failure_policy == FailurePolicy.FAIL_FAST.value
                ):
                    break
            if (
                any(task.status == TaskStatus.FAILED.value for task in campaign.tasks)
                and campaign.failure_policy == FailurePolicy.FAIL_FAST.value
            ):
                break
        report = self._finalize_campaign(campaign)
        return report

    def resume_campaign(self, campaign_id: str) -> CampaignCompletionReport:
        campaign = self.get_campaign(campaign_id)
        if campaign.lifecycle_state not in {
            CampaignLifecycleState.FAILED.value,
            CampaignLifecycleState.BLOCKED.value,
        }:
            raise OrchestratorError("only FAILED or BLOCKED campaigns can be resumed")
        for task in campaign.tasks:
            if task.status == TaskStatus.FAILED.value and task.attempts < task.max_attempts:
                task.status = TaskStatus.PENDING.value
                task.result = None
                task.finished_at = None
            if task.status == TaskStatus.BLOCKED.value:
                task.status = TaskStatus.PENDING.value
        previous_state = campaign.lifecycle_state
        campaign.lifecycle_state = CampaignLifecycleState.READY.value
        self._write_audit(
            campaign=campaign,
            event_type=CampaignAuditEvent.CAMPAIGN_RESUMED,
            detail="Campaign resumed after failure handling",
            previous_state=previous_state,
            new_state=campaign.lifecycle_state,
        )
        self._repository.save_campaign(campaign)
        return self.run_campaign(campaign_id)

    def update_task_payload(
        self,
        campaign_id: str,
        task_id: str,
        payload: dict[str, Any],
    ) -> ResearchCampaign:
        campaign = self.get_campaign(campaign_id)
        task = self._task_by_id(campaign, task_id)
        task.payload = deepcopy(payload)
        campaign.updated_at = _now_iso()
        self._repository.save_campaign(campaign)
        return campaign

    def build_query_engine(self) -> QueryEngine:
        return QueryEngine(
            registries=self._registries,
            graph=self._graph,
            memory=self._memory,
            audit_log=QueryAuditLog(self._base_dir / "orchestrator" / "query-audit"),
        )

    def _execute_task(self, campaign: ResearchCampaign, task: ResearchTask) -> None:
        task.status = TaskStatus.RUNNING.value
        task.attempts += 1
        task.started_at = _now_iso()
        self._write_audit(
            campaign=campaign,
            event_type=CampaignAuditEvent.TASK_STARTED,
            detail=f"Task {task.kind} started",
            task_id=task.task_id,
            previous_state=TaskStatus.READY.value,
            new_state=task.status,
        )
        try:
            result = self._dispatch_task(campaign, task)
            task.result = result
            task.status = TaskStatus.COMPLETED.value
            task.finished_at = _now_iso()
            self._ensure_task_graph_node(campaign, task)
            self._store_task_memory(campaign, task)
            self._write_audit(
                campaign=campaign,
                event_type=CampaignAuditEvent.TASK_COMPLETED,
                detail=f"Task {task.kind} completed",
                task_id=task.task_id,
                previous_state=TaskStatus.RUNNING.value,
                new_state=task.status,
                output_refs=result.output_refs + result.selected_ids,
            )
        except Exception as exc:
            task.result = ResearchTaskResult(error=str(exc))
            task.status = TaskStatus.FAILED.value
            task.finished_at = _now_iso()
            self._write_audit(
                campaign=campaign,
                event_type=CampaignAuditEvent.TASK_FAILED,
                detail=f"Task {task.kind} failed: {exc}",
                task_id=task.task_id,
                previous_state=TaskStatus.RUNNING.value,
                new_state=task.status,
            )
            if not task.allow_failure and campaign.failure_policy == FailurePolicy.RETRY_ONCE.value:
                if task.attempts < task.max_attempts:
                    task.status = TaskStatus.PENDING.value
        finally:
            campaign.updated_at = _now_iso()
            self._repository.save_campaign(campaign)
            self._graph_repository.save(self._graph)

    def _dispatch_task(
        self,
        campaign: ResearchCampaign,
        task: ResearchTask,
    ) -> ResearchTaskResult:
        if task.kind == TaskKind.RESEARCH_QUESTION.value:
            return self._handle_research_question(campaign, task)
        if task.kind in {
            TaskKind.LITERATURE_INTAKE.value,
            TaskKind.KNOWLEDGE_REGISTRATION.value,
            TaskKind.VALIDATION_REQUEST.value,
        }:
            return self._handle_ingestion(task)
        if task.kind in {
            TaskKind.HYPOTHESIS_REGISTRATION.value,
            TaskKind.EXPERIMENT_REGISTRATION.value,
        }:
            return self._handle_entity_registration(task)
        if task.kind == TaskKind.DATASET_SELECTION.value:
            return self._handle_selection(task, candidate_key="candidate_dataset_ids")
        if task.kind == TaskKind.FEATURE_SELECTION.value:
            return self._handle_selection(task, candidate_key="candidate_feature_ids")
        if task.kind == TaskKind.STATISTICAL_EVALUATION.value:
            return self._handle_statistical_evaluation(task)
        if task.kind == TaskKind.CONFIDENCE_UPDATE.value:
            return self._handle_confidence_update(task)
        if task.kind == TaskKind.BACKTEST_EXECUTION.value:
            return self._handle_backtest(task)
        if task.kind == TaskKind.REPLICATION_EVALUATION.value:
            return self._handle_replication(campaign, task)
        if task.kind == TaskKind.STRESS_EVALUATION.value:
            return self._handle_stress(task)
        if task.kind == TaskKind.BENCHMARK_EVALUATION.value:
            return self._handle_benchmark(task)
        if task.kind == TaskKind.FINAL_REPORT.value:
            return self._handle_final_report(campaign)
        raise OrchestratorError(f"unsupported task kind '{task.kind}'")

    def _handle_research_question(
        self,
        campaign: ResearchCampaign,
        task: ResearchTask,
    ) -> ResearchTaskResult:
        existing_id = task.payload.get("research_question_id") or campaign.research_question_id
        if existing_id:
            entity = self._registries["ResearchQuestion"].get(str(existing_id))
            campaign.research_question_id = entity.ikros_id
            return ResearchTaskResult(output_refs=[entity.ikros_id], payload=entity.to_dict())
        entity_result = self._handle_entity_registration(task)
        if entity_result.output_refs:
            campaign.research_question_id = entity_result.output_refs[0]
        return entity_result

    def _handle_ingestion(self, task: ResearchTask) -> ResearchTaskResult:
        source_path = task.payload.get("source_path")
        source_document = task.payload.get("source_document")
        if source_path:
            result = self._ingestion_engine.ingest_path(Path(str(source_path)))
        elif isinstance(source_document, dict):
            result = self._ingestion_engine.ingest_document(SourceDocument(**source_document))
        else:
            raise OrchestratorError("ingestion task requires source_path or source_document")
        source_refs = [result.report.source_ref]
        if source_path:
            source_refs.append(Path(str(source_path)).stem)
        output_refs = _sorted_unique(source_refs + list(result.report.object_ids))
        return ResearchTaskResult(
            output_refs=output_refs,
            metrics={
                "ingestion_status": str(result.status),
                "memory_ids": list(result.report.memory_ids),
                "graph_node_ids": list(result.report.graph_node_ids),
            },
            payload=result.report.to_dict(),
        )

    def _handle_entity_registration(self, task: ResearchTask) -> ResearchTaskResult:
        entity_type = str(task.payload.get("entity_type", ""))
        entity_payload = task.payload.get("entity")
        if not entity_type or not isinstance(entity_payload, dict):
            raise OrchestratorError("entity registration requires entity_type and entity payload")
        entity = self._deserialize_entity(entity_type, entity_payload)
        if entity_type == "FeatureFamily":
            feature_registry = self._feature_registry()
            feature_registry.register_family(cast(FeatureFamily, entity))
        elif entity_type == "Alpha":
            alpha_registry = self._alpha_registry()
            alpha_registry.promote(cast(Alpha, entity).promoted_from, cast(Alpha, entity))
        else:
            self._registry_for_type(entity_type).register(entity)
        self._ensure_reference_node(entity.ikros_id)
        return ResearchTaskResult(output_refs=[entity.ikros_id], payload=entity.to_dict())

    def _handle_selection(self, task: ResearchTask, *, candidate_key: str) -> ResearchTaskResult:
        raw_candidates = task.payload.get(candidate_key, [])
        top_k = int(task.payload.get("top_k", 1))
        if not isinstance(raw_candidates, list) or not raw_candidates:
            raise OrchestratorError(f"{candidate_key} must be a non-empty list")
        ranked_pairs = sorted(
            (
                (str(candidate_id), self._confidence_for_identifier(str(candidate_id)))
                for candidate_id in raw_candidates
            ),
            key=lambda item: (-item[1], item[0]),
        )
        ranked = [
            {"identifier": candidate_id, "confidence": confidence}
            for candidate_id, confidence in ranked_pairs
        ]
        selected: list[str] = [str(item["identifier"]) for item in ranked[:top_k]]
        return ResearchTaskResult(
            selected_ids=selected,
            metrics={"ranked_candidates": ranked},
            payload={"candidate_key": candidate_key, "selected_ids": selected},
        )

    def _handle_statistical_evaluation(self, task: ResearchTask) -> ResearchTaskResult:
        payload = task.payload
        p_value = float(payload.get("p_value", 1.0))
        effect_size = abs(float(payload.get("effect_size", 0.0)))
        consistency_score = float(payload.get("consistency_score", 0.0))
        sharpe_degradation = float(payload.get("sharpe_degradation", 0.0))
        overfitting_index = float(payload.get("overfitting_index", 1.0))
        data_grade = str(payload.get("data_quality_grade", "UNVERIFIED")).upper()
        statistical_confidence = _clamp(1.0 - p_value)
        validation_confidence = _clamp(consistency_score * (1.0 - (sharpe_degradation / 2.0)))
        experimental_confidence = _clamp(max(0.0, 1.0 - ((overfitting_index - 1.0) / 2.0)))
        data_confidence = _DATA_GRADES.get(data_grade, 0.20)
        result_payload = {
            "p_value": p_value,
            "effect_size": effect_size,
            "statistical_confidence": statistical_confidence,
            "validation_confidence": validation_confidence,
            "experimental_confidence": experimental_confidence,
            "data_confidence": data_confidence,
        }
        return ResearchTaskResult(
            metrics=result_payload,
            payload=result_payload,
        )

    def _handle_confidence_update(self, task: ResearchTask) -> ResearchTaskResult:
        target_id = str(task.payload.get("target_id", ""))
        reason = str(task.payload.get("reason", "Campaign confidence update"))
        raw_evidence = task.payload.get("evidence", [])
        if not target_id or not isinstance(raw_evidence, list):
            raise OrchestratorError("confidence update requires target_id and evidence list")
        evidence = [
            ConfidenceEvidence.from_dict(item)
            for item in raw_evidence
            if isinstance(item, dict)
        ]
        assessment = self._confidence_engine.assess(target_id, evidence, reason=reason)
        return ResearchTaskResult(
            output_refs=[assessment.assessment_id],
            metrics={
                "previous_overall": assessment.previous_overall(),
                "new_overall": assessment.new_overall(),
                "audit_id": assessment.audit_id,
                "memory_record_id": assessment.memory_record_id,
            },
            payload=assessment.to_dict(),
        )

    def _handle_backtest(self, task: ResearchTask) -> ResearchTaskResult:
        result = _BacktestHarnessAdapter().run(
            prices=_float_series(task.payload.get("prices", [])),
            strategy_name=str(task.payload.get("strategy", "BUY_AND_HOLD")),
            config=dict(task.payload.get("config", {})),
            strategy_params=dict(task.payload.get("strategy_params", {})),
        )
        return ResearchTaskResult(
            output_refs=[result["replay_checksum"]],
            metrics=result,
            payload=result,
        )

    def _handle_replication(
        self,
        campaign: ResearchCampaign,
        task: ResearchTask,
    ) -> ResearchTaskResult:
        baseline_task_id = str(task.payload.get("baseline_task_id", ""))
        expected_checksum = str(task.payload.get("expected_checksum", ""))
        backtest_result = self._handle_backtest(task)
        baseline_checksum = expected_checksum
        if baseline_task_id:
            baseline_task = self._task_by_id(campaign, baseline_task_id)
            if baseline_task.result is None:
                raise OrchestratorError("baseline task result is not available")
            baseline_checksum = str(
                baseline_task.result.metrics.get(
                    "replay_checksum",
                    baseline_task.result.output_refs[0] if baseline_task.result.output_refs else "",
                )
            )
        if not baseline_checksum:
            raise OrchestratorError(
                "replication evaluation requires baseline_task_id or "
                "expected_checksum"
            )
        replicated = backtest_result.metrics["replay_checksum"] == baseline_checksum
        backtest_result.metrics["replicated"] = replicated
        backtest_result.metrics["baseline_checksum"] = baseline_checksum
        return backtest_result

    def _handle_stress(self, task: ResearchTask) -> ResearchTaskResult:
        scenarios = task.payload.get("scenarios", [])
        if not isinstance(scenarios, list) or not scenarios:
            raise OrchestratorError("stress evaluation requires scenarios")
        adapter = _BacktestHarnessAdapter()
        scenario_results = []
        for index, scenario in enumerate(scenarios, start=1):
            result = adapter.run(
                prices=_float_series(scenario),
                strategy_name=str(task.payload.get("strategy", "BUY_AND_HOLD")),
                config=dict(task.payload.get("config", {})),
                strategy_params=dict(task.payload.get("strategy_params", {})),
            )
            result["scenario_index"] = index
            scenario_results.append(result)
        worst_return = min(result["total_return"] for result in scenario_results)
        worst_drawdown = min(result["max_drawdown"] for result in scenario_results)
        return ResearchTaskResult(
            output_refs=[result["replay_checksum"] for result in scenario_results],
            metrics={
                "scenario_results": scenario_results,
                "worst_total_return": worst_return,
                "worst_max_drawdown": worst_drawdown,
            },
            payload={"scenario_results": scenario_results},
        )

    def _handle_benchmark(self, task: ResearchTask) -> ResearchTaskResult:
        prices = _float_series(task.payload.get("prices", []))
        strategies = task.payload.get("benchmarks", ["BUY_AND_HOLD", "MOVING_AVERAGE_CROSS"])
        if not isinstance(strategies, list) or not strategies:
            raise OrchestratorError("benchmark evaluation requires benchmarks list")
        adapter = _BacktestHarnessAdapter()
        benchmark_results = [
            adapter.run(
                prices=prices,
                strategy_name=str(strategy_name),
                config=dict(task.payload.get("config", {})),
                strategy_params=dict(task.payload.get("strategy_params", {})),
            )
            for strategy_name in strategies
        ]
        ranked = sorted(
            benchmark_results,
            key=lambda item: (-float(item["final_equity"]), str(item["strategy"])),
        )
        return ResearchTaskResult(
            output_refs=[result["replay_checksum"] for result in ranked],
            metrics={"benchmarks": ranked, "best_strategy": ranked[0]["strategy"]},
            payload={"benchmarks": ranked},
        )

    def _handle_final_report(self, campaign: ResearchCampaign) -> ResearchTaskResult:
        progress = campaign.progress()
        completed = [
            task.task_id
            for task in campaign.tasks
            if task.status == TaskStatus.COMPLETED.value
        ]
        failed = [
            task.task_id for task in campaign.tasks if task.status == TaskStatus.FAILED.value
        ]
        blocked = [
            task.task_id
            for task in campaign.tasks
            if task.status == TaskStatus.BLOCKED.value
        ]
        outputs = _sorted_unique(
            ref
            for task in campaign.tasks
            if task.result is not None
            for ref in (task.result.output_refs + task.result.selected_ids)
        )
        return ResearchTaskResult(
            output_refs=outputs,
            metrics={
                "progress": progress,
                "completed_task_ids": completed,
                "failed_task_ids": failed,
                "blocked_task_ids": blocked,
            },
            payload={"campaign_id": campaign.campaign_id, "outputs": outputs},
        )

    def _ready_tasks(self, campaign: ResearchCampaign) -> list[ResearchTask]:
        completed = {
            task.task_id
            for task in campaign.tasks
            if task.status == TaskStatus.COMPLETED.value
        }
        ready: list[ResearchTask] = []
        for task in campaign.tasks:
            if task.status not in {TaskStatus.PENDING.value, TaskStatus.READY.value}:
                continue
            if any(
                self._task_by_id(campaign, dep).status == TaskStatus.FAILED.value
                for dep in task.depends_on
            ):
                continue
            if all(dep in completed for dep in task.depends_on):
                previous = task.status
                task.status = TaskStatus.READY.value
                if previous != TaskStatus.READY.value:
                    self._write_audit(
                        campaign=campaign,
                        event_type=CampaignAuditEvent.TASK_READY,
                        detail=f"Task {task.kind} is ready",
                        task_id=task.task_id,
                        previous_state=previous,
                        new_state=task.status,
                    )
                ready.append(task)
        return sorted(ready, key=lambda item: (item.planned_order, item.task_id))

    def _mark_blocked_tasks(self, campaign: ResearchCampaign) -> None:
        for task in campaign.tasks:
            if task.status != TaskStatus.PENDING.value:
                continue
            dependency_states = {
                self._task_by_id(campaign, dep).status for dep in task.depends_on
            }
            if (
                TaskStatus.FAILED.value in dependency_states
                or TaskStatus.BLOCKED.value in dependency_states
            ):
                task.status = TaskStatus.BLOCKED.value
                self._write_audit(
                    campaign=campaign,
                    event_type=CampaignAuditEvent.TASK_BLOCKED,
                    detail=f"Task {task.kind} blocked by dependency failure",
                    task_id=task.task_id,
                    previous_state=TaskStatus.PENDING.value,
                    new_state=task.status,
                )

    def _finalize_campaign(self, campaign: ResearchCampaign) -> CampaignCompletionReport:
        failed = [
            task.task_id for task in campaign.tasks if task.status == TaskStatus.FAILED.value
        ]
        blocked = [
            task.task_id
            for task in campaign.tasks
            if task.status == TaskStatus.BLOCKED.value
        ]
        skipped = [
            task.task_id
            for task in campaign.tasks
            if task.status == TaskStatus.SKIPPED.value
        ]
        completed = [
            task.task_id
            for task in campaign.tasks
            if task.status == TaskStatus.COMPLETED.value
        ]
        if failed:
            new_state = CampaignLifecycleState.FAILED.value
            event = CampaignAuditEvent.CAMPAIGN_FAILED
            detail = f"Campaign failed with tasks {failed}"
        elif blocked:
            new_state = CampaignLifecycleState.BLOCKED.value
            event = CampaignAuditEvent.CAMPAIGN_FAILED
            detail = f"Campaign blocked with tasks {blocked}"
        else:
            new_state = CampaignLifecycleState.COMPLETED.value
            event = CampaignAuditEvent.CAMPAIGN_COMPLETED
            detail = "Campaign completed successfully"
        previous_state = campaign.lifecycle_state
        campaign.lifecycle_state = new_state
        campaign.finished_at = _now_iso()
        report = CampaignCompletionReport(
            report_id=self._repository.next_report_id(),
            campaign_id=campaign.campaign_id,
            campaign_type=campaign.campaign_type,
            lifecycle_state=campaign.lifecycle_state,
            started_at=campaign.started_at,
            finished_at=campaign.finished_at,
            progress=campaign.progress(),
            completed_task_ids=completed,
            failed_task_ids=failed,
            skipped_task_ids=skipped,
            blocked_task_ids=blocked,
            output_refs=_sorted_unique(
                ref
                for task in campaign.tasks
                if task.result is not None
                for ref in (task.result.output_refs + task.result.selected_ids)
            ),
            memory_record_ids=_sorted_unique(
                task.result.memory_record_id
                for task in campaign.tasks
                if task.result is not None and task.result.memory_record_id
            ),
            audit_ids=list(campaign.audit_ids),
            summary=self._report_summary(campaign, failed, blocked),
        )
        self._repository.save_report(report)
        campaign.completion_report_id = report.report_id
        completion_memory_id = self._store_completion_report_memory(campaign, report)
        report.memory_record_ids = _sorted_unique(
            list(report.memory_record_ids) + [completion_memory_id]
        )
        self._repository.save_report(report)
        self._ensure_report_graph_node(campaign, report)
        self._write_audit(
            campaign=campaign,
            event_type=event,
            detail=detail,
            previous_state=previous_state,
            new_state=campaign.lifecycle_state,
            output_refs=report.output_refs,
        )
        self._write_audit(
            campaign=campaign,
            event_type=CampaignAuditEvent.REPORT_GENERATED,
            detail="Completion report generated",
            output_refs=[report.report_id],
        )
        campaign.updated_at = _now_iso()
        self._repository.save_campaign(campaign)
        self._graph_repository.save(self._graph)
        return report

    def _store_task_memory(self, campaign: ResearchCampaign, task: ResearchTask) -> None:
        if task.result is None:
            return
        memory_id = self._memory.next_id(MemoryTier.EPISODIC)
        record = MemoryRecord(
            memory_id=memory_id,
            tier=MemoryTier.EPISODIC,
            entity_type="ResearchTaskResult",
            title=f"{campaign.title} :: {task.title}",
            summary=f"{task.kind} {task.status}",
            source_ids=[campaign.campaign_id] + task.result.output_refs + task.result.selected_ids,
            evidence_refs=list(campaign.evidence_refs),
            spec_refs=list(campaign.specification_refs),
            capability_refs=list(campaign.capability_refs),
            work_package_refs=list(campaign.work_package_refs),
            graph_node_ids=[
                identifier
                for identifier in [campaign.campaign_id, task.task_id]
                if self._graph.has_node(identifier)
            ],
            dependency_ids=list(task.depends_on),
            tags=["research-orchestrator", task.kind.lower()],
            payload={
                "campaign_id": campaign.campaign_id,
                "task": task.to_dict(),
            },
            confidence=1.0 if task.status == TaskStatus.COMPLETED.value else 0.0,
        )
        self._memory.store(record)
        task.result.memory_record_id = memory_id

    def _store_completion_report_memory(
        self,
        campaign: ResearchCampaign,
        report: CampaignCompletionReport,
    ) -> str:
        memory_id = self._memory.next_id(MemoryTier.INSTITUTIONAL)
        record = MemoryRecord(
            memory_id=memory_id,
            tier=MemoryTier.INSTITUTIONAL,
            entity_type="CampaignCompletionReport",
            title=f"Completion report for {campaign.title}",
            summary=report.summary,
            source_ids=[campaign.campaign_id] + list(report.output_refs),
            evidence_refs=list(campaign.evidence_refs),
            spec_refs=list(campaign.specification_refs),
            capability_refs=list(campaign.capability_refs),
            work_package_refs=list(campaign.work_package_refs),
            graph_node_ids=[
                identifier
                for identifier in [campaign.campaign_id, report.report_id]
                if self._graph.has_node(identifier)
            ],
            tags=["research-orchestrator", "completion-report"],
            payload=report.to_dict(),
            confidence=(
                1.0
                if campaign.lifecycle_state == CampaignLifecycleState.COMPLETED.value
                else 0.5
            ),
        )
        self._memory.store(record)
        return memory_id

    def _ensure_campaign_graph_node(self, campaign: ResearchCampaign) -> None:
        if self._graph.has_node(campaign.campaign_id):
            return
        self._graph.add_node(
            GraphNode(
                node_id=campaign.campaign_id,
                node_type=NodeType.KNOWLEDGE_OBJECT,
                ikros_id=campaign.campaign_id,
                label=campaign.title,
                attributes={
                    "entity_type": "ResearchCampaign",
                    "campaign_type": campaign.campaign_type,
                    "objective": campaign.objective,
                    "pipeline_id": campaign.pipeline.pipeline_id,
                },
                confidence=0.0,
                spec_refs=list(campaign.specification_refs),
                wp_refs=list(campaign.work_package_refs),
                created_at=campaign.created_at,
            )
        )

    def _ensure_task_graph_node(self, campaign: ResearchCampaign, task: ResearchTask) -> None:
        if self._graph.has_node(task.task_id):
            self._graph.update_node(
                task.task_id,
                {
                    "attributes": {
                        "entity_type": "ResearchTask",
                        "campaign_id": campaign.campaign_id,
                        "kind": task.kind,
                        "status": task.status,
                    },
                    "confidence": 1.0 if task.status == TaskStatus.COMPLETED.value else 0.0,
                },
            )
        else:
            self._graph.add_node(
                GraphNode(
                    node_id=task.task_id,
                    node_type=NodeType.KNOWLEDGE_OBJECT,
                    ikros_id=task.task_id,
                    label=task.title,
                    attributes={
                        "entity_type": "ResearchTask",
                        "campaign_id": campaign.campaign_id,
                        "kind": task.kind,
                        "status": task.status,
                    },
                    confidence=1.0 if task.status == TaskStatus.COMPLETED.value else 0.0,
                    spec_refs=list(campaign.specification_refs),
                    wp_refs=list(campaign.work_package_refs),
                    created_at=task.started_at or campaign.created_at,
                )
            )
        self._ensure_edge(campaign.campaign_id, task.task_id, EdgeType.PRODUCED, campaign)
        for dependency in task.depends_on:
            self._ensure_edge(task.task_id, dependency, EdgeType.DEPENDS_ON, campaign)
        if task.result is not None:
            task.result.graph_node_id = task.task_id

    def _ensure_report_graph_node(
        self,
        campaign: ResearchCampaign,
        report: CampaignCompletionReport,
    ) -> None:
        if not self._graph.has_node(report.report_id):
            self._graph.add_node(
                GraphNode(
                    node_id=report.report_id,
                    node_type=NodeType.KNOWLEDGE_OBJECT,
                    ikros_id=report.report_id,
                    label=f"{campaign.title} completion report",
                    attributes={
                        "entity_type": "CampaignCompletionReport",
                        "campaign_id": campaign.campaign_id,
                        "lifecycle_state": report.lifecycle_state,
                    },
                    confidence=(
                        1.0
                        if report.lifecycle_state == CampaignLifecycleState.COMPLETED.value
                        else 0.5
                    ),
                    spec_refs=list(campaign.specification_refs),
                    wp_refs=list(campaign.work_package_refs),
                    created_at=report.finished_at,
                )
            )
        self._ensure_edge(campaign.campaign_id, report.report_id, EdgeType.PRODUCED, campaign)

    def _ensure_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        campaign: ResearchCampaign,
    ) -> None:
        if not self._graph.has_node(source_id) or not self._graph.has_node(target_id):
            return
        for edge in self._graph.get_out_edges(source_id):
            if edge.target_id == target_id and edge.edge_type == edge_type:
                return
        self._graph.add_edge(
            GraphEdge(
                edge_id=self._graph.next_edge_id(),
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                confidence=1.0,
                spec_ref=campaign.specification_refs[0] if campaign.specification_refs else "",
                wp_ref=campaign.work_package_refs[0] if campaign.work_package_refs else "",
            )
        )

    def _write_audit(
        self,
        *,
        campaign: ResearchCampaign,
        event_type: str,
        detail: str,
        task_id: str | None = None,
        previous_state: str | None = None,
        new_state: str | None = None,
        output_refs: list[str] | None = None,
    ) -> None:
        entry = CampaignAuditEntry.build(
            audit_id=self._audit_log.next_audit_id(),
            campaign_id=campaign.campaign_id,
            event_type=event_type,
            actor="ikros-orchestrator",
            detail=detail,
            task_id=task_id,
            previous_state=previous_state,
            new_state=new_state,
            output_refs=output_refs or [],
            previous_hash=self._audit_log.previous_hash(campaign.campaign_id),
        )
        assert_valid_audit_entry(entry)
        self._audit_log.write(entry)
        if entry.audit_id not in campaign.audit_ids:
            campaign.audit_ids.append(entry.audit_id)

    def _task_by_id(self, campaign: ResearchCampaign, task_id: str) -> ResearchTask:
        for task in campaign.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"Task '{task_id}' not found in campaign '{campaign.campaign_id}'")

    def _confidence_for_identifier(self, identifier: str) -> float:
        entity = self._find_entity(identifier)
        if entity is not None:
            return float(entity.confidence.overall())
        if self._graph.has_node(identifier):
            return float(self._graph.get_node(identifier).confidence)
        raise OrchestratorError(f"candidate '{identifier}' was not found in registries or graph")

    def _find_entity(self, identifier: str) -> IKROSEntity | None:
        for registry in self._registries.values():
            if registry.exists(identifier):
                return registry.get(identifier)
            if isinstance(registry, FeatureRegistry):
                try:
                    return registry.get_family(identifier)
                except KeyError:
                    pass
            if isinstance(registry, AlphaRegistry):
                try:
                    return registry.get_alpha(identifier)
                except KeyError:
                    pass
        return None

    def _ensure_reference_node(self, identifier: str) -> None:
        if self._graph.has_node(identifier):
            return
        entity = self._find_entity(identifier)
        if entity is None:
            raise OrchestratorError(f"referenced entity '{identifier}' was not found")
        self._graph.add_node(
            GraphNode(
                node_id=entity.ikros_id,
                node_type=_node_type_for_entity(entity.entity_type),
                ikros_id=entity.ikros_id,
                label=getattr(entity, "title", getattr(entity, "name", entity.ikros_id)),
                attributes=entity.to_dict(),
                confidence=float(entity.confidence.overall()),
                spec_refs=list(entity.spec_refs),
                wp_refs=list(entity.work_package_refs),
                created_at=entity.lineage.origin.created_at,
            )
        )

    def _deserialize_entity(self, entity_type: str, data: dict[str, Any]) -> IKROSEntity:
        normalized = deepcopy(data)
        if entity_type == "ResearchQuestion":
            return ResearchQuestion.from_dict(normalized)
        if entity_type == "Hypothesis":
            return Hypothesis.from_dict(normalized)
        if entity_type == "Experiment":
            return Experiment.from_dict(normalized)
        if entity_type == "Feature":
            return Feature.from_dict(normalized)
        if entity_type == "FeatureFamily":
            return FeatureFamily.from_dict(normalized)
        if entity_type == "AlphaCandidate":
            return AlphaCandidate.from_dict(normalized)
        if entity_type == "Alpha":
            return Alpha.from_dict(normalized)
        raise OrchestratorError(f"unsupported entity_type '{entity_type}'")

    def _registry_for_type(self, entity_type: str) -> BaseRegistry[IKROSEntity]:
        if entity_type == "ResearchQuestion":
            return self._registries["ResearchQuestion"]
        if entity_type == "Hypothesis":
            return self._registries["Hypothesis"]
        if entity_type == "Experiment":
            return self._registries["Experiment"]
        if entity_type in {"Feature", "FeatureFamily"}:
            return self._registries["Feature"]
        if entity_type in {"AlphaCandidate", "Alpha"}:
            return self._registries["AlphaCandidate"]
        raise OrchestratorError(f"no registry configured for '{entity_type}'")

    def _feature_registry(self) -> FeatureRegistry:
        registry = self._registries["Feature"]
        if not isinstance(registry, FeatureRegistry):
            raise OrchestratorError("Feature registry is not configured correctly")
        return registry

    def _alpha_registry(self) -> AlphaRegistry:
        registry = self._registries["AlphaCandidate"]
        if not isinstance(registry, AlphaRegistry):
            raise OrchestratorError("Alpha registry is not configured correctly")
        return registry

    def _default_registries(
        self,
        base_dir: Path,
    ) -> dict[str, BaseRegistry[IKROSEntity]]:
        return {
            "ResearchQuestion": cast(BaseRegistry[IKROSEntity], ResearchRegistry(base_dir)),
            "Hypothesis": cast(BaseRegistry[IKROSEntity], HypothesisRegistry(base_dir)),
            "Experiment": cast(BaseRegistry[IKROSEntity], ExperimentRegistry(base_dir)),
            "Feature": cast(BaseRegistry[IKROSEntity], FeatureRegistry(base_dir)),
            "AlphaCandidate": cast(BaseRegistry[IKROSEntity], AlphaRegistry(base_dir)),
        }

    def _report_summary(
        self,
        campaign: ResearchCampaign,
        failed: list[str],
        blocked: list[str],
    ) -> str:
        if failed:
            return f"{campaign.title} failed after {len(failed)} task failures."
        if blocked:
            return f"{campaign.title} blocked because dependencies could not be satisfied."
        completed = campaign.progress()["completed"]
        return f"{campaign.title} completed with {completed} completed tasks."


class _BacktestHarnessAdapter:
    """Optional adapter for the deterministic AFRP backtest framework."""

    def run(
        self,
        *,
        prices: list[float],
        strategy_name: str,
        config: dict[str, Any],
        strategy_params: dict[str, Any],
    ) -> dict[str, Any]:
        if not prices:
            raise OrchestratorError("backtest requires a non-empty price series")
        import sys

        repo_root = Path(__file__).resolve().parents[3]
        for extra_path in (repo_root / "07-research", repo_root / "06-runtime"):
            path_value = str(extra_path)
            if path_value not in sys.path:
                sys.path.insert(0, path_value)
        from afrp_research.backtest import (
            BacktestConfig,
            BacktestEngine,
            BuyAndHold,
            MovingAverageCross,
        )
        from afrp_runtime.contracts.cio import ObservationKind, RawObservation
        from afrp_runtime.contracts.envelope import make_envelope

        observations = [
            RawObservation(
                envelope=make_envelope(
                    producer_subsystem_id="L1-ING",
                    cognitive_cycle_id="research-campaign",
                    mission_profile_id="MP-04",
                    payload_repr=f"{index}:{price}",
                    generated_at_ns=index,
                ),
                instrument="XAUUSD",
                kind=ObservationKind.TRADE,
                price=price,
                bid=0.0,
                ask=0.0,
                size=1.0,
                venue="REPLAY",
                ingest_sequence=index + 1,
                event_at_ns=index,
            )
            for index, price in enumerate(prices)
        ]
        runner = BacktestEngine(BacktestConfig(**config))
        normalized_name = strategy_name.upper()
        strategy: object
        if normalized_name == "BUY_AND_HOLD":
            strategy = BuyAndHold(**strategy_params)
        elif normalized_name == "MOVING_AVERAGE_CROSS":
            strategy = MovingAverageCross(**strategy_params)
        else:
            raise OrchestratorError(f"unsupported benchmark strategy '{strategy_name}'")
        result = runner.run(observations, strategy)
        return {
            "strategy": normalized_name,
            "final_equity": result.final_equity,
            "initial_equity": result.initial_equity,
            "total_return": result.total_return,
            "max_drawdown": result.max_drawdown,
            "annualized_sharpe": result.annualized_sharpe,
            "trade_count": len(result.trades),
            "replay_checksum": result.replay_checksum,
            "seed": result.seed,
        }


def _default_pipeline_template(
    campaign_type: str,
) -> list[tuple[str, str, list[str]]]:
    if campaign_type == CampaignType.BACKTEST_CAMPAIGN.value:
        return [
            (TaskKind.RESEARCH_QUESTION.value, "Research Question", []),
            (
                TaskKind.BACKTEST_EXECUTION.value,
                "Backtest Execution",
                [TaskKind.RESEARCH_QUESTION.value],
            ),
            (
                TaskKind.STATISTICAL_EVALUATION.value,
                "Statistical Evaluation",
                [TaskKind.BACKTEST_EXECUTION.value],
            ),
            (
                TaskKind.FINAL_REPORT.value,
                "Final Report",
                [TaskKind.STATISTICAL_EVALUATION.value],
            ),
        ]
    if campaign_type == CampaignType.REPLICATION_CAMPAIGN.value:
        return [
            (TaskKind.RESEARCH_QUESTION.value, "Research Question", []),
            (
                TaskKind.REPLICATION_EVALUATION.value,
                "Replication Evaluation",
                [TaskKind.RESEARCH_QUESTION.value],
            ),
            (
                TaskKind.CONFIDENCE_UPDATE.value,
                "Confidence Update",
                [TaskKind.REPLICATION_EVALUATION.value],
            ),
            (TaskKind.FINAL_REPORT.value, "Final Report", [TaskKind.CONFIDENCE_UPDATE.value]),
        ]
    if campaign_type in {
        CampaignType.STRESS_CAMPAIGN.value,
        CampaignType.BENCHMARK_CAMPAIGN.value,
    }:
        evaluation_kind = (
            TaskKind.STRESS_EVALUATION.value
            if campaign_type == CampaignType.STRESS_CAMPAIGN.value
            else TaskKind.BENCHMARK_EVALUATION.value
        )
        return [
            (TaskKind.RESEARCH_QUESTION.value, "Research Question", []),
            (evaluation_kind, "Evaluation", [TaskKind.RESEARCH_QUESTION.value]),
            (TaskKind.STATISTICAL_EVALUATION.value, "Statistical Evaluation", [evaluation_kind]),
            (TaskKind.FINAL_REPORT.value, "Final Report", [TaskKind.STATISTICAL_EVALUATION.value]),
        ]
    return [
        (TaskKind.RESEARCH_QUESTION.value, "Research Question", []),
        (
            TaskKind.LITERATURE_INTAKE.value,
            "Literature Intake",
            [TaskKind.RESEARCH_QUESTION.value],
        ),
        (
            TaskKind.KNOWLEDGE_REGISTRATION.value,
            "Knowledge Registration",
            [TaskKind.LITERATURE_INTAKE.value],
        ),
        (
            TaskKind.HYPOTHESIS_REGISTRATION.value,
            "Hypothesis Registration",
            [TaskKind.KNOWLEDGE_REGISTRATION.value],
        ),
        (
            TaskKind.EXPERIMENT_REGISTRATION.value,
            "Experiment Registration",
            [TaskKind.HYPOTHESIS_REGISTRATION.value],
        ),
        (
            TaskKind.DATASET_SELECTION.value,
            "Dataset Selection",
            [TaskKind.EXPERIMENT_REGISTRATION.value],
        ),
        (TaskKind.FEATURE_SELECTION.value, "Feature Selection", [TaskKind.DATASET_SELECTION.value]),
        (
            TaskKind.VALIDATION_REQUEST.value,
            "Validation Request",
            [TaskKind.FEATURE_SELECTION.value],
        ),
        (
            TaskKind.STATISTICAL_EVALUATION.value,
            "Statistical Evaluation",
            [TaskKind.VALIDATION_REQUEST.value],
        ),
        (
            TaskKind.CONFIDENCE_UPDATE.value,
            "Confidence Update",
            [TaskKind.STATISTICAL_EVALUATION.value],
        ),
        (TaskKind.FINAL_REPORT.value, "Final Report", [TaskKind.CONFIDENCE_UPDATE.value]),
    ]


def _node_type_for_entity(entity_type: str) -> str:
    mapping = {
        "ResearchQuestion": NodeType.RESEARCH_QUESTION,
        "Hypothesis": NodeType.HYPOTHESIS,
        "Experiment": NodeType.EXPERIMENT,
        "Feature": NodeType.FEATURE,
        "FeatureFamily": NodeType.FEATURE_FAMILY,
        "AlphaCandidate": NodeType.ALPHA_CANDIDATE,
        "Alpha": NodeType.ALPHA,
    }
    return mapping.get(entity_type, NodeType.KNOWLEDGE_OBJECT)


def _float_series(values: object) -> list[float]:
    if not isinstance(values, list):
        raise OrchestratorError("price series must be a list")
    return [float(value) for value in values]


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({str(value) for value in values if value})


def _clamp(value: float) -> float:
    return float(max(0.0, min(value, 0.95)))


def _derived_id(seed: str, offset: int) -> str:
    prefix, sequence = seed.rsplit("-", 1)
    return f"{prefix}-{int(sequence) + offset:04d}"


_DATA_GRADES: dict[str, float] = {
    "A": 0.90,
    "B": 0.70,
    "C": 0.50,
    "UNVERIFIED": 0.20,
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
