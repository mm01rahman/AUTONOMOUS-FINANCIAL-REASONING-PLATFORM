"""WP-RT-1002 integration tests for CIO-01 to CIO-02 flow."""

from __future__ import annotations

from afrp_runtime.layer1.features import FeatureStore
from afrp_runtime.layer1.ingest import RawEvent, TickIngestor


def test_cio01_stream_emits_deterministic_cio02_sequence() -> None:
    events: list[RawEvent] = [
        {
            "instrument": "XAUUSD",
            "kind": "QUOTE",
            "bid": 2399.0,
            "ask": 2401.0,
            "event_at_ns": 1_000,
            "venue": "SIM",
        },
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2401.5,
            "size": 1.0,
            "event_at_ns": 2_000,
            "venue": "SIM",
        },
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2402.0,
            "size": 1.0,
            "event_at_ns": 3_000,
            "venue": "SIM",
        },
    ]

    def run_once() -> list[tuple[str, int, str, float]]:
        ingestor = TickIngestor("MP-04", cognitive_cycle_id="cycle-integration")
        store = FeatureStore("MP-04", cognitive_cycle_id="cycle-integration")
        rows: list[tuple[str, int, str, float]] = []
        for event in events:
            observation = ingestor.ingest(event)
            for feature in store.update(observation):
                rows.append(
                    (
                        feature.feature_id,
                        feature.source_sequence,
                        feature.instrument,
                        round(feature.value, 9),
                    )
                )
        return rows

    first = run_once()
    second = run_once()
    assert first == second
    assert len(first) >= 5
    # First quote deterministically emits spread and midpoint features.
    assert first[0][1] == 1 and first[1][1] == 1
