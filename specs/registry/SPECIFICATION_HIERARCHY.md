# AFRP Specification Hierarchy

> **Document ID:** `SPEC-HIER-1.0` | **Authority:** ARB | **Status:** Active
> **Work Package:** WP-IMP-0040

## 1. Hierarchy Overview

The AFRP specification hierarchy enforces a strict authority chain. Higher levels govern
lower levels. No lower-level specification may contradict a higher-level one.

```
Level 0 — Institutional Constitution (Immutable)
│   SPEC-000: Engineering Constitution
│   Authority: Unanimous ARB + Principal Architect
│   Amendment: Formal ADR + Baseline Version Bump
│
└── Level 1 — Architecture Specifications (Semi-Immutable)
    │   SPEC-001: System Architecture
    │   SPEC-002: Runtime Architecture
    │   SPEC-003: Mathematical Foundation
    │   SPEC-004: Reference Specification
    │   SPEC-005: Production Engineering Architecture [PENDING IMPORT]
    │   Authority: ARB
    │   Amendment: Formal ADR
    │
    ├── Level 2 — Research Specifications
    │   │   SPEC-010: Research Standard RS-1.0
    │   │   SPEC-011: Gold Market Specification [PENDING IMPORT]
    │   │   SPEC-012: Alpha Discovery Bible [PENDING IMPORT]
    │   │   SPEC-013: Alpha Validation Framework
    │   │   SPEC-014: Feature Engineering Standard
    │   │   SPEC-015: Financial Reasoning Framework
    │   │   Authority: Principal Quantitative Researcher
    │   │   Amendment: Pull Request with ARB Review
    │   │
    │   └── Level 3 — Engineering Specifications
    │       │   SPEC-020: Engineering Operating System
    │       │   SPEC-021: Implementation Guide
    │       │   Authority: Lead Engineer / Tech Lead
    │       │   Amendment: Pull Request with explicit review
    │       │
    │       └── Level 4 — Implementation (Runtime) Specifications
    │           │   SPEC-030: Multi-Agent Architecture
    │           │   SPEC-031: Memory & Knowledge Architecture
    │           │   SPEC-032: Autonomous Learning & Evolution
    │           │   SPEC-033: Risk Intelligence & Portfolio Construction
    │           │   SPEC-034: Simulation & Digital Twin
    │           │   Authority: EGP-2.0 / Orchestrator
    │           │   Amendment: Governed Work Package
    │           │
    │           ├── Level 5 — Validation Specifications
    │           │       SPEC-040: Validation Framework
    │           │       Authority: VALIDATION team
    │           │       Amendment: Governed Work Package
    │           │
    │           ├── Level 6 — Operational Specifications
    │           │       SPEC-050: Operational Architecture [PENDING IMPORT]
    │           │       Authority: OPS team
    │           │       Amendment: Governed Work Package
    │           │
    │           └── Level 7 — Knowledge & Intelligence Specifications
    │                   SPEC-060: IKROS Architecture [DRAFT]
    │                   Authority: ARB
    │                   Amendment: Formal ADR + ARB Approval
```

## 2. Inheritance Rules

### 2.1 Authority Chain

Every specification inherits constraints from all higher-level specifications.

| Rule | Description |
|------|-------------|
| `INHERIT-001` | Level N specification MUST NOT contradict any Level < N specification |
| `INHERIT-002` | Conflicts resolve in favor of the higher-level specification |
| `INHERIT-003` | Changes to Level 0 or Level 1 require full cascade review to all dependent specs |
| `INHERIT-004` | New capabilities MUST trace to at least one approved specification |
| `INHERIT-005` | Research decisions MUST trace to Level 2 specifications |

### 2.2 Amendment Mechanisms by Level

| Level | Amendment Path | Required Approvals |
|-------|---------------|--------------------|
| 0 | ADR + Baseline bump | Unanimous ARB + Principal Architect |
| 1 | ADR | ARB |
| 2 | ADR or PR with ARB review | Principal Quantitative Researcher + ARB |
| 3 | PR with explicit review | Lead Engineer + Tech Lead |
| 4 | Governed Work Package | EGP-2.0 compliance + Human ARB |
| 5 | Governed Work Package | Validation Lead |
| 6 | Governed Work Package | OPS Lead |
| 7 | ADR + ARB Approval | ARB |

### 2.3 Traceability Requirements

Every Work Package MUST trace to one or more specifications:

```
Work Package
    ↓ implements_spec
Specification
    ↓ governs
Capability
    ↓ implements
Runtime Module / Research Tool
    ↓ verified_by
Validation / Tests
    ↓ produces
Evidence Record
```

## 3. Specification Status Lifecycle

```
Draft → Review → Approved → Implemented → Validated → Deprecated → Archived
```

See `policies/VERSIONING_POLICY.md` for detailed promotion rules.

## 4. Governing Principles from SPEC-000

The following constitutional articles directly govern specification authority:

- **Article I (Truth):** Mathematics (SPEC-003) has precedence over all lower-level specs
- **Article IV (Traceability):** Every artifact traces back to a requirement via TVM
- **Article VII (Evolution):** Platform evolves only through Requirements, Evidence, ADRs, Gates
- **Article IX (Knowledge):** Every failure and benchmark becomes institutional memory (SPEC-060)
- **Article X (Human Authority):** Humans remain accountable for architecture specifications
