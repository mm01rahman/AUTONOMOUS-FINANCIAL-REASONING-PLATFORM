"""WP-RT-1003 integration tests for ingest->persistence round trip."""

from __future__ import annotations

from pathlib import Path

from afrp_runtime.layer1.ingest import (
    MultiProviderIngestor,
    RawPayload,
    TickProviderAdapter,
)
from afrp_runtime.layer1.persistence import RelationalStore


def test_end_to_end_ingest_persistence_replay(tmp_path: Path) -> None:
    db_path = Path(tmp_path) / "ledger.db"
    store = RelationalStore(db_path)
    coordinator = MultiProviderIngestor("MP-04", cognitive_cycle_id="persistence-cycle")
    coordinator.register_provider(TickProviderAdapter(provider_id="tick-a"))

    payloads: list[RawPayload] = [
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2400.0,
            "size": 1.0,
            "event_at_ns": 1_000,
            "venue": "SIM",
        },
        {
            "instrument": "XAUUSD",
            "kind": "TRADE",
            "price": 2401.0,
            "size": 0.8,
            "event_at_ns": 2_000,
            "venue": "SIM",
        },
    ]

    for payload in payloads:
        for observation in coordinator.ingest_payload("tick-a", payload):
            store.append_observation(observation)

    replayed = store.replay(1, 10)
    assert [row.ingest_sequence for row in replayed] == [1, 2]
    assert replayed[0].price == 2400.0
    assert replayed[1].price == 2401.0
    assert store.observation_count() == 2
    store.close()
