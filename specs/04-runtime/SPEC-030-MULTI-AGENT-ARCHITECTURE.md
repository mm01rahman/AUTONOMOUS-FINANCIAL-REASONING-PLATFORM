# SPEC-030 — Multi-Agent Architecture

> **Specification ID:** `SPEC-030`
> **Version:** `1.0.0`
> **Level:** L4 (Implementation Specification)
> **Status:** Approved
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `02-architecture/110_RUNTIME_ARCHITECTURE.md` (SLS-200)
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Specifies the six-agent Layer 2 architecture: domain responsibilities, DSmT mass
emission, and inter-agent independence requirements.

## 2. Six Domain Agents

| Agent | Subsystem | Domain | CIO-03 Contribution | Status |
|-------|-----------|--------|---------------------|--------|
| L2-MAC | SLS-200 | Macroeconomic signals | Macro belief mass | COMPLETE |
| L2-MIC | SLS-200 | Market microstructure | Micro belief mass | COMPLETE |
| L2-LIQ | SLS-200 | Liquidity conditions | Liquidity belief mass | COMPLETE |
| L2-REG | SLS-200 | Market regime classification | Regime belief mass | COMPLETE |
| L2-FOR | SLS-200 | Forward/expectations analysis | Forward belief mass | COMPLETE |
| L2-BEH | SLS-200 | Behavioral finance signals | Behavioral belief mass | COMPLETE |

## 3. Architecture Rules

- All agents MUST operate independently (no cross-agent Python imports)
- Each agent emits CIO-03 (Domain Belief) with DSmT mass over D^Theta
- Agents receive CIO-02 (Standard Features) from L1-FST
- L6-OPT provides CIO-11 (Calibration Weights) to discount unreliable agents
- Agent quorum required for NORMAL operations (NFR-003)

## 4. DSmT Mass Constraints

Every CIO-03 emission must satisfy:
- sum(m_agent(X) for X in D^Theta) ≈ 1.0 (tolerance ≤ 1e-9)
- All masses m(X) ≥ 0
- Validated by Phase B V&V math_checks.py

## 5. Traceability

FR-010 in TVM-001.

## 6. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
