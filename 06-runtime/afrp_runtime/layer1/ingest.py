"""L1-ING telemetry ingress (SLS-100, WP-RT-1001).

Normalizes provider payloads (tick + OHLCV) into canonical CIO-01
``RawObservation`` events with monotonic sequencing and deterministic
normalization. Exposes explicit metrics and health status for ingestion paths.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind, RawObservation
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L1-ING"

RawEvent = dict[str, str | int | float]
RawPayload = Mapping[str, str | int | float]

_REQUIRED_KEYS = ("instrument", "kind", "event_at_ns")
_KIND_MAP = {
    "TRADE": ObservationKind.TRADE,
    "QUOTE": ObservationKind.QUOTE,
    "ORACLE": ObservationKind.ORACLE,
    "MACRO": ObservationKind.MACRO,
}


class MarketDataProvider(Protocol):
    """Provider adapter contract producing canonical raw events."""

    @property
    def provider_id(self) -> str:
        """Stable provider identifier."""

    def normalize(self, payload: RawPayload) -> list[RawEvent]:
        """Normalize one provider payload into one-or-more canonical events."""


def _normalized_timestamp_ns(payload: RawPayload) -> int:
    if "event_at_ns" in payload:
        event_at_ns = int(payload["event_at_ns"])
    elif "event_at_ms" in payload:
        event_at_ns = int(payload["event_at_ms"]) * 1_000_000
    elif "event_at_s" in payload:
        event_at_ns = int(payload["event_at_s"]) * 1_000_000_000
    else:
        raise ContractViolationError("CIO-01", "missing event timestamp field")
    if event_at_ns <= 0:
        raise ContractViolationError("CIO-01", "event timestamp must be positive")
    return event_at_ns


@dataclass(frozen=True)
class TickProviderAdapter:
    """Provider adapter for native tick payloads."""

    provider_id: str

    def normalize(self, payload: RawPayload) -> list[RawEvent]:
        missing = [key for key in ("instrument", "kind") if key not in payload]
        if missing:
            raise ContractViolationError(
                "CIO-01", f"provider {self.provider_id} missing keys: {', '.join(missing)}"
            )
        event: RawEvent = {
            "instrument": str(payload["instrument"]),
            "kind": str(payload["kind"]).upper(),
            "event_at_ns": _normalized_timestamp_ns(payload),
            "venue": str(payload.get("venue", self.provider_id)),
        }
        for key in ("price", "bid", "ask", "size"):
            if key in payload:
                event[key] = float(payload[key])
        return [event]


@dataclass(frozen=True)
class OhlcvProviderAdapter:
    """Provider adapter translating OHLCV bars into canonical CIO-01 trade ticks."""

    provider_id: str

    def normalize(self, payload: RawPayload) -> list[RawEvent]:
        missing = [
            key
            for key in ("instrument", "open", "high", "low", "close", "volume")
            if key not in payload
        ]
        if missing:
            raise ContractViolationError(
                "CIO-01", f"provider {self.provider_id} missing keys: {', '.join(missing)}"
            )
        o = float(payload["open"])
        h = float(payload["high"])
        low = float(payload["low"])
        c = float(payload["close"])
        v = float(payload["volume"])
        if min(o, h, low, c) <= 0.0:
            raise ContractViolationError("CIO-01", "OHLC prices must be positive")
        if low > min(o, c) or h < max(o, c):
            raise ContractViolationError("CIO-01", "OHLC bounds are inconsistent")
        if v <= 0.0:
            raise ContractViolationError("CIO-01", "OHLCV volume must be positive")
        event: RawEvent = {
            "instrument": str(payload["instrument"]),
            "kind": "TRADE",
            "price": c,
            "size": v,
            "event_at_ns": _normalized_timestamp_ns(payload),
            "venue": str(payload.get("venue", self.provider_id)),
        }
        return [event]


@dataclass(frozen=True)
class IngestHealth:
    """Runtime health snapshot for ingress."""

    provider_count: int
    events_ingested: int
    provider_errors: int
    gaps_detected: int
    ready: bool
    last_error: str | None


@dataclass
class TickIngestor:
    """Deterministic CIO-01 producer with per-instrument gap accounting."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"
    _sequence: int = 0
    _last_event_ns: dict[str, int] = field(default_factory=dict)
    gaps_detected: int = 0

    def ingest(self, event: RawEvent) -> RawObservation:
        """Normalize one raw venue event into CIO-01.

        Raises:
            ContractViolationError: required keys missing, unknown kind, or
                non-positive trade/quote prices.
        """
        missing = [key for key in _REQUIRED_KEYS if key not in event]
        if missing:
            raise ContractViolationError("CIO-01", f"missing keys: {', '.join(missing)}")

        kind_label = str(event["kind"])
        kind = _KIND_MAP.get(kind_label)
        if kind is None:
            raise ContractViolationError("CIO-01", f"unknown observation kind {kind_label!r}")

        instrument = str(event["instrument"])
        price = float(event.get("price", 0.0))
        bid = float(event.get("bid", 0.0))
        ask = float(event.get("ask", 0.0))
        size = float(event.get("size", 0.0))
        event_at_ns = int(event["event_at_ns"])

        if kind is ObservationKind.TRADE and price <= 0.0:
            raise ContractViolationError("CIO-01", f"trade price must be positive, got {price}")
        if kind is ObservationKind.QUOTE:
            if bid <= 0.0 or ask <= 0.0:
                raise ContractViolationError("CIO-01", "quote bid/ask must be positive")
            if bid > ask:
                raise ContractViolationError("CIO-01", f"crossed quote bid={bid} ask={ask}")

        previous = self._last_event_ns.get(instrument)
        if previous is not None and event_at_ns < previous:
            self.gaps_detected += 1
        self._last_event_ns[instrument] = max(event_at_ns, previous or event_at_ns)

        self._sequence += 1
        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{instrument}:{kind_label}:{event_at_ns}:{self._sequence}",
            generated_at_ns=event_at_ns,
        )
        return RawObservation(
            envelope=envelope,
            instrument=instrument,
            kind=kind,
            price=price,
            bid=bid,
            ask=ask,
            size=size,
            venue=str(event.get("venue", "")),
            ingest_sequence=self._sequence,
            event_at_ns=event_at_ns,
        )

    def ingest_stream(self, events: list[RawEvent]) -> list[RawObservation]:
        """Ingest an ordered batch, preserving arrival order."""
        return [self.ingest(event) for event in events]

    @property
    def ingest_count(self) -> int:
        """Number of observations emitted by this ingestor instance."""
        return self._sequence

    def health(self) -> IngestHealth:
        """Health snapshot for direct-ingest mode."""
        return IngestHealth(
            provider_count=0,
            events_ingested=self._sequence,
            provider_errors=0,
            gaps_detected=self.gaps_detected,
            ready=True,
            last_error=None,
        )


