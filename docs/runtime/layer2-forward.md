# Layer 2 Forward/Expectations Agent (WP-RT-1010)

`L2-FOR` maps forward-curve slope and reference price context to a deterministic
domain belief (`CIO-03`).

## Signal mapping

- Inputs: `FEATURE_FORWARD_SLOPE`, `FEATURE_MID`
- Positive slope maps to `BULL` conviction.
- Negative slope maps to `BEAR` conviction.
- Residual mass remains in `THETA`.

## Determinism and degradation

- Conviction is bounded and deterministic for fixed feature values.
- Missing or low-quality required features degrade to vacuous `m(THETA)=1` via
  shared `BeliefAgent` behavior.
