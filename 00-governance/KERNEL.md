# KERNEL — AFRP Repository Bootloader

**Baseline:** AFRP-BASELINE-1.0.0 · **Protocol:** EGP-2.0 · **Repository OS:** ROS-1.0.0

## Identity

This repository is the Autonomous Financial Reasoning Platform (AFRP): an AI-native
financial reasoning and execution system governed by machine-verifiable evidence.
Three products: Engineering Operating System (`tools/afrp-cli/`), Runtime Platform
(`06-runtime/`, Layers 1–6), Research Platform (`07-research/`).

## Boot Sequence (mandatory, in order)

1. Read this KERNEL completely.
2. Read `00-governance/000_ENGINEERING_CONSTITUTION.md` — Articles I–X bind every action.
3. Ingest `REPOSITORY_MANIFEST.yaml` (topology, document index).
4. Ingest `03-engineering/CAPABILITY_REGISTRY.yaml` (execution DAG).
5. Verify SHA256 digests against `00-governance/BASELINE_FINGERPRINT.yaml`.
6. Emit the EGP-2.0 `repository_state` diagnostic block.
7. Halt in `BASELINE_VERIFIED`. Await Work Package assignment.

## Authority Hierarchy

Constitution → Architecture (`02-architecture/`) → Reference Specification →
Implementation Guide (`03-engineering/`) → Work Package (`05-work-packages/`) →
Source Code. Lower levels never override higher levels.

## Non-Negotiable Rules

- Write only inside the active Work Package `bounded_files`.
- Every change passes quality gates: `ruff`, `mypy --strict`, `pytest`.
- Layers in `06-runtime/` communicate only via Protobuf contracts (`proto/afrp/v1/`).
  Cross-layer Python imports are forbidden (EDR-002, FIT-004).
- Deterministic math under seed 42 (NFR-004, EDR-009).
- No bare `except:`; no untyped functions (EDR-004, EDR-11).
- Prefer No Trade over a Poor Trade (Article VIII).
- Evidence (`ERS-1.0`) is emitted for every executed Work Package.

## State Model

RSM-1.0 lifecycle: INITIAL → BASELINE_VERIFIED → WORK_PACKAGE_LOADED →
PRECONDITIONS_VERIFIED → EXECUTION_AUTHORIZED → EXECUTING → VALIDATING →
EVIDENCE_GENERATED → REVIEW_PENDING → COMPLETED | HALTED.

Runtime operational model SYS-03: INITIALIZING, NORMAL, OBSERVATION, DEGRADED,
RECOVERY, EMERGENCY_STOP (manual reset only).

## Failure Doctrine

On any integrity, precondition, or gate failure: stop, report cause, remain
zero-write. Never guess. Never bypass governance.
