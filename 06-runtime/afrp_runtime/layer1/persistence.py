"""L1-RDB — relational persistence (SLS-100, WP-IMP-0015).

Append-only SQLite ledger for observations, orders, and fills. Synchronous
commits support the RPO = 0 posture (NFR-005); replay queries by sequence
range support FIT-008 deterministic replay.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind, RawObservation
from afrp_runtime.contracts.envelope import Envelope

_SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    ingest_sequence INTEGER PRIMARY KEY,
    message_id TEXT NOT NULL,
    instrument TEXT NOT NULL,
    kind INTEGER NOT NULL,
    price REAL NOT NULL,
    bid REAL NOT NULL,
    ask REAL NOT NULL,
    size REAL NOT NULL,
    venue TEXT NOT NULL,
    event_at_ns INTEGER NOT NULL,
    trace_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_events (
    rowid_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    event TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    at_ns INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obs_instrument ON observations (instrument);
CREATE INDEX IF NOT EXISTS idx_order_events ON order_events (order_id);
"""


@dataclass(frozen=True)
class StoredObservation:
    """Replay row rehydrated from the ledger."""

    ingest_sequence: int
    message_id: str
    instrument: str
    kind: ObservationKind
    price: float
    bid: float
    ask: float
    size: float
    venue: str
    event_at_ns: int
    trace_id: str


class RelationalStore:
    """Synchronous-commit append-only ledger."""

    def __init__(self, path: Path | str = ":memory:") -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")  # RPO = 0 (NFR-005)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

    def append_observation(self, observation: RawObservation) -> None:
        """Persist one CIO-01; sequence collisions are contract violations.

        Raises:
            ContractViolationError: duplicate ingest_sequence.
        """
        try:
            self._conn.execute(
                "INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    observation.ingest_sequence,
                    observation.envelope.message_id,
                    observation.instrument,
                    int(observation.kind),
                    observation.price,
                    observation.bid,
                    observation.ask,
                    observation.size,
                    observation.venue,
                    observation.event_at_ns,
                    observation.envelope.trace_id,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ContractViolationError(
                "CIO-01", f"duplicate ingest_sequence {observation.ingest_sequence}"
            ) from exc
        self._conn.commit()

    def append_order_event(
        self, order_id: str, event: str, quantity: float, price: float, at_ns: int
    ) -> None:
        """Persist one order lifecycle event (NFR-007 audit trail source)."""
        self._conn.execute(
            "INSERT INTO order_events (order_id, event, quantity, price, at_ns) "
            "VALUES (?,?,?,?,?)",
            (order_id, event, quantity, price, at_ns),
        )
        self._conn.commit()

    def replay(
        self, first_sequence: int, last_sequence: int
    ) -> list[StoredObservation]:
        """Observations in ``[first_sequence, last_sequence]`` in ledger order."""
        rows = self._conn.execute(
            "SELECT * FROM observations WHERE ingest_sequence BETWEEN ? AND ? "
            "ORDER BY ingest_sequence",
            (first_sequence, last_sequence),
        ).fetchall()
        return [
            StoredObservation(
                ingest_sequence=row[0],
                message_id=row[1],
                instrument=row[2],
                kind=ObservationKind(row[3]),
                price=row[4],
                bid=row[5],
                ask=row[6],
                size=row[7],
                venue=row[8],
                event_at_ns=row[9],
                trace_id=row[10],
            )
            for row in rows
        ]

    def order_history(self, order_id: str) -> list[tuple[str, float, float, int]]:
        """(event, quantity, price, at_ns) tuples for ``order_id`` in order."""
        rows = self._conn.execute(
            "SELECT event, quantity, price, at_ns FROM order_events "
            "WHERE order_id = ? ORDER BY rowid_seq",
            (order_id,),
        ).fetchall()
        return [(row[0], row[1], row[2], row[3]) for row in rows]

    def observation_count(self) -> int:
        """Total persisted observations."""
        row = self._conn.execute("SELECT COUNT(*) FROM observations").fetchone()
        return int(row[0])


def rehydrate_envelope(stored: StoredObservation, mission_profile_id: str) -> Envelope:
    """Reconstruct a minimal replay envelope from a stored row (FIT-008)."""
    return Envelope(
        message_id=stored.message_id,
        cognitive_cycle_id="replay",
        producer_subsystem_id="L1-RDB",
        schema_version=1,
        semantic_version=1,
        generated_at_ns=stored.event_at_ns,
        mission_profile_id=mission_profile_id,
        parent_cio_ids=(),
        payload_hash=b"",
        trace_id=stored.trace_id,
        span_id="replay",
    )
