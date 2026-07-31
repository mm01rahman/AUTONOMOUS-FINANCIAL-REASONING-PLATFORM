---
document_id: AFRP-ARCH-REVIEW-CHECKLIST-001
title: AFRP Architecture Review Checklist
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Baseline Governance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Governed by BASELINE_FREEZE_POLICY.md
dependencies:
  - docs/governance/BASELINE_FREEZE_POLICY.md
  - docs/governance/CANONICAL_SOURCE_MAP.yaml
  - 02-architecture/100_SYSTEM_ARCHITECTURE.md
referenced_by:
  - .github/PULL_REQUEST_TEMPLATE.md
  - docs/governance/DEFINITION_OF_DONE.md
review_policy: Use for every pull request; review at every baseline release
---

# AFRP Architecture Review Checklist

Use this checklist for every pull request. Mark `N/A` only with a written rationale.
The reviewer, not the author, owns final disposition.

## 1. Pull Request Identity

- [ ] Purpose and requirement/capability are stated.
- [ ] Active Work Package is identified, or governance-only scope is explained.
- [ ] Base/head references and rollback point are known.
- [ ] Risk, migration, compatibility, and operational impact are described.

## 2. Baseline and ADR Impact

- [ ] `baseline_gate` passes before review.
- [ ] Protected files touched by the PR are listed explicitly.
- [ ] Baseline SemVer impact is classified: None / Patch / Minor / Major.
- [ ] ADR triggers in `BASELINE_FREEZE_POLICY.md` were evaluated.
- [ ] Required ADR is approved before implementation changes merge.
- [ ] Baseline manifest, metadata, fingerprint, and release record update atomically
      when protected content changes.
- [ ] No approved tag is moved or reused.

## 3. Architecture Compliance

- [ ] The change implements an existing canonical owner; it does not create a competing
      source of truth.
- [ ] Authority order is preserved: Constitution > Architecture > Reference
      Specification > Engineering Standard > Work Package > Source.
- [ ] Architecture is not inferred from implementation convenience.
- [ ] Mathematical definitions in MATH-001 remain authoritative.
- [ ] Article VIII is preserved: No Trade over Poor Trade.

## 4. Dependency Direction and Layer Boundaries

- [ ] `afrp validate` passes FIT-002, FIT-004, and FIT-006.
- [ ] Runtime layers do not import sibling layers (EDR-002).
- [ ] Inter-layer communication uses CIO/Protobuf contracts only.
- [ ] High-level logic depends on abstract interfaces/Protocols (EDR-001).
- [ ] I/O and CPU execution models follow EDR-003.
- [ ] No new circular capability or ownership dependency is introduced.

## 5. Contract and Compatibility Review

- [ ] Protobuf compile and FIT-003 custom-option gates pass.
- [ ] NFR-010 compatibility/snapshot gate passes.
- [ ] Field numbers/types and message semantics are not broken.
- [ ] WPS/ERS schema changes validate retained instances.
- [ ] Breaking changes have a major version, migration, deprecation window, and ADR.
- [ ] EDR-012 one-minor-version grace is honored.

## 6. Standards and Code Quality

- [ ] Ruff passes with zero warnings.
- [ ] `mypy --strict` passes with no implicit `Any`.
- [ ] No bare `except:` or swallowed generic `Exception` exists (EDR-004).
- [ ] No hardcoded secret exists (EDR-008).
- [ ] Configuration precedence follows EDR-005.
- [ ] Logging conforms to OBS-01 (EDR-006).
- [ ] Deterministic code uses seed 42/substreams (EDR-009).
- [ ] No TODO, placeholder implementation, dead code, or unrelated refactor remains.

## 7. Tests and Fitness

- [ ] Unit tests cover normal, boundary, failure, and invalid-input behavior.
- [ ] Integration/contract tests cover affected boundaries.
- [ ] Deterministic replay is updated only when an approved semantic change requires it.
- [ ] Performance tests cover affected live decision/execution paths.
- [ ] Chaos/degradation tests cover affected failure modes.
- [ ] FIT-001 through FIT-008 remain green as applicable.
- [ ] NFR latency, availability, recovery, security, audit, and resource constraints are
      evaluated.

## 8. Documentation and Metadata

- [ ] Canonical owner documentation is updated, not duplicated elsewhere.
- [ ] Metadata is complete and matches `DOCUMENT_METADATA.yaml`.
- [ ] Links, paths, ids, versions, owners, and authority are correct.
- [ ] Architecture and operational documentation remain synchronized.
- [ ] Changelog/release notes are updated when user-visible or baseline behavior changes.

## 9. Work Package, Evidence, and Boundaries

- [ ] Work Package validates against WPS-1.0.
- [ ] Preconditions passed before write authorization.
- [ ] Changed implementation files are inside `bounded_files` (FIT-005).
- [ ] Every required quality gate passed.
- [ ] Evidence validates against ERS-1.0.
- [ ] Rollback instructions are executable and bounded.
- [ ] Review disposition is recorded at `REVIEW_PENDING`.

## 10. Traceability and Capability Lifecycle

- [ ] Every implemented requirement has artifact and verification links.
- [ ] TVM remains 100% covered (FIT-007).
- [ ] Capability dependency changes preserve DAG acyclicity (FIT-001).
- [ ] Capability status/unlocks match actual validated state.
- [ ] New capability ownership is approved by ADR if it changes architecture.

## 11. Operations and Security

- [ ] TLS 1.3/mTLS and SPIFFE posture is preserved for internal communication.
- [ ] Vault/environment-only secret policy is preserved.
- [ ] HMAC audit and trace propagation remain complete for order paths.
- [ ] RPO=0 and RTO<60s implications are reviewed.
- [ ] Active-passive lease/fencing/failover posture is not weakened.
- [ ] Production image remains frozen-lock and non-root.

## 12. Final Reviewer Decision

- [ ] All applicable checks complete.
- [ ] Evidence supports the claimed result.
- [ ] No unresolved blocking finding remains.
- [ ] **APPROVE**
- [ ] **REQUEST CHANGES**
- [ ] **ESCALATE TO ARB**

Reviewer:

Date:

Decision rationale:

## 13. Files Created in Step 8

- `docs/governance/ARCHITECTURE_REVIEW_CHECKLIST.md`
- `.github/PULL_REQUEST_TEMPLATE.md`

## 14. Files Modified in Step 8

None.

## 15. Rationale

The checklist operationalizes existing Constitution, NFR, FIT, EDR, WPS, ERS, and
freeze rules at the pull-request boundary.

## 16. Risks

- Mechanical checking without evidence can create false assurance.
- `N/A` can conceal impact unless justified.
- Checklist approval cannot substitute for an ADR when the freeze policy requires one.

## 17. Completion Status

**STEP 8: COMPLETE**

The checklist is suitable for every pull request and is linked from the PR template.
