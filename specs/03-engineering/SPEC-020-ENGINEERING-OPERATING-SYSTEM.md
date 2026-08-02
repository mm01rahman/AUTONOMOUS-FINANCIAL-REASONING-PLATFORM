# SPEC-020 — Engineering Operating System

> **Specification ID:** `SPEC-020`
> **Version:** `1.0.0`
> **Level:** L3 (Engineering Specification)
> **Status:** Approved
> **Owner:** EOS-CLI Team
> **Approval Authority:** Lead Engineer / Tech Lead
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `03-engineering/120_ENGINEERING_OPERATING_SYSTEM.md`
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

Specifies the complete Engineering Operating System (EOS) toolchain that governs
all AI agent execution within the AFRP repository.

## 2. Canonical Content Reference

**`03-engineering/120_ENGINEERING_OPERATING_SYSTEM.md`** (EOS-001, EOS-002, EOS-003)

## 3. EOS Capability Toolchain

| Capability | Command | Function | Status |
|-----------|---------|----------|--------|
| EOS-BOOT | Setup scripts | Workspace skeleton, dependency verification | COMPLETE |
| EOS-CONTEXT | `afrp boot` | Manifest + kernel parsers, word count ≤ 400 | COMPLETE |
| EOS-GRAPH | `afrp plan` | Capability DAG, cycle detection (FIT-001) | COMPLETE |
| EOS-VALIDATOR | `afrp validate` | AST invariant checker (FIT-002, FIT-004, FIT-006) | COMPLETE |
| EOS-EVIDENCE | `afrp evidence` | Boundary audit (FIT-005), ERS-1.0 emission | COMPLETE |
| EOS-HEALTH | `afrp health` | Coverage + TVM traceability (FIT-007) | COMPLETE |
| EOS-ORCHESTRATOR | `afrp run` | EGP-2.0 control plane, write locks, rollback | COMPLETE |

## 4. Orchestrator Contract (EOS-003)

1. Resolve execution DAG from CAPABILITY_REGISTRY.yaml
2. Ingest WP contract from 05-work-packages/WP-IMP-XXXX.yaml
3. Enforce EGP-2.0 handshake + SHA256 baseline verification
4. Grant write locks to bounded_files only
5. Execute quality gates (ruff, mypy --strict, pytest, buf)
6. Emit ERS-1.0 evidence; update registry statuses

## 5. Traceability

FR-001..006 in TVM-001.

## 6. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
