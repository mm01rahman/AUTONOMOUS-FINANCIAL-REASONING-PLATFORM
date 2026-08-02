"""Live market data gateway with deterministic fallback adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

FEED_SEQUENCE = ("xauusd", "dxy", "ust10y", "econ_calendar", "geopolitical")


@dataclass(frozen=True)
class FeedEvent:
    """Normalized live event."""

    source: str
    timestamp: datetime
    metric: str
    value: float
    payload: dict[str, Any]
    heartbeat_ts: datetime
    sequence: int


class FeedAdapter(Protocol):
    """Provider interface for polling feeds."""

    name: str

    def poll(self, when: datetime) -> list[FeedEvent]:
        """Poll a provider endpoint and return normalized events."""


def _ensure_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


class DeterministicPollingAdapter:
    """Deterministic polling adapter used for live-sim mode."""

    def __init__(self, name: str, metric: str, base: float, drift: float, amplitude: float) -> None:
        self.name = name
        self._metric = metric
        self._base = base
        self._drift = drift
        self._amplitude = amplitude
        self._counter = 0

    def poll(self, when: datetime) -> list[FeedEvent]:
        ts = _ensure_utc(when)
        seq = self._counter
        self._counter += 1
        periodic = ((seq % 9) - 4) * self._amplitude
        value = self._base + seq * self._drift + periodic
        event = FeedEvent(
            source=self.name,
            timestamp=ts,
            metric=self._metric,
            value=round(value, 6),
            payload={"mode": "live-sim", "adapter": self.name},
            heartbeat_ts=ts,
            sequence=seq,
        )
        return [event]


class DeterministicCalendarAdapter:
    """Deterministic economic calendar adapter with normalized impact scores."""

    name = "econ_calendar"

    def __init__(self) -> None:
        self._counter = 0

    def poll(self, when: datetime) -> list[FeedEvent]:
        ts = _ensure_utc(when)
        seq = self._counter
        self._counter += 1
        impact = (seq % 5) / 4
        return [
            FeedEvent(
                source=self.name,
                timestamp=ts,
                metric="impact_score",
                value=round(impact, 6),
                payload={"event": f"SIM_EVENT_{seq:04d}", "mode": "live-sim"},
                heartbeat_ts=ts,
                sequence=seq,
            )
        ]


class DeterministicGeopoliticalAdapter:
    """Deterministic geopolitical sentiment adapter."""

    name = "geopolitical"

    def __init__(self) -> None:
        self._counter = 0

    def poll(self, when: datetime) -> list[FeedEvent]:
        ts = _ensure_utc(when)
        seq = self._counter
        self._counter += 1
        sentiment = ((seq % 7) - 3) / 10
        return [
            FeedEvent(
                source=self.name,
                timestamp=ts,
                metric="sentiment",
                value=round(sentiment, 6),
                payload={"headline_id": f"GEO-{seq:05d}", "mode": "live-sim"},
                heartbeat_ts=ts,
                sequence=seq,
            )
        ]


class LiveMarketDataGateway:
    """Gateway with reconnect, heartbeat and deterministic merge ordering."""

    def __init__(
        self,
        adapters: dict[str, FeedAdapter] | None = None,
        reconnect_backoff_seconds: int = 5,
        heartbeat_timeout_seconds: int = 120,
    ) -> None:
        self.adapters = adapters or {
            "xauusd": DeterministicPollingAdapter("xauusd", "price", 2325.0, 0.35, 0.12),
            "dxy": DeterministicPollingAdapter("dxy", "index", 104.0, -0.01, 0.02),
            "ust10y": DeterministicPollingAdapter("ust10y", "yield", 4.15, 0.002, 0.01),
            "econ_calendar": DeterministicCalendarAdapter(),
            "geopolitical": DeterministicGeopoliticalAdapter(),
        }
        self.reconnect_backoff_seconds = reconnect_backoff_seconds
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self._last_heartbeat: dict[str, datetime] = {}
        self._reconnect_after: dict[str, datetime] = {}
        self._failure_count: dict[str, int] = {}

    def poll_cycle(self, when: datetime) -> list[FeedEvent]:
        now = _ensure_utc(when)
        events: list[FeedEvent] = []
        for name in FEED_SEQUENCE:
            adapter = self.adapters.get(name)
            if adapter is None:
                continue
            reconnect_at = self._reconnect_after.get(name)
            if reconnect_at is not None and now < reconnect_at:
                continue
            try:
                adapter_events = adapter.poll(now)
                for event in adapter_events:
                    normalized = FeedEvent(
                        source=event.source,
                        timestamp=_ensure_utc(event.timestamp),
                        metric=event.metric,
                        value=event.value,
                        payload=event.payload,
                        heartbeat_ts=_ensure_utc(event.heartbeat_ts),
                        sequence=event.sequence,
                    )
                    events.append(normalized)
                    self._last_heartbeat[name] = normalized.heartbeat_ts
                self._failure_count[name] = 0
                self._reconnect_after.pop(name, None)
            except Exception:
                fail_count = self._failure_count.get(name, 0) + 1
                self._failure_count[name] = fail_count
                self._reconnect_after[name] = now + timedelta(
                    seconds=self.reconnect_backoff_seconds * fail_count
                )

        return self._merge_order(events)

    def _merge_order(self, events: list[FeedEvent]) -> list[FeedEvent]:
        order_index = {key: idx for idx, key in enumerate(FEED_SEQUENCE)}
        return sorted(
            events,
            key=lambda item: (
                item.timestamp,
                order_index.get(item.source, 999),
                item.sequence,
                item.metric,
            ),
        )

    def heartbeat_status(self, when: datetime) -> dict[str, str]:
        now = _ensure_utc(when)
        states: dict[str, str] = {}
        timeout = timedelta(seconds=self.heartbeat_timeout_seconds)
        for name in FEED_SEQUENCE:
            ts = self._last_heartbeat.get(name)
            if ts is None:
                states[name] = "missing"
            elif now - ts > timeout:
                states[name] = "stale"
            else:
                states[name] = "healthy"
        return states

    def build_snapshot(self, when: datetime) -> dict[str, Any]:
        now = _ensure_utc(when)
        events = self.poll_cycle(now)
        latest: dict[str, float] = {}
        for event in events:
            latest[event.source] = event.value
        return {
            "timestamp": now.isoformat(),
            "feeds": latest,
            "heartbeat": self.heartbeat_status(now),
            "event_count": len(events),
            "mode": "provider-interface-live-sim",
        }
