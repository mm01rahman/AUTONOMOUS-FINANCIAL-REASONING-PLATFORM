# Redundancy Analysis

| Regime | Retained | Pruned | Abs Corr | Reason |
| --- | --- | --- | --- | --- |
| bull_trend | xau_return_20 | dxy_return_20 | 0.1084 | Forward expectation retained the cross-asset information with clearer economic interpretation. |
| bull_trend | regime_return_60 | trend_gap_20_120 | 0.8261 | Longer regime return anchor dominated the overlapping medium-horizon trend signal. |
| crisis_dislocation | breakout_60 | xau_return_5 | 0.3809 | Breakout expansion dominated short-horizon return echo during crisis states. |
| macro_transition | xau_return_1 | micro_momentum | 0.9400 | One-bar gold reaction subsumed standalone micro momentum during transitions. |
| range_compression | forward_expectation | dxy_return_20 | 1.0000 | Forward expectation captured the same cross-asset channel with cleaner semantics. |
