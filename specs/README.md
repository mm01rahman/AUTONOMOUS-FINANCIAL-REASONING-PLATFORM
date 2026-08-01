# AFRP Canonical Specification Library

> **Authority Level:** Level 1 (Contractual) | **Document ID:** `SPEC-INDEX-1.0`
> **Owner:** Architecture Review Board (ARB) | **Status:** Active
> **Work Package:** WP-IMP-0040

## Purpose

This directory is the **canonical home of every AFRP institutional specification**.

Every future capability, Work Package, ADR, Runtime module, validation artifact, and
evidence record shall trace back to one or more approved specifications in this library.

## Specification Hierarchy

```
Level 0 — Institutional Constitution
    ↓
Level 1 — Architecture Specifications
    ↓
Level 2 — Research Specifications
    ↓
Level 3 — Engineering Specifications
    ↓
Level 4 — Implementation (Runtime) Specifications
    ↓
Level 5 — Validation Specifications
    ↓
Level 6 — Operational Specifications
    ↓
Level 7 — Knowledge & Intelligence Specifications
```

## Directory Structure

```
specs/
├── README.md                              ← This file (Documentation Index)
├── registry/
│   ├── SPECIFICATION_REGISTRY.yaml        ← Authoritative spec catalog
│   ├── SPECIFICATION_HIERARCHY.md         ← Hierarchy & inheritance rules
│   ├── SPECIFICATION_DEPENDENCY_GRAPH.md  ← Dependency relationships
│   └── CONFORMANCE_MATRIX.md              ← ARB Conformance Audit Report
├── policies/
│   ├── VERSIONING_POLICY.md               ← Lifecycle management rules
│   └── REPOSITORY_ORGANIZATION_STANDARD.md← Structural standards
├── 00-constitution/
│   └── SPEC-000-INSTITUTIONAL-CONSTITUTION.md
├── 01-architecture/
│   ├── SPEC-001-SYSTEM-ARCHITECTURE.md
│   ├── SPEC-002-RUNTIME-ARCHITECTURE.md
│   ├── SPEC-003-MATHEMATICAL-FOUNDATION.md
│   ├── SPEC-004-REFERENCE-SPECIFICATION.md
│   └── SPEC-005-PRODUCTION-ENGINEERING-ARCHITECTURE.md
├── 02-research/
│   ├── SPEC-010-RESEARCH-STANDARD-RS10.md
│   ├── SPEC-011-GOLD-MARKET-SPECIFICATION.md
│   ├── SPEC-012-ALPHA-DISCOVERY-BIBLE.md
│   ├── SPEC-013-ALPHA-VALIDATION-FRAMEWORK.md
│   ├── SPEC-014-FEATURE-ENGINEERING-STANDARD.md
│   └── SPEC-015-FINANCIAL-REASONING-FRAMEWORK.md
├── 03-engineering/
│   ├── SPEC-020-ENGINEERING-OPERATING-SYSTEM.md
│   └── SPEC-021-IMPLEMENTATION-GUIDE.md
├── 04-runtime/
│   ├── SPEC-030-MULTI-AGENT-ARCHITECTURE.md
│   ├── SPEC-031-MEMORY-KNOWLEDGE-ARCHITECTURE.md
│   ├── SPEC-032-AUTONOMOUS-LEARNING-EVOLUTION.md
│   ├── SPEC-033-RISK-INTELLIGENCE-PORTFOLIO.md
│   └── SPEC-034-SIMULATION-DIGITAL-TWIN.md
├── 05-validation/
│   └── SPEC-040-VALIDATION-FRAMEWORK.md
├── 06-operations/
│   └── SPEC-050-OPERATIONAL-ARCHITECTURE.md
└── 07-knowledge/
    └── SPEC-060-IKROS-ARCHITECTURE.md
```

## Quick Navigation

| Spec ID | Title | Level | Status | Coverage |
|---------|-------|-------|--------|----------|
| SPEC-000 | Institutional Constitution | L0 | Approved | Fully Implemented |
| SPEC-001 | System Architecture | L1 | Approved | Fully Implemented |
| SPEC-002 | Runtime Architecture | L1 | Approved | Fully Implemented |
| SPEC-003 | Mathematical Foundation | L1 | Approved | Fully Implemented |
| SPEC-004 | Reference Specification | L1 | Approved | Fully Implemented |
| SPEC-005 | Production Engineering Architecture | L1 | Pending Import | Missing |
| SPEC-010 | Research Standard RS-1.0 | L2 | Draft | Partially Implemented |
| SPEC-011 | Gold Market Specification | L2 | Pending Import | Research Only |
| SPEC-012 | Alpha Discovery Bible | L2 | Pending Import | Research Only |
| SPEC-013 | Alpha Validation Framework | L2 | Draft | Partially Implemented |
| SPEC-014 | Feature Engineering Standard | L2 | Draft | Partially Implemented |
| SPEC-015 | Financial Reasoning Framework | L2 | Draft | Partially Implemented |
| SPEC-020 | Engineering Operating System | L3 | Approved | Fully Implemented |
| SPEC-021 | Implementation Guide | L3 | Approved | Fully Implemented |
| SPEC-030 | Multi-Agent Architecture | L4 | Approved | Fully Implemented |
| SPEC-031 | Memory & Knowledge Architecture | L4 | Draft | Partially Implemented |
| SPEC-032 | Autonomous Learning & Evolution | L4 | Draft | Partially Implemented |
| SPEC-033 | Risk Intelligence & Portfolio Construction | L4 | Draft | Partially Implemented |
| SPEC-034 | Simulation & Digital Twin | L4 | Draft | Prototype |
| SPEC-040 | Validation Framework | L5 | Approved | Fully Implemented |
| SPEC-050 | Operational Architecture | L6 | Pending Import | Partially Implemented |
| SPEC-060 | IKROS Architecture | L7 | Draft | Missing |

## Key Governance Rules

1. Every specification must be registered in `registry/SPECIFICATION_REGISTRY.yaml`
2. Every specification must follow the versioning lifecycle in `policies/VERSIONING_POLICY.md`
3. No implementation may begin without an approved specification at L1 or higher
4. Specifications supersede prior documents — all conflicts resolved in favor of specs
5. ARB approval required for any Level 0 or Level 1 specification change

## Traceability

All specifications in this library trace to `03-engineering/TRACEABILITY_MATRIX.yaml`
via requirements NFR-033, NFR-034, NFR-035.

The full bidirectional traceability map is in `registry/CONFORMANCE_MATRIX.md`.
