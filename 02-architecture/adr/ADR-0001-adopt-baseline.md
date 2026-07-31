# ADR-0001 — Adopt AFRP-BASELINE-1.0.0 and EOS-First Build Order

**Status:** Accepted · **Date:** 2026-07-31 · **Level:** 0/1 (Baseline adoption)

## Context

The AFRP Master Engineering Documentation Suite v1.0 (AFRP-BASELINE-1.0.0) defines the
constitution, architecture, mathematical foundation, reference specification, and
implementation guide for the platform. The repository begins at pre-genesis with no
tracked artifacts.

## Decision

1. Adopt AFRP-BASELINE-1.0.0 verbatim as the governing corpus, materialized at the
   canonical paths recorded in `REPOSITORY_MANIFEST.yaml` (`document_index`).
2. Build order follows EOS-002: the Engineering Operating System toolchain
   (EOS-BOOT → EOS-CONTEXT → EOS-GRAPH → EOS-VALIDATOR → EOS-EVIDENCE → EOS-HEALTH →
   EOS-ORCHESTRATOR) is completed before any `06-runtime/` layer, so that all runtime
   Work Packages execute under governed EGP-2.0 controls.
3. `WP-IMP-0003` (doc 300 §3) is the first formal Work Package; the genesis actions
   (baseline materialization + EOS-BOOT) are governance actions preceding it.
4. Integrity of the baseline is anchored by SHA256 digests in
   `00-governance/BASELINE_FINGERPRINT.yaml` and the git tag `m1.1-start`.

## Consequences

- Every subsequent change flows through Work Packages with `bounded_files`, quality
  gates, and ERS-1.0 evidence.
- The capability DAG in `03-engineering/CAPABILITY_REGISTRY.yaml` is the sole
  execution ordering authority (FIT-001 enforced).
