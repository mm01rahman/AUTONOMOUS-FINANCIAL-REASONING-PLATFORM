"""Discovery Cycle 4: Institutional Market Observability & Data Expansion Program."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC4_DIR = Path("11-research") / "discovery-cycle-4" / "institutional-market-observability"

# ---------------------------------------------------------------------------
# Phase A: Observability Audit — state variables per alpha mechanism
# ---------------------------------------------------------------------------

# Each mechanism lists: required_vars, currently_observed, proxy_vars, unavailable_vars
_MECHANISM_OBSERVABILITY: dict[str, dict[str, Any]] = {
    "cross_asset_transition":  {"required": ["dxy_spot", "us_10y_yield", "real_yield_tip", "gold_spot", "cross_asset_topology_weight"], "observed": ["dxy_spot", "us_10y_yield", "gold_spot"], "proxies": ["cross_asset_topology_weight"], "unavailable": ["real_yield_tip_direct", "instantaneous_flow_data"], "family": "FAM-004"},
    "macro_repricing":         {"required": ["cpi_surprise", "fomc_rate_path", "us_10y_yield", "dxy_spot", "gold_spot", "fed_funds_futures"], "observed": ["us_10y_yield", "dxy_spot", "gold_spot"], "proxies": ["cpi_surprise_proxy_via_cpi_diff"], "unavailable": ["fed_funds_futures", "sofr_futures", "economic_surprise_index"], "family": "FAM-001"},
    "liquidity_withdrawal":    {"required": ["bid_ask_spread_proxy", "vix", "ted_spread", "fra_ois", "gold_volume", "market_depth"], "observed": ["gold_volume"], "proxies": ["vix_via_vol_features"], "unavailable": ["vix", "ted_spread", "fra_ois", "bid_ask_spread", "order_book_depth"], "family": "FAM-002"},
    "dealer_inventory":        {"required": ["comex_positioning", "cot_dealers", "gold_lease_rate", "gold_spot", "vol_surface"], "observed": ["gold_spot"], "proxies": ["cot_commercial_proxy"], "unavailable": ["comex_positioning_direct", "cot_dealers", "gold_lease_rate", "vol_surface"], "family": "FAM-002"},
    "expectation_reset":       {"required": ["fed_funds_futures", "sofr_futures", "breakeven_inflation", "fomc_meeting_prob", "economic_surprise_index"], "observed": [], "proxies": ["rate_diff_proxy"], "unavailable": ["fed_funds_futures", "sofr_futures", "breakeven_inflation", "economic_surprise_index"], "family": "FAM-005"},
    "safe_haven_migration":    {"required": ["vix", "ted_spread", "gld_etf_flows", "iau_etf_flows", "chf_usd", "jpy_usd", "us_treasury_flows", "geopolitical_risk_index"], "observed": ["chf_usd", "jpy_usd"], "proxies": ["stress_topology_proxy"], "unavailable": ["vix", "ted_spread", "gld_etf_flows", "iau_etf_flows", "geopolitical_risk_index"], "family": "FAM-003"},
    "etf_flow_propagation":    {"required": ["gld_shares_outstanding", "iau_shares_outstanding", "etf_nav_premium", "etf_creation_redemption"], "observed": [], "proxies": ["gold_price_momentum_as_flow_proxy"], "unavailable": ["gld_shares_outstanding", "iau_shares_outstanding", "etf_nav_premium", "etf_creation_redemption"], "family": "FAM-004"},
    "policy_repricing":        {"required": ["fomc_statement_embedding", "fed_funds_futures", "sofr_futures", "dot_plot_surprise", "cpi_actuals"], "observed": [], "proxies": ["rate_change_dummy"], "unavailable": ["fomc_statement_embedding", "fed_funds_futures", "sofr_futures", "dot_plot_surprise"], "family": "FAM-005"},
    "decision_cascade":        {"required": ["order_flow_imbalance", "volume_delta", "trade_aggressor_ratio", "dealer_gamma", "intraday_vol_clustering"], "observed": [], "proxies": ["decision_ecology_score_invalid"], "unavailable": ["order_flow_imbalance", "volume_delta", "trade_aggressor_ratio", "dealer_gamma"], "family": "FAM-006"},
    "information_cascade":     {"required": ["cross_asset_lagged_corr", "news_embedding_velocity", "macro_event_embedding", "directed_edge_weight"], "observed": ["cross_asset_lagged_corr"], "proxies": ["daily_corr_as_cascade_proxy"], "unavailable": ["news_embedding_velocity", "macro_event_embedding", "directed_edge_weight"], "family": "FAM-004"},
    "adaptive_ecology_shift":  {"required": ["cot_participant_mix", "etf_vs_futures_ratio", "dealer_net_position_change", "institutional_flow_direction"], "observed": [], "proxies": ["vol_regime_proxy"], "unavailable": ["cot_participant_mix", "etf_vs_futures_ratio", "dealer_net_position_change", "institutional_flow_direction"], "family": "FAM-007"},
    "regime_transition_chain": {"required": ["macro_regime_indicator", "vol_regime_indicator", "liquidity_regime_indicator", "flow_regime_indicator", "cross_asset_stress_composite"], "observed": ["macro_regime_indicator_proxy"], "proxies": ["price_momentum_regime"], "unavailable": ["vol_regime_indicator", "liquidity_regime_indicator", "flow_regime_indicator", "cross_asset_stress_composite"], "family": "FAM-007"},
}

# ---------------------------------------------------------------------------
# Phase B: Dataset Gap Catalogue
# ---------------------------------------------------------------------------

DATASET_CATALOGUE: list[dict[str, Any]] = [
    {"dataset_id": "DS-001", "name": "VIX Index", "economic_purpose": "Equity implied volatility; safe-haven activation gauge and liquidity stress indicator", "supported_families": ["FAM-002", "FAM-003", "FAM-007"], "update_frequency": "Real-time / Daily close", "resolution": "Daily", "historical_availability": "1990-present", "source": "CBOE / FRED", "licensing": "Free (FRED)", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-002", "name": "MOVE Index", "economic_purpose": "US Treasury implied volatility; rates uncertainty and gold safe-haven driver", "supported_families": ["FAM-001", "FAM-003", "FAM-005"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "1988-present", "source": "ICE BofA / Bloomberg", "licensing": "Commercial", "acquisition_difficulty": "MEDIUM", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-003", "name": "TED Spread", "economic_purpose": "Interbank credit risk; systemic stress and liquidity withdrawal proxy", "supported_families": ["FAM-002", "FAM-003"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "1986-present", "source": "FRED", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-004", "name": "FRA/OIS Spread", "economic_purpose": "Short-term dollar funding stress; direct liquidity stress indicator", "supported_families": ["FAM-002", "FAM-003"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2000-present", "source": "Bloomberg / ICE", "licensing": "Commercial", "acquisition_difficulty": "MEDIUM", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-005", "name": "SOFR Futures", "economic_purpose": "Market-implied rate path; policy repricing and expectation reset driver", "supported_families": ["FAM-001", "FAM-005"], "update_frequency": "Real-time / Daily", "resolution": "Daily", "historical_availability": "2018-present", "source": "CME", "licensing": "Commercial / Free delayed", "acquisition_difficulty": "MEDIUM", "maintenance_cost": "MEDIUM", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-006", "name": "Fed Funds Futures", "economic_purpose": "FOMC meeting probability; direct policy expectation proxy", "supported_families": ["FAM-001", "FAM-005"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "1988-present", "source": "CME", "licensing": "Commercial / Free delayed", "acquisition_difficulty": "MEDIUM", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-007", "name": "GLD ETF Shares Outstanding", "economic_purpose": "Institutional gold ETF demand flows; safe-haven and flow propagation signal", "supported_families": ["FAM-003", "FAM-004"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2004-present", "source": "SPDR / SEC filings / FRED", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-008", "name": "IAU ETF Shares Outstanding", "economic_purpose": "Secondary gold ETF demand; cross-validates GLD signal", "supported_families": ["FAM-003", "FAM-004"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2005-present", "source": "iShares / SEC", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "MEDIUM", "priority": "P2"},
    {"dataset_id": "DS-009", "name": "COMEX Non-Commercial Positioning", "economic_purpose": "Speculative gold futures positioning; flow and sentiment indicator", "supported_families": ["FAM-002", "FAM-004", "FAM-007"], "update_frequency": "Weekly (COT)", "resolution": "Weekly", "historical_availability": "1986-present", "source": "CFTC COT Report", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-010", "name": "COMEX Dealer Net Position", "economic_purpose": "Dealer inventory pressure; dealer inventory redistribution mechanism", "supported_families": ["FAM-002"], "update_frequency": "Weekly (COT)", "resolution": "Weekly", "historical_availability": "2006-present (disaggregated)", "source": "CFTC COT Disaggregated", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-011", "name": "Gold Volatility Index (GVZ)", "economic_purpose": "Gold options implied volatility; vol surface proxy and gamma/vanna estimation", "supported_families": ["FAM-002", "FAM-006"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2008-present", "source": "CBOE", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-012", "name": "Breakeven Inflation Rates (5Y, 10Y)", "economic_purpose": "Real yield computation; gold pricing vs real rates causal mechanism", "supported_families": ["FAM-001", "FAM-005"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2003-present", "source": "FRED", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-013", "name": "Economic Surprise Index (Citi/Bloomberg)", "economic_purpose": "Macro data surprise; expectation reset and macro repricing trigger", "supported_families": ["FAM-001", "FAM-005"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2000-present", "source": "Bloomberg (commercial)", "licensing": "Commercial", "acquisition_difficulty": "HIGH", "maintenance_cost": "MEDIUM", "expected_scientific_value": "HIGH", "priority": "P2"},
    {"dataset_id": "DS-014", "name": "Central Bank Gold Purchases (IMF/WGC)", "economic_purpose": "Institutional structural demand; long-horizon gold price support", "supported_families": ["FAM-003", "FAM-007"], "update_frequency": "Monthly/Quarterly", "resolution": "Monthly", "historical_availability": "2000-present", "source": "IMF IFS / World Gold Council", "licensing": "Free (WGC), Subscription (IMF)", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "MEDIUM", "priority": "P2"},
    {"dataset_id": "DS-015", "name": "Order Flow Imbalance Proxy (VWAP deviation)", "economic_purpose": "Intraday cascade initiator; decision cascade and flow propagation", "supported_families": ["FAM-004", "FAM-006"], "update_frequency": "Intraday", "resolution": "1-min / 5-min", "historical_availability": "Limited to data provider", "source": "Polygon / Tiingo / LBMA", "licensing": "Commercial", "acquisition_difficulty": "MEDIUM", "maintenance_cost": "MEDIUM", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-016", "name": "News and Event Embeddings (NLP)", "economic_purpose": "Information cascade velocity; macro event embedding for policy repricing", "supported_families": ["FAM-004", "FAM-005"], "update_frequency": "Real-time / Daily", "resolution": "Event-level", "historical_availability": "2010-present (commercial)", "source": "Refinitiv / Bloomberg NLP / Custom NLP", "licensing": "Commercial", "acquisition_difficulty": "HIGH", "maintenance_cost": "HIGH", "expected_scientific_value": "MEDIUM", "priority": "P3"},
    {"dataset_id": "DS-017", "name": "Geopolitical Risk Index (GPR)", "economic_purpose": "Exogenous safe-haven demand driver; stress topology complement", "supported_families": ["FAM-003"], "update_frequency": "Monthly", "resolution": "Monthly", "historical_availability": "1900-present", "source": "Caldara & Iacoviello (Fed / academic)", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "MEDIUM", "priority": "P2"},
    {"dataset_id": "DS-018", "name": "US Treasury 2Y Yield (FRED)", "economic_purpose": "Short-end rate; policy sensitivity and gold real-rate anchor", "supported_families": ["FAM-001", "FAM-005"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "1976-present", "source": "FRED", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-019", "name": "TIPS 10Y Real Yield (FRED)", "economic_purpose": "Real rate anchor; primary gold pricing causal mechanism", "supported_families": ["FAM-001", "FAM-004"], "update_frequency": "Daily", "resolution": "Daily", "historical_availability": "2003-present", "source": "FRED", "licensing": "Free", "acquisition_difficulty": "LOW", "maintenance_cost": "LOW", "expected_scientific_value": "HIGH", "priority": "P1"},
    {"dataset_id": "DS-020", "name": "Intraday Gold Tick Data (LBMA / CME)", "economic_purpose": "Microstructure; order flow imbalance and cascade detection", "supported_families": ["FAM-006"], "update_frequency": "Intraday", "resolution": "Tick", "historical_availability": "2010-present (limited)", "source": "CME / LBMA / Commercial", "licensing": "Commercial", "acquisition_difficulty": "HIGH", "maintenance_cost": "HIGH", "expected_scientific_value": "MEDIUM", "priority": "P3"},
]

# ---------------------------------------------------------------------------
# Phase C: Institutional Data Source Registry
# ---------------------------------------------------------------------------

DATA_SOURCES: list[dict[str, Any]] = [
    {"source_id": "SRC-001", "name": "FRED (Federal Reserve Economic Data)", "operator": "Federal Reserve Bank of St. Louis", "coverage": "Macro, rates, credit, money supply, inflation, employment", "datasets": ["VIX", "TED Spread", "Breakeven Inflation", "TIPS Yields", "US Treasury Yields", "M2", "CPI"], "quality": "HIGH", "latency": "T+1 to T+5", "reliability": "VERY_HIGH", "licensing": "Free and open", "cost": "Free", "api_support": True, "historical_depth": "1940s-present", "governance": "Federal Reserve", "priority": "P1"},
    {"source_id": "SRC-002", "name": "CME Group (CME DataMine)", "operator": "CME Group", "coverage": "Futures: gold, rates, FX, equity; SOFR futures, Fed Funds futures, COMEX gold", "datasets": ["COMEX Gold Futures", "SOFR Futures", "Fed Funds Futures", "Eurodollar Futures"], "quality": "HIGH", "latency": "Real-time (commercial), Delayed free", "reliability": "VERY_HIGH", "licensing": "Commercial", "cost": "Subscription", "api_support": True, "historical_depth": "1972-present", "governance": "CFTC-regulated", "priority": "P1"},
    {"source_id": "SRC-003", "name": "CFTC (Commitments of Traders)", "operator": "Commodity Futures Trading Commission", "coverage": "Futures positioning by participant class: dealers, leveraged, asset managers, small speculators", "datasets": ["COT Legacy", "COT Disaggregated", "COT Financial Traders"], "quality": "HIGH", "latency": "Weekly (Friday release, Tuesday data)", "reliability": "HIGH", "licensing": "Free", "cost": "Free", "api_support": True, "historical_depth": "1986-present", "governance": "US Government", "priority": "P1"},
    {"source_id": "SRC-004", "name": "CBOE (Chicago Board Options Exchange)", "operator": "Cboe Global Markets", "coverage": "Equity and commodity volatility indices: VIX, GVZ, MOVE", "datasets": ["VIX", "GVZ (Gold VIX)", "VXN", "SKEW"], "quality": "HIGH", "latency": "Real-time (delayed free)", "reliability": "HIGH", "licensing": "Free for historical, commercial for real-time", "cost": "Free (delayed)", "api_support": True, "historical_depth": "1990-present", "governance": "SEC-regulated", "priority": "P1"},
    {"source_id": "SRC-005", "name": "World Gold Council (WGC)", "operator": "World Gold Council", "coverage": "Gold demand, ETF flows, central bank purchases, supply/demand reports", "datasets": ["ETF Holdings", "Central Bank Purchases", "Mine Supply", "Demand by Sector"], "quality": "HIGH", "latency": "Monthly/Quarterly", "reliability": "HIGH", "licensing": "Free (aggregated)", "cost": "Free", "api_support": False, "historical_depth": "2000-present", "governance": "Industry body", "priority": "P1"},
    {"source_id": "SRC-006", "name": "LBMA (London Bullion Market Association)", "operator": "LBMA", "coverage": "Gold and silver fixings, clearing statistics, vault holdings", "datasets": ["LBMA Gold Price", "Gold Clearing Statistics", "Vault Holdings"], "quality": "HIGH", "latency": "Daily / Monthly", "reliability": "HIGH", "licensing": "Free (prices), restricted (clearing)", "cost": "Free (prices)", "api_support": True, "historical_depth": "1968-present", "governance": "Industry self-regulatory", "priority": "P2"},
    {"source_id": "SRC-007", "name": "IMF (International Monetary Fund)", "operator": "IMF", "coverage": "Central bank reserves, gold reserves, IFS database", "datasets": ["Central Bank Gold Reserves", "IFS Macro Data", "COFER"], "quality": "HIGH", "latency": "Monthly/Quarterly", "reliability": "HIGH", "licensing": "Free", "cost": "Free", "api_support": True, "historical_depth": "1950-present", "governance": "International", "priority": "P2"},
    {"source_id": "SRC-008", "name": "Polygon.io", "operator": "Polygon.io", "coverage": "Equities, FX, crypto intraday; limited commodities", "datasets": ["Intraday Equity", "FX intraday", "Aggregated bars"], "quality": "MEDIUM-HIGH", "latency": "Real-time / 15-min delayed (free)", "reliability": "MEDIUM", "licensing": "Free tier / Commercial", "cost": "Free starter, paid tiers", "api_support": True, "historical_depth": "2004-present", "governance": "Commercial", "priority": "P2"},
    {"source_id": "SRC-009", "name": "Nasdaq Data Link (Quandl)", "operator": "Nasdaq", "coverage": "Broad financial data; FRED mirror, COT, futures", "datasets": ["FRED data", "COT mirror", "Commodity futures", "Alternative data"], "quality": "HIGH", "latency": "T+1 to real-time", "reliability": "HIGH", "licensing": "Free (many) / Commercial (premium)", "cost": "Mixed", "api_support": True, "historical_depth": "Varies by dataset", "governance": "Nasdaq-operated", "priority": "P2"},
    {"source_id": "SRC-010", "name": "Academic Datasets (Caldara-Iacoviello GPR, ADS)", "operator": "Federal Reserve / Academic", "coverage": "Geopolitical risk index, business conditions index", "datasets": ["GPR Index", "ADS Business Conditions"], "quality": "HIGH", "latency": "Monthly (GPR)", "reliability": "HIGH", "licensing": "Free (academic)", "cost": "Free", "api_support": False, "historical_depth": "1900-present (GPR)", "governance": "Federal Reserve / Academic peer-reviewed", "priority": "P2"},
    {"source_id": "SRC-011", "name": "SEC EDGAR (ETF Holdings)", "operator": "US Securities and Exchange Commission", "coverage": "ETF N-PORT filings; holdings, shares outstanding", "datasets": ["GLD Holdings", "IAU Holdings", "ETF N-CEN"], "quality": "HIGH", "latency": "Monthly (N-PORT lag)", "reliability": "HIGH", "licensing": "Free", "cost": "Free", "api_support": True, "historical_depth": "2004-present", "governance": "SEC", "priority": "P2"},
    {"source_id": "SRC-012", "name": "SPDR ETF (State Street) Direct", "operator": "State Street Global Advisors", "coverage": "GLD daily shares outstanding and NAV", "datasets": ["GLD Shares Outstanding", "GLD NAV", "GLD Premium/Discount"], "quality": "HIGH", "latency": "Daily (T+1)", "reliability": "HIGH", "licensing": "Free (published)", "cost": "Free", "api_support": False, "historical_depth": "2004-present", "governance": "SEC-regulated", "priority": "P1"},
]

# ---------------------------------------------------------------------------
# Phase D: Market State Model
# ---------------------------------------------------------------------------

MARKET_STATE_DOMAINS: list[dict[str, Any]] = [
    {"domain_id": "DOM-001", "name": "Macro", "variables": ["cpi_yoy", "pce_yoy", "nfp_surprise", "gdp_qoq", "unemployment_rate", "economic_surprise_index", "ism_manufacturing", "consumer_confidence"], "causal_links": ["CPI surprise → gold repricing", "NFP surprise → rate path → gold"], "update_cadence": "Monthly/Weekly", "confidence": 0.72},
    {"domain_id": "DOM-002", "name": "Rates", "variables": ["us_2y_yield", "us_10y_yield", "tips_10y_real_yield", "breakeven_inflation_5y", "breakeven_inflation_10y", "fed_funds_futures_implied_rate", "sofr_futures_front", "dot_plot_median"], "causal_links": ["Real yield → gold price", "Rate path expectation → gold repricing", "Yield curve inversion → safe-haven demand"], "update_cadence": "Daily", "confidence": 0.75},
    {"domain_id": "DOM-003", "name": "FX", "variables": ["dxy_index", "eur_usd", "usd_jpy", "usd_chf", "usd_cny", "dxy_momentum", "dxy_regime"], "causal_links": ["DXY → gold inverse correlation", "USD safe-haven vs gold safe-haven competition"], "update_cadence": "Daily", "confidence": 0.78},
    {"domain_id": "DOM-004", "name": "Gold", "variables": ["xau_usd_spot", "xau_usd_1m_future", "xau_usd_3m_future", "gold_lease_rate_1m", "lbma_am_fix", "lbma_pm_fix", "gold_open_interest_comex"], "causal_links": ["Spot-future basis → carry regime", "Lease rate → supply pressure", "Open interest → positioning pressure"], "update_cadence": "Daily", "confidence": 0.80},
    {"domain_id": "DOM-005", "name": "Volatility", "variables": ["vix", "gvz", "move_index", "vxn", "realized_vol_xau_20d", "realized_vol_xau_5d", "vol_regime_indicator"], "causal_links": ["VIX spike → safe-haven demand", "GVZ spike → gold uncertainty → positioning change", "MOVE spike → rates uncertainty → gold repricing"], "update_cadence": "Daily", "confidence": 0.70},
    {"domain_id": "DOM-006", "name": "Credit", "variables": ["ted_spread", "fra_ois_spread", "hy_credit_spread", "ig_credit_spread", "libor_ois_spread"], "causal_links": ["TED spread → systemic stress → safe-haven demand", "Credit spread widening → liquidity withdrawal → gold demand"], "update_cadence": "Daily", "confidence": 0.68},
    {"domain_id": "DOM-007", "name": "Liquidity", "variables": ["fed_balance_sheet", "m2_growth", "repo_rate", "sofr_rate", "excess_reserves", "bank_reserve_requirement"], "causal_links": ["Liquidity contraction → risk-off → gold demand", "QE expansion → inflation expectation → gold demand"], "update_cadence": "Weekly/Monthly", "confidence": 0.65},
    {"domain_id": "DOM-008", "name": "Flows", "variables": ["gld_shares_outstanding", "iau_shares_outstanding", "etf_creation_redemption_net", "central_bank_gold_purchases_monthly", "comex_warehouse_stock_change"], "causal_links": ["ETF creation → physical demand → price pressure", "CB purchases → long-horizon structural demand"], "update_cadence": "Daily/Weekly/Monthly", "confidence": 0.72},
    {"domain_id": "DOM-009", "name": "Positioning", "variables": ["cot_leveraged_net", "cot_asset_manager_net", "cot_dealer_net", "cot_other_reportable_net", "comex_speculative_net_pct_oi"], "causal_links": ["Crowded long → vulnerability to liquidation → drawdown risk", "Dealer short → inventory constraint → bid withdrawal"], "update_cadence": "Weekly", "confidence": 0.70},
    {"domain_id": "DOM-010", "name": "Options", "variables": ["gold_25d_risk_reversal", "gold_atm_implied_vol", "gvz_term_structure", "dealer_gamma_proxy", "put_call_ratio_gold"], "causal_links": ["Risk reversal → directional sentiment", "Dealer gamma → mechanical market-making flow → intraday dynamics"], "update_cadence": "Daily", "confidence": 0.60},
    {"domain_id": "DOM-011", "name": "Microstructure", "variables": ["bid_ask_spread_proxy", "volume_delta", "vwap_deviation", "trade_aggressor_ratio", "intraday_vol_clustering"], "causal_links": ["Order flow imbalance → short-term price pressure", "Volume delta → initiator identification for cascade mechanism"], "update_cadence": "Intraday", "confidence": 0.55},
    {"domain_id": "DOM-012", "name": "Geopolitics_Sentiment", "variables": ["geopolitical_risk_index", "news_macro_event_score", "us_political_uncertainty_index", "global_uncertainty_index"], "causal_links": ["GPR spike → safe-haven demand surge", "Political uncertainty → gold allocation increase"], "update_cadence": "Monthly/Event-driven", "confidence": 0.58},
]

# ---------------------------------------------------------------------------
# Phase E: Observability Scoring
# ---------------------------------------------------------------------------

_OBS_THRESHOLD = 0.60  # minimum observation completeness to permit validation


def _observability_score(mechanism_type: str) -> dict[str, Any]:
    m = _MECHANISM_OBSERVABILITY[mechanism_type]
    req = cast(list[str], m["required"])
    obs = cast(list[str], m["observed"])
    prx = cast(list[str], m["proxies"])
    unav = cast(list[str], m["unavailable"])
    obs_completeness = round(len(obs) / max(1, len(req)), 4)
    evidence_completeness = round((len(obs) + 0.3 * len(prx)) / max(1, len(req)), 4)
    proxy_dependence = round(len(prx) / max(1, len(req)), 4)
    expected_uncertainty = round(1.0 - evidence_completeness, 4)
    val_readiness = obs_completeness >= _OBS_THRESHOLD
    conf_ceiling = round(min(0.85, evidence_completeness * 0.9), 4)
    return {
        "mechanism_type": mechanism_type,
        "family_id": str(m["family"]),
        "required_count": len(req),
        "observed_count": len(obs),
        "proxy_count": len(prx),
        "unavailable_count": len(unav),
        "observation_completeness": obs_completeness,
        "evidence_completeness": evidence_completeness,
        "proxy_dependence": proxy_dependence,
        "expected_uncertainty": expected_uncertainty,
        "validation_readiness": val_readiness,
        "scientific_confidence_ceiling": conf_ceiling,
        "blocked_by_observability": not val_readiness,
    }


def _family_observability(scores: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    family_groups: dict[str, list[dict[str, Any]]] = {}
    for s in scores:
        fam = str(s["family_id"])
        family_groups.setdefault(fam, []).append(s)
    result: dict[str, dict[str, Any]] = {}
    for fam_id, group in family_groups.items():
        avg_obs = sum(float(s["observation_completeness"]) for s in group) / len(group)
        avg_ev = sum(float(s["evidence_completeness"]) for s in group) / len(group)
        avg_ceil = sum(float(s["scientific_confidence_ceiling"]) for s in group) / len(group)
        blocked = any(s["blocked_by_observability"] for s in group)
        result[fam_id] = {
            "family_id": fam_id,
            "mechanism_count": len(group),
            "avg_observation_completeness": round(avg_obs, 4),
            "avg_evidence_completeness": round(avg_ev, 4),
            "avg_scientific_confidence_ceiling": round(avg_ceil, 4),
            "any_blocked": blocked,
            "scientific_readiness": "BLOCKED" if blocked else "READY",
        }
    return result

# ---------------------------------------------------------------------------
# Phase F: Data Foundation V2 Specification
# ---------------------------------------------------------------------------

DATA_FOUNDATION_V2_SPEC: dict[str, Any] = {
    "version": "2.0.0",
    "title": "AFRP Data Foundation V2",
    "principles": [
        "Every dataset must trace to at least one scientific hypothesis.",
        "All datasets are versioned with SHA-256 content hash.",
        "All ingestion pipelines are deterministic and reproducible.",
        "No live broker connections; offline data only.",
        "All datasets include quality scores, provenance, and update audit trail.",
        "Time synchronisation: all timestamps normalized to UTC.",
        "Schema validation is mandatory before any dataset enters the research layer.",
    ],
    "pipeline_stages": [
        {"stage": "ACQUISITION", "description": "Deterministic download from authorised sources; retry logic; checksum verification.", "components": ["SourceAdapter", "RetryPolicy", "ChecksumVerifier"]},
        {"stage": "VALIDATION", "description": "Schema validation, range checks, missing-value audits, outlier detection.", "components": ["SchemaValidator", "RangeChecker", "MissingValueAuditor", "OutlierDetector"]},
        {"stage": "NORMALIZATION", "description": "UTC timestamp alignment, unit normalization, calendar adjustment, frequency harmonization.", "components": ["TimestampNormalizer", "UnitConverter", "CalendarAdjuster", "FrequencyHarmonizer"]},
        {"stage": "VERSIONING", "description": "Immutable versioned snapshots with SHA-256 hash, git-like ancestry, tagged releases.", "components": ["DataVersionStore", "ContentHasher", "SnapshotRegistry"]},
        {"stage": "METADATA", "description": "Source provenance, license, acquisition date, data quality score, update cadence.", "components": ["MetadataStore", "ProvenanceTracker", "LicenseRegistry"]},
        {"stage": "EVIDENCE_TRACKING", "description": "IKROS evidence linkage: every dataset update creates an evidence record.", "components": ["EvidenceEmitter", "IKROSLinker"]},
        {"stage": "QUALITY_SCORING", "description": "Automated quality score: completeness × timeliness × consistency × lineage.", "components": ["DataQualityScorer", "CompletenessChecker", "TimelinessMonitor"]},
    ],
    "priority_datasets": ["DS-001", "DS-003", "DS-007", "DS-009", "DS-010", "DS-011", "DS-012", "DS-018", "DS-019"],
    "governance": "All dataset acquisitions require ARB approval before implementation.",
    "offline_only": True,
    "live_broker_prohibited": True,
}

# ---------------------------------------------------------------------------
# Phase G: Feature Expansion Roadmap
# ---------------------------------------------------------------------------

FEATURE_EXPANSION_ROADMAP: list[dict[str, Any]] = [
    {"feature_family": "vol_features_v2", "new_features": ["vix_regime", "gvz_term_slope", "vol_risk_premium_gold", "cross_vol_ratio_vix_gvz"], "depends_on": ["DS-001", "DS-011"], "causal_purpose": "Volatility-regime conditioning for safe-haven and liquidity mechanisms", "research_opportunity": "Test VIX-regime as conditioning variable for safe_haven_migration trigger"},
    {"feature_family": "rates_features_v2", "new_features": ["real_yield_tips_10y", "breakeven_inflation_5y", "real_yield_regime", "rate_path_surprise", "yield_curve_slope", "fed_funds_implied_hike"], "depends_on": ["DS-005", "DS-006", "DS-012", "DS-018", "DS-019"], "causal_purpose": "Real-rate anchor computation and policy repricing detection", "research_opportunity": "Replace rate_diff_proxy with direct real yield feature for macro_repricing and policy_repricing mechanisms"},
    {"feature_family": "flow_features_v1", "new_features": ["etf_flow_momentum_gld", "etf_nav_premium_gld", "etf_flow_z_score", "institutional_demand_composite"], "depends_on": ["DS-007", "DS-008"], "causal_purpose": "Direct ETF flow signal for etf_flow_propagation and safe_haven_migration", "research_opportunity": "Replace gold_price_momentum_as_flow_proxy with direct ETF flow series"},
    {"feature_family": "positioning_features_v1", "new_features": ["cot_dealer_net_z", "cot_leveraged_net_z", "cot_asset_manager_net_z", "cot_crowd_indicator", "speculative_net_pct_oi"], "depends_on": ["DS-009", "DS-010"], "causal_purpose": "Positioning pressure and dealer inventory constraint detection", "research_opportunity": "Validate dealer inventory redistribution mechanism with direct COT dealer positioning"},
    {"feature_family": "stress_features_v1", "new_features": ["ted_spread_z", "fra_ois_z", "composite_stress_index", "stress_regime_indicator"], "depends_on": ["DS-003", "DS-004"], "causal_purpose": "Composite systemic stress index for liquidity_withdrawal and safe_haven_migration", "research_opportunity": "Replace stress_topology_proxy with composite_stress_index for safe_haven_migration"},
    {"feature_family": "cascade_proxy_features_v1", "new_features": ["dxy_momentum_divergence", "yield_inversion_speed", "order_flow_imbalance_gvz_proxy", "vol_clustering_score"], "depends_on": ["DS-011"], "causal_purpose": "Ecology-independent cascade proxy for decision_cascade mechanism", "research_opportunity": "Implement EXP-DC-001: order-flow cascade proxy standalone walk-forward"},
    {"feature_family": "geopolitical_features_v1", "new_features": ["gpr_monthly", "us_political_uncertainty", "global_uncertainty_index_monthly"], "depends_on": ["DS-017"], "causal_purpose": "Exogenous safe-haven demand driver from geopolitical risk", "research_opportunity": "Add geopolitical conditioning to safe_haven_migration mechanism"},
]

# ---------------------------------------------------------------------------
# Main artifact builder
# ---------------------------------------------------------------------------

def prepare_dc4_observability_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(".")

    # Load alpha registry
    import json  # noqa: PLC0415
    reg_path = root / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program" / "dc3_institutional_alpha_registry.json"
    if not reg_path.exists():
        reg_path = Path(".") / "11-research" / "discovery-cycle-3" / "institutional-alpha-discovery-program" / "dc3_institutional_alpha_registry.json"
    mechanisms = cast(list[dict[str, Any]], json.loads(reg_path.read_text(encoding="utf-8")))

    # Phase A: Observability audit
    observability_matrix = {m["mechanism_type"]: _MECHANISM_OBSERVABILITY[str(m["mechanism_type"])] for m in mechanisms if str(m["mechanism_type"]) in _MECHANISM_OBSERVABILITY}

    # Phase E: Scoring
    scores = [_observability_score(str(m["mechanism_type"])) for m in mechanisms if str(m["mechanism_type"]) in _MECHANISM_OBSERVABILITY]
    family_obs = _family_observability(scores)

    # Aggregate statistics
    total_required = sum(int(s["required_count"]) for s in scores)
    total_observed = sum(int(s["observed_count"]) for s in scores)
    avg_completeness = round(sum(float(s["observation_completeness"]) for s in scores) / len(scores), 4)
    blocked_count = sum(1 for s in scores if s["blocked_by_observability"])

    # Priority dataset summary
    p1_datasets = [d for d in DATASET_CATALOGUE if d["priority"] == "P1"]
    p2_datasets = [d for d in DATASET_CATALOGUE if d["priority"] == "P2"]
    p3_datasets = [d for d in DATASET_CATALOGUE if d["priority"] == "P3"]

    # Unique unavailable variables (deduplicated)
    all_unavailable: set[str] = set()
    for m in observability_matrix.values():
        all_unavailable.update(cast(list[str], m["unavailable"]))

    analysis: dict[str, Any] = {
        "phase": "DISCOVERY_CYCLE_4",
        "title": "Institutional Market Observability & Data Expansion Program",
        "mechanism_count": len(mechanisms),
        "state_variables_identified": sum(len(cast(list[str], d["variables"])) for d in MARKET_STATE_DOMAINS),
        "missing_datasets": len(DATASET_CATALOGUE),
        "total_required_variables": total_required,
        "total_observed_variables": total_observed,
        "total_unavailable_variables": len(all_unavailable),
        "avg_observation_completeness": avg_completeness,
        "mechanisms_blocked_by_observability": blocked_count,
        # Phase A
        "observability_matrix": observability_matrix,
        # Phase B
        "dataset_gap_catalogue": DATASET_CATALOGUE,
        "p1_dataset_count": len(p1_datasets),
        "p2_dataset_count": len(p2_datasets),
        "p3_dataset_count": len(p3_datasets),
        # Phase C
        "data_source_registry": DATA_SOURCES,
        # Phase D
        "market_state_domains": MARKET_STATE_DOMAINS,
        "market_state_domain_count": len(MARKET_STATE_DOMAINS),
        # Phase E
        "observability_scores": scores,
        "family_observability": family_obs,
        # Phase F
        "data_foundation_v2_spec": DATA_FOUNDATION_V2_SPEC,
        # Phase G
        "feature_expansion_roadmap": FEATURE_EXPANSION_ROADMAP,
        "new_feature_families": len(FEATURE_EXPANSION_ROADMAP),
        "new_features_total": sum(len(cast(list[str], f["new_features"])) for f in FEATURE_EXPANSION_ROADMAP),
        # ARB
        "arb_recommendation": {
            "observation_completeness_avg": avg_completeness,
            "mechanisms_blocked": blocked_count,
            "p1_datasets_recommended": [d["dataset_id"] for d in p1_datasets],
            "immediate_free_acquisitions": [d["dataset_id"] for d in DATASET_CATALOGUE if d["acquisition_difficulty"] == "LOW" and d["priority"] == "P1"],
            "promote_now": False,
            "validate_additional_now": False,
            "recommended_next_action": "Implement Data Foundation V2 with P1 free datasets (FRED: VIX, TED, Breakeven, TIPS, 2Y yield; CFTC: COT; CBOE: GVZ; SPDR: GLD; WGC: ETF flows). Await ARB approval before implementation.",
            "scientific_blind_spots": list(all_unavailable)[:10],
        },
        "ecology_knowledge_graph": _graph_payload(scores, family_obs),
    }

    out_dir = root / DC4_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc4_observability_analysis.json", analysis)
    return analysis


def _graph_payload(scores: list[dict[str, Any]], family_obs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    obs_nodes = [
        {
            "node_id": f"IKROS-DC4-OBS-{s['mechanism_type'][:12].upper().replace('_', '')}",
            "label": f"DC4 Observability: {s['mechanism_type']} ({s['observation_completeness']:.0%})",
            "node_type": "KNOWLEDGE_OBJECT",
            "confidence": float(s["scientific_confidence_ceiling"]),
        }
        for s in scores
    ]
    conclusion_node = {
        "node_id": "IKROS-DC4-CONCLUSION-20260802-0001",
        "label": "DC4 Institutional Market Observability Conclusion",
        "node_type": "RESEARCH_CONCLUSION",
        "confidence": 0.72,
    }
    edges: list[dict[str, Any]] = []
    for s, node in zip(scores, obs_nodes, strict=True):
        edges.append({"source": str(s.get("mechanism_type", "")), "target": str(node["node_id"]), "relation": "ASSESSED_BY", "confidence": float(s["scientific_confidence_ceiling"])})
        edges.append({"source": str(node["node_id"]), "target": str(conclusion_node["node_id"]), "relation": "SUPPORTED_BY", "confidence": 0.70})
    return {"obs_nodes": obs_nodes, "conclusion_node": conclusion_node, "edges": edges}


# ---------------------------------------------------------------------------
# Report emission
# ---------------------------------------------------------------------------

def emit_dc4_observability_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC4_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    scores = cast(list[dict[str, Any]], analysis["observability_scores"])
    family_obs = cast(dict[str, Any], analysis["family_observability"])
    datasets = cast(list[dict[str, Any]], analysis["dataset_gap_catalogue"])
    sources = cast(list[dict[str, Any]], analysis["data_source_registry"])
    domains = cast(list[dict[str, Any]], analysis["market_state_domains"])
    roadmap = cast(list[dict[str, Any]], analysis["feature_expansion_roadmap"])
    arb = cast(dict[str, Any], analysis["arb_recommendation"])
    df_v2 = cast(dict[str, Any], analysis["data_foundation_v2_spec"])

    # Observability Matrix
    obs_md = out_dir / "OBSERVABILITY_MATRIX.md"
    obs_rows = [[s["mechanism_type"], s["family_id"], s["observation_completeness"], s["evidence_completeness"], s["scientific_confidence_ceiling"], "BLOCKED" if s["blocked_by_observability"] else "READY"] for s in scores]
    write_markdown(obs_md, f"# Observability Matrix\n## Discovery Cycle 4\n\n{markdown_table(['Mechanism', 'Family', 'Obs. Complete', 'Evid. Complete', 'Conf. Ceiling', 'Status'], obs_rows)}\n")
    written["observability_matrix"] = str(obs_md)

    # Dataset Gap Report
    ds_md = out_dir / "DATASET_GAP_REPORT.md"
    ds_rows = [[d["dataset_id"], d["name"], d["priority"], d["acquisition_difficulty"], d["expected_scientific_value"], d["source"]] for d in datasets]
    write_markdown(ds_md, f"# Dataset Gap Report\n## Discovery Cycle 4\n\n{markdown_table(['ID', 'Dataset', 'Priority', 'Difficulty', 'Value', 'Source'], ds_rows)}\n")
    written["dataset_gap_report"] = str(ds_md)

    # Institutional Data Source Registry
    src_md = out_dir / "INSTITUTIONAL_DATA_SOURCE_REGISTRY.md"
    src_rows = [[s["source_id"], s["name"], s["priority"], s["licensing"], s["quality"], s["api_support"]] for s in sources]
    write_markdown(src_md, f"# Institutional Data Source Registry\n## Discovery Cycle 4\n\n{markdown_table(['ID', 'Source', 'Priority', 'Licensing', 'Quality', 'API'], src_rows)}\n")
    written["data_source_registry"] = str(src_md)

    # Market State Variable Atlas
    msv_md = out_dir / "MARKET_STATE_VARIABLE_ATLAS.md"
    msv_rows = [[d["domain_id"], d["name"], len(cast(list[str], d["variables"])), d["update_cadence"], d["confidence"]] for d in domains]
    write_markdown(msv_md, f"# Market State Variable Atlas\n## Discovery Cycle 4\n\n{markdown_table(['Domain ID', 'Domain', 'Var Count', 'Update Cadence', 'Confidence'], msv_rows)}\n")
    written["market_state_variable_atlas"] = str(msv_md)

    # Scientific Readiness Report
    sci_md = out_dir / "SCIENTIFIC_READINESS_REPORT.md"
    sci_rows = [[fid, fdata["mechanism_count"], fdata["avg_observation_completeness"], fdata["avg_scientific_confidence_ceiling"], fdata["scientific_readiness"]] for fid, fdata in family_obs.items()]
    write_markdown(sci_md, f"# Scientific Readiness Report\n## Discovery Cycle 4\n\n{markdown_table(['Family', 'Mechanisms', 'Avg Obs Completeness', 'Avg Conf Ceiling', 'Status'], sci_rows)}\n")
    written["scientific_readiness_report"] = str(sci_md)

    # Validation Readiness Report
    val_md = out_dir / "VALIDATION_READINESS_REPORT.md"
    val_rows = [[s["mechanism_type"], s["observation_completeness"], s["scientific_confidence_ceiling"], "YES" if s["validation_readiness"] else "NO (BLOCKED)"] for s in scores]
    write_markdown(val_md, f"# Validation Readiness Report\n## Discovery Cycle 4\n\n{markdown_table(['Mechanism', 'Obs Completeness', 'Conf Ceiling', 'Validation Ready'], val_rows)}\n")
    written["validation_readiness_report"] = str(val_md)

    # Data Foundation V2 Specification
    df_md = out_dir / "DATA_FOUNDATION_V2_SPECIFICATION.md"
    pipeline_rows = [[p["stage"], ", ".join(cast(list[str], p["components"])), p["description"][:80]] for p in cast(list[dict[str, Any]], df_v2["pipeline_stages"])]
    principles = "\n".join(f"- {p}" for p in cast(list[str], df_v2["principles"]))
    write_markdown(
        df_md,
        f"""# Data Foundation V2 Specification
