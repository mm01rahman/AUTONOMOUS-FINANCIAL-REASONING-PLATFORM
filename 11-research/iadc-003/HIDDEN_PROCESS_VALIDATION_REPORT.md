# Hidden Process Validation Report

**Campaign:** IADC-003  
**Deterministic run timestamp:** 2026-08-03T10:55:08Z  
**Scientific status:** observational; causal confidence is null

Outcome: **MIXED_STRUCTURE_FORWARD_UNSUPPORTED**. Validation covers chronological loadings, recurrence, sensitivity, matching, regimes, failures, and walk-forward behavior.

## Walk-forward comparison

| Mode | Model | Mean OOS R² | Positive folds | Direction accuracy |
|---|---|---:|---:|---:|
| Contemporaneous | latent factors | 0.01139999 | 1 | 0.51644305 |
| Contemporaneous | isolated benchmark | 0.00490654 | 2 | 0.51074417 |
| Forward 5-session | latent factors | -0.01069032 | 0 | 0.52001611 |
| Forward 5-session | isolated benchmark | -0.00751485 | 0 | 0.54505956 |

BH-significant signed-process edges at 5%: **0**.
Process-edge tests are retrospective descriptive subsequent-outcome associations, not OOS/predictive alpha evidence.
BH-significant cross-process transition edges: **0**; supported overlaps: **2**.
Contemporaneous comparison: **UNRESOLVED_HIGHER_MEAN_LOWER_FOLD_CONSISTENCY**; latent mean R² is higher but positive-R² folds are 1 versus 2.
Primary rank/columns: **18/18**; covariance condition number: **8031.99285332**.
