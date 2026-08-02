# Feature Stability Report

| Feature | Approved Regimes | Bootstrap | Corr Stability | Drift | Robust Regimes |
| --- | --- | --- | --- | --- | --- |
| regime_return_60 | ['bull_trend', 'calm_carry'] | 0.9479 | 0.1268 | 0.1330 | 6 |
| xau_return_20 | ['bull_trend', 'bear_unwind'] | 0.9583 | 0.1089 | 0.1430 | 6 |
| breakdown_20 | ['bull_trend', 'crisis_dislocation'] | 0.8646 | 0.1164 | 0.2207 | 5 |
| forward_expectation | ['bull_trend', 'range_compression'] | 0.8854 | 0.1464 | 0.3296 | 5 |
| regime_vol_20 | ['bear_unwind', 'calm_carry', 'range_compression'] | 0.8385 | 0.1556 | 0.3984 | 4 |
| trend_gap_30_180 | ['bear_unwind'] | 0.8021 | 0.1398 | 0.3113 | 5 |
| macro_trend_interaction | ['calm_carry', 'range_compression'] | 0.9635 | 0.1429 | 0.2276 | 5 |
| breakout_60 | ['crisis_dislocation'] | 0.7604 | 0.0914 | 0.1882 | 5 |
| trend_gap_20_120 | ['crisis_dislocation'] | 0.8438 | 0.1274 | 0.1861 | 5 |
| xau_return_1 | ['macro_transition'] | 0.7552 | 0.0698 | 0.0753 | 5 |
| trend_breakout_interaction | ['macro_transition'] | 0.7969 | 0.1389 | 0.2585 | 5 |
| sessionless_event_pressure | ['macro_transition'] | 0.9635 | 0.1174 | 0.1919 | 5 |
