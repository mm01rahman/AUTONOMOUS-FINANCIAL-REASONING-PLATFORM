# Revision Report: safe_haven_migration
## Discovery Cycle 3 Phase 5

**Alpha ID**: IKROS-ALPHA-DC3-20260802-0006
**Family**: FAM-003
**Phase 4 Outcome**: RESEARCH
**ARB Decision**: READY_FOR_REVALIDATION
**ARB Rationale**: Core economic mechanism remains scientifically plausible. Identified failures are addressable through trigger redesign and dataset expansion. Mechanism is not rejected — revalidation is warranted after composite trigger implementation.

### Failed Assumptions
| Assumption | Revision Action | Priority |
| --- | --- | --- |
| Safe-haven trigger is stable across all post-2010 regimes. | REDESIGN_TRIGGER | HIGH |
| Static trigger threshold remains valid under all volatility environments. | REPLACE_WITH_REGIME_CONDITIONAL_THRESHOLD | HIGH |
| White's Reality Check and SPA test will confirm edge over benchmark ensemble. | EXPAND_DATASET_AND_RETEST | MEDIUM |

### Supported Assumptions
- Safe-haven demand activation during systemic stress events is economically plausible and consistent with DC2 ecology model.
- Directional signal during crisis_dislocation and bull_trend regimes maintains moderate accuracy (walk-forward PASS, historical replay 4/6 episodes).
- PBO P(overfitting) = 0.32 confirms mechanism is not simply a backtest artefact.
- Probabilistic SR > 0.5 in 58% of bootstrap trials — positive tail exists.
