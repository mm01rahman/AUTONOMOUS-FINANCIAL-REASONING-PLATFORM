"""IKROS orchestrator models — deterministic campaigns, tasks, reports, and audit."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CampaignType(StrEnum):
    LITERATURE_REVIEW = "LITERATURE_REVIEW"
    HYPOTHESIS_VALIDATION = "HYPOTHESIS_VALIDATION"
    FEATURE_EVALUATION = "FEATURE_EVALUATION"
    DATASET_VALIDATION = "DATASET_VALIDATION"
    BACKTEST_CAMPAIGN = "BACKTEST_CAMPAIGN"
    REPLICATION_CAMPAIGN = "REPLICATION_CAMPAIGN"
    STRESS_CAMPAIGN = "STRESS_CAMPAIGN"
    BENCHMARK_CAMPAIGN = "BENCHMARK_CAMPAIGN"
    RESEARCH_AUDIT = "RESEARCH_AUDIT"


class CampaignLifecycleState(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class TaskKind(StrEnum):
    RESEARCH_QUESTION = "RESEARCH_QUESTION"
    LITERATURE_INTAKE = "LITERATURE_INTAKE"
    KNOWLEDGE_REGISTRATION = "KNOWLEDGE_REGISTRATION"
    HYPOTHESIS_REGISTRATION = "HYPOTHESIS_REGISTRATION"
    EXPERIMENT_REGISTRATION = "EXPERIMENT_REGISTRATION"
    DATASET_SELECTION = "DATASET_SELECTION"
    FEATURE_SELECTION = "FEATURE_SELECTION"
    VALIDATION_REQUEST = "VALIDATION_REQUEST"
    STATISTICAL_EVALUATION = "STATISTICAL_EVALUATION"
    CONFIDENCE_UPDATE = "CONFIDENCE_UPDATE"
    BACKTEST_EXECUTION = "BACKTEST_EXECUTION"
    REPLICATION_EVALUATION = "REPLICATION_EVALUATION"
    STRESS_EVALUATION = "STRESS_EVALUATION"
    BENCHMARK_EVALUATION = "BENCHMARK_EVALUATION"
    FINAL_REPORT = "FINAL_REPORT"


class FailurePolicy(StrEnum):
    FAIL_FAST = "FAIL_FAST"
    CONTINUE = "CONTINUE"
    RETRY_ONCE = "RETRY_ONCE"


class CampaignAuditEvent(StrEnum):
    CAMPAIGN_REGISTERED = "CAMPAIGN_REGISTERED"
    CAMPAIGN_STARTED = "CAMPAIGN_STARTED"
    CAMPAIGN_COMPLETED = "CAMPAIGN_COMPLETED"
    CAMPAIGN_FAILED = "CAMPAIGN_FAILED"
    CAMPAIGN_RESUMED = "CAMPAIGN_RESUMED"
    TASK_READY = "TASK_READY"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_BLOCKED = "TASK_BLOCKED"
    REPORT_GENERATED = "REPORT_GENERATED"


@dataclass
class ResearchTaskResult:
    output_refs: list[str] = field(default_factory=list)
    selected_ids: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    memory_record_id: str | None = None
    graph_node_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_refs": list(self.output_refs),
            "selected_ids": list(self.selected_ids),
            "metrics": self.metrics,
            "payload": self.payload,
            "memory_record_id": self.memory_record_id,
            "graph_node_id": self.graph_node_id,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchTaskResult:
        return cls(
            output_refs=_sorted_unique(data.get("output_refs", [])),
            selected_ids=_sorted_unique(data.get("selected_ids", [])),
            metrics=dict(data.get("metrics", {})),
            payload=dict(data.get("payload", {})),
            memory_record_id=(
                str(data["memory_record_id"]) if data.get("memory_record_id") else None
            ),
            graph_node_id=str(data["graph_node_id"]) if data.get("graph_node_id") else None,
            error=str(data["error"]) if data.get("error") else None,
        )


@dataclass
class ResearchTask:
    task_id: str
    kind: str
    title: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    planned_order: int = 0
    attempts: int = 0
    max_attempts: int = 1
    allow_failure: bool = False
    result: ResearchTaskResult | None = None
    started_at: str | None = None
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "kind": str(self.kind),
            "title": self.title,
            "payload": self.payload,
            "depends_on": list(self.depends_on),
            "status": str(self.status),
            "planned_order": self.planned_order,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "allow_failure": self.allow_failure,
            "result": None if self.result is None else self.result.to_dict(),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchTask:
        result_data = data.get("result")
        return cls(
            task_id=str(data["task_id"]),
            kind=str(data["kind"]),
            title=str(data["title"]),
            payload=dict(data.get("payload", {})),
            depends_on=_sorted_unique(data.get("depends_on", [])),
            status=str(data.get("status", TaskStatus.PENDING.value)),
            planned_order=int(data.get("planned_order", 0)),
            attempts=int(data.get("attempts", 0)),
            max_attempts=int(data.get("max_attempts", 1)),
            allow_failure=bool(data.get("allow_failure", False)),
            result=(
                ResearchTaskResult.from_dict(result_data)
                if isinstance(result_data, dict)
                else None
            ),
            started_at=str(data["started_at"]) if data.get("started_at") else None,
            finished_at=str(data["finished_at"]) if data.get("finished_at") else None,
        )


@dataclass
class ResearchPipeline:
    pipeline_id: str
    name: str
    stages: list[str]
    task_ids: list[str]
    deterministic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "stages": list(self.stages),
            "task_ids": list(self.task_ids),
            "deterministic": self.deterministic,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchPipeline:
        return cls(
            pipeline_id=str(data["pipeline_id"]),
            name=str(data["name"]),
            stages=[str(stage) for stage in data.get("stages", [])],
            task_ids=[str(task_id) for task_id in data.get("task_ids", [])],
            deterministic=bool(data.get("deterministic", True)),
        )


@dataclass
class ResearchCampaign:
    campaign_id: str
    campaign_type: str
    title: str
    objective: str
    pipeline: ResearchPipeline
    tasks: list[ResearchTask]
    lifecycle_state: str = CampaignLifecycleState.DRAFT.value
    failure_policy: str = FailurePolicy.FAIL_FAST.value
    research_question_id: str | None = None
    specification_refs: list[str] = field(default_factory=lambda: ["SPEC-060"])
    capability_refs: list[str] = field(default_factory=lambda: ["IKROS-ORCHESTRATOR"])
    work_package_refs: list[str] = field(default_factory=lambda: ["WP-IMP-0048"])
    evidence_refs: list[str] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    completion_report_id: str | None = None

    def progress(self) -> dict[str, int | float]:
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        failed = sum(1 for task in self.tasks if task.status == TaskStatus.FAILED)
        skipped = sum(1 for task in self.tasks if task.status == TaskStatus.SKIPPED)
        blocked = sum(1 for task in self.tasks if task.status == TaskStatus.BLOCKED)
        percent = 0.0 if total == 0 else round((completed / total) * 100.0, 2)
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "blocked": blocked,
            "percent_complete": percent,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_type": str(self.campaign_type),
            "title": self.title,
            "objective": self.objective,
            "pipeline": self.pipeline.to_dict(),
            "tasks": [task.to_dict() for task in self.tasks],
            "lifecycle_state": str(self.lifecycle_state),
            "failure_policy": str(self.failure_policy),
            "research_question_id": self.research_question_id,
            "specification_refs": list(self.specification_refs),
            "capability_refs": list(self.capability_refs),
            "work_package_refs": list(self.work_package_refs),
            "evidence_refs": list(self.evidence_refs),
            "audit_ids": list(self.audit_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "completion_report_id": self.completion_report_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResearchCampaign:
        return cls(
            campaign_id=str(data["campaign_id"]),
            campaign_type=str(data["campaign_type"]),
            title=str(data["title"]),
            objective=str(data.get("objective", "")),
            pipeline=ResearchPipeline.from_dict(dict(data["pipeline"])),
            tasks=[
                ResearchTask.from_dict(item)
                for item in data.get("tasks", [])
                if isinstance(item, dict)
            ],
            lifecycle_state=str(
                data.get("lifecycle_state", CampaignLifecycleState.DRAFT.value)
            ),
            failure_policy=str(data.get("failure_policy", FailurePolicy.FAIL_FAST.value)),
            research_question_id=(
                str(data["research_question_id"])
                if data.get("research_question_id")
                else None
            ),
            specification_refs=_sorted_unique(data.get("specification_refs", ["SPEC-060"])),
            capability_refs=_sorted_unique(data.get("capability_refs", ["IKROS-ORCHESTRATOR"])),
            work_package_refs=_sorted_unique(data.get("work_package_refs", ["WP-IMP-0048"])),
            evidence_refs=_sorted_unique(data.get("evidence_refs", [])),
            audit_ids=_sorted_unique(data.get("audit_ids", [])),
            created_at=str(data.get("created_at", _now_iso())),
            updated_at=str(data.get("updated_at", _now_iso())),
            started_at=str(data["started_at"]) if data.get("started_at") else None,
            finished_at=str(data["finished_at"]) if data.get("finished_at") else None,
            completion_report_id=(
                str(data["completion_report_id"])
                if data.get("completion_report_id")
                else None
            ),
        )


@dataclass
class CampaignCompletionReport:
    report_id: str
    campaign_id: str
    campaign_type: str
    lifecycle_state: str
    started_at: str | None
    finished_at: str
    progress: dict[str, int | float]
    completed_task_ids: list[str]
    failed_task_ids: list[str]
    skipped_task_ids: list[str]
    blocked_task_ids: list[str]
    output_refs: list[str]
    memory_record_ids: list[str]
    audit_ids: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "campaign_id": self.campaign_id,
            "campaign_type": self.campaign_type,
            "lifecycle_state": self.lifecycle_state,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": dict(self.progress),
            "completed_task_ids": list(self.completed_task_ids),
            "failed_task_ids": list(self.failed_task_ids),
            "skipped_task_ids": list(self.skipped_task_ids),
            "blocked_task_ids": list(self.blocked_task_ids),
            "output_refs": list(self.output_refs),
            "memory_record_ids": list(self.memory_record_ids),
            "audit_ids": list(self.audit_ids),
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CampaignCompletionReport:
        return cls(
            report_id=str(data["report_id"]),
            campaign_id=str(data["campaign_id"]),
            campaign_type=str(data["campaign_type"]),
            lifecycle_state=str(data["lifecycle_state"]),
            started_at=str(data["started_at"]) if data.get("started_at") else None,
            finished_at=str(data["finished_at"]),
            progress=dict(data.get("progress", {})),
            completed_task_ids=_sorted_unique(data.get("completed_task_ids", [])),
            failed_task_ids=_sorted_unique(data.get("failed_task_ids", [])),
            skipped_task_ids=_sorted_unique(data.get("skipped_task_ids", [])),
            blocked_task_ids=_sorted_unique(data.get("blocked_task_ids", [])),
            output_refs=_sorted_unique(data.get("output_refs", [])),
            memory_record_ids=_sorted_unique(data.get("memory_record_ids", [])),
            audit_ids=_sorted_unique(data.get("audit_ids", [])),
            summary=str(data.get("summary", "")),
        )


@dataclass
class CampaignAuditEntry:
    audit_id: str
    campaign_id: str
    event_type: str
    timestamp: str
    actor: str
    detail: str
    task_id: str | None = None
    previous_state: str | None = None
    new_state: str | None = None
    output_refs: list[str] = field(default_factory=list)
    previous_hash: str = ""
    entry_hash: str = ""

    def fingerprint(self) -> str:
        return json.dumps(
            {
                "audit_id": self.audit_id,
                "campaign_id": self.campaign_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp,
                "actor": self.actor,
                "detail": self.detail,
                "task_id": self.task_id,
                "previous_state": self.previous_state,
                "new_state": self.new_state,
                "output_refs": sorted(self.output_refs),
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "campaign_id": self.campaign_id,
            "event_type": str(self.event_type),
            "timestamp": self.timestamp,
            "actor": self.actor,
            "detail": self.detail,
            "task_id": self.task_id,
            "previous_state": None if self.previous_state is None else str(self.previous_state),
            "new_state": None if self.new_state is None else str(self.new_state),
            "output_refs": [str(value) for value in self.output_refs],
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CampaignAuditEntry:
        return cls(
            audit_id=str(data["audit_id"]),
            campaign_id=str(data["campaign_id"]),
            event_type=str(data["event_type"]),
            timestamp=str(data["timestamp"]),
            actor=str(data["actor"]),
            detail=str(data.get("detail", "")),
            task_id=str(data["task_id"]) if data.get("task_id") else None,
            previous_state=str(data["previous_state"]) if data.get("previous_state") else None,
            new_state=str(data["new_state"]) if data.get("new_state") else None,
            output_refs=_sorted_unique(data.get("output_refs", [])),
            previous_hash=str(data.get("previous_hash", "")),
            entry_hash=str(data.get("entry_hash", "")),
        )

    @classmethod
    def build(
        cls,
        *,
        audit_id: str,
        campaign_id: str,
        event_type: str,
        actor: str,
        detail: str,
        task_id: str | None,
        previous_state: str | None,
        new_state: str | None,
        output_refs: list[str],
        previous_hash: str,
    ) -> CampaignAuditEntry:
        entry = cls(
            audit_id=audit_id,
            campaign_id=campaign_id,
            event_type=event_type,
            timestamp=_now_iso(),
            actor=actor,
            detail=detail,
            task_id=task_id,
            previous_state=previous_state,
            new_state=new_state,
            output_refs=_sorted_unique(output_refs),
            previous_hash=previous_hash,
        )
        entry.entry_hash = hashlib.sha256(entry.fingerprint().encode("utf-8")).hexdigest()
        return entry


def _sorted_unique(values: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    return sorted({str(value) for value in values if value})
