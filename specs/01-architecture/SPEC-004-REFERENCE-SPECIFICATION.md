# SPEC-004 — Reference Specification

> **Specification ID:** `SPEC-004`
> **Version:** `1.0.0`
> **Level:** L1 (Architecture — Contractual)
> **Status:** Approved
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `02-architecture/200_REFERENCE_SPECIFICATION.md`
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Defines all contractual interfaces: CognitiveEnvelope, CIO taxonomy, WPS-1.0/ERS-1.0
schemas, and the EGP-2.0 governance protocol.

## 2. Canonical Content Reference

**`02-architecture/200_REFERENCE_SPECIFICATION.md`** (REF-001)

## 3. CognitiveEnvelope

Universal transport header (11 fields): message_id, cognitive_cycle_id, producer_subsystem_id,
schema_version, semantic_version, generated_at_ns, mission_profile_id, parent_cio_ids,
payload_hash, trace_id, span_id.

Location: `proto/afrp/v1/envelope.proto`

## 4. CIO Taxonomy

| CIO | Name | Producer | Consumer |
|-----|------|----------|---------|
| CIO-01 | Raw Observation | L1-ING | L1-FST |
| CIO-02 | Standard Feature | L1-FST | L2-* |
| CIO-03 | Domain Belief | L2-* | L3-WRM |
| CIO-04 | WorldState Vector | L3-WRM | L4-FUS |
| CIO-05A | ScenarioSet | L3-SIM | L4-FUS |
| CIO-05B | DecisionContext | L4-FUS | L4-DEC |
| CIO-06 | Execution Candidate | L4-DEC | L4-VAL |
| CIO-07 | Authorized Action | L4-VAL | L5-EXE |
| CIO-08 | Execution Intent | L5-EXE | L5-EXE |
| CIO-09 | Execution Report | L5-EXE | L6-OPT |
| CIO-10 | Portfolio State | L5-EXE | L6-OPT |
| CIO-11 | Calibration Weights | L6-OPT | L2-* |
| CIO-12 | Episodic Embedding | L6-OPT | L1-MEM |

## 5. Schemas

- WPS-1.0: `09-validation/schemas/wps-1.0.schema.json`
- ERS-1.0: `09-validation/schemas/ers-1.0.schema.json`

## 6. EGP-2.0 Protocol States

INITIAL → BASELINE_VERIFIED → WORK_PACKAGE_LOADED → PRECONDITIONS_VERIFIED →
EXECUTION_AUTHORIZED → EXECUTING → VALIDATING → EVIDENCE_GENERATED →
REVIEW_PENDING → COMPLETED | HALTED

## 7. Traceability

FR-007 in TVM-001. All proto capabilities COMPLETE.

## 8. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
