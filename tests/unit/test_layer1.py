"""Unit tests for Layer 1 (SLS-100): ingest, features, persistence, memory."""

from __future__ import annotations

from pathlib import Path

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind
from afrp_runtime.contracts.features import (
    FEATURE_EWM_VOL,
    FEATURE_LOG_RETURN,
    FEATURE_MID,
    FEATURE_SPREAD_BPS,
)
from afrp_runtime.layer1.features import FeatureStore
from afrp_runtime.layer1.ingest import RawEvent, TickIngestor
from afrp_runtime.layer1.memory import MemoryRecord, VectorMemory, cosine_similarity
from afrp_runtime.layer1.persistence import RelationalStore

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


class TestTickIngestor:
    def test_normalizes_quote(self) -> None:
        ingestor = TickIngestor("MP-04")
        observation = ingestor.ingest(quote(10, 2399.5, 2400.5))
        assert observation.kind is ObservationKind.QUOTE
        assert observation.ingest_sequence == 1
        assert observation.envelope.producer_subsystem_id == "L1-ING"
        assert observation.envelope.mission_profile_id == "MP-04"

    def test_sequence_is_monotonic(self) -> None:
        ingestor = TickIngestor("MP-04")
        batch = ingestor.ingest_stream([trade(1, 2400.0), trade(2, 2401.0), trade(3, 2402.0)])
        assert [o.ingest_sequence for o in batch] == [1, 2, 3]

    def test_missing_keys_rejected(self) -> None:
        with pytest.raises(ContractViolationError, match="missing keys"):
            TickIngestor("MP-04").ingest({"instrument": "XAUUSD"})

    def test_unknown_kind_rejected(self) -> None:
        with pytest.raises(ContractViolationError, match="unknown observation kind"):
            TickIngestor("MP-04").ingest(
                {"instrument": "X", "kind": "VIBES", "event_at_ns": 1}
            )

    def test_crossed_quote_rejected(self) -> None:
        with pytest.raises(ContractViolationError, match="crossed"):
            TickIngestor("MP-04").ingest(quote(1, 2401.0, 2400.0))

    def test_nonpositive_trade_rejected(self) -> None:
        with pytest.raises(ContractViolationError, match="positive"):
            TickIngestor("MP-04").ingest(trade(1, 0.0))

    def test_out_of_order_event_counts_gap(self) -> None:
        ingestor = TickIngestor("MP-04")
        ingestor.ingest(trade(10, 2400.0))
        ingestor.ingest(trade(5, 2399.0))  # regression in event time
        assert ingestor.gaps_detected == 1


class TestFeatureStore:
    def test_quote_yields_mid_and_spread(self) -> None:
        store = FeatureStore("MP-04")
        ingestor = TickIngestor("MP-04")
        features = store.update(ingestor.ingest(quote(10, 2399.0, 2401.0)))
        by_id = {f.feature_id: f for f in features}
        assert by_id[FEATURE_MID].value == pytest.approx(2400.0)
        assert by_id[FEATURE_SPREAD_BPS].value == pytest.approx(8.3333, rel=1e-3)

    def test_returns_and_vol_after_history(self) -> None:
        store = FeatureStore("MP-04", window_seconds=300)
        ingestor = TickIngestor("MP-04")
        emitted: dict[str, float] = {}
        for second, price in ((0, 2400.0), (30, 2406.0), (60, 2412.0)):
            for feature in store.update(ingestor.ingest(trade(second, price))):
                emitted[feature.feature_id] = feature.value
        assert FEATURE_LOG_RETURN in emitted and FEATURE_EWM_VOL in emitted
        assert emitted[FEATURE_LOG_RETURN] == pytest.approx(0.0049875, rel=1e-3)
        assert emitted[FEATURE_EWM_VOL] > 0.0

    def test_window_eviction(self) -> None:
        store = FeatureStore("MP-04", window_seconds=10)
        ingestor = TickIngestor("MP-04")
        store.update(ingestor.ingest(trade(0, 2400.0)))
        features = store.update(ingestor.ingest(trade(60, 2500.0)))
        # first price evicted -> no return computable against it
        ids = {f.feature_id for f in features}
        assert FEATURE_LOG_RETURN not in ids

    def test_cache_is_immutable_by_key(self) -> None:
        store = FeatureStore("MP-04")
        ingestor = TickIngestor("MP-04")
        observation = ingestor.ingest(quote(10, 2399.0, 2401.0))
        first = store.update(observation)
        second = store.update(observation)
        assert [f.envelope.message_id for f in first] == [
            f.envelope.message_id for f in second
        ]

    def test_latest_returns_highest_sequence(self) -> None:
        store = FeatureStore("MP-04")
        ingestor = TickIngestor("MP-04")
        store.update(ingestor.ingest(quote(10, 2399.0, 2401.0)))
        store.update(ingestor.ingest(quote(20, 2400.0, 2402.0)))
        latest = store.latest("XAUUSD")
        assert latest[FEATURE_MID].value == pytest.approx(2401.0)

    def test_provenance_chains_to_observation(self) -> None:
        store = FeatureStore("MP-04")
        ingestor = TickIngestor("MP-04")
        observation = ingestor.ingest(quote(10, 2399.0, 2401.0))
        feature = store.update(observation)[0]
        assert observation.envelope.message_id in feature.envelope.parent_cio_ids
        assert feature.envelope.trace_id == observation.envelope.trace_id


