# SPEC-012 — XAU/USD Alpha Discovery Bible

> **Specification ID:** `SPEC-012`
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

**PENDING IMPORT.** This specification will serve as the definitive institutional
catalogue of all alpha signals and hypotheses evaluated for XAU/USD, including
their rationale, implementation, validation results, and conclusions.

## 2. Scope

This specification shall constitute:
- Canonical alpha taxonomy for XAU/USD
- Systematic discovery protocol
- Hypothesis catalogue (active, rejected, pending)
- Rejection register with documented evidence
- Signal combination methodology
- Regime-conditional alpha behaviour

## 3. Current State (Phase E Evidence)

Phase E evaluated 6 alpha hypotheses. **All fail promotion.** Results are in
`11-research/phase-e/` but not captured in a formal institutional catalogue.

| Hypothesis | Full Sharpe | WF Sharpe | Ruin Prob | Decision |
|-----------|-------------|-----------|-----------|---------|
| Trend Following | -2.21 | -0.82 | 0.00 | FAIL |
| Mean Reversion | -3.17 | -3.27 | 0.08 | FAIL |
| Liquidity Sweep | -12.27 | -12.24 | 0.00 | FAIL |
| Macro Only | -2.13 | -1.98 | 0.01 | FAIL |
| Technical Only | -1.16 | -0.41 | 0.01 | FAIL |
| Hybrid | -2.06 | -1.51 | 0.01 | FAIL |

**Key research insight:** Direction accuracy 51.3% (marginally above random).
Best candidate: Technical Only (lowest ruin probability, best walk-forward profile).

**This evidence is currently lost as institutional knowledge without IKROS or this spec.**

## 4. Import Requirements

When importing this specification:

1. **Alpha Taxonomy** — Classification of signal types (momentum, mean-reversion,
   carry, liquidity, macro, microstructure, behavioral)
2. **Discovery Protocol** — Systematic process for generating new hypotheses
3. **Hypothesis Register** — Catalogue of all evaluated hypotheses with status
4. **Rejection Register** — Why each hypothesis was rejected with evidence references
5. **Signal Combination Rules** — How to combine individual signals into strategies
6. **Regime Conditioning** — How alpha signals behave across market regimes
7. **Future Hypotheses Pipeline** — Ranked candidate hypotheses for future research

## 5. Blocking Impact

Without this specification:
- Phase E failures accumulate no institutional learning
- Future research repeats failed hypotheses
- No systematic discovery framework exists
- Alpha research is ad-hoc

**Priority: Tier 2 — Required for next structured alpha research cycle.**

## 6. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.0.1 | 2026-08-02 | Stub created; Phase E evidence recorded; full import pending |
