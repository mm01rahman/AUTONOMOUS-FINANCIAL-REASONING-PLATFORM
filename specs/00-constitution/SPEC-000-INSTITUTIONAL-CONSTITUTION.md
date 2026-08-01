# SPEC-000 — Institutional Constitution

> **Specification ID:** `SPEC-000`
> **Version:** `1.0.0`
> **Level:** L0 (Constitutional — Immutable)
> **Status:** Approved
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** Unanimous ARB + Principal Architect
> **Work Package:** WP-IMP-0040
> **Canonical Source:** `00-governance/000_ENGINEERING_CONSTITUTION.md`
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

This specification formally registers the AFRP Engineering Constitution as Level 0 of
the institutional specification hierarchy. The constitution is the highest authority
in the AFRP governance framework and governs all subordinate specifications.

## 2. Scope

All AFRP capabilities, work packages, specifications, runtime modules, research artifacts,
and evidence records fall under this constitutional framework.

## 3. Canonical Content Reference

The normative content of this specification resides in:

**`00-governance/000_ENGINEERING_CONSTITUTION.md`**

Key constitutional elements:
- Ten Constitutional Articles (`CPG-00`)
- Nine Core Architectural Principles (`GOV-001`)
- Authority Hierarchy & Change Matrix (`GOV-002`)

## 4. Constitutional Articles Summary

| Article | Title | Mandate |
|---------|-------|---------|
| I | Truth | Mathematics precedes implementation code |
| II | Evidence | Every decision requires measurable evidence |
| III | Explainability | Every output and trade must be explainable |
| IV | Traceability | Every artifact traces to a requirement via TVM |
| V | Modularity | Single-responsibility via defined contracts |
| VI | Reproducibility | Deterministic experiments under seed=42 |
| VII | Evolution | Only via Requirements, Evidence, ADRs, Gates |
| VIII | Safety | System prefers No Trade over Poor Trade |
| IX | Knowledge | Failures and benchmarks become institutional memory |
| X | Human Authority | Humans accountable for architecture and deployment |

## 5. Traceability

| Requirement | Capability | Status |
|-------------|-----------|--------|
| GOV-001 | GOV-BASELINE | Implemented |
| GOV-002 | GOV-BASELINE | Implemented |

## 6. Conformance Evidence

- `00-governance/BASELINE_FINGERPRINT.yaml` — Baseline verified
- `00-governance/KERNEL.md` — ≤ 400 words (FIT-006 PASS)
- `03-engineering/CAPABILITY_REGISTRY.yaml` — GOV-BASELINE COMPLETE
- `afrp validate` PASS — FIT-002, FIT-004, FIT-006

## 7. Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-08-02 | Initial import into canonical specification library |
