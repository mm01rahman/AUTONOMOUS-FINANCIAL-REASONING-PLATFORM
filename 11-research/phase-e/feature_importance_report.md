# Phase E Feature Importance Report

| Feature | MI | Corr Mean | Corr Stability | Drift | Redundancy | Permutation | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| macro_pressure | 0.0009 | -0.0368 | 0.1161 | 0.0281 | 0.9899 | 0.4390 | redundant |
| regime_vol_20 | 0.0013 | -0.0407 | 0.1052 | 0.4186 | 0.4422 | 0.4300 | useful |
| micro_momentum | 0.0006 | -0.0112 | 0.0584 | 0.0213 | 0.9210 | 0.1263 | redundant |
| forward_expectation | 0.0005 | -0.0461 | 0.1118 | 0.1695 | 1.0000 | 0.0516 | redundant |
| xau_return_1 | 0.0002 | -0.0157 | 0.0626 | 0.0130 | 0.9210 | 0.0219 | redundant |
| regime_return_60 | 0.0009 | -0.1537 | 0.1019 | 0.0747 | 0.8538 | 0.0076 | useless |
| xau_return_5 | 0.0005 | -0.0494 | 0.1135 | 0.0285 | 0.7333 | 0.0000 | useless |
| xau_return_20 | 0.0019 | -0.1060 | 0.0953 | 0.0587 | 0.7930 | 0.0000 | useless |
| trend_gap_20_120 | 0.0007 | -0.1669 | 0.1044 | 0.1283 | 0.9617 | 0.0000 | useless |
| range_pct | 0.0009 | -0.0273 | 0.0948 | 0.0033 | 0.7087 | 0.0000 | useless |
| range_zscore_20 | 0.0009 | -0.0133 | 0.0856 | 0.0172 | 0.7087 | 0.0000 | useless |
| zscore_60 | 0.0014 | -0.0839 | 0.0833 | 0.1211 | 0.8130 | 0.0000 | useless |
| breakout_60 | 0.0014 | -0.0993 | 0.1091 | 0.1559 | 0.8130 | 0.0000 | useless |
| breakdown_20 | 0.0003 | -0.0753 | 0.0934 | 0.2455 | 0.7930 | 0.0000 | useless |
| dxy_return_1 | 0.0005 | -0.0051 | 0.0656 | 0.0375 | 0.4480 | 0.0000 | useless |

Useless / redundant / unstable features were tagged explicitly in `feature_importance.json`.
