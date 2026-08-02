# Expected Validation Matrix

| ID | Expected Horizon | Regime Scope | Validation Plan |
| --- | --- | --- | --- |
| IKROS-HYP-20260802-0401 | 5D | bull_trend | walk_forward validation inside bull_trend windows; CPCV with regime-preserving folds; Monte Carlo path reshuffling conditioned on bull_trend membership; sensitivity to expectation-shock sign changes |
| IKROS-HYP-20260802-0404 | 5D | crisis_dislocation | event-window walk_forward validation around crisis episodes; bootstrap conditioned on crisis subtypes; Monte Carlo sequencing of crisis event order; stress testing versus immediate post-event reversals |
| IKROS-HYP-20260802-0405 | 1-5D | macro_transition | event-synchronous walk_forward splits; CPCV around clustered macro-event windows; sensitivity to shock sign and immediate reversal risk; Monte Carlo resampling of event sequences |
| IKROS-HYP-20260802-0402 | 5D | bear_unwind | walk_forward validation restricted to bear_unwind segments; CPCV across non-overlapping unwind episodes; stress testing around major macro announcements and shock dates; sensitivity to volatility deceleration |
| IKROS-HYP-20260802-0408 | 5-15D | macro_transition, bull_trend | state-transition walk_forward validation; CPCV preserving transition-to-bull handoff sequences; sensitivity to the duration of the handoff window; Monte Carlo over transition ordering |
| IKROS-HYP-20260802-0407 | 5-10D | bear_unwind, crisis_dislocation | episode-based walk_forward validation around extreme selloffs; Monte Carlo sequencing of stress and rebound episodes; stress testing against extended liquidation paths; sensitivity to rebound timing lag |
| IKROS-HYP-20260802-0403 | 5-10D | calm_carry | walk_forward tests on calm_carry windows; bootstrap around low-volatility subsamples; sensitivity to transition breakpoints into macro_transition; capacity and turnover diagnostics deferred to later campaigns |
| IKROS-HYP-20260802-0406 | 3-5D | range_compression | walk_forward validation on compression windows only; sensitivity to breakout false-positive detection; bootstrap on low-volatility subsamples; transition audit into macro_transition and bull_trend states |
