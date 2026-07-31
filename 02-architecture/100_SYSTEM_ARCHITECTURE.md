# DOCUMENT 100 — `100_SYSTEM_ARCHITECTURE.md`

> **Authority Level:** Level 1 (Semi-Immutable) | **Specification ID:** `ARCH-001`
> 

## 1. Three Product Architecture (`ARCH-002`)

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PRODUCT 1: ENGINEERING OPERATING SYSTEM (EOS)                                    │
│ Path: tools/afrp-cli/ | 03-engineering/ | 05-work-packages/                       │
│ Responsibility: Governs AI agent execution, DAG planning, AST validation, and   │
│                 evidence collection.                                            │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Governs & Builds
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PRODUCT 2: AFRP RUNTIME PLATFORM                                                │
│ Path: 06-runtime/ (Layers 1 through 6)                                          │
│ Responsibility: Real-time telemetry ingestion, belief formation, world model    │
│                 synthesis, trade decisioning, and order execution.              │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Informs & Calibrates
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PRODUCT 3: RESEARCH & STRATEGY PLATFORM                                         │
│ Path: 07-research/                                                              │
│ Responsibility: Offline backtesting, strategy discovery, model training, regime   │
│                 clustering, and synthetic scenario generation.                  │
└─────────────────────────────────────────────────────────────────────────────────┘

```

## 2. Non-Functional Requirements Specification (`NFR-001`..`010`)

* **`NFR-001` (Latency Budget):** P99 decision execution loop latency MUST NOT exceed $50\text{ms}$ ($10\text{ms}$ target).


* **`NFR-002` (Availability SLO):** High-availability active-passive clustering satisfying 99.99% operational uptime.


* **`NFR-003` (Graceful Degradation):** Telemetry feed loss MUST trigger degraded quorum operation ($m(\Theta)$ padding) rather than panic crashes.


* **`NFR-004` (Determinism):** Offline math logic MUST produce identical results given identical inputs and random seed `42`.


* **`NFR-005` (RPO / RTO Bounds):** Recovery Point Objective $\text{RPO} = 0.0$ lost trades; Recovery Time Objective $\text{RTO} < 60\text{s}$.


* **`NFR-006` (Security Zero-Trust):** All internal gRPC calls MUST enforce mTLS (TLS 1.3) with SPIFFE/SPIRE identities.


* **`NFR-007` (Auditability):** Every order MUST carry a cryptographically signed HMAC audit log and OpenTelemetry trace.


* **`NFR-008` (Resource Confinement):** Memory allocations inside the live execution path MUST be pre-allocated or pooled.


* **`NFR-009` (Type Safety):** 100% strict MyPy compliance (`mypy --strict`) across all Python codebases.


* **`NFR-010` (Contract Immutability):** Protobuf wire interfaces MUST pass `buf breaking` validation against `main`.



## 3. Architecture Fitness Functions (`FIT-001`..`008`)

1. **`FIT-001` (DAG Circularity Check):** Executed by `afrp plan`. Asserts zero cyclic dependencies in `CAPABILITY_REGISTRY.yaml`.


2. **`FIT-002` (AST Illegal Syntax Audit):** Executed by `afrp validate`. Flags bare `except:` clauses or untyped functions.


3. **`FIT-003` (Protobuf Custom Option Check):** Asserts every message defines `cio_id`, `owner_subsystem`, and `stability_level`.


4. **`FIT-004` (Cross-Layer Import Prohibition):** Verifies `06-runtime/` layers do not import across sibling layer directories.


5. **`FIT-005` (Boundary Confinement Verification):** Compares `git diff` against `bounded_files` array in active Work Package.


6. **`FIT-006` (Kernel Length Check):** Asserts `00-governance/KERNEL.md` contains $\le 400$ words.


7. **`FIT-007` (Traceability Verification):** Asserts 100% requirement coverage in `03-engineering/TRACEABILITY_MATRIX.yaml`.


8. **`FIT-008` (Deterministic Replay Verification):** Replays historical ticks (`MP-04`) to assert state reproduction.



## 4. Engineering Decision Rules (`EDR-001`..`012`)

* **`EDR-001`:** All high-level business logic MUST depend on abstract interfaces (Protobuf, ABCs, Protocols).


* **`EDR-002`:** Direct cross-layer Python imports in `06-runtime/` are STRICTLY FORBIDDEN.


* **`EDR-003`:** I/O-bound code MUST use `asyncio`; CPU-bound math MUST use process pools or Rust extensions.


* **`EDR-004`:** Catching bare `except:` or generic `Exception` without re-raising is STRICTLY PROHIBITED.


* **`EDR-005`:** Config Precedence: Emergency Overrides > Mission Profile > Policy Bundle > Subsystem Config.


* **`EDR-006`:** All logging MUST emit structured JSON conforming to `OBS-01` schema.


* **`EDR-007`:** Live decision execution path (`Layer 4`/`5`) MUST NOT exceed $50\text{ms}$ (P99).


* **`EDR-008`:** Zero hardcoded secrets. Vault mTLS or environment variables ONLY.


* **`EDR-009`:** Offline math logic MUST be testable under deterministic seeds (`seed=42`).


* **`EDR-10`:** Protobuf breaking wire changes are FORBIDDEN without major version bumps.


* **`EDR-11`:** 100% `mypy --strict` compliance. Implicit `Any` is STRICTLY PROHIBITED.


* **`EDR-12`:** Deprecations require a 1-minor-version grace period before removal.
