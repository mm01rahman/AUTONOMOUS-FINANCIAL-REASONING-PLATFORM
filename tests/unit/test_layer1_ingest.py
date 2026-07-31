"""WP-RT-1001 unit tests for Layer 1 ingestion."""

from __future__ import annotations

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind
from afrp_runtime.layer1.ingest import (
    MultiProviderIngestor,
    OhlcvProviderAdapter,
    TickIngestor,
    TickProviderAdapter,
)


def test_tick_provider_normalization_from_milliseconds() -> None:
    provider = TickProviderAdapter(provider_id="tick-a")
    normalized = provider.normalize(
        {
            "instrument": "XAUUSD",
            "kind": "trade",
            "price": 2400.25,
            "size": 1.5,
            "event_at_ms": 1710000000000,
        }
    )
    assert normalized == [
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2400.25,
            "size": 1.5,
            "event_at_ns": 1710000000000 * 1_000_000,
            "venue": "tick-a",
        }
    ]


def test_ohlcv_provider_maps_to_trade_close_price() -> None:
    provider = OhlcvProviderAdapter(provider_id="ohlcv-a")
    event = provider.normalize(
        {
            "instrument": "XAUUSD",
            "open": 2398.0,
            "high": 2405.0,
            "low": 2396.0,
            "close": 2402.5,
            "volume": 120.0,
            "event_at_s": 1710000000,
        }
    )[0]
    assert event["kind"] == "TRADE"
    assert event["price"] == 2402.5
    assert event["size"] == 120.0
    assert event["event_at_ns"] == 1710000000 * 1_000_000_000


def test_ohlcv_inconsistent_bounds_rejected() -> None:
    provider = OhlcvProviderAdapter(provider_id="ohlcv-a")
    with pytest.raises(ContractViolationError, match="inconsistent"):
        provider.normalize(
            {
                "instrument": "XAUUSD",
                "open": 2400.0,
                "high": 2401.0,
                "low": 2390.0,
                "close": 2410.0,
                "volume": 10.0,
                "event_at_ns": 1,
            }
        )


def test_multi_provider_ingest_emits_canonical_cio01() -> None:
    coordinator = MultiProviderIngestor("MP-04")
    coordinator.register_provider(TickProviderAdapter(provider_id="tick-a"))
    coordinator.register_provider(OhlcvProviderAdapter(provider_id="bar-a"))

    first = coordinator.ingest_payload(
        "tick-a",
        {
            "instrument": "XAUUSD",
            "kind": "QUOTE",
            "bid": 2399.0,
            "ask": 2401.0,
            "event_at_ns": 1_000,
        },
    )
    second = coordinator.ingest_payload(
        "bar-a",
        {
            "instrument": "XAUUSD",
            "open": 2400.0,
            "high": 2402.0,
            "low": 2398.0,
            "close": 2401.5,
            "volume": 100.0,
            "event_at_ns": 2_000,
        },
    )

    assert first[0].kind is ObservationKind.QUOTE
    assert second[0].kind is ObservationKind.TRADE
    assert [first[0].ingest_sequence, second[0].ingest_sequence] == [1, 2]
    assert second[0].price == pytest.approx(2401.5)
    assert coordinator.events_by_provider == {"tick-a": 1, "bar-a": 1}


def test_health_and_error_metrics_exposed() -> None:
    coordinator = MultiProviderIngestor("MP-04")
    coordinator.register_provider(TickProviderAdapter(provider_id="tick-a"))
    coordinator.ingest_payload(
        "tick-a",
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2400.0,
            "size": 1.0,
            "event_at_ns": 1_000,
        },
    )
    with pytest.raises(ContractViolationError, match="not registered"):
        coordinator.ingest_payload("missing", {"instrument": "XAUUSD", "kind": "TRADE"})
    health = coordinator.health()
    assert health.provider_count == 1
    assert health.events_ingested == 1
    assert health.provider_errors == 1
    assert health.ready is True
    assert health.last_error is not None


def test_tick_ingestor_health_snapshot() -> None:
    ingestor = TickIngestor("MP-04")
    ingestor.ingest(
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2400.0,
            "size": 1.0,
            "event_at_ns": 1_000,
        }
    )
    health = ingestor.health()
    assert health.events_ingested == 1
    assert health.gaps_detected == 0
