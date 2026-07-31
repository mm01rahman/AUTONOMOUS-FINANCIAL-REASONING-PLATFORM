# Layer 3 World Model Kernel (WP-RT-1012)

`L3-WRM` fuses six `CIO-03` domain belief assignments from Layer 2 agents
into a unified `CIO-04` `WorldStateVector` via deterministic DSmT PCR5.

## Architecture

- **`dsmt.py`** — pure DSmT library: label parsing, mass validation, PCR5
  combination, Shafer discounting, pignistic transform.
- **`worldmodel.py`** — `WorldModelKernel` orchestrates the fusion pipeline:
  reliability discounting, sequential PCR5 fold, regime hypothesis extraction.

## PCR5 fusion (MATH-001 §2)

Focal elements live on Dedekind's lattice `D^Θ`, Θ = {BULL, BEAR, RANGE}.
Hybrid model M1 constrains RANGE∩BULL = RANGE∩BEAR = ∅.

Two-source combination:

    m12(X) = Σ_{A∩B=X} m1(A)·m2(B)

PCR5 conflict redistribution for each conflicting pair (X,Y), X∩Y = ∅:

    m(X) += m1(X)²·m2(Y) / (m1(X)+m2(Y)) + m2(X)²·m1(Y) / (m2(X)+m1(Y))

Multi-source fusion: sequential left fold (fold order is canonical agent order).

## Degradation (NFR-003)

Missing or excluded agents are padded with the vacuous belief `m(Θ)=1`.
Zero healthy sources produce a vacuous world state; `L4-VAL` authorizes
`a_null` in that case.

## Determinism

- No I/O, no clocks, no randomness.
- Output is determined by agent belief inputs and calibration weights.
