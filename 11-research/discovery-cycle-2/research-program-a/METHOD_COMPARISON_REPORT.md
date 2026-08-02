# Method Comparison Report

| Method | Decision | Rationale |
|---|---|---|
| Cross-correlation at lags | ACCEPT | Direct, interpretable; reveals timing of cross-market information transfer. |
| Transfer entropy proxy (MI at lags) | ACCEPT | Captures nonlinear information flow without model fitting infrastructure. |
| Granger causality proxy (OLS R²) | ACCEPT | Provides linear predictive improvement test; complements MI. |
| State-conditioned MI | ACCEPT | Regime-conditioned MI reveals whether information flow changes across the six states. |
| Dynamic Time Warping | DEFERRED | Requires additional tooling; not necessary at this stage of ecology mapping. |
| VAR (Vector Autoregression) | DEFERRED | Introduces multivariate model infrastructure; deferred to DC2 validation campaign. |
| Bayesian Networks | DEFERRED | Requires causal discovery library; reserved for DC2 Causal Alpha program. |
| Structural Causal Models | DEFERRED | Requires domain-specific causal graph specification; reserved for later research. |
| Temporal Graph Networks | DEFERRED | Requires deep learning infrastructure beyond the frozen stack. |
| Cointegration Tests | DEFERRED | Requires additional governed dataset series; deferred to validation. |
| Network Analysis / Graph Centrality | PARTIAL | Implemented via correlation matrix; full network analysis deferred until cross-asset series acquired. |

## Conclusion
Four methods were applied. Dynamic methods (VAR, Bayesian Networks, SCM) deferred until cross-asset datasets available.
