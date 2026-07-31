"""WP-RT-1003 unit tests for Layer 1 relational persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.layer1.ingest import RawEvent, TickIngestor
from afrp_runtime.layer1.persistence import RelationalStore, rehydrate_envelope

NS = 1_000_000_000


def trade(ts_s: int, price: float, size: float = 1.0) -> RawEvent:
    return {
        "instrument": "XAUUSD",
        "kind": "TRADE",
        "price": price,
        "size": size,
        "event_at_ns": ts_s * NS,
        "venue": "SIM",
    }


def test_append_and_replay_round_trip(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path / "ledger.db")
    ingestor = TickIngestor("MP-04")
    for event in (trade(1, 2400.0), trade(2, 2401.0), trade(3, 2402.0)):
        store.append_observation(ingestor.ingest(event))
    rows = store.replay(1, 3)
    assert [row.ingest_sequence for row in rows] == [1, 2, 3]
    assert rows[1].price == pytest.approx(2401.0)
    assert store.observation_count() == 3
    store.close()


def test_duplicate_sequence_rejected(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path / "ledger.db")
    ingestor = TickIngestor("MP-04")
    observation = ingestor.ingest(trade(1, 2400.0))
    store.append_observation(observation)
    with pytest.raises(ContractViolationError, match="duplicate"):
        store.append_observation(observation)
    store.close()


def test_order_event_audit_trail_is_deterministic(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path / "ledger.db")
    store.append_order_event("ord-1", "SUBMITTED", 1.0, 2400.0, 1)
    store.append_order_event("ord-1", "FILLED", 1.0, 2400.5, 2)
    history = store.order_history("ord-1")
    assert [event for event, *_ in history] == ["SUBMITTED", "FILLED"]
    store.close()


def test_rehydrate_envelope_from_stored_row(tmp_path: Path) -> None:
    store = RelationalStore(tmp_path / "ledger.db")
    ingestor = TickIngestor("MP-04")
    observation = ingestor.ingest(trade(1, 2400.0))
    store.append_observation(observation)
    row = store.replay(1, 1)[0]
    envelope = rehydrate_envelope(row, "MP-04")
    assert envelope.message_id == observation.envelope.message_id
    assert envelope.trace_id == observation.envelope.trace_id
    assert envelope.producer_subsystem_id == "L1-RDB"
    store.close()
