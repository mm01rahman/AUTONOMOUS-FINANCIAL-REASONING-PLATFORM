# Layer 1 Relational Persistence (WP-RT-1003)

`L1-RDB` provides deterministic relational durability for Layer 1 observations
and order lifecycle audit events.

## Persistence model

- Engine: SQLite with `journal_mode=WAL` and `synchronous=FULL`.
- Primary observation key: `ingest_sequence`.
- Order event trail: append-only `order_events` keyed by auto-increment row order.

## Guarantees

- Append and replay preserve sequence ordering.
- Duplicate `ingest_sequence` writes fail as explicit contract violations.
- Query paths (`replay`, `order_history`, `observation_count`) are deterministic.
- Replay envelope rehydration preserves message and trace identity for downstream FIT-008 flows.
