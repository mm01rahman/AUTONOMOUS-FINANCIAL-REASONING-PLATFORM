# AFRP_BASELINE_v1 — Platform Architecture Baseline Anchor

> **Authority Level:** Level 1 (GOV-002) · **Baseline:** AFRP-BASELINE-1.0.0

```text
========================================================================================
                 AUTONOMOUS FINANCIAL REASONING PLATFORM (AFRP)
                     MASTER ENGINEERING DOCUMENTATION SUITE
========================================================================================
 Suite Baseline ID:   AFRP-BASELINE-1.0.0
 Baseline Tag:        eos-baseline-v1.0 (Commit: m1.1-start)
 Governance Protocol: Execution Governance Protocol (EGP-2.0)
 Repository OS:       ROS-1.0.0 / AEF-01 / WPS-1.0 / ERS-1.0 / RSM-1.0
 Effective Date:      July 31, 2026
 Authority:           Architecture Review Board (ARB) & Engineering OS Core
 Target Consumer:     EGP-2.0 Compliant AI Coding Agents (AEF-02) & Human ARB Reviewers
========================================================================================
```

This anchor binds the Level-1 architecture surface referenced by GOV-002. The
normative content lives in the constituent documents; consult them via
`REPOSITORY_MANIFEST.yaml` → `document_index`:

| Document | Specification ID | Canonical Path |
| --- | --- | --- |
| Engineering Constitution | CPG-00 / GOV-001/002 | `00-governance/000_ENGINEERING_CONSTITUTION.md` |
| Formal System Glossary | GLOSS-001 | `02-architecture/050_FORMAL_SYSTEM_GLOSSARY.md` |
| System Architecture | ARCH-001/002, NFR, FIT, EDR | `02-architecture/100_SYSTEM_ARCHITECTURE.md` |
| Runtime Architecture | RUN-001/002, SYS-03 | `02-architecture/110_RUNTIME_ARCHITECTURE.md` |
| Engineering Operating System | EOS-001/002/003 | `03-engineering/120_ENGINEERING_OPERATING_SYSTEM.md` |
| Mathematical Foundation | MATH-001 | `02-architecture/130_MATHEMATICAL_FOUNDATION.md` |
| Reference Specification | REF-001 | `02-architecture/200_REFERENCE_SPECIFICATION.md` |
| Implementation Guide | IMP-001 | `03-engineering/300_IMPLEMENTATION_GUIDE.md` |

Wire contracts (`proto/afrp/v1/*.proto`) are part of this Level-1 surface; changes
require an ADR with ARB approval (GOV-002) and must pass compatibility validation
(NFR-010, EDR-010).

Genesis decisions and toolchain waivers: `02-architecture/adr/ADR-0001-adopt-baseline.md`,
`02-architecture/adr/ADR-0002-genesis-normalizations.md`.
