# Layer 1 Feature Store (WP-RT-1002)

`L1-FST` transforms `CIO-01` `RawObservation` events into deterministic,
immutable `CIO-02` feature emissions.

## Inputs and outputs

- Input: `RawObservation` from `L1-ING` (`QUOTE`, `TRADE`, optional ORACLE/MACRO passthrough).
- Output: `StandardFeature` envelopes keyed by:
  - `feature_id`
  - `instrument`
  - `source_sequence`

## Deterministic feature set

- `FEATURE_MID`
  - From quote midpoint or trade price.
- `FEATURE_SPREAD_BPS`
  - From quote spread normalized to basis points.
- `FEATURE_LOG_RETURN`
  - Log return against oldest retained price in the active window.
- `FEATURE_EWM_VOL`
  - Exponentially weighted volatility from step returns.

## Guarantees

- Immutable cache semantics by `(feature_id, instrument, source_sequence)`.
- Provenance chaining to parent CIO-01 envelope IDs.
- Deterministic window eviction by `window_seconds`.
- Idempotent replay behavior for previously processed observations.
