---
document_id: AFRP-GOV-AUDIT-001
title: AFRP Architecture Baseline Repository Audit
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Governance Assurance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Pull request with ARB review
dependencies:
  - 00-governance/000_ENGINEERING_CONSTITUTION.md
  - REPOSITORY_MANIFEST.yaml
referenced_by:
  - docs/governance/PHASE_1_COMPLETION_REPORT.md
review_policy: Review at every architecture baseline release
---

# AFRP Architecture Baseline Repository Audit

## 1. Scope and Method

This report records the read-only audit performed before Phase 1 baseline-freeze
changes. It covers architecture, governance, engineering standards, schemas,
contracts, ADRs, repository structure, the capability registry, and traceability.

Methods:

- Enumerated all tracked files and governed candidate formats.
- Verified EGP-2.0 baseline fingerprints with `afrp boot`.
- Verified capability DAG acyclicity and completion with `afrp plan`.
- Verified TVM coverage with `afrp health --assert-full`.
- Compared SHA256 values to detect exact duplicate governed artifacts.
- Searched canonical terminology, identifiers, paths, version markers, ownership,
  authority, status, and change-policy metadata.

No repository files were modified during the audit.

## 2. Repository Inventory

| Measure | Observed |
| --- | ---: |
| Tracked files | 172 |
| Markdown | 20 |
| YAML/YML | 76 |
| JSON | 3 |
| Protobuf | 3 |
| Python | 63 |
| Governed candidate files (`md/yaml/json/proto`) | 102 |
| Exact duplicate groups | 0 |
| Capabilities | 33/33 complete |
| TVM requirements | 47/47 covered |
| Work Packages / evidence records | 31 / 31 |
| Existing immutable fingerprint entries | 20, all verified |
| Tags | `m1.1-start`, `v1.0.0` |

The repository structure matches the topology declared in
`REPOSITORY_MANIFEST.yaml`. No orphan top-level product directory was found.

## 3. Baseline Document Audit

`Version` below is the effective version inferred from the adopted
AFRP-BASELINE-1.0.0 where a document does not carry an explicit version field.

