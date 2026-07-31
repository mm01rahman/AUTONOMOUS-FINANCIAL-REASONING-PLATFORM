# Layer 2 Microstructure Agent (WP-RT-1007)

`L2-MIC` maps short-horizon return and volatility features into deterministic
microstructure-domain beliefs (`CIO-03`).

## Signal mapping

- Inputs: `FEATURE_LOG_RETURN`, `FEATURE_EWM_VOL`
- Volatility-normalized positive return maps to `BULL`.
- Volatility-normalized negative return maps to `BEAR`.
- Weak directional signal preserves `RANGE` mass.
- `THETA` retains explicit uncertainty budget.

## Determinism and degradation

- Rule output is deterministic for fixed feature values.
- Missing or low-quality required features degrade to vacuous `m(THETA)=1` via
  shared base-agent behavior.
