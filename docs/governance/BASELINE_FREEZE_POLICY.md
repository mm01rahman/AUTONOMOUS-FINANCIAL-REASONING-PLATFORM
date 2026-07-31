---
document_id: AFRP-BASELINE-FREEZE-001
title: AFRP Architecture Baseline Freeze Policy
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Baseline Governance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: This policy is itself protected by the policy and the Constitution
dependencies:
  - 00-governance/000_ENGINEERING_CONSTITUTION.md
  - docs/governance/BASELINE_MANIFEST.md
  - docs/governance/CANONICAL_SOURCE_MAP.yaml
referenced_by:
  - docs/governance/ARCHITECTURE_REVIEW_CHECKLIST.md
  - docs/governance/DEFINITION_OF_DONE.md
  - tools/baseline_gate.py
review_policy: Review at every architecture baseline release
---

# AFRP Architecture Baseline Freeze Policy

## 1. Purpose

This policy freezes the approved AFRP architecture without redesigning it. The
Constitution and GOV-002 remain upstream; this policy defines the mechanics used to
version, verify, review, and release their protected artifact set.

## 2. What Is Frozen

Every artifact in Sections 2-7 of
[`BASELINE_MANIFEST.md`](BASELINE_MANIFEST.md) is frozen as Architecture Baseline
v1.0.0.

Freeze protects:

- canonical path;
- byte content recorded by the architecture fingerprint;
- document id and version;
- owner and authority;
- concern ownership in the canonical source map;
- dependency direction;
- schema and Protobuf wire compatibility;
- mathematical definitions, NFR, FIT, EDR, runtime layers, and governance rules.

Moving or renaming a protected artifact is a baseline change even if its content is
unchanged.

## 3. What Is Mutable

Artifacts in Baseline Manifest Section 8 remain mutable only through their governing
mechanism:

- capability/traceability/health ledgers through EOS and reviewed updates;
- Work Packages and evidence through WPS-1.0, ERS-1.0, and EGP-2.0;
- source, tests, research, operations, and tools through bounded Work Packages;
- CI/build configuration through BUILD_PROFILE and reviewed pull requests;
- release records as append-only release history;
- the ADR directory by adding new ADRs, never rewriting accepted history.

Mutable artifacts cannot override a frozen owner. When implementation and architecture
conflict, the implementation is wrong (Constitution Article I).

## 4. Approval Matrix

| Change | Vehicle | Approval | Baseline version |
| --- | --- | --- | --- |
| Level-0 constitutional meaning, owner, or authority | ADR + constitutional amendment | Unanimous ARB + Principal Architect | Major |
| Level-1 architecture, math, runtime boundary, NFR/FIT/EDR, conceptual contract | ADR | ARB | Major or Minor |
| Breaking schema/Protobuf wire change | ADR + compatibility migration | ARB | Major |
| Backward-compatible additive Level-1 contract | ADR | ARB | Minor |
| Level-2 normative engineering standard | Reviewed PR; ADR if architecture/dependency/ownership changes | Lead Engineer + required ARB reviewer | Minor or Patch |
| Non-semantic typo/link/metadata correction in a protected artifact | Baseline patch PR with evidence | Owner + ARB reviewer | Patch |
| Mutable implementation under an approved WP | WPS/ERS lifecycle | EGP-2.0 + human review | No baseline bump unless architecture changes |

No source-code change can approve an architecture change.

## 5. When an ADR Is Required

An ADR is mandatory when a change:

- changes a canonical owner or authority;
- adds, removes, merges, or splits an architecture concern;
- changes layer boundaries or dependency direction;
- changes mathematical semantics;
- changes an NFR, FIT, EDR, mission-profile invariant, or SYS-03 transition;
- changes WPS/ERS semantics;
- changes a Protobuf field number/type/meaning or removes a field/message;
- adds an architectural product/subsystem/capability family;
- supersedes an accepted ADR;
- requires an exception to a frozen rule.

