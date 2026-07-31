---
document_id: AFRP-BASELINE-MANIFEST-001
title: AFRP Architecture Baseline Manifest
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Baseline Governance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Governed by BASELINE_FREEZE_POLICY.md
dependencies:
  - 02-architecture/AFRP_BASELINE_v1.md
  - docs/governance/CANONICAL_SOURCE_MAP.yaml
  - docs/governance/DOCUMENT_METADATA.yaml
referenced_by:
  - docs/governance/BASELINE_FREEZE_POLICY.md
  - docs/governance/ARCHITECTURE_BASELINE_FINGERPRINT.yaml
  - tools/baseline_gate.py
review_policy: Review at every architecture baseline release
---

# AFRP Architecture Baseline Manifest

## 1. Baseline Identity

| Field | Value |
| --- | --- |
| Baseline | **AFRP Architecture Baseline v1.0.0** |
| Baseline tag | `v1.0.0-baseline` |
| Release date | 2026-07-31 |
| Constitutional baseline | AFRP-BASELINE-1.0.0 |
| Governance protocol | EGP-2.0 |
| Repository OS | ROS-1.0.0 |
| Approval authority | Architecture Review Board |
| Canonical ownership map | `docs/governance/CANONICAL_SOURCE_MAP.yaml` |
| Metadata registry | `docs/governance/DOCUMENT_METADATA.yaml` |
| Freeze fingerprint | `docs/governance/ARCHITECTURE_BASELINE_FINGERPRINT.yaml` |

This manifest defines membership only. It does not replace, summarize, or override any
listed artifact.

## 2. Protected Constitutional Governance

| Artifact | Protection |
| --- | --- |
| `00-governance/000_ENGINEERING_CONSTITUTION.md` | Level 0, immutable except constitutional amendment |
| `00-governance/KERNEL.md` | Level 0 boot contract |
| `00-governance/BASELINE_FINGERPRINT.yaml` | Genesis integrity ledger; scope preserved under ADR-0002 |

## 3. Protected Vision and Architecture

| Artifact | Document ID |
| --- | --- |
| `01-vision/CHARTER.md` | AFRP-CHARTER-001 |
| `02-architecture/050_FORMAL_SYSTEM_GLOSSARY.md` | GLOSS-001 |
| `02-architecture/100_SYSTEM_ARCHITECTURE.md` | ARCH-001 |
| `02-architecture/110_RUNTIME_ARCHITECTURE.md` | RUN-001 |
| `02-architecture/130_MATHEMATICAL_FOUNDATION.md` | MATH-001 |
| `02-architecture/200_REFERENCE_SPECIFICATION.md` | REF-001 |
| `02-architecture/AFRP_BASELINE_v1.md` | AFRP-ARCH-BASELINE-001 |

## 4. Protected Architecture Decisions

| Artifact | Status |
| --- | --- |
| `02-architecture/adr/ADR-0001-adopt-baseline.md` | Accepted, immutable history |
| `02-architecture/adr/ADR-0002-genesis-normalizations.md` | Accepted, immutable history |
| `02-architecture/adr/ADR-0003-contract-enforcement.md` | Accepted, immutable history |
| `02-architecture/adr/ADR-TEMPLATE.md` | Controlled ADR structure |

The ADR directory is append-only. New approved ADRs do not mutate accepted historical
records; an ADR may supersede another by reference.

## 5. Protected Engineering Standards

| Artifact | Document ID / concern |
| --- | --- |
| `03-engineering/120_ENGINEERING_OPERATING_SYSTEM.md` | EOS-001 |
| `03-engineering/300_IMPLEMENTATION_GUIDE.md` | IMP-001, historical bootstrap guidance |
| `03-engineering/BUILD_PROFILE.yaml` | AFRP-BUILD-001 |
| `03-engineering/DEPRECATION_POLICY.yaml` | AFRP-DEPRECATION-001 |
| `04-ai-framework/AI_ENGINEER_PLAYBOOK.md` | AEF-01 |
| `04-ai-framework/ORCHESTRATOR.md` | AEF-ORCH-001 |

## 6. Protected Schemas and Contracts