class TestRelationalStore:
    def test_append_and_replay_round_trip(self, tmp_path: Path) -> None:
        store = RelationalStore(tmp_path / "ledger.db")
        ingestor = TickIngestor("MP-04")
        for event in (trade(1, 2400.0), trade(2, 2401.0), trade(3, 2402.0)):
            store.append_observation(ingestor.ingest(event))
        rows = store.replay(1, 3)
        assert [r.ingest_sequence for r in rows] == [1, 2, 3]
        assert rows[1].price == pytest.approx(2401.0)
        assert store.observation_count() == 3
        store.close()

    def test_duplicate_sequence_rejected(self, tmp_path: Path) -> None:
        store = RelationalStore(tmp_path / "ledger.db")
        ingestor = TickIngestor("MP-04")
        observation = ingestor.ingest(trade(1, 2400.0))
        store.append_observation(observation)
        with pytest.raises(ContractViolationError, match="duplicate"):
            store.append_observation(observation)
        store.close()

    def test_order_event_audit_trail(self, tmp_path: Path) -> None:
        store = RelationalStore(tmp_path / "ledger.db")
        store.append_order_event("ord-1", "SUBMITTED", 1.0, 2400.0, 1)
        store.append_order_event("ord-1", "FILLED", 1.0, 2400.5, 2)
        history = store.order_history("ord-1")
        assert [event for event, *_ in history] == ["SUBMITTED", "FILLED"]
        store.close()


class TestVectorMemory:
    def test_store_and_topk_query(self) -> None:
        memory = VectorMemory(dimension=3)
        memory.store(MemoryRecord("a", (1.0, 0.0, 0.0), "trend", 0, 1))
        memory.store(MemoryRecord("b", (0.0, 1.0, 0.0), "range", 0, 1))
        memory.store(MemoryRecord("c", (0.9, 0.1, 0.0), "trend", 0, 1))
        results = memory.query((1.0, 0.0, 0.0), top_k=2)
        assert results[0][0] == "a" and results[1][0] == "c"

    def test_dimension_mismatch_rejected(self) -> None:
        memory = VectorMemory(dimension=2)
        with pytest.raises(ContractViolationError):
            memory.store(MemoryRecord("x", (1.0,), "r", 0, 1))
        with pytest.raises(ContractViolationError):
            memory.query((1.0, 2.0, 3.0))

    def test_null_vector_similarity_zero(self) -> None:
        assert cosine_similarity((0.0, 0.0), (1.0, 1.0)) == 0.0

    def test_deterministic_tie_break(self) -> None:
        memory = VectorMemory(dimension=2)
        memory.store(MemoryRecord("z", (1.0, 0.0), "r", 0, 1))
        memory.store(MemoryRecord("a", (1.0, 0.0), "r", 0, 1))
        results = memory.query((1.0, 0.0), top_k=2)
        assert [rid for rid, _ in results] == ["a", "z"]
