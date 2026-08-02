# Changelog

All notable AFRP changes are recorded here. The project follows semantic versioning.

## [1.3.0] — 2026-08-01

### Added

- Phase E alpha research and strategy-evolution toolkit (`tools/alpha_research/`):
  deterministic local dataset ingestion, feature engineering, governed strategy
  research, anti-overfitting parameter search, walk-forward validation,
  Monte Carlo robustness, regime adaptation, and promotion assessment outputs.
- Phase E artifacts under `11-research/phase-e/`, documentation
  `docs/research/PHASE_E_ALPHA_RESEARCH.md`, and governance package
  `WP-IMP-0039` / evidence `EXEC-041`.

### Fixed

- Phase D.5 risk monitoring now suppresses false-positive concentration alerts for
  single-instrument shadow runs by using supplied per-position notionals when
  available.
- Phase D.5 decision-log generation now resets JSONL output per run so digests and
  record counts remain truthful when reusing the same artifact directory.

### Added

- Phase D paper-trading and live shadow execution platform (`tools/paper_trading/`):
  - live market data gateway with provider interfaces and deterministic live-sim feeds;
  - shadow execution engine (fills, partial fills, simulated failures, spread/slippage/latency);
  - virtual portfolio, decision logs, risk/performance monitors, dashboard and reporting outputs.
- Phase D governance package `WP-IMP-0038` and evidence `EXEC-038`.
- Phase D unit/integration tests and deterministic artifact generation under `11-research/phase-d/`.

### Changed

- `03-engineering/CAPABILITY_REGISTRY.yaml` adds `PAPER-SHADOW-EXEC` (depends on `QUANT-BACKTEST`).
- `03-engineering/TRACEABILITY_MATRIX.yaml` adds NFR-025..NFR-028 for Phase D.
- `.github/workflows/quality.yml` now runs Phase D report generation and uploads artifacts.

## [1.2.0] — 2026-08-01

### Added

- Official Runtime implementation backlog:
  - 18 Runtime Work Packages (`WP-RT-1001` .. `WP-RT-1018`) created under
    `05-work-packages/` for Layer 1 through Layer 6 runtime capabilities.
  - Planning-only package metadata added (objectives, acceptance criteria, tests,
    evidence requirements, complexity, quality gates, architecture references).

### Changed

- Runtime capability entries in `03-engineering/CAPABILITY_REGISTRY.yaml` updated to:
  - point to approved Runtime backlog work packages (`WP-RT-*`);
  - reflect planning lifecycle (`AVAILABLE`/`LOCKED`) instead of completed runtime state;
  - include planning status (`READY`), layer metadata, and traceability metadata.

### Planning Milestone Artifacts

- Runtime planning report:
  - `10-release/RUNTIME_PLANNING_REPORT_v1.2.0.md`
- Runtime backlog release notes:
  - `docs/releases/v1.2.0-runtime-backlog.md`

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