## Version {df_v2['version']}

### Principles
{principles}

### Pipeline Stages
{markdown_table(['Stage', 'Components', 'Description'], pipeline_rows)}

### Priority Datasets
{", ".join(cast(list[str], df_v2['priority_datasets']))}

Offline only: {df_v2['offline_only']} | Live broker prohibited: {df_v2['live_broker_prohibited']}
""",
    )
    written["data_foundation_v2_spec"] = str(df_md)

    # Dataset Acquisition Roadmap
    acq_md = out_dir / "DATASET_ACQUISITION_ROADMAP.md"
    p1_free = [d for d in datasets if d["priority"] == "P1" and d["acquisition_difficulty"] == "LOW"]
    p1_comm = [d for d in datasets if d["priority"] == "P1" and d["acquisition_difficulty"] in {"MEDIUM", "HIGH"}]
    p1f_rows = [[d["dataset_id"], d["name"], d["source"], d["licensing"]] for d in p1_free]
    p1c_rows = [[d["dataset_id"], d["name"], d["source"], d["licensing"]] for d in p1_comm]
    write_markdown(
        acq_md,
        f"""# Dataset Acquisition Roadmap
## Discovery Cycle 4

### Phase 1 — Free P1 Datasets (Immediate)
{markdown_table(['ID', 'Dataset', 'Source', 'Licensing'], p1f_rows)}

