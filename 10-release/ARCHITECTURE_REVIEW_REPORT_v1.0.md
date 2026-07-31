# AFRP Version 1.0 — Final Architecture Review Report

**Review date:** 2026-07-31  
**Baseline:** AFRP-BASELINE-1.0.0 · EGP-2.0 · ROS-1.0.0  
**Release candidate:** AFRP 1.0.0 (`v1.0.0`)  
**ARB disposition:** **GO for core-platform release; CONDITIONAL NO-GO for live-money activation**

## 1. Executive Decision

The repository implementation is complete against the approved capability DAG:
**33/33 capabilities are COMPLETE**, **47/47 requirements have artifact and
verification coverage**, **31/31 executable Work Packages have schema-valid
ERS-1.0 evidence**, and `afrp plan` reports no executable targets.

The AFRP core platform is recommended for Version 1.0 release. Live-money activation
remains gated on environment-specific controls that cannot be materialized without an
approved venue and deployment environment: SPIRE/Vault provisioning, a deployed
replicated lease/persistence backend with failover drill, venue-adapter certification,
and target-host performance/recovery certification.

## 2. Completed Architecture

| Product / Layer | Completed capabilities | Primary evidence |
| --- | --- | --- |
| Engineering OS | EOS-BOOT, CONTEXT, GRAPH, VALIDATOR, EVIDENCE, HEALTH, ORCHESTRATOR | EXEC-001..006 |
| Contracts | annotations, CognitiveEnvelope, CIO-01..12, compatibility snapshot | EXEC-007..009 |
| Runtime common | Config precedence, OBS-01, errors, SYS-03, seed discipline, bindings | EXEC-010 |
| Layer 1 / SLS-100 | Ingress, feature store, relational ledger, vector memory | EXEC-011..014 |
| Layer 2 / SLS-200 | DSmT base + MAC/MIC/LIQ/REG/FOR/BEH agents | EXEC-015..021 |
| Layer 3 / SLS-300/301 | PCR5 world model, equilibrium scenario simulator | EXEC-022..023 |
| Layer 4 / SLS-400/401/402 | Synthesis, risk-adjusted optimizer, policy projection | EXEC-024..026 |
| Layer 5 / SLS-500 | Order FSM, fills, HMAC audit, recovery, portfolio state | EXEC-027 |
| Layer 6 / SLS-600 | Brier calibration and deterministic regime embeddings | EXEC-028 |
| Research | Deterministic, cost-aware backtest harness | EXEC-029 |
| Operations | HA/security/recovery/observability policy, image, CI | EXEC-030 |
| System validation | Frozen replay, feed-loss chaos, latency, deprecation policy | EXEC-031 |

All runtime layer edges use CIO contracts; `afrp validate` reports zero FIT-004
cross-layer imports.

## 3. Mathematical and Safety Review

- PCR5 implements the MATH-001 conjunctive consensus and proportional conflict
  redistribution. Three numeric conflict oracles pass to 1e-9.
- Property tests prove BBA non-negativity, unit sum, two-source commutativity, and
  vacuous-source neutrality.
- Total feed loss produces the vacuous world state `m(THETA)=1`, quorum zero,
  SYS-03 `DEGRADED`, and trading disabled.
- `U_r = U - lambda*R` is optimized over a pre-allocated action grid with a flat
  action always available.
- `Pi_C` projection and every constraint failure default to signed `a_null`.
- Layer 6 is advisory-only; it cannot mutate Layer 4 policy constraints.

Article I (mathematics over code) and Article VIII (No Trade over Poor Trade) are
preserved.

## 4. Quality and Evidence Metrics

| Metric | Result |
| --- | ---: |
| Tests | 372 passed, 0 failed |
| Line/branch-aware coverage | 90.7613% |
| Statements / covered lines | 2,823 / 2,625 |
| Branches / covered branches | 684 / 558 |
| Strict type checking | PASS across 63 source/test files |
| Ruff | PASS, zero warnings |
| Protobuf messages | 20, compile/FIT-003/NFR-010 PASS |
| Capabilities | 33/33 COMPLETE |
| TVM | 47/47 covered (100%) |
| Work Packages / evidence | 31 / 31 |
| KERNEL budget | 265 / 400 words |
| MP-04 replay checksum | `9742f494fdfc3515e8b0e323af38d4ed73ecb039f6eeb671be7903a99ca8e079` |
| L4/L5 decision P99 | 0.207 ms observed / 50 ms budget |

