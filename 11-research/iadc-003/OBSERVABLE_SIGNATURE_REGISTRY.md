# Observable Signature Registry

**Campaign:** IADC-003  
**Deterministic run timestamp:** 2026-08-03T10:55:08Z  
**Scientific status:** observational; causal confidence is null

The primary frame contains **18** nonredundant signatures under a conservative next-session availability convention over **4562** sessions. This does not prove point-in-time safety.

| Variable | Domain | Transformation | Source | Analysis-only |
|---|---|---|---|---|
| real_yield_10y_change | real_yields | difference_bp | IADC002-DFII10 | False |
| breakeven_5y_change | inflation_expectations | difference_bp | IADC002-T5YIE | False |
| breakeven_10y_change | inflation_expectations | difference_bp | IADC002-T10YIE | False |
| yield_2y_change | nominal_yields | difference_bp | IADC002-DGS2 | False |
| yield_10y_change | nominal_yields | difference_bp | IADC002-DGS10 | False |
| yield_30y_change | nominal_yields | difference_bp | IADC002-DGS30 | False |
| policy_rate_change | policy | difference_bp | IADC002-DFF | False |
| sofr_policy_spread_change | policy_liquidity | difference_bp | derived:SOFR-DFF | False |
| dxy_return | usd_fx | log_return | official:DXY-1D | False |
| eurusd_return | cross_asset_fx | log_return | IADC002-DEXUSEU | False |
| usdjpy_return | cross_asset_fx | log_return | IADC002-DEXJPUS | False |
| wti_return | commodity | log_return | IADC002-DCOILWTICO | False |
| vix_return | cross_asset_volatility | log_return | IADC002-VIXCLS | True |
| gvz_return | gold_volatility | log_return | IADC002-GVZCLS | True |
| gld_holdings_change | etf_positioning | log_return | IADC002-GLD-HISTORY | True |
| managed_money_share_change | institutional_positioning | difference | IADC002-CFTC-COMEX-GOLD | False |
| producer_share_change | institutional_positioning | difference | IADC002-CFTC-COMEX-GOLD | False |
| cftc_open_interest_change | market_liquidity_proxy | log_return | IADC002-CFTC-COMEX-GOLD | False |
