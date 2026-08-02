"""IKROS orchestrator persistence — deterministic YAML repositories for campaigns and audit."""

from __future__ import annotations

import abc
from datetime import UTC, datetime
from pathlib import Path

from tools.ikros.orchestrator.models import (
    CampaignAuditEntry,
    CampaignCompletionReport,
    ResearchCampaign,
)
from tools.ikros.persistence import read_entity, write_entity


class OrchestratorRepository(abc.ABC):
    """Abstract persistence port for orchestrator campaigns and reports."""

    @abc.abstractmethod
    def save_campaign(self, campaign: ResearchCampaign) -> None:
        """Persist a research campaign."""

    @abc.abstractmethod
    def get_campaign(self, campaign_id: str) -> ResearchCampaign:
        """Fetch a persisted research campaign."""

    @abc.abstractmethod
    def list_campaigns(self) -> list[ResearchCampaign]:
        """Return all campaigns in deterministic order."""

    @abc.abstractmethod
    def save_report(self, report: CampaignCompletionReport) -> None:
        """Persist a completion report."""

    @abc.abstractmethod
    def list_reports(self) -> list[CampaignCompletionReport]:
        """Return all completion reports."""

    @abc.abstractmethod
    def next_campaign_id(self) -> str:
        """Return the next deterministic campaign ID."""

    @abc.abstractmethod
    def next_pipeline_id(self) -> str:
        """Return the next deterministic pipeline ID."""

    @abc.abstractmethod
    def next_task_id(self) -> str:
        """Return the next deterministic task ID."""

    @abc.abstractmethod
    def next_report_id(self) -> str:
        """Return the next deterministic report ID."""


class YAMLOrchestratorRepository(OrchestratorRepository):
    """YAML-backed repository for orchestrator state."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._campaigns_dir = base_dir / "campaigns"
        self._reports_dir = base_dir / "reports"

    def save_campaign(self, campaign: ResearchCampaign) -> None:
        write_entity(self._campaigns_dir / f"{campaign.campaign_id}.yaml", campaign.to_dict())

    def get_campaign(self, campaign_id: str) -> ResearchCampaign:
        path = self._campaigns_dir / f"{campaign_id}.yaml"
        if not path.exists():
            raise KeyError(f"Campaign '{campaign_id}' not found")
        return ResearchCampaign.from_dict(read_entity(path))

    def list_campaigns(self) -> list[ResearchCampaign]:
        if not self._campaigns_dir.exists():
            return []
        return [
            ResearchCampaign.from_dict(read_entity(path))
            for path in sorted(self._campaigns_dir.glob("IKROS-RESEARCHCAMPAIGN-*.yaml"))
        ]

    def save_report(self, report: CampaignCompletionReport) -> None:
        write_entity(self._reports_dir / f"{report.report_id}.yaml", report.to_dict())

    def list_reports(self) -> list[CampaignCompletionReport]:
        if not self._reports_dir.exists():
            return []
        return [
            CampaignCompletionReport.from_dict(read_entity(path))
            for path in sorted(self._reports_dir.glob("IKROS-CAMPAIGNREPORT-*.yaml"))
        ]

    def next_campaign_id(self) -> str:
        return _next_id("IKROS-RESEARCHCAMPAIGN", len(self.list_campaigns()) + 1)

    def next_pipeline_id(self) -> str:
        total_pipelines = sum(1 for campaign in self.list_campaigns())
        return _next_id("IKROS-RESEARCHPIPELINE", total_pipelines + 1)

    def next_task_id(self) -> str:
        total_tasks = sum(len(campaign.tasks) for campaign in self.list_campaigns())
        return _next_id("IKROS-RESEARCHTASK", total_tasks + 1)

    def next_report_id(self) -> str:
        return _next_id("IKROS-CAMPAIGNREPORT", len(self.list_reports()) + 1)


class CampaignAuditLog:
    """YAML-backed append-only campaign audit log with hash chaining."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def next_audit_id(self) -> str:
        return _next_id("IKROS-CAMPAIGNAUDIT", len(self.list_entries()) + 1)

    def previous_hash(self, campaign_id: str) -> str:
        campaign_entries = [
            entry for entry in self.list_entries() if entry.campaign_id == campaign_id
        ]
        if not campaign_entries:
            return ""
        return campaign_entries[-1].entry_hash

    def write(self, entry: CampaignAuditEntry) -> None:
        write_entity(self._base_dir / f"{entry.audit_id}.yaml", entry.to_dict())

    def list_entries(self) -> list[CampaignAuditEntry]:
        if not self._base_dir.exists():
            return []
        return [
            CampaignAuditEntry.from_dict(read_entity(path))
            for path in sorted(self._base_dir.glob("IKROS-CAMPAIGNAUDIT-*.yaml"))
        ]


def _next_id(prefix: str, sequence: int) -> str:
    date_code = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_code}-{sequence:04d}"
