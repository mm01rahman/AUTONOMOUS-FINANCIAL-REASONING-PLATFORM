# Layer 2 Behavioral Agent (WP-RT-1011)

`L2-BEH` converts positioning and sentiment into a contrarian DSmT belief mass
assignment (`CIO-03`).

## Signal mapping

- Inputs: `FEATURE_SENTIMENT`
- Positive crowd sentiment pushes contrarian `BEAR` mass.
- Negative crowd sentiment pushes contrarian `BULL` mass.
- Mid sentiment allocates paradoxical `BULL&BEAR` mass.
- Residual uncertainty is assigned to `THETA`.

## Determinism and degradation

- Mapping is deterministic for identical inputs.
- Missing or low-quality telemetry degrades through the shared `BeliefAgent`
  path to vacuous mass `m(THETA)=1`.