### Phase 2 — Commercial P1 Datasets (ARB approval required)
{markdown_table(['ID', 'Dataset', 'Source', 'Licensing'], p1c_rows)}
""",
    )
    written["dataset_acquisition_roadmap"] = str(acq_md)

    # Feature Expansion Roadmap
    feat_md = out_dir / "FEATURE_EXPANSION_ROADMAP.md"
    feat_rows = [[f["feature_family"], len(cast(list[str], f["new_features"])), ", ".join(cast(list[str], f["depends_on"])), f["research_opportunity"][:80]] for f in roadmap]
    write_markdown(feat_md, f"# Feature Expansion Roadmap\n## Discovery Cycle 4\n\n{markdown_table(['Feature Family', 'New Features', 'Depends On', 'Research Opportunity'], feat_rows)}\n")
    written["feature_expansion_roadmap"] = str(feat_md)

    # Observability Dashboard
    dash_md = out_dir / "OBSERVABILITY_DASHBOARD.md"
    blind_spots = "\n".join(f"- {b}" for b in cast(list[str], arb["scientific_blind_spots"]))
    write_markdown(
        dash_md,
        f"""# Observability Dashboard
## Discovery Cycle 4

- Mechanisms assessed: {analysis['mechanism_count']}
- State variables identified: {analysis['state_variables_identified']}
- Missing datasets catalogued: {analysis['missing_datasets']}
- Total required variables: {analysis['total_required_variables']}
- Currently observed: {analysis['total_observed_variables']}
- Unavailable (unique): {analysis['total_unavailable_variables']}
- Average observation completeness: {analysis['avg_observation_completeness']:.1%}
- Mechanisms blocked by observability: {analysis['mechanisms_blocked_by_observability']}
- P1 datasets: {analysis['p1_dataset_count']}
- New feature families proposed: {analysis['new_feature_families']}
- New features total: {analysis['new_features_total']}

### Top Scientific Blind Spots
{blind_spots}
""",
    )
    written["observability_dashboard"] = str(dash_md)

    # ARB Recommendation
    arb_md = out_dir / "ARB_RECOMMENDATION_DC4.md"
    free_p1 = "\n".join(f"- {d}" for d in cast(list[str], arb["immediate_free_acquisitions"]))
    write_markdown(
        arb_md,
        f"""# ARB Recommendation — Discovery Cycle 4
## Institutional Market Observability & Data Expansion

- Observation completeness (avg): {arb['observation_completeness_avg']:.1%}
- Mechanisms blocked: {arb['mechanisms_blocked']}
- P1 datasets recommended: {arb['p1_datasets_recommended']}
- Promote now: {arb['promote_now']}
- Validate additional now: {arb['validate_additional_now']}

### Immediate Free P1 Acquisitions
{free_p1}

### Recommendation
{arb['recommended_next_action']}
""",
    )
    written["arb_recommendation"] = str(arb_md)

    if campaign_result is not None:
        write_json(out_dir / "dc4_campaign_result.json", campaign_result)
        written["campaign_result"] = str(out_dir / "dc4_campaign_result.json")
    return written
