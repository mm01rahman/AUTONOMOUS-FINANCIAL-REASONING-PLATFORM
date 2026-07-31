# Layer 3 Scenario Simulator (WP-RT-1013)

`L3-SIM` generates `CIO-05A` `ScenarioSet` from a `CIO-04` `WorldStateVector`
via deterministic Monte-Carlo simulation on the equilibrium manifold ℰ.

## Algorithm

Sigma_EWM samples Geometric Brownian Motion paths and admits only those
trajectories τ satisfying |ln(S_T/S_0)| ≤ `max_abs_log_move` (ℰ boundary):

    Σ_EWM(τ) = P_raw(τ | S_t, a) / Z   if τ ∈ ℰ, else 0

Drift and volatility are derived from the pignistic transform of the fused
CIO-04 masses:

    drift   = (BetP(BULL) - BetP(BEAR)) × drift_scale × (1 - ε)
    sigma   = base_volatility × (1 + ε)

where ε = `WorldStateVector.epistemic_uncertainty`.

## Differential entropy

Aleatory dispersion is reported as the differential Shannon entropy of the
Gaussian closure of the admitted terminal log-return distribution:

    H = ½ · ln(2πe · σ²)

## Determinism

`component_rng(SUBSYSTEM_ID, cycle)` produces a stable stream per cycle.
Same input + same cycle → identical `ScenarioSet` (EDR-009/NFR-004).

## Output (CIO-05A)

- `scenarios`: tuple of `Scenario` (equal-weight probability normalization)
- `differential_entropy`: float (Gaussian closure of admitted terminals)
- `horizon_seconds`: simulation time horizon
- `random_seed`: 42 (canonical per EDR-009)
- `envelope`: provenance trace linking back to CIO-04 parent
