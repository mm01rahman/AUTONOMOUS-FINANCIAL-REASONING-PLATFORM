# AFRP Specification Dependency Graph

> **Document ID:** `SPEC-DEP-1.0` | **Authority:** ARB | **Status:** Active
> **Work Package:** WP-IMP-0040

## 1. Dependency Graph

```
SPEC-000 (Constitution)
    │
    ├── SPEC-001 (System Architecture)
    │       │
    │       ├── SPEC-002 (Runtime Architecture)
    │       │       │
    │       │       ├── SPEC-030 (Multi-Agent Architecture)
    │       │       │       └── [L2 agents: MAC, MIC, LIQ, REG, FOR, BEH]
    │       │       │
    │       │       ├── SPEC-031 (Memory & Knowledge)
    │       │       │       ├── [L1-MEM, L1-RDB]
    │       │       │       └── SPEC-060 (IKROS Architecture) ← not yet implemented
    │       │       │
    │       │       ├── SPEC-032 (Autonomous Learning)
    │       │       │       └── [L6-OPT]
    │       │       │
    │       │       ├── SPEC-033 (Risk & Portfolio)
    │       │       │       └── [L4-DEC, L4-VAL, L5-EXE]
    │       │       │
    │       │       ├── SPEC-034 (Simulation & Digital Twin)
    │       │       │       └── [L3-SIM]
    │       │       │
    │       │       └── SPEC-040 (Validation Framework)
    │       │               └── [tools/verification, tools/system_gate.py]
    │       │
    │       ├── SPEC-003 (Mathematical Foundation)
    │       │       ├── SPEC-015 (Financial Reasoning Framework)
    │       │       │       └── [L3-WRM, L4-FUS, L4-DEC]
    │       │       └── SPEC-013 (Alpha Validation Framework)
    │       │               └── [tools/verification, tools/backtest]
    │       │
    │       ├── SPEC-004 (Reference Specification)
    │       │       └── [proto/afrp/v1/, contracts/cio.py]
    │       │
    │       └── SPEC-005 (Production Engineering) [PENDING IMPORT]
    │               └── [08-operations/]
    │
    ├── SPEC-010 (Research Standard RS-1.0)
    │       │
    │       ├── SPEC-011 (Gold Market Specification) [PENDING IMPORT]
    │       │       └── [L1-ING, L1-FST, L2-MAC, L2-MIC, L2-LIQ]
    │       │
    │       ├── SPEC-012 (Alpha Discovery Bible) [PENDING IMPORT]
    │       │       └── [tools/alpha_research]
    │       │
    │       ├── SPEC-013 (Alpha Validation Framework)
    │       │
    │       ├── SPEC-014 (Feature Engineering Standard)
    │       │       └── [L1-FST, L2-BASE..L2-BEH]
    │       │
    │       └── SPEC-015 (Financial Reasoning Framework)
    │
    └── SPEC-020 (Engineering OS)
            │
            └── SPEC-021 (Implementation Guide)
```

## 2. Critical Path Analysis

### 2.1 Blocking Dependencies for IKROS (WP-IMP-0041)

```
SPEC-000 ✓
    → SPEC-001 ✓
        → SPEC-010 (DRAFT — requires formal approval)
            → SPEC-013 (DRAFT — requires formal approval)
                → SPEC-031 (DRAFT — requires formal approval)
                    → SPEC-060 (DRAFT — requires ARB approval)
                        → WP-IMP-0041 (IKROS Architecture) ← BLOCKED
```

**SPEC-060 is the gate** for IKROS implementation. This spec has been imported (WP-IMP-0040)
but requires ARB approval before implementation begins.

### 2.2 Missing Specification Dependencies

| Gap | Impact | Specs Affected | Priority |
|-----|--------|----------------|----------|
| Gold Market Specification (SPEC-011) | L2 agents lack instrument-specific design | L2-MAC, L2-MIC, L2-LIQ | High |
| Alpha Discovery Bible (SPEC-012) | No canonical alpha catalogue | ALPHA-RESEARCH | High |
| Production Engineering (SPEC-005) | Deployment lacks formal specification | OPS-DEPLOY | Medium |
| Digital Twin depth (SPEC-034) | L3-SIM is prototype, not full spec | L3-SIM | Medium |
| Operational Architecture (SPEC-050) | Operations underdocumented | OPS-DEPLOY | Low |

## 3. Circular Dependency Checks

**No circular dependencies detected.** The specification DAG is acyclic.

All dependency arrows point strictly from lower levels to higher levels (consumer → provider).

## 4. Version Compatibility Matrix

| Consumer Spec | Depends On | Compatible Versions |
|---------------|-----------|---------------------|
| SPEC-030 | SPEC-002 | ≥ 1.0 |
| SPEC-031 | SPEC-002, SPEC-060 | ≥ 1.0 / any |
| SPEC-032 | SPEC-002, SPEC-003 | ≥ 1.0 |
| SPEC-033 | SPEC-002, SPEC-003 | ≥ 1.0 |
| SPEC-034 | SPEC-002, SPEC-003 | ≥ 1.0 |
| SPEC-040 | SPEC-001, SPEC-002 | ≥ 1.0 |
| SPEC-060 | SPEC-000..SPEC-032 | ≥ 1.0 for Lvl 0-1 |

## 5. Runtime Module → Specification Mapping

| Runtime Module | Primary Spec | Secondary Specs |
|----------------|-------------|-----------------|
| `06-runtime/layer1` | SPEC-002 | SPEC-014, SPEC-004 |
| `06-runtime/layer2` | SPEC-030 | SPEC-014, SPEC-003 |
| `06-runtime/layer3` | SPEC-002 | SPEC-003, SPEC-034, SPEC-015 |
| `06-runtime/layer4` | SPEC-033 | SPEC-003, SPEC-015 |
| `06-runtime/layer5` | SPEC-033 | SPEC-002, SPEC-004 |
| `06-runtime/layer6` | SPEC-032 | SPEC-003 |
| `tools/verification` | SPEC-040 | SPEC-013 |
| `tools/backtest` | SPEC-040 | SPEC-010, SPEC-013 |
| `tools/alpha_research` | SPEC-012 | SPEC-013, SPEC-010 |
| `tools/paper_trading` | SPEC-033 | SPEC-010 |
