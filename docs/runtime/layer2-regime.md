# Layer 2 Regime Agent (WP-RT-1009)

`L2-REG` classifies volatility regime and emits deterministic regime-domain
belief masses (`CIO-03`).

## Signal mapping

- Input: `FEATURE_EWM_VOL`
- Low volatility favors `RANGE` mass.
- High volatility shifts mass toward `BULL|BEAR` (trend likely, direction
  unresolved by this agent).
- Fixed uncertainty floor remains in `THETA`.

## Determinism and degradation

- Rule mapping is deterministic for fixed volatility inputs.
- Missing or low-quality telemetry degrades to vacuous `m(THETA)=1` via shared
  `BeliefAgent` behavior.
