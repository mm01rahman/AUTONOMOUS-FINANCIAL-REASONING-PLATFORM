# Feature Revision Plan
## Discovery Cycle 3 Phase 5

| Alpha ID | Feature | Proposed Replacement | New Data Required |
| --- | --- | --- | --- |
| IKROS-ALPHA-DC3-20260802-0006 | safe_haven_trigger | Regime-conditional stress index: VIX regime × DXY regime × y | ['VIX', 'TED_spread'] |
| IKROS-ALPHA-DC3-20260802-0006 | safe_haven_persistence | Regime-exit signal: exits safe-haven position when ecology s | [] |
| IKROS-ALPHA-DC3-20260802-0009 | cascade_initiator_proxy | Dual-proxy approach: (1) large-order-flow imbalance proxy fr | ['options_data_proxy', 'order_flow_imbalance_proxy'] |
| IKROS-ALPHA-DC3-20260802-0009 | cascade_depth_estimator | Intra-day volatility clustering score as cascade amplificati | [] |
