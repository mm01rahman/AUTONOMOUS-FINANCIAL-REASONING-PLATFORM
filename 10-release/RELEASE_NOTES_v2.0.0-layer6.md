# Release Notes — v2.0.0-layer6
**AFRP Runtime Layer 6 — Learning and Calibration Loop**

---

## What's New

### L6-OPT: Brier Calibration and Episodic Embeddings (WP-RT-1018)

The Layer 6 learning module delivers the out-of-band calibration and embedding capabilities required by FR-014 and NFR-004.

**Key capabilities delivered:**

- **Multiclass Brier scoring** — `multiclass_brier()` computes the `[0, 2]` score over the `{BULL, BEAR, RANGE}` frame with strict validation (probabilities must sum to 1.0 ± 1e-9, be in `[0, 1]`, and cover all three outcomes).
- **Rolling calibration** — `BrierCalibrator` maintains a configurable-length deque per agent; `weights()` maps mean Brier score to bounded reliability `[floor, 1.0]`.
- **CIO-11 emission** — `emit()` produces a schema-valid `CalibrationWeights` with full provenance chain from observed forecast CIO IDs.
- **Deterministic embeddings** — `RegimeEmbedder` projects named scalar features to L2-normalized vectors via `blake2b` hash projection; sorted key iteration ensures order invariance (NFR-004).
- **CIO-12 emission** — `emit()` produces a reproducible `EpisodicEmbedding` with regime label, window timestamps, and parent CIO provenance.
- **Out-of-band guarantee** — CIO-11 and CIO-12 carry no `verdict`, no `hmac_signature`, and no authorization. Policy enforcement remains exclusively in L4-VAL.

---

## Files Changed

| File | Change |
|------|--------|
| `06-runtime/afrp_runtime/layer6/learning.py` | Pre-implemented source (unchanged) |
| `tests/unit/test_layer6.py` | 22 unit tests (pre-existing) |
| `tests/integration/test_layer6_learning_integration.py` | 10 integration tests (new) |
| `docs/runtime/layer6-learning.md` | Runtime documentation (new) |
| `05-work-packages/WP-RT-1018.yaml` | Status → Completed |
| `05-work-packages/WP-RT-1018/evidence/EXEC-118.yaml` | ERS-1.0 evidence record |
| `03-engineering/CAPABILITY_REGISTRY.yaml` | L6-OPT COMPLETE; all Runtime capabilities COMPLETE |

---

## Test Coverage

- **Layer 6 tests:** 32 (22 unit + 10 integration)
- **Cumulative layer tests:** 294 (all L1-L6 passing)

---

## Breaking Changes

None. Layer 6 adds new modules only. No existing contracts modified.

---

## Dependencies

- L5-EXE (Execution Gateway) — COMPLETE ✓
- L1-RDB (Persistent Key-Value Store) — COMPLETE ✓
- L1-MEM (Episodic Memory) — COMPLETE ✓

---

## Runtime Implementation Complete

All 15 Runtime Work Packages (WP-RT-1001 through WP-RT-1018) are COMPLETE.  
All 15 Runtime Capabilities (L1-L6) are COMPLETE.  
**ARB approval required before any production work.**
