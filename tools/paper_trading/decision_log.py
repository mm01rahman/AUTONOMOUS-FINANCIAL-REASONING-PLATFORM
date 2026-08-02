"""Decision logging with deterministic ordering and run checksums."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "timestamp",
    "market_snapshot",
    "world_model",
    "decision_context",
    "utility",
    "policy_outcome",
    "execution_simulation",
    "portfolio_state",
    "learning_outputs",
)


@dataclass(frozen=True)
class DecisionRecord:
    sequence: int
    timestamp: datetime
    market_snapshot: dict[str, Any]
    world_model: dict[str, Any]
    decision_context: dict[str, Any]
    utility: dict[str, Any]
    policy_outcome: dict[str, Any]
    execution_simulation: dict[str, Any]
    portfolio_state: dict[str, Any]
    learning_outputs: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        ts = (
            self.timestamp
            if self.timestamp.tzinfo is not None
            else self.timestamp.replace(tzinfo=UTC)
        )
        return {
            "sequence": self.sequence,
            "timestamp": ts.astimezone(UTC).isoformat(),
            "market_snapshot": self.market_snapshot,
            "world_model": self.world_model,
            "decision_context": self.decision_context,
            "utility": self.utility,
            "policy_outcome": self.policy_outcome,
            "execution_simulation": self.execution_simulation,
            "portfolio_state": self.portfolio_state,
            "learning_outputs": self.learning_outputs,
        }


class DecisionLogWriter:
    """JSONL log writer with deterministic serialization and cumulative hash."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")
        self._hasher = hashlib.sha256()
        self._count = 0

    def write(self, record: DecisionRecord) -> None:
        payload = record.to_dict()
        for field in REQUIRED_FIELDS:
            if field not in payload:
                raise ValueError(f"missing required field: {field}")
        line = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self._hasher.update((line + "\n").encode("utf-8"))
        self._count += 1

    def finalize(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "records": self._count,
            "checksum": self._hasher.hexdigest(),
        }


def compute_file_checksum(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
