# Layer 1 Ingestion (WP-RT-1001)

`L1-ING` provides deterministic canonicalization from heterogeneous market
provider payloads into `CIO-01` `RawObservation` events.

## Supported provider payload classes

1. **Tick payloads** (`TickProviderAdapter`)
   - Input: `instrument`, `kind`, timestamp (`event_at_ns|ms|s`), optional
     `price`, `size`, `bid`, `ask`, `venue`.
   - Output: canonical raw tick event consumed by `TickIngestor`.
2. **OHLCV payloads** (`OhlcvProviderAdapter`)
   - Input: `instrument`, `open`, `high`, `low`, `close`, `volume`,
     timestamp (`event_at_ns|ms|s`), optional `venue`.
   - Output: canonical `TRADE` event using `close` as price and `volume` as size.

## Runtime interfaces

- `MarketDataProvider`: provider contract exposing `provider_id` and `normalize`.
- `MultiProviderIngestor`: coordinator for provider registration, payload ingest,
  normalization, and event emission.
- `TickIngestor`: canonical CIO-01 emitter with sequence monotonicity and gap
  accounting.

## Health and metrics

`IngestHealth` exposes:

- `provider_count`
- `events_ingested`
- `provider_errors`
- `gaps_detected`
- `ready`
- `last_error`

`MultiProviderIngestor.events_by_provider` returns deterministic per-provider
ingest counters.
