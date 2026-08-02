# SPEC-011 — Gold Market Specification

> **Specification ID:** `SPEC-011`
> **Version:** `0.0.1`
> **Level:** L2 (Research Specification)
> **Status:** Pending_Import
> **Owner:** Research Team
> **Approval Authority:** Principal Quantitative Researcher
> **Work Package:** WP-IMP-0040 (stub) / TBD (full import)
> **Canonical Source:** None (PENDING IMPORT)
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

**PENDING IMPORT.** This specification will define the complete institutional
understanding of the XAU/USD gold market, providing the foundational domain
knowledge for all AFRP research and runtime agent design.

## 2. Scope

This specification shall govern:
- XAU/USD instrument properties and contract specifications
- Trading session definitions (London, New York, Asian)
- Liquidity profiles by session and regime
- Macroeconomic driver catalogue (DXY, real rates, geopolitical risk)
- Market microstructure model (bid-ask dynamics, order flow)
- Behavioural patterns catalogue
- Geopolitical and event risk taxonomy

## 3. Current State (Pre-Import)

Partial evidence exists in the repository and AFRP-Datasets:

| Evidence | Location | Completeness |
|----------|---------|-------------|
| XAU/USD daily OHLCV (2000-2026) | AFRP-Datasets | Data only |
| XAU/USD hourly OHLCV | AFRP-Datasets | Data only |
| DXY daily/hourly | AFRP-Datasets | Data only |
| Treasury yields (1960-2026) | AFRP-Datasets | Data only |
| Geopolitical events (12 curated) | AFRP-Datasets | Partial |
| L2-MAC agent (macro signals) | `06-runtime/layer2/` | Logic only |
| L2-MIC agent (microstructure) | `06-runtime/layer2/` | Logic only |
| Phase C regime analysis | `11-research/regime_analysis.md` | Research only |

## 4. Import Requirements

When importing this specification:

1. **Instrument Specification** — Contract size, tick size, margin, settlement
2. **Session Taxonomy** — London fix (10:30), NY session, Asian session boundaries
3. **Macroeconomic Driver Model** — DXY correlation, real rates transmission, Fed policy impact
4. **Geopolitical Risk Framework** — Event taxonomy, historical impact analysis
5. **Microstructure Model** — Bid-ask spread model, order flow imbalance, VWAP benchmarks
6. **Regime Classification** — Bull/bear/ranging definitions for gold specifically
7. **Seasonal Patterns** — Known statistical seasonalities (Indian wedding season, etc.)

## 5. Blocking Impact

This specification's absence means:
- L2 domain agents implement gold-specific logic without formal domain specification
- No formal basis for feature engineering decisions (SPEC-014)
- Alpha discovery (SPEC-012) lacks instrument context

**Priority: Tier 2 — Required for next alpha research cycle.**

## 6. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.0.1 | 2026-08-02 | Stub created; import pending |
