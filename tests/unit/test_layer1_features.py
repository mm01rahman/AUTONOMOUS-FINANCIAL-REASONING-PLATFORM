"""WP-RT-1002 unit tests for Layer 1 feature emission."""

from __future__ import annotations

import pytest
from afrp_runtime.contracts.features import (
    FEATURE_EWM_VOL,
    FEATURE_LOG_RETURN,
    FEATURE_MID,
    FEATURE_SPREAD_BPS,
)
from afrp_runtime.layer1.features import FeatureStore
from afrp_runtime.layer1.ingest import RawEvent, TickIngestor

NS = 1_000_000_000


def quote(ts_s: int, bid: float, ask: float, instrument: str = "XAUUSD") -> RawEvent:
    return {
        "instrument": instrument,
        "kind": "QUOTE",
        "bid": bid,
        "ask": ask,
        "event_at_ns": ts_s * NS,
        "venue": "SIM",
    }


def trade(ts_s: int, price: float, size: float = 1.0) -> RawEvent:
    return {
        "instrument": "XAUUSD",
        "kind": "TRADE",
        "price": price,
        "size": size,
        "event_at_ns": ts_s * NS,
        "venue": "SIM",
    }


def test_quote_yields_mid_and_spread() -> None:
    store = FeatureStore("MP-04")
    ingestor = TickIngestor("MP-04")
    features = store.update(ingestor.ingest(quote(10, 2399.0, 2401.0)))
    by_id = {feature.feature_id: feature for feature in features}
    assert by_id[FEATURE_MID].value == pytest.approx(2400.0)
    assert by_id[FEATURE_SPREAD_BPS].value == pytest.approx(8.3333, rel=1e-3)


def test_returns_and_vol_after_history() -> None:
    store = FeatureStore("MP-04", window_seconds=300)
    ingestor = TickIngestor("MP-04")
    emitted: dict[str, float] = {}
    for second, price in ((0, 2400.0), (30, 2406.0), (60, 2412.0)):
        for feature in store.update(ingestor.ingest(trade(second, price))):
            emitted[feature.feature_id] = feature.value
    assert FEATURE_LOG_RETURN in emitted and FEATURE_EWM_VOL in emitted
    assert emitted[FEATURE_LOG_RETURN] == pytest.approx(0.0049875, rel=1e-3)
    assert emitted[FEATURE_EWM_VOL] > 0.0


def test_window_eviction_is_bounded_and_deterministic() -> None:
    store = FeatureStore("MP-04", window_seconds=10)
    ingestor = TickIngestor("MP-04")
    store.update(ingestor.ingest(trade(0, 2400.0)))
    features = store.update(ingestor.ingest(trade(60, 2500.0)))
    ids = {feature.feature_id for feature in features}
    assert FEATURE_LOG_RETURN not in ids


def test_cache_is_immutable_by_key() -> None:
    store = FeatureStore("MP-04")
    ingestor = TickIngestor("MP-04")
    observation = ingestor.ingest(quote(10, 2399.0, 2401.0))
    first = store.update(observation)
    second = store.update(observation)
    assert [feature.envelope.message_id for feature in first] == [
        feature.envelope.message_id for feature in second
    ]


def test_provenance_chains_to_observation() -> None:
    store = FeatureStore("MP-04")
    ingestor = TickIngestor("MP-04")
    observation = ingestor.ingest(quote(10, 2399.0, 2401.0))
    feature = store.update(observation)[0]
    assert observation.envelope.message_id in feature.envelope.parent_cio_ids
    assert feature.envelope.trace_id == observation.envelope.trace_id
