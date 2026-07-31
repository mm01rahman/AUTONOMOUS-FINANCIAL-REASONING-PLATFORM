"""WP-RT-1001 integration tests for mixed-provider ingestion."""

from __future__ import annotations

from afrp_runtime.layer1.ingest import (
    MultiProviderIngestor,
    OhlcvProviderAdapter,
    RawPayload,
    TickProviderAdapter,
)


def test_mixed_provider_pipeline_is_deterministic() -> None:
    payloads: list[tuple[str, RawPayload]] = [
        (
            "tick-a",
            {
                "instrument": "XAUUSD",
                "kind": "QUOTE",
                "bid": 2399.0,
                "ask": 2401.0,
                "event_at_ns": 1_000,
                "venue": "SIM-A",
            },
        ),
        (
            "bar-a",
            {
                "instrument": "XAUUSD",
                "open": 2400.0,
                "high": 2404.0,
                "low": 2398.0,
                "close": 2402.0,
                "volume": 200.0,
                "event_at_ns": 2_000,
                "venue": "SIM-B",
            },
        ),
        (
            "tick-a",
            {
                "instrument": "XAUUSD",
                "kind": "TRADE",
                "price": 2402.5,
                "size": 0.7,
                "event_at_ns": 3_000,
                "venue": "SIM-A",
            },
        ),
    ]

    def run_once() -> list[tuple[int, str, float, str]]:
        coordinator = MultiProviderIngestor("MP-04", cognitive_cycle_id="integration-cycle")
        coordinator.register_provider(TickProviderAdapter(provider_id="tick-a"))
        coordinator.register_provider(OhlcvProviderAdapter(provider_id="bar-a"))
        rows: list[tuple[int, str, float, str]] = []
        for provider_id, payload in payloads:
            observations = coordinator.ingest_payload(provider_id, payload)
            for observation in observations:
                rows.append(
                    (
                        observation.ingest_sequence,
                        observation.kind.name,
                        observation.price,
                        observation.venue,
                    )
                )
        return rows

    first = run_once()
    second = run_once()
    assert first == second
    assert first == [
        (1, "QUOTE", 0.0, "SIM-A"),
        (2, "TRADE", 2402.0, "SIM-B"),
        (3, "TRADE", 2402.5, "SIM-A"),
    ]
