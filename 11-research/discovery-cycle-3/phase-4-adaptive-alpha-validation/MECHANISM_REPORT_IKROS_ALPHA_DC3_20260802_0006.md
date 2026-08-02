# Mechanism Validation Report
## IKROS-ALPHA-DC3-20260802-0006 — safe_haven_migration

**Outcome**: RESEARCH
**Confidence prior**: 0.6 → **posterior**: 0.5866 (DECREASE)
**Rationale**: Insufficient pass-rate. Additional research required before re-validation.

### Statistical Methods
| Method | Status | Score | Note |
| --- | --- | --- | --- |
| walk_forward_validation | PASS | 0.5800 | Walk-forward transitions detected at moderate accuracy. False-transition rate elevated under low-vol regimes. |
| nested_walk_forward | PASS | 0.5400 | Nested WF confirms modest consistency. Regime-boundary degradation observed. |
| combinatorial_purged_cross_validation | WARN | 0.4900 | CPCV reveals mild information leakage across safe-haven event windows. |
| monte_carlo | PASS | 0.5500 | Monte Carlo distribution non-trivially above random baseline. |
| bootstrap | PASS | 0.5300 | Bootstrap confidence intervals stable; lower tail elevated. |
| sensitivity_analysis | WARN | 0.4700 | Trigger-threshold sensitivity moderate; results degrade under ±20% parameter shift. |
| stress_testing | WARN | 0.4600 | Stress robustness reduced at COVID, Flash Crash, and banking-crisis subsets. |
| historical_replay | PASS | 0.5600 | Historical replay finds 4/6 expected safe-haven episodes captured. |
| out_of_sample_validation | PASS | 0.5200 | OOS holdout: directional accuracy slightly above baseline. |
| probability_of_backtest_overfitting | PASS | 0.6100 | PBO: P(overfitting) = 0.32. Below concern threshold. |
| deflated_sharpe_ratio | WARN | 0.4800 | Deflated SR positive but only marginally significant across all trials. |
| probabilistic_sharpe_ratio | PASS | 0.5400 | PSR > 0.5 in 58% of bootstrap trials. |
| whites_reality_check | WARN | 0.4700 | White's RC p-value marginal at 0.09. Borderline significance. |
| spa_test | WARN | 0.4600 | SPA p-value = 0.11. Cannot confirm alpha survives multiple-hypothesis correction. |
| concept_drift_detection | WARN | 0.4400 | Concept drift detected in post-2020 period; mechanism persistence uncertain. |
| stability_analysis | PASS | 0.5300 | Rolling performance stable within crisis sub-regimes; choppy inter-regime. |
| failure_replay | WARN | 0.4500 | Failure replay confirms over-sensitive trigger in FOMC windows. |

### Known Failure Modes
- Elevated false-transition rate indicates over-sensitive trigger assumptions.
- Robustness under stress/event subsets is weaker than at least one simpler baseline.
