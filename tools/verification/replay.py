"""Historical replay engine primitives (Phase B / WP-B1)."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


def _parse_timestamp_to_ns(raw: str) -> int:
    stamp = raw.strip()
    if stamp.endswith("Z"):
        stamp = stamp[:-1] + "+00:00"
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = parsed.astimezone(UTC)
    return int(parsed.timestamp() * 1_000_000_000)


@dataclass(frozen=True, order=True)
class ReplayEvent:
    """Canonical replay event in UTC nanoseconds."""

    timestamp_ns: int
    sequence: int
    stream: str
    kind: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "sequence": self.sequence,
            "stream": self.stream,
            "kind": self.kind,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class ReplayConfig:
    """Replay configuration."""

    mission_profile_id: str = "MP-04"
    speed_multiplier: float = 1.0
    deterministic_seed: int = 42
    timezone: str = "UTC"
    strict_ordering: bool = True

    def validate(self) -> None:
        if self.speed_multiplier <= 0:
            raise ValueError("speed_multiplier must be > 0")
        if self.timezone != "UTC":
            raise ValueError("replay engine is UTC-only")


@dataclass
class ReplayScheduler:
    """Sorted event scheduler."""

    events: list[ReplayEvent] = field(default_factory=list)
    _cursor: int = 0

    def add(self, event: ReplayEvent) -> None:
        self.events.append(event)

    def sort(self) -> None:
        self.events.sort(key=lambda e: (e.timestamp_ns, e.sequence, e.stream, e.kind))
        self._cursor = 0

    def has_next(self) -> bool:
        return self._cursor < len(self.events)

    def peek(self) -> ReplayEvent:
        return self.events[self._cursor]

    def pop(self) -> ReplayEvent:
        event = self.events[self._cursor]
        self._cursor += 1
        return event

    def reset(self) -> None:
        self._cursor = 0


@dataclass
class DeterministicReplayClock:
    """Deterministic replay clock supporting speed control."""

    speed_multiplier: float = 1.0
    _now_ns: int = 0

    def set(self, timestamp_ns: int) -> None:
        self._now_ns = timestamp_ns

    def advance_to(self, timestamp_ns: int) -> int:
        if timestamp_ns < self._now_ns:
            raise ValueError("clock cannot move backwards")
        delta = timestamp_ns - self._now_ns
        scaled = int(delta / self.speed_multiplier)
        self._now_ns += scaled
        return self._now_ns

    @property
    def now_ns(self) -> int:
        return self._now_ns


@dataclass(frozen=True)
class ReplayRunResult:
    """Replay result and reproducibility evidence."""

    event_count: int
    market_event_count: int
    macro_event_count: int
    geo_event_count: int
    first_timestamp_ns: int
    last_timestamp_ns: int
    speed_multiplier: float
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReplayController:
    """Replay controller coordinating scheduler and deterministic clock."""

    def __init__(self, config: ReplayConfig, scheduler: ReplayScheduler) -> None:
        config.validate()
        self.config = config
        self.scheduler = scheduler
        self.clock = DeterministicReplayClock(speed_multiplier=config.speed_multiplier)

    def run(self) -> ReplayRunResult:
        if not self.scheduler.events:
            raise ValueError("no replay events scheduled")
        self.scheduler.sort()
        first = self.scheduler.events[0]
        self.clock.set(first.timestamp_ns)
        processed: list[dict[str, Any]] = []
        market = 0
        macro = 0
        geo = 0

        while self.scheduler.has_next():
            event = self.scheduler.pop()
            self.clock.advance_to(event.timestamp_ns)
            if event.stream == "market":
                market += 1
            elif event.stream == "macro":
                macro += 1
            elif event.stream == "geopolitical":
                geo += 1
            processed.append(
                {
                    "event": event.to_dict(),
                    "clock_ns": self.clock.now_ns,
                }
            )

        canonical = json.dumps(processed, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return ReplayRunResult(
            event_count=len(processed),
            market_event_count=market,
            macro_event_count=macro,
            geo_event_count=geo,
            first_timestamp_ns=first.timestamp_ns,
            last_timestamp_ns=self.scheduler.events[-1].timestamp_ns,
            speed_multiplier=self.config.speed_multiplier,
            checksum=checksum,
        )


def load_market_ohlcv(path: Path, stream: str = "market") -> list[ReplayEvent]:
    """Load OHLCV events from CSV."""
    rows: list[ReplayEvent] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader):
            timestamp = row.get("timestamp", "")
            if not timestamp:
                continue
            timestamp_ns = _parse_timestamp_to_ns(timestamp)
            rows.append(
                ReplayEvent(
                    timestamp_ns=timestamp_ns,
                    sequence=idx,
                    stream=stream,
                    kind="ohlcv",
                    payload={
                        "open": float(row.get("open", "0") or 0.0),
                        "high": float(row.get("high", "0") or 0.0),
                        "low": float(row.get("low", "0") or 0.0),
                        "close": float(row.get("close", "0") or 0.0),
                        "volume": float(row.get("volume", "0") or 0.0),
                        "symbol": row.get("symbol", "XAUUSD"),
                    },
                )
            )
    return rows


def load_events_yaml(path: Path, stream: str, kind: str) -> list[ReplayEvent]:
    """Load macro/geopolitical events from YAML list."""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        raise ValueError(f"{path} must contain a top-level list")
    events: list[ReplayEvent] = []
    for idx, row in enumerate(loaded):
        if not isinstance(row, dict):
            continue
        raw_ts = row.get("timestamp")
        if not isinstance(raw_ts, str):
            continue
        events.append(
            ReplayEvent(
                timestamp_ns=_parse_timestamp_to_ns(raw_ts),
                sequence=idx,
                stream=stream,
                kind=kind,
                payload=row,
            )
        )
    return events
