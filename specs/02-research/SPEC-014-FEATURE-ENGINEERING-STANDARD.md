# SPEC-014 — Feature Engineering Standard

> **Specification ID:** `SPEC-014`
> **Version:** `0.5.0`
> **Level:** L2 (Research Specification)
> **Status:** Draft
> **Owner:** Research Team
> **Approval Authority:** Principal Quantitative Researcher
> **Work Package:** WP-IMP-0040 (stub) / TBD (formal approval)
> **Canonical Source:** Derived from L1-FST + L2 agent implementations
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines the standard for feature engineering across all AFRP research and runtime
components. Features are the bridge between raw market data (CIO-01) and domain
beliefs (CIO-03).

## 2. Feature Taxonomy (Derived)

All features are classified into six families matching the six L2 domain agents:

| Family | Agent | Examples | CIO Output |
|--------|-------|---------|------------|
| Macro | L2-MAC | DXY return, yield spread, real rate, inflation surprise | CIO-03 |
| Microstructure | L2-MIC | Bid-ask spread, volume VWAP ratio, tick imbalance | CIO-03 |
| Liquidity | L2-LIQ | Order book depth ratio, spread percentile, market impact | CIO-03 |
| Regime | L2-REG | Volatility cluster (regime_vol_20), trend strength, ADX | CIO-03 |
| Forward | L2-FOR | Rate expectations, futures basis, implied vol term structure | CIO-03 |
| Behavioral | L2-BEH | Sentiment proxy, positioning, momentum divergence | CIO-03 |

**Top features by permutation importance (Phase E):**
1. macro_pressure
2. regime_vol_20
3. micro_momentum
4. forward_expectation
5. xau_return_1

## 3. Feature Standard (Normative)

### 3.1 Normalization

- All features normalized to [-1, +1] range before CIO-02 emission
- Normalization method: rolling z-score with 252-bar window (daily) or 5040-bar (hourly)
- Clipping at ±3 sigma to prevent outlier contamination

### 3.2 Stationarity

- All features must be stationary (ADF test p-value < 0.05)
- Returns preferred over price levels
- Log-returns used for multiplicative series

### 3.3 Forward-Look Contamination Prevention

- No future data in feature calculation
- Rolling windows use only historical data
- All features must be causally valid at decision time

### 3.4 Feature Governance

Features must be:
- Named consistently (snake_case)
- Documented with economic rationale
- Registered in Feature Registry (requires IKROS SPEC-060)
- Version-tagged with dataset versions

## 4. CIO-02 Contract

Standard Feature emitted by L1-FST carrying normalized feature vector.
Each CIO-02 contains: feature_name, value (float), timestamp, source_agent.

## 5. Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Feature normalization | Implemented | `06-runtime/layer1/feature_store.py` |
| Domain feature extraction | Implemented | `06-runtime/layer2/` |
| Feature importance analysis | Implemented | `tools/alpha_research/features.py` |
| Feature Registry | **MISSING** | Requires IKROS |
| Formal feature taxonomy document | Draft (this file) | — |

## 6. Traceability

FR-009 (L1-FST) in TVM-001.

## 7. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.5.0 | 2026-08-02 | Draft derived from Layer 1/2 implementation |