| Artifact | Contract / protection |
| --- | --- |
| `09-validation/schemas/wps-1.0.schema.json` | WPS-1.0 |
| `09-validation/schemas/ers-1.0.schema.json` | ERS-1.0 |
| `proto/afrp/v1/annotations.proto` | Governance options |
| `proto/afrp/v1/envelope.proto` | ENVELOPE-v1 |
| `proto/afrp/v1/cio.proto` | CIO-01..CIO-12 v1 |
| `09-validation/contracts/afrp_v1.snapshot.json` | NFR-010 compatibility oracle |

## 7. Protected Repository Governance

| Artifact | Purpose |
| --- | --- |
| `REPOSITORY_MANIFEST.yaml` | Canonical repository topology and document paths |
| `docs/governance/CANONICAL_SOURCE_MAP.yaml` | Machine-readable singular ownership |
| `docs/governance/CANONICAL_SOURCE_MAP.md` | Human-readable dependency map |
| `docs/governance/DOCUMENT_METADATA.yaml` | Canonical metadata registry |
| `docs/governance/DOCUMENT_METADATA.md` | Metadata standard |
| `docs/governance/BASELINE_MANIFEST.md` | Baseline membership |
| `docs/governance/BASELINE_FREEZE_POLICY.md` | Change and version policy |
| `docs/governance/ARCHITECTURE_REVIEW_CHECKLIST.md` | PR architecture review procedure |
| `docs/governance/DEFINITION_OF_DONE.md` | Repository-wide completion contract |
| `docs/governance/ARCHITECTURE_BASELINE_FINGERPRINT.yaml` | SHA256 freeze ledger |

These Phase 1 files are assurance/procedure artifacts. They are not Level-0
constitutional authorities and cannot override canonical owners in Sections 2-6.

## 8. Controlled Mutable Artifacts

The following are governed but not byte-frozen architecture:

| Family | Why mutable | Governing owner |
| --- | --- | --- |
| `03-engineering/CAPABILITY_REGISTRY.yaml` | Capability lifecycle status changes | EOS-001 / FIT-001 |
| `03-engineering/TRACEABILITY_MATRIX.yaml` | Evidence links evolve | ARCH-001 FIT-007 |
| `03-engineering/REPOSITORY_HEALTH.yaml` | Measured health changes per run | EOS-HEALTH |
| `05-work-packages/WP-*.yaml` | Lifecycle/result fields change under WPS | WPS-1.0 |
| `05-work-packages/WP-*/evidence/EXEC-*.yaml` | Append-only execution evidence | ERS-1.0 |
| `06-runtime/`, `07-research/`, `tools/`, `tests/` | Implementations evolve through WPs | Architecture + WPS |
| `08-operations/` | Environment policy/configuration evolves | NFR/EDR + reviewed WP |
| `.github/workflows/quality.yml` | CI implementation evolves | BUILD_PROFILE |
| `pyproject.toml`, `Cargo.toml`, `uv.lock` | Build implementation/version evolves | BUILD_PROFILE |
| `10-release/`, `CHANGELOG.md` | Append-only release records | Release process |

Mutable means change is permitted through its governing process. It does not permit
architecture override.

## 9. Excluded Assurance Records

The following Phase 1 records document the freeze but are not normative architecture:

- `docs/governance/REPOSITORY_AUDIT.md`
- `docs/governance/BASELINE_ISSUES_AND_RECOMMENDATIONS.md`
- `docs/governance/GOVERNANCE_VALIDATION_REPORT.md`
- `docs/governance/PHASE_1_COMPLETION_REPORT.md`
- `docs/releases/v1.0.0-baseline.md`

## 10. Files Created in Step 5

- `docs/governance/BASELINE_MANIFEST.md`

## 11. Files Modified in Step 5

None.

## 12. Rationale

The manifest freezes architecture and its governance mechanics while retaining the
existing constitutional distinction between immutable sources and governed living
ledgers.

## 13. Risks

- Misclassifying lifecycle ledgers as byte-frozen would block Phase 2 execution.
- Misclassifying source code as architecture would let implementation override design.
- The new architecture fingerprint must exclude itself to avoid recursive hashing.

## 14. Completion Status

**STEP 5: COMPLETE**

Architecture Baseline v1.0.0 membership is explicit and contains 36 protected
artifacts with standardized metadata.
