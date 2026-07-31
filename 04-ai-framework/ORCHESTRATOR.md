# ORCHESTRATOR (AEF-01 Runbook)

The orchestrator (`afrp run`, capability EOS-ORCHESTRATOR) is the supervisory control
plane executing Work Packages under EGP-2.0 (EOS-003).

## Contract

1. Resolve the execution DAG from `03-engineering/CAPABILITY_REGISTRY.yaml` (EOS-GRAPH).
2. Select the next `AVAILABLE` capability whose Work Package exists in `05-work-packages/`.
3. Verify baseline: SHA256 of every ledger entry in
   `00-governance/BASELINE_FINGERPRINT.yaml` must match. Mismatch → HALT.
4. Drive RSM-1.0: INITIAL → BASELINE_VERIFIED → WORK_PACKAGE_LOADED →
   PRECONDITIONS_VERIFIED → EXECUTION_AUTHORIZED → EXECUTING → VALIDATING →
   EVIDENCE_GENERATED → REVIEW_PENDING → COMPLETED | HALTED.
5. Grant write locks strictly to `scope.bounded_files`.
6. Execute quality gates exactly as written in the WP contract; any required-gate
   failure → rollback per `rollback.strategy` and HALT with evidence.
7. Emit/require ERS-1.0 evidence; update registry statuses
   (`COMPLETE`, unlock dependents to `AVAILABLE`).

## Dispatch Rules

- One WP in flight at a time unless `execution.parallelizable: true` and bounded
  file sets are disjoint.
- Priority order: registry dependency order first, then WP `execution.priority`.
- REVIEW_PENDING requires AEF-03 (ARB) disposition before COMPLETED.
