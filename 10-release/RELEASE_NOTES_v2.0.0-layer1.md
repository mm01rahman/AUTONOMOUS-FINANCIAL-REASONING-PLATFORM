# Release Notes: v2.0.0-layer1 (Draft)

## Scope

Layer 1 Runtime milestone completion.

## Included work packages

- WP-RT-1001: Market data collection engine (`L1-ING`)
- WP-RT-1002: Feature store emission (`L1-FST`)
- WP-RT-1003: Relational persistence (`L1-RDB`)
- WP-RT-1004: Vector memory (`L1-MEM`)

## Highlights

- Canonical mixed-provider ingestion (tick + OHLCV) to CIO-01.
- Deterministic CIO-02 feature emission with immutable cache semantics.
- Deterministic relational append/replay and audit trail persistence.
- Deterministic vector memory retrieval with stable top-k tie breaking.

## Governance and quality

- All mandatory quality gates passed per work package.
- ERS evidence generated for each work package and layer milestone.
- Capability registry synchronized and dependency graph remains acyclic.

## Tagging

Do not create the Git tag automatically. Await repository owner approval before tagging `v2.0.0-layer1`.