| Artifact | Purpose / owner | Version | Completeness | Duplicate/conflict review | Missing metadata |
| --- | --- | --- | --- | --- | --- |
| `00-governance/000_ENGINEERING_CONSTITUTION.md` | Constitutional authority; ARB | 1.0.0 | Complete | Path alias conflict is resolved by ADR-0002 | Version, owner, dates, dependency map |
| `00-governance/KERNEL.md` | Agent boot sequence; ARB/EOS | 1.0.0 | Complete; 265/400 words | No duplicate | Owner, dates, referenced-by |
| `00-governance/BASELINE_FINGERPRINT.yaml` | Immutable SHA256 ledger; ARB | 1.0 | Complete for its declared 20-file scope | Intentionally excludes living ledgers per ADR-0002 | Owner, authority, review policy |
| `01-vision/CHARTER.md` | Product mission; Product/ARB | 1.0.0 | Complete | Intentionally derives from Constitution | Full metadata |
| `02-architecture/050_FORMAL_SYSTEM_GLOSSARY.md` | Canonical terminology; ARB | GLOSS-001 / 1.0.0 | Complete | No exact duplicate | Owner, dates, dependencies |
| `02-architecture/100_SYSTEM_ARCHITECTURE.md` | Products, NFR, FIT, EDR; ARB | ARCH-001 / 1.0.0 | Complete | EDR-10..12 use non-padded source identifiers | Owner, dates, referenced-by |
| `02-architecture/110_RUNTIME_ARCHITECTURE.md` | Six layers and SYS-03; ARB | RUN-001 / 1.0.0 | Complete | No conflict found | Owner, dates, dependencies |
| `02-architecture/130_MATHEMATICAL_FOUNDATION.md` | State, PCR5, entropy, optimization; ARB | MATH-001 / 1.0.0 | Complete | No conflict found | Owner, dates, review policy |
| `02-architecture/200_REFERENCE_SPECIFICATION.md` | Envelope, CIO taxonomy, schemas, EGP; ARB | REF-001 / 1.0.0 | Complete | No conflict found | Owner, dates, dependencies |
| `02-architecture/AFRP_BASELINE_v1.md` | Level-1 architecture index; ARB | 1.0.0 | Complete | Correctly points to modular canonical docs | Full referenced-by list |
| `02-architecture/adr/ADR-0001-adopt-baseline.md` | Baseline adoption decision; ARB | 1.0 | Accepted | No conflict | Standard metadata fields are partial |
| `02-architecture/adr/ADR-0002-genesis-normalizations.md` | Path/tool normalization; ARB | 1.0 | Accepted | Resolves Constitution path alias | Standard metadata fields are partial |
| `02-architecture/adr/ADR-0003-contract-enforcement.md` | Wire enforcement strategy; ARB | 1.0 | Accepted | EDR-10 spelling follows source document | Standard metadata fields are partial |
| `02-architecture/adr/ADR-TEMPLATE.md` | ADR authoring template; ARB | 1.0 | Complete | Placeholder identifiers are intentional template syntax | Owner/version/review policy |
| `03-engineering/120_ENGINEERING_OPERATING_SYSTEM.md` | EOS capability contract; EOS Core | EOS-001 / 1.0.0 | Complete | Diagram says `EPS-1.0`; prose says canonical `ERS-1.0` | Owner, dates, dependencies |
| `03-engineering/300_IMPLEMENTATION_GUIDE.md` | Genesis/bootstrap historical guide; EOS Core | IMP-001 / 1.0.0 | Complete | Embedded `0.1.0` is historical bootstrap, not release drift | Owner, status, historical marker |
| `03-engineering/BUILD_PROFILE.yaml` | Toolchain and quality gates; Lead Engineer | 1.0 | Complete | W-001/W-002 are explicit waivers | Referenced-by/review policy |
| `03-engineering/CAPABILITY_REGISTRY.yaml` | Capability lifecycle DAG; EOS | 1.0 | Complete; 33/33 | DAG is acyclic; no duplicate ids | Change/review policy |
| `03-engineering/TRACEABILITY_MATRIX.yaml` | Requirement evidence ownership; ARB/EOS | 1.0 | Complete; 47/47 | Normalizes `EDR-010` from source `EDR-10` | Change/review policy |
| `03-engineering/DEPRECATION_POLICY.yaml` | EDR-012 lifecycle; Lead Engineer | 1.0 | Complete | No conflict | Owner, authority, dependencies |
| `04-ai-framework/AI_ENGINEER_PLAYBOOK.md` | AEF role/write procedure; EOS Core | AEF-01 / 1.0 | Complete | References canonical governed artifacts | Full metadata |
| `04-ai-framework/ORCHESTRATOR.md` | AEF-01 orchestration runbook; EOS Core | 1.0 | Complete | No conflict | Full metadata |
| `09-validation/schemas/wps-1.0.schema.json` | Work Package contract; ARB/EOS | WPS-1.0 | Complete | Single schema owner | Owner/authority metadata |
| `09-validation/schemas/ers-1.0.schema.json` | Execution evidence contract; ARB/EOS | ERS-1.0 | Complete | Single schema owner | Owner/authority metadata |
| `proto/afrp/v1/annotations.proto` | Contract trace options; ARB | afrp.v1 / 1.0 | Complete | No duplicate options | Owner/change policy outside comments |
| `proto/afrp/v1/envelope.proto` | Universal transport header; ARB | ENVELOPE-v1 | Complete | Matches REF-001 | Owner/change policy outside comments |
| `proto/afrp/v1/cio.proto` | CIO-01..12 wire contracts; ARB | afrp.v1 / 1.0 | Complete | No duplicate message ownership | Owner/change policy outside comments |
| `09-validation/contracts/afrp_v1.snapshot.json` | Wire-compatibility oracle; ARB | 1.0 | Complete | Derived from canonical proto files | Owner/authority metadata |
| `REPOSITORY_MANIFEST.yaml` | Canonical topology/document index; ARB | 1.0 | Complete | Single topology owner | Review policy |
| `10-release/ARCHITECTURE_REVIEW_REPORT_v1.0.md` | Core 1.0 release review; ARB | 1.0.0 | Complete | Release evidence, not architecture authority | Full metadata |
| `10-release/RELEASE_MANIFEST_v1.0.yaml` | Core release manifest; Release/ARB | 1.0.0 | Complete | No conflict | Review policy |

