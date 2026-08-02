"""IKROS confidence persistence — deterministic YAML repositories for assessments and audit."""

from __future__ import annotations

import abc
from datetime import UTC, datetime
from pathlib import Path

from tools.ikros.confidence.models import (
    ConfidenceAssessment,
    ConfidenceAuditEntry,
    ConfidenceHistoryEntry,
)
from tools.ikros.persistence import read_entity, write_entity


class ConfidenceRepository(abc.ABC):
    """Abstract persistence port for confidence assessments and history."""

    @abc.abstractmethod
    def save_assessment(self, assessment: ConfidenceAssessment) -> None:
        """Persist a confidence assessment."""

    @abc.abstractmethod
    def save_history_entry(self, entry: ConfidenceHistoryEntry) -> None:
        """Persist a confidence history entry."""

    @abc.abstractmethod
    def list_assessments(self) -> list[ConfidenceAssessment]:
        """Return all confidence assessments."""

    @abc.abstractmethod
    def list_history(self) -> list[ConfidenceHistoryEntry]:
        """Return all history entries."""

    @abc.abstractmethod
    def latest_assessment(self, target_id: str) -> ConfidenceAssessment | None:
        """Return the latest assessment for the given target, if any."""

    @abc.abstractmethod
    def history_for_target(self, target_id: str) -> list[ConfidenceHistoryEntry]:
        """Return ordered confidence history for the target."""

    @abc.abstractmethod
    def next_assessment_id(self) -> str:
        """Return the next deterministic assessment ID."""

    @abc.abstractmethod
    def next_history_id(self) -> str:
        """Return the next deterministic history ID."""


class YAMLConfidenceRepository(ConfidenceRepository):
    """YAML-backed repository for assessments and history."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._assessments_dir = base_dir / "assessments"
        self._history_dir = base_dir / "history"

    def save_assessment(self, assessment: ConfidenceAssessment) -> None:
        write_entity(
            self._assessments_dir / f"{assessment.assessment_id}.yaml", assessment.to_dict()
        )

    def save_history_entry(self, entry: ConfidenceHistoryEntry) -> None:
        write_entity(self._history_dir / f"{entry.history_id}.yaml", entry.to_dict())

    def list_assessments(self) -> list[ConfidenceAssessment]:
        if not self._assessments_dir.exists():
            return []
        return [
            ConfidenceAssessment.from_dict(read_entity(path))
            for path in sorted(self._assessments_dir.glob("ICA-*.yaml"))
        ]

    def list_history(self) -> list[ConfidenceHistoryEntry]:
        if not self._history_dir.exists():
            return []
        return [
            ConfidenceHistoryEntry.from_dict(read_entity(path))
            for path in sorted(self._history_dir.glob("ICH-*.yaml"))
        ]

    def latest_assessment(self, target_id: str) -> ConfidenceAssessment | None:
        matches = [item for item in self.list_assessments() if item.target_id == target_id]
        if not matches:
            return None
        return sorted(matches, key=lambda item: (item.assessed_at, item.assessment_id))[-1]

    def history_for_target(self, target_id: str) -> list[ConfidenceHistoryEntry]:
        matches = [item for item in self.list_history() if item.target_id == target_id]
        return sorted(matches, key=lambda item: (item.timestamp, item.history_id))

    def next_assessment_id(self) -> str:
        return _next_sequence_id("ICA", len(self.list_assessments()) + 1)

    def next_history_id(self) -> str:
        return _next_sequence_id("ICH", len(self.list_history()) + 1)


class ConfidenceAuditLog:
    """YAML-backed append-only confidence audit log with hash chaining."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def next_audit_id(self) -> str:
        return _next_sequence_id("ICAUD", len(self.list_entries()) + 1)

    def previous_hash(self) -> str:
        entries = self.list_entries()
        if not entries:
            return ""
        return entries[-1].entry_hash

    def write(self, entry: ConfidenceAuditEntry) -> None:
        write_entity(self._base_dir / f"{entry.audit_id}.yaml", entry.to_dict())

    def list_entries(self) -> list[ConfidenceAuditEntry]:
        if not self._base_dir.exists():
            return []
        return [
            ConfidenceAuditEntry.from_dict(read_entity(path))
            for path in sorted(self._base_dir.glob("ICAUD-*.yaml"))
        ]


def _next_sequence_id(prefix: str, sequence: int) -> str:
    date_code = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_code}-{sequence:04d}"
