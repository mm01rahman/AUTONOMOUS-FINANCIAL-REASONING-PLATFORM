# Mechanism Change Proposal: decision_cascade
## Discovery Cycle 3 Phase 5

### Feature Redesign
| Feature | Proposed Replacement | Failure Mode |
| --- | --- | --- |
| cascade_initiator_proxy | Dual-proxy approach: (1) large-order-flow imbalance proxy from DXY momentum dive | Ecology-proxy leakage; high sensitivity; non-stationary post |
| cascade_depth_estimator | Intra-day volatility clustering score as cascade amplification proxy (available  | Ecology model not validated; proxy is circular with initiato |

### Proxy Replacements
| Current Proxy | Proposed Proxy | Rationale |
| --- | --- | --- |
| decision_ecology_score | dxy_momentum_divergence × yield_inversion_speed | Order-flow-based proxies are not contingent on unvalidated ecology model. Litera |
| participant_count_proxy | vol_clustering_score (intra-day GARCH-derived) | Volatility clustering is an observable footprint of sequential institutional ord |

### Remaining Plausible Causal Mechanisms
- Large institutional actor initiates position; order flow imbalance creates directional pressure that forces constrained actors to adjust: causally plausible.
- Cascade amplification through dealer inventory stress: consistent with liquidity evidence from Program D/E.