An ADR is not required for a demonstrably non-semantic spelling, broken-link, date, or
sidecar-metadata correction, but the patch still updates the fingerprint and baseline
release record.

## 6. Versioning Policy

Architecture baselines use semantic versioning: `MAJOR.MINOR.PATCH`.

### Major

Increment MAJOR for an incompatible architecture or governance change:

- constitutional meaning or authority change;
- removed/renumbered/retyped Protobuf wire element;
- incompatible WPS/ERS schema;
- changed mathematical model semantics;
- removed layer, product, required capability, or safety invariant;
- changed direction of a protected dependency.

### Minor

Increment MINOR for backward-compatible architecture expansion:

- additive optional contract fields/messages;
- new subsystem/capability that preserves existing contracts and boundaries;
- new accepted engineering standard;
- additive NFR/FIT/EDR with no incompatible behavior;
- new mission profile preserving existing profile semantics.

### Patch

Increment PATCH only when meaning does not change:

- spelling/formatting correction;
- broken link or stale cross-reference;
- metadata date/owner contact correction that does not change authority;
- clarification that introduces no new requirement;
- regenerated equivalent compatibility/fingerprint representation.

Pre-release identifiers may be used before approval (for example,
`1.1.0-rc.1`). Approved tags are immutable.

## 7. Breaking Change Policy

1. The proposing ADR identifies affected owners, consumers, migration, rollback, and
   compatibility window.
2. Protobuf changes run compile, FIT-003, and breaking/snapshot gates.
3. WPS/ERS changes validate all retained instance fixtures.
4. A major baseline is prepared in parallel; the existing baseline remains supported
   until the declared deprecation period expires.
5. EDR-012 requires at least one minor-version grace period before removal.
6. The baseline manifest, metadata registry, fingerprints, source map, TVM, release
   notes, and tags update atomically.

## 8. Emergency Change Policy

Safety containment takes priority, but emergency authority does not erase governance.

1. A human incident commander may authorize the minimum mutable-artifact change needed
   to stop harm, preserve data, or disable trading.
2. Protected baseline content must not be silently edited during containment.
3. The system defaults to `EMERGENCY_STOP` or `a_null`; manual reset remains required.
4. The emergency change receives a bounded WP (or emergency record if tooling is
   unavailable), tests, audit evidence, rollback instructions, and named approver.
5. If protected architecture must change, an ADR and new baseline are required before
   the change becomes normal operation. A retrospective ADR is completed before the
   next deployment.
6. Emergency tags never replace or move an approved baseline tag.

## 9. Baseline Change Procedure

1. Verify the current fingerprint and clean repository state.
2. Classify the proposed change by owner, authority, and SemVer effect.
3. Approve the required ADR or reviewed patch.
4. Update only authorized artifacts.
5. Update metadata, source map, manifest, traceability, and release notes.
6. Regenerate the architecture fingerprint.
7. Run `baseline_gate`, `proto_gate`, `ops_gate`, `system_gate`, ruff, mypy, and pytest
   as applicable.
8. Complete the Architecture Review Checklist.
9. Obtain required human approval.
10. Create a new immutable annotated baseline tag.

## 10. Tag Policy

- `v1.0.0-baseline` identifies this architecture freeze.
- A tag is created only from a clean commit that passes governance validation.
- Baseline tags are never force-moved or reused.
- Product release tags and architecture baseline tags are distinct, even when they
  share a version number.

## 11. Files Created in Step 6

- `docs/governance/BASELINE_FREEZE_POLICY.md`

## 12. Files Modified in Step 6

None.

## 13. Rationale

The policy translates existing constitutional authority into a repeatable freeze and
evolution procedure without creating a new architecture owner.

## 14. Risks

- Misusing Patch for semantic changes would bypass ADR review.
- Emergency containment could become permanent without retrospective governance.
- Moving an existing tag would destroy reproducibility.

## 15. Completion Status

**STEP 6: COMPLETE**

Frozen/mutable scope, approvals, ADR triggers, SemVer, breaking changes, emergency
handling, and immutable tagging are defined.
