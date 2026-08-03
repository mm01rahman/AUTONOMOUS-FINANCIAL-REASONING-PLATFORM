# Mechanism Validation Report
## IKROS-ALPHA-DC3-20260802-0009 — decision_cascade

**Outcome**: RESEARCH
**Confidence prior**: 0.59 → **posterior**: 0.4351 (DECREASE)
**Rationale**: Critical statistical tests failed (3/3 critical failures). Mechanism requires additional evidence before promotion consideration.

### Statistical Methods
| Method | Status | Score | Note |
| --- | --- | --- | --- |
| walk_forward_validation | PASS | 0.5300 | WF detects cascade patterns with moderate accuracy. False cascade rate elevated. |
| nested_walk_forward | WARN | 0.4700 | Nested WF shows degradation in calm-carry regimes where cascades are absent. |
| combinatorial_purged_cross_validation | WARN | 0.4400 | CPCV performance below safe-haven family; ecology-proxy leakage suspected. |
| monte_carlo | WARN | 0.4800 | Monte Carlo distribution narrow positive; partially explained by noise sensitivity. |
| bootstrap | PASS | 0.5100 | Bootstrap CI overlaps zero at 90th percentile. Statistically weak. |
| sensitivity_analysis | FAIL | 0.3800 | High sensitivity to cascade-initiator threshold. Results inversion under ±15% shift. |
| stress_testing | WARN | 0.4300 | Stress robustness inadequate; pattern absent in COVID and banking-crisis sub-samples. |
| historical_replay | WARN | 0.4600 | Historical replay: 3/7 decision-cascade episodes identified correctly. |
| out_of_sample_validation | WARN | 0.4700 | OOS accuracy marginally above random; very narrow edge. |
| probability_of_backtest_overfitting | WARN | 0.4900 | PBO: P(overfitting) = 0.45. Elevated concern for decision-cascade proxy. |
| deflated_sharpe_ratio | FAIL | 0.3700 | Deflated SR effectively zero after multiple-comparison adjustment. |
| probabilistic_sharpe_ratio | WARN | 0.4600 | PSR > 0.5 in only 44% of bootstrap trials. |
| whites_reality_check | FAIL | 0.3600 | White's RC: mechanism does not survive multiple-hypothesis correction (p=0.18). |
| spa_test | FAIL | 0.3500 | SPA test p-value = 0.21. Mechanism not superior to benchmark ensemble. |
| concept_drift_detection | FAIL | 0.3400 | Significant concept drift detected post-2019. Cascade patterns not stable. |
| stability_analysis | WARN | 0.4400 | Rolling stability marginal; mechanism strength highly period-dependent. |
| failure_replay | WARN | 0.4300 | Failure replay: cascade aborts account for majority of signal losses. |

### Known Failure Modes
- Confidence calibration is weak under transition-risk scoring.
- Robustness under stress/event subsets is weaker than at least one simpler baseline.
