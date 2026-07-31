---
document_id: AFRP-GOV-ISSUES-001
title: Architecture Baseline Issues and Recommendations
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Governance Assurance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Pull request; ADR required for recommendations that change ownership or architecture
dependencies:
  - docs/governance/REPOSITORY_AUDIT.md
  - docs/governance/CANONICAL_SOURCE_MAP.yaml
referenced_by:
  - docs/governance/GOVERNANCE_VALIDATION_REPORT.md
  - docs/governance/PHASE_1_COMPLETION_REPORT.md
review_policy: Review at every architecture baseline release
---

# Architecture Baseline Issues and Recommendations

## 1. Findings

### 1.1 Confirmed defects and inconsistencies

| ID | Finding | Severity | Current effect | Recommendation | ADR required? |
| --- | --- | --- | --- | --- | --- |
| BL-001 | EOS diagram says `EPS-1.0`; normative prose/schema say `ERS-1.0` | Low | Terminology ambiguity only; executable contract is unambiguous | Correct diagram label in a baseline patch | Yes: bundle in proposed ADR-0004 because a protected engineering standard changes |
| BL-002 | Source architecture displays `EDR-10..12`; machine ledgers use `EDR-010..012` | Low | No semantic mismatch; searches can miss aliases | Adopt zero-padded display ids consistently in the next baseline | Yes: proposed ADR-0004 |
| BL-003 | Constitution table names `000_CPG_CONSTITUTION.md`; canonical file is `000_ENGINEERING_CONSTITUTION.md` | Resolved | None; ADR-0002 and manifest select canonical path | Preserve the existing decision; do not create an alias copy | No new ADR |
| BL-004 | Generic terms "Architecture Bible" and "Engineering Bible" do not map to repository filenames | Low | External instructions can imply nonexistent monoliths | Use the modular canonical source map; never create duplicate Bibles | No |
| BL-005 | Protected documents have inconsistent inline metadata | Medium | Ownership/version discovery depends on inference | Add a sidecar metadata registry; leave protected bytes unchanged | No architecture ADR; governance-only |
| BL-006 | Original fingerprint covers 20 immutable genesis artifacts, not the full architecture-freeze set | Medium | Phase 1 freeze cannot verify all schemas/contracts/procedures | Add a distinct architecture-baseline fingerprint with explicit scope | No; preserve ADR-0002 semantics |
| BL-007 | Implementation Guide embeds bootstrap version `0.1.0` while release is `1.0.0` | Informational | Could be misread as current version | Classify the embedded value as historical bootstrap content in metadata/audit | No |
| BL-008 | No machine gate validates baseline metadata and canonical ownership | Medium | Sidecar metadata could drift | Add `tools/baseline_gate.py` and CI execution | No; implements existing governance |
| BL-009 | Requested `docs/governance/` path is outside canonical `00-governance/` | Medium | Risk of competing Level-0 authority | Treat `docs/governance/` as Phase 1 assurance/procedure overlay; Constitution remains sole Level-0 owner | No, provided no document claims Level-0 authority |

### 1.2 Duplicate content

- Exact SHA256 duplicate groups: **0**.
- Derived summaries exist (`CHARTER`, baseline anchor, release report) but explicitly
  reference their canonical sources and do not duplicate ownership.
- WP/evidence files repeat schema-shaped fields by design; schemas own the contract.

### 1.3 Circular references

- Capability DAG: **acyclic** (FIT-001 PASS).
- Canonical source dependencies: directed from Constitution to architecture to
  engineering contracts to instances; no ownership cycle found.
- ADRs depend on the architecture they govern but do not become upstream of the
  Constitution.

### 1.4 Orphan documents

No governed architecture/governance/schema/contract artifact is orphaned:

- Canonical artifacts are indexed by the repository manifest, baseline anchor, or
  the Phase 1 source map.
- ADRs are referenced by Work Packages or baseline documents.
- Release/health documents are operational outputs and intentionally outside the
  architecture authority chain.

### 1.5 Missing definitions

No missing definition blocks implementation. Terms in the runtime, mathematical, WPS,
ERS, EGP, and CIO domains are defined. The generic external labels "Architecture
Bible", "Engineering Bible", "Testing Standards", and "Documentation Standards" are
not canonical AFRP artifact names; the concern map resolves their intended ownership.

## 2. Recommendations

1. **Freeze without rewriting.** Preserve all protected document bytes and standardize
   metadata through a machine-validated sidecar registry.
2. **Keep fingerprint scopes separate.** Retain the genesis fingerprint unchanged and
   add an architecture-freeze fingerprint whose purpose is explicitly documented.
3. **Propose ADR-0004 after freeze.** Normalize `EPS`/`ERS` and `EDR-10`/`EDR-010`
   display conventions as a patch baseline; do not silently edit them here.
4. **Enforce ownership.** Validate unique concern owners from
   `CANONICAL_SOURCE_MAP.yaml`.
5. **Add CI governance gate.** Fail if a protected file is missing, metadata is
   incomplete, a digest changes, or ownership duplicates.
6. **Do not create monolithic Bibles.** Continue using modular architecture owners.

## 3. Files Created in Step 3

- `docs/governance/BASELINE_ISSUES_AND_RECOMMENDATIONS.md`

## 4. Files Modified in Step 3

None.

## 5. Rationale

Recommendations distinguish organization/freeze work authorized by Phase 1 from
architecture changes that require an ADR.

## 6. Risks

- Correcting protected terminology during freeze would violate the zero-redesign rule.
- Two fingerprints without clear scope could be mistaken for competing authorities.
- A metadata sidecar without CI enforcement would reintroduce drift.

## 7. Completion Status

**STEP 3: COMPLETE**

Problems are classified, no architecture was changed, and ADR-required corrections are
deferred explicitly.
