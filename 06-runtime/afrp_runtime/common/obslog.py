"""Structured OBS-01 JSON logging (RT-COMMON, EDR-006).

Every runtime log record is a single-line JSON document with the OBS-01
shape: ``ts_ns, level, subsystem, event, trace_id, span_id, cycle_id, data``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import TextIO

_OBS01_REQUIRED = ("ts_ns", "level", "subsystem", "event")


class LogLevel(StrEnum):
    """OBS-01 severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Obs01Record:
    """One OBS-01 structured log record."""

    ts_ns: int
    level: LogLevel
    subsystem: str
    event: str
    trace_id: str
    span_id: str
    cycle_id: str
    data: dict[str, str | int | float | bool]

    def to_json(self) -> str:
        """Serialize as a canonical single-line JSON document."""
        payload = {
            "ts_ns": self.ts_ns,
            "level": self.level.value,
            "subsystem": self.subsystem,
            "event": self.event,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "cycle_id": self.cycle_id,
            "data": self.data,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def validate_obs01(document: str) -> bool:
    """True iff ``document`` is a valid OBS-01 JSON record."""
    try:
        parsed = json.loads(document)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict):
        return False
    if any(key not in parsed for key in _OBS01_REQUIRED):
        return False
    return parsed["level"] in LogLevel.__members__


@dataclass
class Obs01Logger:
    """Minimal OBS-01 emitter bound to a subsystem and an output stream."""

    subsystem: str
    stream: TextIO
    trace_id: str = ""
    span_id: str = ""
    cycle_id: str = ""

    def log(
        self,
        level: LogLevel,
        event: str,
        data: dict[str, str | int | float | bool] | None = None,
    ) -> Obs01Record:
        """Emit one record; returns it for assertion in tests."""
        record = Obs01Record(
            ts_ns=time.time_ns(),
            level=level,
            subsystem=self.subsystem,
            event=event,
            trace_id=self.trace_id,
            span_id=self.span_id,
            cycle_id=self.cycle_id,
            data=dict(data or {}),
        )
        self.stream.write(record.to_json() + "\n")
        return record