Quality gates passing: ruff, mypy `--strict`, pytest, WPS schema, ERS schema,
proto compile/compatibility, FIT-001..008, operations gate, and system gate.

## 5. Work Package and Evidence Review

The execution sequence followed the registry dependency order:

1. WP-IMP-0003..0008 — Engineering OS.
2. WP-IMP-0009..0012 — contracts and common runtime.
3. WP-IMP-0013..0016 — Layer 1.
4. WP-IMP-0017..0023 — Layer 2.
5. WP-IMP-0024..0025 — Layer 3.
6. WP-IMP-0026..0028 — Layer 4.
7. WP-IMP-0029 — Layer 5.
8. WP-IMP-0030 — Layer 6.
9. WP-IMP-0031..0033 — research, operations, system validation.

Evidence `EXEC-001` through `EXEC-031` validates against ERS-1.0 and records
preconditions, bounded-file compliance, gate outcomes, artifacts, and review
disposition.

## 6. Security, Availability, and Recovery

- TLS 1.3 mutual authentication and SPIFFE workload identity are mandatory.
- Secrets may originate only from Vault or environment variables.
- The production image uses a pinned Python 3.11 line, frozen lock, and non-root
  UID/GID 10001.
- Active-passive posture requires at least two anti-affine replicas, durable lease,
  fencing token, 5-second heartbeat, 15-second lease, and failover within 30 seconds.
- Order events are synchronous (`SQLite FULL` in the local adapter), every transition
  is HMAC authenticated and trace-bearing, and checkpoint restore is below the
  60-second RTO.
- CI executes every repository, contract, operations, and system fitness gate.

## 7. Remaining Technical Debt and Release Exceptions

| Item | Impact | Disposition |
| --- | --- | --- |
| W-001: `buf` absent on genesis host | Tool substitution, not contract gap | Accept for core v1.0; restore `buf lint/breaking` in a provisioned runner |
| W-002: cargo absent | Rust acceleration unavailable | Accept; Python path is deterministic and far inside latency budget |
| Coverage below 100% | Primarily CLI/tool failure-rendering branches | Non-blocking; 90.76%, all requirement paths covered |
| Docker unavailable on genesis host | Production image was statically gated, not built locally | Build and publish from the Docker-capable release runner |
| No approved venue adapter | Live orders cannot reach a broker | Blocking only for live-money activation; requires governed adapter WP |
| SPIRE/Vault and replicated lease/storage not provisioned | Environment controls not demonstrated | Blocking only for live activation; deploy and drill in target environment |
| P99 measured on development host | Hardware/network certification outstanding | Repeat under production load before activation |

No repository TODOs, placeholder implementations, dead capability nodes, unresolved
traceability rows, or executable Work Packages remain.

## 8. Deployment Readiness

**Core platform / research / Engineering OS:** **GO** for `v1.0.0`.

**Live-money deployment:** **CONDITIONAL NO-GO** until the ARB receives evidence for:

1. SPIRE workload registration, TLS 1.3 handshake, certificate rotation, and Vault
   secret retrieval in the target cluster.
2. Active-passive deployment using replicated durable storage and fencing, with
   measured failover <30 seconds, RPO=0, and recovery <60 seconds.
3. A venue-specific adapter contract, sandbox certification, reconciliation drill,
   and kill-switch exercise.
4. Target-infrastructure load test reproducing P99 <50 ms.

## 9. Version 1.0 Recommendations

1. Tag and publish the core repository as `v1.0.0`.
2. Keep live trading disabled (`MP-04`/`MP-05`) in all unqualified environments.
3. Treat the four live-activation prerequisites as release-gate evidence, not as
   permission to weaken architecture or safety policy.
4. Restore native `buf` and cargo toolchains when the governed build environment
   supplies them; retain current substitute gates as defense in depth.

**Final ARB recommendation:** release AFRP Core 1.0.0; do not activate live money
until all environment-specific evidence is approved.
