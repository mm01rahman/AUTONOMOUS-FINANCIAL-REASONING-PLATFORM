# AI Engineer Playbook (AEF-01)

Operating manual for EGP-2.0 compliant AI coding agents working inside `afrp-platform`.

## Roles (Role Taxonomy)

| Role | ID | Authority |
| --- | --- | --- |
| Principal Architect | AEF-00 | Owns architecture; approves Level 0/1 ADRs with ARB |
| Orchestrator | AEF-01 | Dispatches Work Packages; enforces EGP-2.0; never writes source |
| Software Engineer | AEF-02 | Executes exactly one Work Package at a time inside `bounded_files` |
| Reviewer (ARB) | AEF-03 | Reviews REVIEW_PENDING evidence; approves or rejects |

## The Only Legal Write Path

1. `afrp boot` — EGP-2.0 handshake; verify baseline fingerprints; reach `BASELINE_VERIFIED`.
2. Load `05-work-packages/WP-IMP-XXXX.yaml`; validate against `wps-1.0.schema.json`.
3. Evaluate every precondition. Any FAIL → HALT, zero writes.
4. `EXECUTION_AUTHORIZED`: write access is limited to `scope.bounded_files`. Nothing else.
5. Implement. Tests accompany implementation. No TODOs, no placeholders, no dead code.
6. Run every quality gate in the contract. All must PASS.
7. Emit ERS-1.0 evidence (`EXEC-XXX.yaml`), schema-valid, into the WP evidence dir.
8. Update `CAPABILITY_REGISTRY.yaml` status and `TRACEABILITY_MATRIX.yaml` rows for
   the produced capability (these updates are part of the governed flow, GOV-002 Level 2).
9. Halt at `REVIEW_PENDING` for ARB review. COMPLETED only after approval.

## Absolute Prohibitions

- Writing outside `bounded_files` (FIT-005 will catch it; rollback follows).
- Bare `except:`/swallowed `Exception` (EDR-004); untyped defs (EDR-11).
- Cross-layer imports inside `06-runtime/` (EDR-002/FIT-004).
- Breaking Protobuf wire changes (NFR-010/EDR-10).
- Hardcoded secrets (EDR-008). Nondeterministic math paths (EDR-009).
- Inventing requirements or architecture. When blocked: stop and report.

## Failure Handling

On gate failure: fix within scope, or rollback per WP `rollback.strategy` and record
a HALTED evidence record. Never leave the repository between states.
