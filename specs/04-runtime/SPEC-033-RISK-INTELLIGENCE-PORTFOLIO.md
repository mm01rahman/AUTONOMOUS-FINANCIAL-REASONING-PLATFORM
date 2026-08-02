# SPEC-033 — Risk Intelligence & Portfolio Construction

> **Specification ID:** `SPEC-033`
> **Version:** `0.5.0`
> **Level:** L4 (Implementation Specification)
> **Status:** Draft
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040 (stub) / TBD (formal approval)
> **Canonical Source:** Derived from L4-VAL + L4-DEC + L5-EXE + paper_trading/risk.py
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Specifies risk intelligence and portfolio construction capabilities including utility
optimization, policy constraints, position sizing, and portfolio-level risk management.

## 2. Current Implementation (COMPLETE)

### 2.1 Decision Layer (L4)

| Component | Function | CIO | Status |
|-----------|----------|-----|--------|
| L4-FUS | Synthesizes DecisionContext from WorldState + Scenarios | CIO-05B | COMPLETE |
| L4-DEC | Solves argmax U_r risk-adjusted utility | CIO-06 | COMPLETE |
| L4-VAL | Enforces Pi_C projection + a_null fallback + MP-01..05 | CIO-07 | COMPLETE |

### 2.2 Mission Profiles

| Profile | Risk Posture | Use Case |
|---------|-------------|----------|
| MP-01 | Ultra-conservative | High-uncertainty markets |
| MP-02 | Conservative | Normal operations |
| MP-03 | Moderate | Trend-following conditions |
| MP-04 | Aggressive | High-conviction opportunities |
| MP-05 | Emergency stop | Critical risk events |

### 2.3 Paper Trading Risk Engine

| Component | Implementation | Location |
|-----------|---------------|----------|
| Stop-loss | Per-trade and trailing | `tools/paper_trading/risk.py` |
| Take-profit | Per-trade | `tools/paper_trading/risk.py` |
| Daily loss limit | Session-level | `tools/paper_trading/risk.py` |
| Position sizing | Fixed fractional | `tools/paper_trading/portfolio.py` |

## 3. Portfolio Construction Gaps (NOT IMPLEMENTED)

| Gap | Description | Priority |
|----|-------------|----------|
| **Kelly Sizing** | Optimal position sizing under known edge | Tier 2 |
| **Multi-Asset Portfolio** | Beyond single XAU/USD instrument | Tier 3 |
| **Correlation Risk** | Cross-asset risk management | Tier 3 |
| **Drawdown-Based Sizing** | Dynamic position reduction on drawdown | Tier 2 |
| **VaR / CVaR** | Formal risk measurement | Tier 2 |

## 4. Traceability

FR-012, FR-013, NFR-005, NFR-007, NFR-008 in TVM-001.

## 5. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.5.0 | 2026-08-02 | Draft derived from L4/L5 + paper trading implementation |
