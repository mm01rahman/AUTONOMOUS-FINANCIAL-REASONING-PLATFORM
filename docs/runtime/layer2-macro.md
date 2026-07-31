# Layer 2 Macro Agent (WP-RT-1006)

`L2-MAC` maps real-yield and dollar dynamics into deterministic macro-domain
belief masses (`CIO-03`).

## Signal mapping

- Inputs: `FEATURE_REAL_YIELD`, `FEATURE_DXY_RETURN`
- Falling real yields and dollar weakness increase `BULL` mass.
- Rising real yields and dollar strength increase `BEAR` mass.
- Residual uncertainty remains in `THETA`.

## Determinism and degradation

- Logistic signal transforms and conviction blending are deterministic.
- Missing or low-quality inputs degrade to vacuous `m(THETA)=1` via the shared
  `BeliefAgent` path.
