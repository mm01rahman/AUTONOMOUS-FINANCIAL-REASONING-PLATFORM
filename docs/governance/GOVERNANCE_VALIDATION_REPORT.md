---
document_id: AFRP-GOV-VALIDATION-001
title: AFRP Architecture Baseline Governance Validation Report
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Governance Assurance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Append a new report for each baseline; do not rewrite approved results
dependencies:
  - docs/governance/BASELINE_MANIFEST.md
  - docs/governance/BASELINE_FREEZE_POLICY.md
  - docs/governance/DOCUMENT_METADATA.yaml
  - docs/governance/CANONICAL_SOURCE_MAP.yaml
  - docs/governance/ARCHITECTURE_BASELINE_FINGERPRINT.yaml
referenced_by:
  - docs/governance/PHASE_1_COMPLETION_REPORT.md
  - docs/releases/v1.0.0-baseline.md
review_policy: Regenerate for every architecture baseline release
---

# AFRP Architecture Baseline Governance Validation Report

## 1. Validation Decision

**PASS - Architecture Baseline v1.0.0 is internally consistent and freeze-ready.**

Validation command:

```text
uv run python -m tools.baseline_gate
```

Observed result:

```text
baseline_gate: PASS
  protected artifacts: 36
  fingerprinted artifacts: 35
  canonical concerns: 26
  metadata: complete and unique
  dependencies: acyclic
  duplicate protected content: none
  KERNEL: <=400 words
```

The fingerprint ledger excludes itself to avoid recursive hashing. Its own integrity
is anchored by the immutable `v1.0.0-baseline` tag.

## 2. Protected Document Validation

| Check | Result | Evidence |
| --- | --- | --- |
| Every protected path exists | PASS | 36/36 metadata paths resolve |
| Every protected document has metadata | PASS | 36/36 registry entries |
| Every document has owner | PASS | Non-empty `owner` on 36/36 |
| Every document has version | PASS | Non-empty `version` on 36/36 |
| Every document has authority | PASS | Non-empty `authority` on 36/36 |
| Required metadata fields complete | PASS | 12/12 required fields per entry |
| Document ids unique | PASS | 36 unique ids |
| Canonical paths unique | PASS | 36 unique paths |
| Phase 1 Markdown front matter | PASS | All protected Phase 1 Markdown |
| Protected artifacts fingerprinted | PASS | 35/35 non-self artifacts |
| SHA256 values match | PASS | 35/35 |
| Exact duplicate protected content | PASS | 0 duplicate groups |

## 3. Ownership and Dependency Validation

| Check | Result |
| --- | --- |
| Canonical concerns | 26 |
| Concern ids unique | PASS |
| Exactly one owner per concern | PASS |
| Every owner path resolves | PASS |
| Dependency references resolve | PASS |
| Ownership dependency graph acyclic | PASS |
| Source code owns architecture | No |
| Competing Architecture/Engineering Bible | No |

## 4. Existing Governance Compatibility

| Existing mechanism | Result |
| --- | --- |
| EGP-2.0 zero-write boot | `BASELINE_VERIFIED` |
| Genesis fingerprint | PASS, 20/20 |
| KERNEL length | PASS, 265/400 |
| Capability DAG FIT-001 | PASS |
| TVM FIT-007 | PASS, 47/47 |
| Protobuf compatibility NFR-010 | PASS |

The Phase 1 fingerprint does not replace the genesis fingerprint. Their scopes are:

- Genesis ledger: original immutable materialization and ADR-0002 semantics.
- Architecture ledger: full protected Architecture Baseline v1.0.0 set.

## 5. Conflict and Duplicate Review

No blocking conflict or duplicate owner remains.

Known non-blocking inconsistencies are recorded in
`BASELINE_ISSUES_AND_RECOMMENDATIONS.md`:

- `EPS-1.0` diagram label versus canonical `ERS-1.0`.
- `EDR-10..12` display versus zero-padded machine ids.
- Historical Constitution filename alias resolved by ADR-0002.

No protected file was edited to resolve these. A future ADR/baseline patch is the
recommended vehicle.

## 6. Governance Gate Tests

Fifteen tests prove:

- the real baseline passes;
- metadata path/id uniqueness;
- required-field detection;
- unresolved metadata-reference detection;
- source-map cycle and missing-owner detection;
- fingerprint tamper and coverage-gap detection;
- Phase 1 front-matter enforcement;
- KERNEL budget enforcement;
- required governance artifacts exist.

Ruff and mypy `--strict` pass for the gate and tests.

## 7. Files Created in Step 7

- `tools/baseline_gate.py`
- `tests/unit/test_baseline_governance.py`
- `docs/governance/ARCHITECTURE_BASELINE_FINGERPRINT.yaml`
- `docs/governance/GOVERNANCE_VALIDATION_REPORT.md`

## 8. Files Modified in Step 7

- `.github/workflows/quality.yml` - executes `baseline_gate`.
- `tools/ops_gate.py` - asserts CI contains the governance gate.

## 9. Rationale

Governance validation is executable rather than dependent on manual inspection. It
fails on absence, metadata drift, ownership ambiguity, dependency cycles, duplicate
content, or digest changes.

## 10. Risks

- Any protected change now intentionally fails until a reviewed baseline update
  regenerates metadata/fingerprint/release records.
- The fingerprint file must remain tag-protected because self-hashing is impossible.
- Existing non-blocking terminology defects remain until an ADR authorizes correction.

## 11. Completion Status

**STEP 7: COMPLETE**

Every protected artifact exists, has complete metadata/owner/version/authority,
ownership is singular and acyclic, fingerprints match, and no conflicting duplicate
was found.
