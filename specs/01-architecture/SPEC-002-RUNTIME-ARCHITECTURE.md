# SPEC-002 — Runtime Architecture

> **Specification ID:** `SPEC-002`
> **Version:** `1.0.0`
> **Level:** L1 (Architecture — Semi-Immutable)
> **Status:** Approved
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `02-architecture/110_RUNTIME_ARCHITECTURE.md`
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Specifies the six cognitive runtime layers, their responsibilities, CIO contracts,
and the operational state machine.

## 2. Canonical Content Reference

**`02-architecture/110_RUNTIME_ARCHITECTURE.md`** (RUN-001, RUN-002, SYS-03)

## 3. Six Cognitive Runtime Layers (RUN-002)

| Layer | Subsystem | Capabilities | CIOs Emitted | Status |
|-------|-----------|-------------|--------------|--------|
| L1 — Data Platform | SLS-100 | L1-ING, L1-FST, L1-RDB, L1-MEM | CIO-01, CIO-02 | COMPLETE |
| L2 — Domain Agents | SLS-200 | L2-MAC, L2-MIC, L2-LIQ, L2-REG, L2-FOR, L2-BEH | CIO-03 | COMPLETE |
| L3 — World Model | SLS-300/301 | L3-WRM, L3-SIM | CIO-04, CIO-05A | COMPLETE |
| L4 — Decision Engine | SLS-400/401/402 | L4-FUS, L4-DEC, L4-VAL | CIO-05B, CIO-06, CIO-07 | COMPLETE |
| L5 — Execution Gateway | SLS-500 | L5-EXE | CIO-08, CIO-09, CIO-10 | COMPLETE |
| L6 — Learning & Adaptation | SLS-600 | L6-OPT | CIO-11, CIO-12 | COMPLETE |

## 4. Operational State Machine (SYS-03)

States: INITIALIZING → NORMAL ↔ OBSERVATION ↔ DEGRADED → RECOVERY → NORMAL
Emergency path: any state → EMERGENCY_STOP (requires manual reset)

## 5. Architecture Rules

- No cross-layer Python imports (EDR-002, FIT-004)
- All inter-layer communication via Protobuf CIOs only (EDR-001)
- asyncio for I/O-bound; process pools for CPU-bound math (EDR-003)

## 6. Traceability

FR-009..014 in TVM-001 all covered. All 18 runtime capabilities COMPLETE.

## 7. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