## 4. Work Package and Evidence Families

| Family | Purpose | Version/completeness | Ownership / duplication |
| --- | --- | --- | --- |
| `05-work-packages/WP-IMP-0003..0033.yaml` | Immutable implementation contracts | WPS-1.0; 31/31 schema-valid | One WP per capability; no duplicated ids |
| `05-work-packages/WP-IMP-*/evidence/EXEC-001..031.yaml` | Execution evidence | ERS-1.0; 31/31 schema-valid | One evidence id per WP; no duplicated ids |
| `03-engineering/REPOSITORY_HEALTH.yaml` | Measured repository state | 1.0.0; GREEN | Operational ledger, not architecture authority |

These are controlled mutable lifecycle records. They are not byte-frozen with the
architecture corpus because their status and evidence fields change through governed
execution.

## 5. Findings

### A-01 - Canonical architecture is modular, not a single "Architecture Bible"

The repository has no file named Architecture Bible. Canonical architecture is the
modular Level-1 set indexed by `02-architecture/AFRP_BASELINE_v1.md`. Treating a new
"Bible" as authoritative would duplicate ownership.

### A-02 - Canonical engineering rules are distributed by concern

There is no Engineering Bible, Testing Standards, or Documentation Standards file.
The current canonical owners are Constitution + ARCH-001 EDR/FIT + BUILD_PROFILE +
WPS quality gates. Consolidation would change ownership and therefore requires an ADR.

### A-03 - Constitution filename alias is historical and resolved

GOV-002 names `000_CPG_CONSTITUTION.md`; the canonical suite header names
`000_ENGINEERING_CONSTITUTION.md`. ADR-0002 already resolves this in favor of the
existing canonical path. No duplicate alias file should be created.

### A-04 - Evidence acronym inconsistency

The EOS diagram labels the telemetry engine `EPS-1.0`; every normative prose section,
schema, Work Package, and evidence record uses `ERS-1.0`. This is a documentation
defect, not a competing schema. Correcting the Level-2 EOS document should be proposed
through an ADR or baseline patch, not silently edited during freeze.

### A-05 - EDR identifier formatting differs

ARCH-001 uses `EDR-10`, `EDR-11`, `EDR-12`; machine ledgers normalize these as
`EDR-010`, `EDR-011`, `EDR-012`. Semantics are consistent. A future ADR should choose
one display convention.

### A-06 - Inline metadata is incomplete and inconsistent

Most Markdown documents carry authority/specification headers but not the full
requested metadata set. Rewriting all protected files would invalidate their existing
SHA256 baseline. Phase 1 should therefore add a canonical sidecar metadata registry,
while all newly created freeze documents carry complete inline metadata.

### A-07 - Existing fingerprint has a narrower purpose

`00-governance/BASELINE_FINGERPRINT.yaml` correctly freezes the original immutable
governance corpus and excludes living ledgers under ADR-0002. Phase 1 needs a separate
architecture-freeze ledger covering protected architecture, schemas, contracts, and
freeze-governance documents without changing the existing ledger's semantics.

## 6. Files Created in Step 1

- `docs/governance/REPOSITORY_AUDIT.md`

## 7. Files Modified in Step 1

None.

## 8. Rationale

The audit is recorded separately so approved architecture remains byte-identical.
Findings distinguish true conflicts from intentional historical aliases and mutable
execution records.

## 9. Risks

- Adding a second architecture owner would create ambiguity; Phase 1 must map, not
  copy, canonical content.
- Prepending metadata to protected documents would invalidate current fingerprints;
  use a sidecar registry unless an ADR authorizes corpus rewrites.
- Treating completed WP/evidence ledgers as immutable architecture would prevent
  governed lifecycle updates.

## 10. Completion Status

**STEP 1: COMPLETE**

The repository audit is complete, no architecture was modified, and the identified
issues are bounded for Steps 2-7.
