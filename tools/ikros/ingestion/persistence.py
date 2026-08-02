"""IKROS ingestion persistence — deterministic YAML-backed ingestion reports."""

from __future__ import annotations

import abc
from datetime import UTC, datetime
from pathlib import Path

from tools.ikros.ingestion.models import IngestionReport
from tools.ikros.persistence import read_entity, write_entity


class IngestionRepository(abc.ABC):
    @abc.abstractmethod
    def save_report(self, report: IngestionReport) -> None:
        """Persist a single ingestion report."""

    @abc.abstractmethod
    def load_reports(self) -> list[IngestionReport]:
        """Load all reports in deterministic order."""

    @abc.abstractmethod
    def next_ingestion_id(self) -> str:
        """Return the next deterministic ingestion-report ID."""

    @abc.abstractmethod
    def find_by_source(self, source_ref: str, source_hash: str) -> IngestionReport | None:
        """Return the report for an already-ingested exact source version, if any."""

    @abc.abstractmethod
    def known_fingerprints(self) -> set[str]:
        """Return all previously-ingested object fingerprints."""


class YAMLIngestionRepository(IngestionRepository):
    """Deterministic YAML repository for ingestion reports."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._reports_dir = base_dir / "reports"

    def save_report(self, report: IngestionReport) -> None:
        write_entity(self._reports_dir / f"{report.ingestion_id}.yaml", report.to_dict())

    def load_reports(self) -> list[IngestionReport]:
        if not self._reports_dir.exists():
            return []
        reports: list[IngestionReport] = []
        for path in sorted(self._reports_dir.glob("IKING-*.yaml")):
            reports.append(IngestionReport.from_dict(read_entity(path)))
        return reports

    def next_ingestion_id(self) -> str:
        sequence = len(self.load_reports()) + 1
        day = datetime.now(UTC).strftime("%Y%m%d")
        return f"IKING-{day}-{sequence:04d}"

    def find_by_source(self, source_ref: str, source_hash: str) -> IngestionReport | None:
        for report in self.load_reports():
            if report.source_ref == source_ref and report.source_hash == source_hash:
                return report
        return None

    def known_fingerprints(self) -> set[str]:
        fingerprints: set[str] = set()
        for report in self.load_reports():
            fingerprints.update(report.object_fingerprints)
        return fingerprints

