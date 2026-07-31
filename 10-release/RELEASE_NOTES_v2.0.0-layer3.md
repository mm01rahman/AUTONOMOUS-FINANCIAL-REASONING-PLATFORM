# Release Notes — v2.0.0-layer3

## Runtime Layer 3: World Model Kernel + Scenario Simulator

### New Capabilities

**L3-WRM — World Model Kernel (CIO-04)**

Fuses six Layer 2 domain belief assignments into a unified market world state
via deterministic DSmT PCR5 combination. Supports degraded quorum operation:
missing or excluded agents are padded with vacuous belief m(THETA)=1 so the
system never blocks on incomplete agent input (NFR-003).

Key components:
- `dsmt.py`: Pure DSmT PCR5 library (label parsing, mass validation, two-source
  combination, Shafer discounting, pignistic transform).
- `worldmodel.py`: `WorldModelKernel.fuse()` orchestrates reliability discounting,
  sequential PCR5 fold, and regime hypothesis extraction.

**L3-SIM — Sigma_EWM Scenario Simulator (CIO-05A)**

Generates deterministic Monte-Carlo price trajectories conditioned on the
CIO-04 world state. Enforces the equilibrium manifold ℰ boundary
(|ln(S_T/S_0)| ≤ max_abs_log_move) and computes aleatory dispersion via
Gaussian closure differential entropy H = 0.5 * ln(2πeσ²).

Key component:
- `simulator.py`: `ScenarioSimulator.simulate()` with seeded RNG per cognitive
  cycle (EDR-009/NFR-004 determinism guarantee).

### Quality Gate Results

- ruff: PASS
- mypy --strict: PASS
- pytest: 244 tests PASS (38 new Layer 3 tests)
- Architecture validation: PASS
- ERS evidence: EXEC-112.yaml, EXEC-113.yaml

### Capability Registry State

- L3-WRM: COMPLETE
- L3-SIM: COMPLETE
- L4-FUS: AVAILABLE (unlocked; awaiting ARB approval to begin Layer 4)

### Architecture Impact

None. Layer 3 implements only pre-approved capabilities per the Runtime
Planning v1.2.0 backlog. No CIO contracts modified. No Layer 1/2 changes.
