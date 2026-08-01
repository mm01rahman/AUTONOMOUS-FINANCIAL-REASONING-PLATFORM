# Release Notes — v2.0.0-layer5
**AFRP Runtime Layer 5 — Execution Gateway & Portfolio Reconciliation**

---

## What's New

### L5-EXE: Order Gateway and Portfolio Reconciliation (WP-RT-1017)

The Layer 5 execution module delivers the deterministic order lifecycle, venue event processing, and portfolio reconciliation capabilities required by FR-013, NFR-005, and NFR-007.

**Key capabilities delivered:**

- **Deterministic Order FSM** — exhaustive state machine with 8 `OrderState` values and explicit legal transition table; illegal transitions raise `ContractViolationError` immediately.
- **Fill quantity conservation** — `PARTIAL_FILL` must leave unfilled remainder; `FILL` must complete exactly the authorized quantity; overfill is unconditionally rejected.
- **HMAC audit ledger** — every state transition is synchronously signed (`HMAC-SHA256`) and appended to an append-only audit ledger; tamper detection via constant-time comparison.
- **Portfolio reconciliation** — fill-driven ledger tracking cash, position quantity, weighted average cost basis, unrealized PnL, and gross exposure; `snapshot()` emits CIO-10 with mark-to-market valuation.
- **Recovery paths** — `restore_order()` and `restore()` enable RTO recovery from durable CIO-08 / CIO-10 checkpoints with action-ID validation.

---

## Files Changed

| File | Change |
|------|--------|
| `06-runtime/afrp_runtime/layer5/execution.py` | Pre-implemented source (unchanged) |
| `tests/unit/test_layer5.py` | 26 unit tests (pre-existing) |
| `tests/integration/test_layer5_execution_integration.py` | 6 integration tests (new) |
| `docs/runtime/layer5-execution.md` | Runtime documentation (new) |
| `05-work-packages/WP-RT-1017.yaml` | Status → Completed |
| `05-work-packages/WP-RT-1017/evidence/EXEC-117.yaml` | ERS-1.0 evidence record |
| `03-engineering/CAPABILITY_REGISTRY.yaml` | L5-EXE COMPLETE; L6-OPT AVAILABLE |

---

## Test Coverage

- **Layer 5 tests:** 32 (26 unit + 6 integration)
- **Cumulative layer tests:** 284 (all L1-L5 passing)

---

## Breaking Changes

None. Layer 5 adds new modules only. No existing contracts modified.

---

## Dependencies

- L4-VAL (Policy Validation Engine) — COMPLETE ✓
- L1-RDB (Persistent Key-Value Store) — COMPLETE ✓

---

## Next Steps

Layer 6 (L6-OPT, WP-RT-1018) is now AVAILABLE.  
**ARB approval required before beginning Layer 6.**
