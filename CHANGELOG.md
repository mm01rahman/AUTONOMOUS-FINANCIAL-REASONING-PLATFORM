# Changelog

All notable AFRP changes are recorded here. The project follows semantic versioning.

## [1.0.0] — 2026-07-31

### Added

- AFRP-BASELINE-1.0.0 governance corpus, EGP-2.0 bootloader, manifests, fingerprint
  ledger, WPS-1.0/ERS-1.0 schemas, capability DAG, and traceability matrix.
- Engineering OS commands: `afrp boot`, `plan`, `validate`, `evidence`, `health`,
  and `run`, including RSM-1.0 lifecycle enforcement and rollback.
- Protobuf custom annotations, CognitiveEnvelope, CIO-01 through CIO-12, and
  descriptor-snapshot compatibility enforcement.
- Six-layer runtime:
  - Layer 1 ingestion, features, synchronous relational ledger, vector memory.
  - Layer 2 DSmT mass foundation and six domain belief agents.
  - Layer 3 PCR5 world model and equilibrium scenario simulator.
  - Layer 4 risk-adjusted decision optimization and signed policy projection.
  - Layer 5 exhaustive order FSM, audit ledger, fills, recovery, reconciliation.
  - Layer 6 Brier calibration and deterministic episodic embeddings.
- Deterministic research backtest harness with cost model, metrics, and replay hash.
- Enforceable operations policies, non-root frozen container, and CI quality gates.
- System fitness gate: frozen MP-04 replay, total-feed-loss chaos, and P99 latency.

### Quality

- 372 tests passing.
- 90.7613% line/branch-aware coverage.
- 33/33 capabilities complete; 47/47 requirements covered.
- 31/31 Work Packages have ERS-1.0 evidence.
- Decision/execution P99 observed below 0.4 ms against the 50 ms requirement.

### Known release exceptions

- W-001: `buf` unavailable on the genesis host; grpcio-tools + descriptor snapshot
  enforce syntax, FIT-003, and NFR-010.
- W-002: Rust/cargo unavailable; CPU paths are pure deterministic Python and the
  empty Cargo workspace preserves the extension boundary.

[1.0.0]: https://github.com/mm01rahman/AUTONOMOUS-FINANCIAL-REASONING-PLATFORM/releases/tag/v1.0.0
