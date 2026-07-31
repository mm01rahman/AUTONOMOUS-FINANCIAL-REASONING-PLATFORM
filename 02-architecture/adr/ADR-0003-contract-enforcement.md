# ADR-0003 — Wire Contract Enforcement and Runtime Binding Strategy

**Status:** Accepted · **Date:** 2026-07-31 · **Level:** 1 (ARB)

## Context

`proto/afrp/v1/` is the Level-1 wire contract surface (GOV-002). The host lacks
`buf` (waiver W-001) and `cargo` (W-002). Runtime layers must communicate only via
CIO contracts (EDR-002/FIT-004), and tests must stay deterministic and offline.

## Decision

1. **Authoritative wire contracts** live in `proto/afrp/v1/`:
   `annotations.proto` (custom options), `envelope.proto` (`CognitiveEnvelope`
   verbatim from REF-001 §1), `cio.proto` (CIO-01..CIO-12).
2. **Enforcement (buf substitute, W-001):** `tools/proto_gate.py`
   (`uv run python -m tools.proto_gate`) compiles the contracts with
   `grpcio-tools`, asserts **FIT-003** (every message carries `cio_id`,
   `owner_subsystem`, `stability_level`), and enforces **NFR-010/EDR-10** by
   comparing the compiled `FileDescriptorSet` against the committed snapshot at
   `09-validation/contracts/afrp_v1.snapshot.json` (no removed message, no removed
   or renumbered/retyped field). Snapshot changes require an ADR.
3. **In-process binding:** runtime layers exchange frozen, typed dataclasses in
   `06-runtime/afrp_runtime/contracts/` mirroring the proto messages
   field-for-field (names, numbers documented). Generated `*_pb2.py` code is
   **not** committed; the proto gate regenerates it on demand into an ignored
   directory, and round-trip parity tests (dataclass → pb2 → bytes → dataclass)
   run in system validation. This keeps tests deterministic across protoc
   versions while the proto remains the single wire truth.

## Consequences

- Any contract drift (proto vs dataclasses) is caught by parity tests.
- Breaking wire changes fail the snapshot gate; additive evolution passes.
- When `buf` becomes available its `lint`/`breaking` gates are restored verbatim
  alongside (not replacing) the snapshot gate.
