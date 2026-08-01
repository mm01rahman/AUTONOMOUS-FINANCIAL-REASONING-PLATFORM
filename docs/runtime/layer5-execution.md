# Layer 5: Order Gateway and Portfolio Reconciliation

## Overview

Layer 5 (`L5-EXE`) implements the deterministic execution layer of the Autonomous Financial Reasoning Platform. It transforms authorized CIO-07 actions into submitted orders (CIO-08), processes venue events (CIO-09), and emits auditable portfolio snapshots (CIO-10).

**Work Package:** WP-RT-1017  
**Subsystem:** SLS-500  
**Source:** `06-runtime/afrp_runtime/layer5/execution.py`

---

## Architecture

```
CIO-07 AuthorizedAction
        │
        ▼
  OrderGateway.submit()
        │
        ▼
CIO-08 ExecutionIntent  ─── (state machine) ──► FILLED / CANCELLED / ...
        │
CIO-09 ExecutionReport ──► apply_report()
        │
        ▼
PortfolioReconciler.apply_fill()
        │
        ▼
CIO-10 PortfolioState
```

---

## Order State Machine

Legal transitions are exhaustive and explicitly enumerated in `_LEGAL_TRANSITIONS`:

```
NEW ──► SUBMITTED ──► ACKNOWLEDGED ──► PARTIALLY_FILLED ──► FILLED  (terminal)
     │                             │                     │
     ▼                             ▼                     ▼
 CANCELLED                     CANCELLED              CANCELLED (terminal)
 (terminal)                  REJECTED (terminal)     EXPIRED  (terminal)
                              EXPIRED  (terminal)
```

- Terminal states: `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`
- Illegal transitions are rejected with `ContractViolationError`

---

## Components

### OrderGateway

The `OrderGateway` owns the order state machine and provides the following operations:

| Method | Description |
|--------|-------------|
| `submit(action, at_ns)` | Commits an authorized CIO-07 as a new SUBMITTED CIO-08 |
| `apply_report(report)` | Applies a CIO-09 venue event and advances the FSM |
| `cancel(order_id, at_ns)` | Locally cancels a live order |
| `snapshot(order_id, at_ns)` | Returns a CIO-08 checkpoint without FSM side effects |
| `restore_order(intent, action)` | Restores an order from a durable checkpoint (RTO path) |
| `record(order_id)` | Returns the live `OrderRecord` for inspection |

### Validation in `submit()`

- `verdict` must be `AUTHORIZED` or `PROJECTED` — `NULL_TRADE` / `REJECTED` / `UNSPECIFIED` raise `ContractViolationError`
- `direction` must be `+1.0` or `-1.0`; `size` must be positive
- `hmac_signature` must be non-empty

### Fill Quantity Conservation

`apply_report()` enforces two fill-conservation invariants:

1. **`PARTIAL_FILL` must leave remainder** — a partial fill equal to or exceeding the authorized quantity raises.
2. **`FILL` must complete exactly** — a final fill that leaves any unfilled quantity raises.
3. **Non-fill events must carry zero fill quantity**.

### AuditLedger

Every state transition is synchronously HMAC-signed and appended to `AuditLedger.entries`:

- Signature covers: `order_id : state_int : event : at_ns : trace_id : span_id`
- Digest: `HMAC-SHA256`
- Key source: `AFRP_AUDIT_HMAC_KEY` environment variable (or injected directly for testing)
- `verify(entry)` performs constant-time comparison

### PortfolioReconciler

Fill-driven ledger maintaining cash and position cost basis:

| Method | Description |
|--------|-------------|
| `apply_fill(intent, report)` | Applies a fill to cash and position average cost |
| `snapshot(marks, at_ns)` | Marks open positions and emits a CIO-10 snapshot |
| `restore(state)` | Restores from a durable CIO-10 checkpoint (RTO path) |

**Cash accounting:**
- LONG fill: `cash -= fill_quantity × fill_price`
- SHORT fill: `cash += fill_quantity × fill_price` (via `signed_fill = direction × quantity`)

**Position cost basis:** weighted average for same-direction fills; reversal resets or keeps average based on net quantity.

---

## Environment Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `AFRP_AUDIT_HMAC_KEY` | Yes | HMAC key for audit ledger signatures |

---

## Test Coverage

| File | Tests | Description |
|------|-------|-------------|
| `tests/unit/test_layer5.py` | 26 | FSM transitions, fill accounting, audit, recovery |
| `tests/integration/test_layer5_execution_integration.py` | 6 | Full pipeline from authorized action to reconciled portfolio |

### Key test scenarios

- Terminal states have no legal successors
- Submit with `NULL_TRADE`/unsigned action raises
- `PARTIAL_FILL` completing total raises; overfill raises
- Non-fill event with nonzero fill quantity raises
- Unknown order raises
- Audit entry tamper detection
- Order checkpoint restore
- Long/short fill with mark-to-market PnL
- Weighted average cost basis across partial fills
- Missing mark raises on `snapshot()`
- Portfolio checkpoint restore

---

## Traceability

| Item | Reference |
|------|-----------|
| Functional Requirement | FR-013 |
| Non-Functional Requirements | NFR-005, NFR-007 |
| Subsystem | SLS-500 |
| CIO contracts | CIO-08, CIO-09, CIO-10 |
| ADR | ADR-0001 |
| VVC | TVM-001 |
