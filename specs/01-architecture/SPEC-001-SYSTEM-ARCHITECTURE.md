# SPEC-001 — System Architecture

> **Specification ID:** `SPEC-001`
> **Version:** `1.0.0`
> **Level:** L1 (Architecture — Semi-Immutable)
> **Status:** Approved
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `02-architecture/100_SYSTEM_ARCHITECTURE.md`
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines the three-product platform architecture, all non-functional requirements (NFR),
architecture fitness functions (FIT), and engineering decision rules (EDR).

## 2. Canonical Content Reference

**`02-architecture/100_SYSTEM_ARCHITECTURE.md`** (ARCH-001)

## 3. Three-Product Architecture (ARCH-002)

| Product | Path | Responsibility |
|---------|------|----------------|
| Engineering OS (EOS) | `tools/`, `03-engineering/`, `05-work-packages/` | Governance, DAG planning, AST validation, evidence |
| AFRP Runtime Platform | `06-runtime/` | Telemetry, belief formation, world model, decisioning, execution |
| Research & Strategy Platform | `07-research/`, `tools/backtest/`, `tools/alpha_research/` | Offline backtesting, strategy discovery, calibration |

## 4. Non-Functional Requirements

| ID | Title | Status |
|----|-------|--------|
| NFR-001 | P99 decision latency ≤ 50ms | Implemented — measured via FIT-008 |
| NFR-002 | 99.99% HA active-passive clustering | NOT DEPLOYED — pre-live gap |
| NFR-003 | Graceful degradation on feed loss | Implemented — m(Θ) padding |
| NFR-004 | Determinism under seed=42 | Implemented — FIT-008 PASS |
| NFR-005 | RPO=0 lost trades, RTO < 60s | Implemented — L1-RDB + L5-EXE |
| NFR-006 | mTLS / SPIFFE zero-trust | NOT DEPLOYED — pre-live gap |
| NFR-007 | Auditability with HMAC + OpenTelemetry | Implemented — CognitiveEnvelope |
| NFR-008 | Resource confinement / pre-allocation | Implemented — L4/L5 path |
| NFR-009 | 100% mypy --strict | Implemented — 126 files PASS |
| NFR-010 | Protobuf backward compatibility | Implemented — buf breaking PASS |

## 5. Architecture Fitness Functions

| ID | Name | Gate | Status |
|----|------|------|--------|
| FIT-001 | DAG Circularity | `afrp plan` | PASS |
| FIT-002 | AST Illegal Syntax | `afrp validate` | PASS |
| FIT-003 | Protobuf Custom Options | `buf lint` | PASS |
| FIT-004 | Cross-Layer Import Prohibition | `afrp validate` | PASS |
| FIT-005 | Boundary Confinement | `afrp evidence` | PASS |
| FIT-006 | Kernel Length ≤ 400 words | `afrp validate` | PASS |
| FIT-007 | Traceability 100% | `afrp health` | PASS |
| FIT-008 | Deterministic Replay | `system_gate.py` | PASS |

## 6. Traceability

All NFR-001..010 and EDR-001..012 tracked in `03-engineering/TRACEABILITY_MATRIX.yaml`.

## 7. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
