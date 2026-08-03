# Transition Engine Revision Plan
## Discovery Cycle 2 Program E Phase 1

| Step | Action | Component | Rationale |
| --- | --- | --- | --- |
| 1 | REMOVE | participant_ecology_layer | Institutional participant behavior proxies: geopolitical severity and safe-haven flow |
| 2 | REDESIGN | cross_asset_network_layer | Cross-asset information network: DXY momentum signals at 1d, 5d, 20d horizons |
| 3 | REDESIGN | interaction_layer | Trigger-type interaction logic: regime-specific signal inversion for volatility_decay |
| 4 | REDESIGN | liquidity_layer | Market liquidity and volatility: realized vol, breakout, breakdown signals |
| 5 | REDESIGN | regime_layer | Primary asset price momentum: XAU/USD return signals |
| 6 | INVESTIGATE | decision_ecology_layer | Institutional expectation formation: forward expectation signals |
| 7 | INVESTIGATE | macro_layer | Macroeconomic conditions: rates, FX levels, Fed surprise, yield curve |

### Summary
- **Components to retain**: none
- **Components to redesign**: cross_asset_network_layer, interaction_layer, liquidity_layer, regime_layer
- **Components to remove**: participant_ecology_layer
- **Components requiring evidence**: decision_ecology_layer, macro_layer

Expected benefit: Improved transition detection accuracy and reduced false-transition rate
