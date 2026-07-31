# Layer 1 Vector Memory (WP-RT-1004)

`L1-MEM` stores deterministic fixed-dimension embeddings for regime memory and
retrieves nearest episodes by cosine similarity.

## Data model

- `MemoryRecord` fields:
  - `record_id`
  - `vector`
  - `regime_label`
  - `window_start_ns`
  - `window_end_ns`

## Guarantees

- Strict dimension validation on `store` and `query`.
- Deterministic top-k ordering by:
  1. descending similarity
  2. ascending `record_id` tie-break
- Numerically stable similarity: returns `0.0` for null vectors.
- Bounded query behavior for `top_k <= 0` and oversized `top_k`.
