# Layer 6: Learning and Calibration Loop

## Overview

Layer 6 (`L6-OPT`) implements the out-of-band learning subsystem of the AFRP Runtime. It computes reliability calibration weights (CIO-11) from rolling Brier scores and deterministic regime embeddings (CIO-12) from named scalar features. Both outputs feed back into Layers 3 and 4 — never bypassing policy controls.

**Work Package:** WP-RT-1018  
**Subsystem:** SLS-600  
**Source:** `06-runtime/afrp_runtime/layer6/learning.py`

---

## Architecture

```
Historical outcomes (resolved forecasts)
        │
        ▼
  BrierCalibrator.observe()
        │  rolling window per agent
        ▼
  BrierCalibrator.emit()
        │
        ▼
CIO-11 CalibrationWeights  ──► L3-WRM (belief discounting)

Named scalar features (from L1-FEA)
        │
        ▼
  RegimeEmbedder.embed()
        │  sorted, hash-projected, L2-normalized
        ▼
  RegimeEmbedder.emit()
        │
        ▼
CIO-12 EpisodicEmbedding  ──► L1-MEM (episodic memory)
```

**L6-OPT is strictly out-of-band.** CIO-11 and CIO-12 carry no verdict, no HMAC signature, and no authorization. L4-VAL independently re-validates every proposed action (Article VIII).

---

## Components

### `multiclass_brier(probabilities, outcome)`

Computes the multiclass Brier score over the three-state frame `{BULL, BEAR, RANGE}`.

- Range: `[0, 2]`
- Perfect forecast: `0.0`
- Worst forecast: `2.0`
- Uniform prior: `2/3 ≈ 0.667`

**Validation:** probabilities must cover exactly the three outcomes, be in `[0, 1]`, and sum to `1.0 ± 1e-9`. Unknown outcomes raise `ContractViolationError`.

### `BrierCalibrator`

Rolling-window agent calibration producing bounded discounting weights (CIO-11).

| Parameter | Default | Description |
|-----------|---------|-------------|
| `window_cycles` | 100 | Max observations per agent (deque maxlen) |
| `weight_floor` | 0.05 | Minimum reliability weight |

**Weight formula:** `weight = max(floor, min(1.0, 1.0 - mean_brier / 2.0))`

- Perfect agent (`mean_brier = 0.0`) → weight `1.0`
- Worst agent (`mean_brier = 2.0`) → weight `floor`
- Uniform prior (`mean_brier ≈ 0.667`) → weight `≈ 0.667`

| Method | Description |
|--------|-------------|
| `observe(agent_id, probs, outcome, parent_cio_id)` | Record one resolved forecast |
| `mean_scores()` | Rolling mean Brier score per agent |
| `weights()` | Bounded reliability weight per agent |
| `emit(generated_at_ns)` | Emit CIO-11 with provenance chain |

### `RegimeEmbedder`

Deterministic hash-projection embedder for episodic regime memory (CIO-12).

**Embedding algorithm:**

1. Sort features by key (order-invariant by NFR-004)
2. For each `(feature_id, value)` pair, project onto each dimension via `_projection_sign(feature_id, dimension)` — a deterministic `blake2b` hash function
3. Scale by `1 / sqrt(n_features)` to normalize contribution
4. L2-normalize the resulting vector

**Properties:**
- Dimension: configurable (default 16)
- Identical inputs → identical vectors (replay reproducibility)
- Insertion-order invariant (sorted feature iteration)
- Non-finite values rejected with `ContractViolationError`

| Method | Description |
|--------|-------------|
| `embed(features)` | Project features → L2-normalized tuple |
| `emit(...)` | Emit deterministic CIO-12 episode |

---

## CIO Contracts

| CIO | Type | Fields |
|-----|------|--------|
| CIO-11 | `CalibrationWeights` | `envelope`, `agent_weights`, `brier_scores`, `window_cycles` |
| CIO-12 | `EpisodicEmbedding` | `envelope`, `instrument`, `vector`, `regime_label`, `window_start_ns`, `window_end_ns` |

---

## Out-of-Band Guarantee

CIO-11 and CIO-12 are **read-only calibration artifacts** — they carry no `verdict`, no `hmac_signature`, and no authorization. The learning loop updates beliefs and embeddings; it never authorizes execution. Policy enforcement remains exclusively in L4-VAL.

---

## Test Coverage

| File | Tests | Description |
|------|-------|-------------|
| `tests/unit/test_layer6.py` | 22 | Brier math, weight bounds, window eviction, embedding properties |
| `tests/integration/test_layer6_learning_integration.py` | 10 | CIO-11/12 pipeline, replay reproducibility, out-of-band guarantee |

### Key test scenarios

- Perfect/worst forecast Brier score correctness
- Malformed probability distribution rejected
- Rolling window evicts old observations
- Multiple agents tracked independently
- CIO-11 provenance and metadata
- Invalid constructor bounds rejected
- Embedding unit norm and order invariance
- Replay reproducibility (bit-for-bit identical across runs)
- Different regime labels produce different envelope hashes
- CIO-11/12 carry no verdict or HMAC signature

---

## Traceability

| Item | Reference |
|------|-----------|
| Functional Requirement | FR-014 |
| Non-Functional Requirement | NFR-004 |
| Subsystem | SLS-600 |
| CIO contracts | CIO-11, CIO-12 |
| ADR | ADR-0001 |
| VVC | TVM-001 |
