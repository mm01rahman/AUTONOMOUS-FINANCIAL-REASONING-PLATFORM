# Mechanism Change Proposal: safe_haven_migration
## Discovery Cycle 3 Phase 5

### Feature Redesign
| Feature | Proposed Replacement | Failure Mode |
| --- | --- | --- |
| safe_haven_trigger | Regime-conditional stress index: VIX regime × DXY regime × yield-spread regime → | Non-stationary; concept drift confirmed post-2020. |
| safe_haven_persistence | Regime-exit signal: exits safe-haven position when ecology stress score drops be | Over-stay confirmed in stability_analysis; rolling performan |

### Proxy Replacements
| Current Proxy | Proposed Proxy | Rationale |
| --- | --- | --- |
| stress_topology (graph-derived, single-path) | composite_stress_index (VIX × yield_spread × DXY_momentum) | Composite multi-channel stress index is less susceptible to topology disruption  |

### Remaining Plausible Causal Mechanisms
- Systemic stress → institutional safe-haven demand → gold allocation increase: core causal chain remains intact in crisis_dislocation evidence.
- ETF investor coordination with institutional safe-haven mandate: DC2 Decision Ecology supports this cascade.
- Safe-haven activation precedes price impact: lead-lag structure confirmed in historical replay (4/6 episodes).
