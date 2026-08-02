# Method Comparison Report

## Decision

Accepted methodology: **Institutional Six-State Overlay Taxonomy v1**

| Method | Executed | Determinism | Interpretability | Cost | Stability | Utility | Institutional Fit | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hidden Markov Models | False | 3 | 2 | 2 | 3 | 2 | 2 | REJECT |
| Gaussian Mixture Models | False | 3 | 2 | 3 | 2 | 2 | 2 | REJECT |
| Hierarchical Clustering | False | 4 | 3 | 3 | 3 | 3 | 3 | DEFER |
| Spectral Clustering | False | 3 | 2 | 2 | 2 | 2 | 2 | REJECT |
| Bayesian Change Point Detection | False | 4 | 4 | 3 | 3 | 3 | 4 | DEFER |
| Density-based Clustering | False | 4 | 2 | 3 | 2 | 2 | 2 | REJECT |
| Volatility-State Baseline | True | 5 | 5 | 5 | 5 | 2 | 4 | REJECT |
| Deterministic Macro-Event Overlay Taxonomy | True | 5 | 5 | 5 | 4 | 5 | 5 | ACCEPT |

## Accepted rationale

Institutional Six-State Overlay Taxonomy v1 improved return separation to
**0.004942**
versus **0.001211** for the volatility-only
baseline and **0.002401** for the trend/volatility
partition, while preserving **0.7801** transition stability.
