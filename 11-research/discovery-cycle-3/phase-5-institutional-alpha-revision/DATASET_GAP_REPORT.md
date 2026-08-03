# Dataset Gap Report
## Discovery Cycle 3 Phase 5

| Mechanism | Dataset Gap | Impact | Priority |
| --- | --- | --- | --- |
| safe_haven_migration | VIX daily series | Required for composite_stress_index; currently absent from standard dataset. | HIGH |
| safe_haven_migration | TED spread daily series | Systemic liquidity stress proxy; required for multi-channel composite index. | HIGH |
| safe_haven_migration | Gold ETF flow proxy (GLD shares outstanding) | Institutional demand proxy currently missing; needed to validate activation casc | MEDIUM |
| safe_haven_migration | CHF, JPY, Treasury safe-haven series | Required to control for competing safe-haven destinations; currently absent. | MEDIUM |
| decision_cascade | Intra-day order flow imbalance proxy | Required for proposed cascade-initiator replacement proxy. | HIGH |
| decision_cascade | Options market pressure proxy (GVZ or similar) | Optionality pressure indicator for cascade initiation signal. | HIGH |
| decision_cascade | Regime-specific XAU/USD micro-structure data | Decision cascade hypothesis requires micro-structure evidence to validate. | MEDIUM |
