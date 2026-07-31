# Release Notes — v2.0.0-layer4

## Runtime Layer 4: Decision Context, Optimizer, Policy Engine

### New Capabilities

**L4-FUS — Decision Context Synthesizer (CIO-05B)**

Combines CIO-04 `WorldStateVector`, CIO-05A `ScenarioSet`, and CIO-10
`PortfolioState` into a `DecisionContext` optimization payload. Risk
aversion λ is derived from the mission profile risk tolerance (EDR-005
configuration authority): λ = 2.0 / max(risk_tolerance, 0.25). Provenance
preserved via parent CIO IDs and trace_id inheritance.

**L4-DEC — Utility Optimizer (CIO-06)**

Solves MATH-001 §4 over a 12-action pre-allocated grid (NFR-008):
U_r(a) = U(a) - λ·R(a). U(a) = scenario-expected P&L; R(a) = expected
shortfall over worst 10% tail. Stop-loss enforced within evaluation.
Flat action (dir=0, U_r=0) serves as the safe baseline (Article VIII bias).
Deterministic tie-break by grid index (EDR-009).

**L4-VAL — Policy Engine (CIO-07)**

Projects unconstrained a* onto the feasible constraint set 𝒞 via
Pi_C(a*). Eight NULL_TRADE trigger conditions enforce Article VIII (No
Trade over a Poor Trade): non-NORMAL state, trading forbidden by profile,
quorum deficiency, spread cap, non-positive utility, missing stop, exposure
cap. Every CIO-07 carries an HMAC-SHA256 audit signature (NFR-007; key
from AFRP_AUDIT_HMAC_KEY env, EDR-008).

### Quality Gate Results

- ruff: PASS
- mypy --strict: PASS
- pytest: 278 tests PASS (34 new Layer 4 tests)
- Architecture validation: PASS
- ERS evidence: EXEC-114.yaml, EXEC-115.yaml, EXEC-116.yaml

### Capability Registry State

- L4-FUS: COMPLETE
- L4-DEC: COMPLETE
- L4-VAL: COMPLETE
- L5-EXE: AVAILABLE (unlocked; awaiting ARB approval to begin Layer 5)

### Architecture Impact

None. Layer 4 implements only pre-approved capabilities per Runtime Planning
v1.2.0 backlog. No CIO contracts modified. No Layer 1/2/3 changes.
