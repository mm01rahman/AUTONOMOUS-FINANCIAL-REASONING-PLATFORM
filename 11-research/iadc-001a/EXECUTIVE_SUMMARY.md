# IADC-001A Executive Summary

AFRP re-analyzed all **22** retained IADC-001 associations, grouped them into
**5** dependency clusters, and classified all **1,058** rejected
hypotheses. The result is an evidence-quality map, not a causal or trading-alpha claim.

**AFRP has repeatable but weak-to-moderate observational knowledge concentrated in USD, nominal-yield, and curve relationships. Scientific maturity is capped by dependent variants, absent multi-provider replication, and major expectation, flow, positioning, event, and causal-identification gaps.**

## Ranked observational relationships

| Rank | Observation | Driver | Regime | Lag | Horizon | Fold repeatability | Confidence | Maturity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | IADC-OBS-001A-016 | yield_10y_change_5 | policy_easing | 20 | 5 | 1.0000 | 0.7638 | REPEATABLE_OBSERVATION |
| 2 | IADC-OBS-001A-017 | yield_10y_change_5 | market_stress | 20 | 5 | 0.8333 | 0.7508 | REPEATABLE_OBSERVATION |
| 3 | IADC-OBS-001A-014 | yield_10y_change_5 | market_stress | 20 | 1 | 0.8333 | 0.7444 | REPEATABLE_OBSERVATION |
| 4 | IADC-OBS-001A-008 | yield_10y_change_1 | market_stress | 20 | 5 | 0.8333 | 0.7327 | REPEATABLE_OBSERVATION |
| 5 | IADC-OBS-001A-003 | dxy_return_1 | market_stress | 0 | 1 | 1.0000 | 0.7265 | REPEATABLE_OBSERVATION |
| 6 | IADC-OBS-001A-002 | dxy_return_1 | usd_strength | 0 | 1 | 1.0000 | 0.7117 | REPEATABLE_OBSERVATION |
| 7 | IADC-OBS-001A-004 | dxy_return_1 | gold_bull | 10 | 1 | 1.0000 | 0.7054 | REPEATABLE_OBSERVATION |
| 8 | IADC-OBS-001A-015 | yield_10y_change_5 | all | 20 | 5 | 0.8333 | 0.6920 | REPEATABLE_OBSERVATION |
| 9 | IADC-OBS-001A-001 | dxy_return_1 | all | 0 | 1 | 1.0000 | 0.6902 | REPEATABLE_OBSERVATION |
| 10 | IADC-OBS-001A-011 | yield_10y_change_5 | gold_bear | 1 | 5 | 0.8333 | 0.6812 | REPEATABLE_OBSERVATION |
| 11 | IADC-OBS-001A-013 | yield_10y_change_5 | gold_bear | 5 | 20 | 1.0000 | 0.6769 | REPEATABLE_OBSERVATION |
| 12 | IADC-OBS-001A-005 | yield_10y_change_1 | all | 0 | 1 | 0.8333 | 0.6743 | REPEATABLE_OBSERVATION |
| 13 | IADC-OBS-001A-021 | curve_change_5 | all | 10 | 5 | 0.8333 | 0.6613 | REPEATABLE_OBSERVATION |
| 14 | IADC-OBS-001A-006 | yield_10y_change_1 | policy_easing | 0 | 1 | 0.6667 | 0.6449 | CONDITIONAL_OBSERVATION |
| 15 | IADC-OBS-001A-009 | yield_10y_change_5 | gold_bear | 0 | 5 | 0.6667 | 0.6433 | CONDITIONAL_OBSERVATION |
| 16 | IADC-OBS-001A-012 | yield_10y_change_5 | gold_bear | 5 | 1 | 0.6667 | 0.6416 | CONDITIONAL_OBSERVATION |
| 17 | IADC-OBS-001A-022 | curve_change_5 | gold_bull | 10 | 5 | 0.8333 | 0.6372 | REPEATABLE_OBSERVATION |
| 18 | IADC-OBS-001A-018 | yield_10y_change_20 | gold_bear | 0 | 5 | 0.6667 | 0.6337 | CONDITIONAL_OBSERVATION |
| 19 | IADC-OBS-001A-020 | yield_10y_change_20 | gold_bear | 1 | 5 | 0.6667 | 0.6215 | CONDITIONAL_OBSERVATION |
| 20 | IADC-OBS-001A-007 | yield_10y_change_1 | policy_easing | 1 | 1 | 0.6667 | 0.6061 | CONDITIONAL_OBSERVATION |
| 21 | IADC-OBS-001A-019 | yield_10y_change_20 | gold_bear | 1 | 1 | 0.6667 | 0.5953 | CONDITIONAL_OBSERVATION |
| 22 | IADC-OBS-001A-010 | yield_10y_change_5 | usd_strength | 0 | 5 | 0.6667 | 0.5942 | CONDITIONAL_OBSERVATION |

## Failure classification

| Failure class | Count | Share |
| --- | --- | --- |
| EVIDENCE_SUPPORTS_NULL_OR_NEGLIGIBLE_EFFECT | 513 | 0.4849 |
| TEMPORAL_COVERAGE_INSUFFICIENT | 206 | 0.1947 |
| OBSERVABILITY_INSUFFICIENT | 135 | 0.1276 |
| MULTIPLE_TESTING_OR_EFFECT_GATE_FAILURE | 128 | 0.1210 |
| TEMPORAL_INSTABILITY | 49 | 0.0463 |
| REPEATABILITY_OR_PLACEBO_FAILURE | 27 | 0.0255 |

## Highest-return research gaps

| Rank | Gap | Information gain | Cost | Return score | Recommended dataset |
| --- | --- | --- | --- | --- | --- |
| 1 | Historical real yields and breakevens | 0.9000 | LOW | 90.0000 | FRED DGS10, DFII10, T10YIE |
| 2 | Multi-cycle CFTC positioning | 0.8800 | LOW | 88.0000 | CFTC disaggregated COMEX gold history |
| 3 | Multi-cycle ETF holdings and flows | 0.8600 | LOW | 86.0000 | GLD/IAU shares, NAV, creation-redemption history |
| 4 | Cross-asset risk observatory | 0.7800 | LOW | 78.0000 | VIX, GVZ, EURUSD, USDJPY, silver, oil, equities |
| 5 | Macro release actual/consensus/vintage history | 0.9200 | MEDIUM | 46.0000 | ALFRED/FRED plus consensus archive |
| 6 | Identified causal designs | 0.9700 | HIGH | 32.3333 | Policy instruments, natural experiments, and vintage controls |
| 7 | FOMC and rate-expectation history | 0.9500 | HIGH | 31.6667 | Fed Funds and SOFR futures with event timestamps |
| 8 | Intraday event sequencing | 0.9400 | VERY_HIGH | 23.5000 | Timestamped gold, DXY, rates, spreads and event tape |
