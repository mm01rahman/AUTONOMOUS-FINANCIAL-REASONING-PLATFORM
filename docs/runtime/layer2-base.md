# Layer 2 Base and DSmT Foundation (WP-RT-1005)

`L2-BASE` defines deterministic shared primitives for Layer 2 domain agents.

## Core elements

- Canonical focal labels over `D^Theta`:
  - singleton: `BULL`, `BEAR`, `RANGE`
  - union: e.g. `BEAR|BULL`
  - intersection: e.g. `BEAR&BULL`
  - uncertainty: `THETA`
- Mass primitives:
  - `normalize_masses`
  - `vacuous_bba`
  - `pad_ignorance`
- Contract-driven abstract base:
  - `BeliefAgent` with deterministic `evaluate` output as `CIO-03` `DomainBelief`.

## Guarantees

- Mass assignments are normalized and validated before emission.
- Missing or low-quality telemetry degrades to vacuous belief instead of failing.
- Deterministic envelope/provenance for downstream fusion in Layer 3.
