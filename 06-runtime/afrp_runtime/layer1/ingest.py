"""L1-ING — telemetry ingress (SLS-100, WP-IMP-0013).

Normalizes raw venue events into CIO-01 :class:`RawObservation` objects with
monotonic ingest sequencing, structural validation, and gap detection.
Communicates downstream exclusively via contracts (EDR-002).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind, RawObservation
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L1-ING"

RawEvent = dict[str, str | int | float]

_REQUIRED_KEYS = ("instrument", "kind", "event_at_ns")
_KIND_MAP = {
    "TRADE": ObservationKind.TRADE,
    "QUOTE": ObservationKind.QUOTE,
    "ORACLE": ObservationKind.ORACLE,
    "MACRO": ObservationKind.MACRO,
}


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
