# SPEC-005 — Production Engineering Architecture

> **Specification ID:** `SPEC-005`
> **Version:** `0.0.1`
> **Level:** L1 (Architecture — Semi-Immutable)
> **Status:** Pending_Import
> **Owner:** Architecture Review Board (ARB)
> **Approval Authority:** ARB
> **Work Package:** WP-IMP-0040 (stub) / TBD (full import)
> **Canonical Source:** None (PENDING IMPORT)
> **Effective Date:** 2026-08-02
> **Supersedes:** None

## 1. Purpose

**PENDING IMPORT.** This specification will define the complete production engineering
architecture for AFRP deployment, including high-availability clustering, zero-trust
networking, secrets management, and operational SLOs.

## 2. Scope

This specification shall govern:
- High-availability active-passive clustering (NFR-002)
- mTLS / SPIFFE / SPIRE zero-trust networking (NFR-006)
- HashiCorp Vault secrets management (EDR-008)
- Kubernetes deployment manifests
- Monitoring, alerting, and SLO definitions
- Operational runbooks

## 3. Current State (Pre-Import)

Partial evidence exists in the repository:

| Path | Content | Completeness |
|------|---------|-------------|
| `08-operations/docker/` | Docker and compose configs | ~30% |
| `08-operations/policies/` | Operational policies | ~40% |
| `03-engineering/DEPRECATION_POLICY.yaml` | Deprecation rules | 100% |

## 4. Import Requirements

When importing this specification, the document must address:

1. **HA Clustering** — Active-passive topology, failover SLA (NFR-002)
2. **Zero-Trust Networking** — SPIFFE identities, SPIRE attestation, mTLS on all gRPC (NFR-006)
3. **Secrets Management** — Vault integration, no hardcoded secrets (EDR-008)
4. **Container Orchestration** — Kubernetes manifests for all 6 runtime layers
5. **Observability Stack** — OpenTelemetry collection, metrics, logging, tracing
6. **Recovery Procedures** — RPO=0, RTO<60s runbook (NFR-005)
7. **Security Hardening** — Network policies, RBAC, image scanning

## 5. Dependencies

- SPEC-002 (Runtime Architecture) — defines what must be deployed
- SPEC-040 (Validation Framework) — production validation criteria

## 6. Blocking Impact

This specification's absence means:
- NFR-002 (HA) is formally uncovered
- NFR-006 (mTLS) is formally uncovered
- No governed path to live trading deployment

**Priority: Tier 1 — Required before live trading.**

## 7. Revision History

| Version | Date | Change |
|---------|------|--------|
| 0.0.1 | 2026-08-02 | Stub created; import pending |