@dataclass
class MultiProviderIngestor:
    """Coordinator over provider adapters + canonical CIO-01 emission."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"
    _providers: dict[str, MarketDataProvider] = field(default_factory=dict)
    _events_ingested: int = 0
    _provider_errors: int = 0
    _last_error: str | None = None
    _events_by_provider: dict[str, int] = field(default_factory=dict)
    _ingestor: TickIngestor = field(init=False)

    def __post_init__(self) -> None:
        self._ingestor = TickIngestor(
            mission_profile_id=self.mission_profile_id,
            cognitive_cycle_id=self.cognitive_cycle_id,
        )

    def register_provider(self, provider: MarketDataProvider) -> None:
        self._providers[provider.provider_id] = provider

    def ingest_payload(self, provider_id: str, payload: RawPayload) -> list[RawObservation]:
        provider = self._providers.get(provider_id)
        if provider is None:
            self._provider_errors += 1
            self._last_error = f"provider {provider_id!r} is not registered"
            raise ContractViolationError("CIO-01", self._last_error)
        try:
            events = provider.normalize(payload)
            observations = self._ingestor.ingest_stream(events)
        except ContractViolationError as exc:
            self._provider_errors += 1
            self._last_error = str(exc)
            raise
        self._events_ingested += len(observations)
        self._events_by_provider[provider_id] = (
            self._events_by_provider.get(provider_id, 0) + len(observations)
        )
        return observations

    def health(self) -> IngestHealth:
        return IngestHealth(
            provider_count=len(self._providers),
            events_ingested=self._events_ingested,
            provider_errors=self._provider_errors,
            gaps_detected=self._ingestor.gaps_detected,
            ready=len(self._providers) > 0,
            last_error=self._last_error,
        )

    @property
    def events_by_provider(self) -> dict[str, int]:
        return dict(self._events_by_provider)
