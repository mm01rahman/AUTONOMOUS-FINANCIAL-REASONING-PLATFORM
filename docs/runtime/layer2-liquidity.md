# Layer 2 Liquidity Agent (WP-RT-1008)

`L2-LIQ` maps spread stress into a deterministic liquidity-domain belief mass
assignment (`CIO-03`).

## Signal mapping

- Input: `FEATURE_SPREAD_BPS`
- Tight spreads increase `RANGE` support.
- Widening spreads increase uncertainty (`THETA`).
- A small `BULL|BEAR` union mass captures direction-agnostic trend openness.

## Determinism and degradation

- Spread-to-stress mapping is deterministic and bounded.
- Missing or low-quality inputs degrade to vacuous `m(THETA)=1` via shared base
  agent behavior.
