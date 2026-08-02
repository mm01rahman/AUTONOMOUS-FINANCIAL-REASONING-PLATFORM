"""IKROS query audit logging — deterministic YAML audit records."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tools.ikros.persistence import read_entity, write_entity
from tools.ikros.query.models import QueryAuditEntry


class QueryAuditLog:
    """YAML-backed audit log for query executions."""

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def next_audit_id(self) -> str:
        sequence = len(self.list_entries()) + 1
        date_code = datetime.now(UTC).strftime("%Y%m%d")
        return f"IQA-{date_code}-{sequence:04d}"

    def write(self, entry: QueryAuditEntry) -> None:
        write_entity(self._base_dir / f"{entry.audit_id}.yaml", entry.to_dict())

    def list_entries(self) -> list[QueryAuditEntry]:
        if not self._base_dir.exists():
            return []
        entries: list[QueryAuditEntry] = []
        for path in sorted(self._base_dir.glob("IQA-*.yaml")):
            data = read_entity(path)
            entries.append(
                QueryAuditEntry(
                    audit_id=str(data["audit_id"]),
                    executed_at=str(data["executed_at"]),
                    raw_query=str(data["raw_query"]),
                    parsed_query=dict(data.get("parsed_query", {})),
                    plan=dict(data.get("plan", {})),
                    result_ids=list(data.get("result_ids", [])),
                    result_count=int(data.get("result_count", 0)),
                )
            )
        return entries
