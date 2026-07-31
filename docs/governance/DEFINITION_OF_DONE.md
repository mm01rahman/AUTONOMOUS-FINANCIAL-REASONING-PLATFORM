---
document_id: AFRP-DOD-001
title: AFRP Repository Definition of Done
version: 1.0.0
status: Approved
owner: Architecture Review Board
authority: Level 2 - Baseline Governance
approved_date: 2026-07-31
last_modified: 2026-07-31
change_policy: Governed by BASELINE_FREEZE_POLICY.md
dependencies:
  - 09-validation/schemas/wps-1.0.schema.json
  - 09-validation/schemas/ers-1.0.schema.json
  - 03-engineering/TRACEABILITY_MATRIX.yaml
  - docs/governance/ARCHITECTURE_REVIEW_CHECKLIST.md
referenced_by:
  - 04-ai-framework/AI_ENGINEER_PLAYBOOK.md
  - .github/PULL_REQUEST_TEMPLATE.md
review_policy: Evaluate for every Work Package and baseline release
---

# AFRP Repository Definition of Done

A Work Package is **Done** only when every applicable item below is satisfied and
supported by ERS-1.0 evidence. Code completion alone is never Done.

## 1. Contract and Preconditions

- [ ] A schema-valid WPS-1.0 Work Package exists.
- [ ] Capability, requirement, SLS, ADR, and TVM references resolve.
- [ ] Preconditions were evaluated before write authorization.
- [ ] Required inputs and tools exist.
- [ ] Scope, bounded files, non-goals, quality gates, rollback, and completion criteria
      are unambiguous.
- [ ] No implementation began while a prerequisite capability was incomplete.

## 2. Architecture

- [ ] Implementation conforms to the canonical source map.
- [ ] No source or lower-authority artifact overrides architecture.
- [ ] Dependency direction and single responsibility are preserved.
- [ ] Runtime layers communicate only through approved CIO/Protobuf contracts.
- [ ] Mathematical behavior matches MATH-001 and numeric oracles.
- [ ] Safety defaults to `a_null` / No Trade on invalid or degraded paths.
- [ ] ADR requirements were evaluated; required ADR is approved.
- [ ] Baseline impact and SemVer class are recorded.

## 3. Implementation Quality

- [ ] Code is readable, modular, deterministic, strongly typed, testable, observable,
      replaceable, and auditable.
- [ ] Public behavior has explicit types and stable contracts.
- [ ] No bare `except:`, swallowed generic exception, implicit `Any`, hardcoded secret,
      cross-layer import, dead code, TODO, or placeholder remains.
- [ ] Configuration, logging, exception, seed, and deprecation rules are followed.
- [ ] Backward compatibility is preserved unless an approved major change says otherwise.
- [ ] Refactoring is limited to the Work Package need.

## 4. Tests

- [ ] Unit tests cover normal behavior.
- [ ] Boundary and invalid-input tests cover contract edges.
- [ ] Failure tests prove typed, observable failure behavior.
- [ ] Integration tests cover changed subsystem boundaries.
- [ ] Contract tests cover changed WPS/ERS/Protobuf surfaces.
- [ ] Deterministic replay tests cover affected state.
- [ ] Performance tests prove applicable NFR budgets.
- [ ] Chaos/degradation tests prove applicable operational behavior.
- [ ] All existing tests pass with no warnings.

## 5. Quality and Fitness Gates

- [ ] Ruff passes with zero findings.
- [ ] Mypy `--strict` passes with zero findings.
- [ ] Pytest passes 100%.
- [ ] WPS and ERS schemas validate.
- [ ] Protobuf compile, FIT-003, and compatibility gates pass when applicable.
- [ ] FIT-001 DAG acyclicity passes.
- [ ] FIT-002 AST audit passes.
- [ ] FIT-004 cross-layer import prohibition passes.
- [ ] FIT-005 bounded-file audit passes.
- [ ] FIT-006 KERNEL budget passes.
- [ ] FIT-007 TVM coverage remains 100%.
- [ ] FIT-008 deterministic replay passes when applicable.
- [ ] Operations and system gates pass when applicable.
- [ ] Baseline gate passes.

## 6. Documentation

- [ ] Canonical documentation is synchronized with behavior.
- [ ] No duplicate source of truth was introduced.
- [ ] Metadata, ids, versions, owners, authority, dates, dependencies, and review policy
      are current.
- [ ] Changelog and release notes are updated for user-visible/baseline changes.
- [ ] Operational runbooks and failure/recovery behavior are updated when affected.
- [ ] Documentation links and repository paths resolve.

## 7. Evidence and Auditability

- [ ] ERS-1.0 evidence exists at the expected path.
- [ ] Evidence identifies agent, lifecycle transitions, preconditions, boundaries,
      quality gates, artifacts, unlocks, and verdict.
- [ ] Evidence is schema-valid and truthful.
- [ ] Every changed file is accounted for.
- [ ] Rollback was verified or is demonstrably executable.
- [ ] Security/audit-sensitive changes preserve HMAC and trace lineage.

## 8. Traceability

- [ ] Every implemented requirement lists at least one artifact.
- [ ] Every implemented requirement lists at least one verification.
- [ ] TVM status matches implementation and evidence.
- [ ] All changed contracts/fields trace to their requirement and SLS.
- [ ] No requirement is implemented only in undocumented code.

## 9. Capability Lifecycle

- [ ] Produced capability version matches the Work Package.
- [ ] Capability becomes COMPLETE only after validation/evidence.
- [ ] Dependents become AVAILABLE only when every dependency is COMPLETE.
- [ ] Registry remains acyclic and contains no duplicate/orphan capability.
- [ ] No capability claim exceeds validated behavior.

## 10. Review

- [ ] Author self-review completed.
- [ ] Architecture Review Checklist completed.
- [ ] Required domain/security/operations reviewers approved.
- [ ] REVIEW_PENDING disposition is recorded.
- [ ] All blocking comments are resolved.
- [ ] Human authority approves architecture/deployment decisions.

## 11. Repository State

- [ ] Working tree is clean after commit.
- [ ] Commit message explains why and includes required attribution.
- [ ] Branch is pushed and CI is green.
- [ ] No generated temporary artifact is committed unintentionally.
- [ ] Approved immutable tags are created only after all gates pass.

## 12. Work Package Completion Rule

```text
DONE =
  contract_valid
  AND preconditions_pass
  AND boundary_compliant
  AND architecture_compliant
  AND implementation_complete
  AND tests_pass
  AND quality_gates_pass
  AND documentation_current
  AND evidence_valid
  AND traceability_complete
  AND capability_updated
  AND review_approved
```

If any term is false, status is not Done. Use `HALTED`, `ReviewPending`, or the
applicable incomplete state; never shape failure as success.

## 13. Files Created in Step 9

- `docs/governance/DEFINITION_OF_DONE.md`

## 14. Files Modified in Step 9

None.

## 15. Rationale

The Definition of Done composes existing WPS, ERS, NFR, FIT, EDR, EOS, and
constitutional obligations into one execution/review checklist.

## 16. Risks

- Treating the checklist as documentation-only would weaken enforcement.
- Marking capability COMPLETE before evidence would violate the lifecycle.
- Waiving a check without an ADR/record would create untraceable debt.

## 17. Completion Status

**STEP 9: COMPLETE**

The repository-wide Definition of Done covers documentation, tests, evidence, review,
quality gates, capability updates, traceability, and architecture compliance.
