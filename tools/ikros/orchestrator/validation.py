"""IKROS orchestrator validation — campaign, pipeline, task, and audit checks."""

from __future__ import annotations

from collections import deque

from tools.ikros.orchestrator.models import (
    CampaignAuditEntry,
    CampaignLifecycleState,
    CampaignType,
    FailurePolicy,
    ResearchCampaign,
    ResearchPipeline,
    ResearchTask,
    TaskKind,
    TaskStatus,
)


class OrchestratorValidationError(ValueError):
    """Raised when orchestrator configuration or persisted state is invalid."""


def validate_task(task: ResearchTask) -> list[str]:
    errors: list[str] = []
    if not task.task_id:
        errors.append("task_id is required")
    if not task.title:
        errors.append("task title is required")
    if task.kind not in {item.value for item in TaskKind}:
        errors.append(f"unsupported task kind '{task.kind}'")
    if task.status not in {item.value for item in TaskStatus}:
        errors.append(f"unsupported task status '{task.status}'")
    if task.max_attempts <= 0:
        errors.append("max_attempts must be positive")
    if task.attempts < 0:
        errors.append("attempts must be non-negative")
    return errors


def validate_pipeline(pipeline: ResearchPipeline, tasks: list[ResearchTask]) -> list[str]:
    errors: list[str] = []
    if not pipeline.pipeline_id:
        errors.append("pipeline_id is required")
    if not pipeline.name:
        errors.append("pipeline name is required")
    if not pipeline.task_ids:
        errors.append("pipeline must contain at least one task")
    task_ids = {task.task_id for task in tasks}
    missing = sorted(task_id for task_id in pipeline.task_ids if task_id not in task_ids)
    if missing:
        errors.append(f"pipeline references unknown task ids: {missing}")
    return errors


def validate_campaign(campaign: ResearchCampaign) -> list[str]:
    errors: list[str] = []
    if not campaign.campaign_id:
        errors.append("campaign_id is required")
    if campaign.campaign_type not in {item.value for item in CampaignType}:
        errors.append(f"unsupported campaign_type '{campaign.campaign_type}'")
    if not campaign.title:
        errors.append("campaign title is required")
    if campaign.lifecycle_state not in {item.value for item in CampaignLifecycleState}:
        errors.append(f"unsupported lifecycle_state '{campaign.lifecycle_state}'")
    if campaign.failure_policy not in {item.value for item in FailurePolicy}:
        errors.append(f"unsupported failure_policy '{campaign.failure_policy}'")
    if not campaign.specification_refs:
        errors.append("campaign requires at least one specification reference")
    if not campaign.capability_refs:
        errors.append("campaign requires at least one capability reference")
    task_ids: set[str] = set()
    final_reports = 0
    for task in campaign.tasks:
        errors.extend(validate_task(task))
        if task.task_id in task_ids:
            errors.append(f"duplicate task_id '{task.task_id}'")
        task_ids.add(task.task_id)
        if task.kind == TaskKind.FINAL_REPORT.value:
            final_reports += 1
    for task in campaign.tasks:
        missing = [dep for dep in task.depends_on if dep not in task_ids]
        if missing:
            errors.append(f"task '{task.task_id}' depends on unknown tasks {missing}")
    if final_reports != 1:
        errors.append("campaign must contain exactly one FINAL_REPORT task")
    errors.extend(validate_pipeline(campaign.pipeline, campaign.tasks))
    errors.extend(_validate_acyclic_dependencies(campaign.tasks))
    return errors


def validate_audit_entry(entry: CampaignAuditEntry) -> list[str]:
    errors: list[str] = []
    if not entry.audit_id:
        errors.append("audit_id is required")
    if not entry.campaign_id:
        errors.append("campaign_id is required")
    if not entry.event_type:
        errors.append("event_type is required")
    if not entry.timestamp:
        errors.append("timestamp is required")
    if not entry.actor:
        errors.append("actor is required")
    if not entry.entry_hash:
        errors.append("entry_hash is required")
    return errors


def assert_valid_campaign(campaign: ResearchCampaign) -> None:
    errors = validate_campaign(campaign)
    if errors:
        raise OrchestratorValidationError("\n".join(errors))


def assert_valid_audit_entry(entry: CampaignAuditEntry) -> None:
    errors = validate_audit_entry(entry)
    if errors:
        raise OrchestratorValidationError("\n".join(errors))


def _validate_acyclic_dependencies(tasks: list[ResearchTask]) -> list[str]:
    indegree: dict[str, int] = {task.task_id: 0 for task in tasks}
    adjacency: dict[str, list[str]] = {task.task_id: [] for task in tasks}
    for task in tasks:
        for dep in task.depends_on:
            adjacency[dep].append(task.task_id)
            indegree[task.task_id] += 1
    queue: deque[str] = deque(
        sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    )
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for neighbor in sorted(adjacency[current]):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    if visited != len(tasks):
        return ["task dependency graph must be acyclic"]
    return []
