# Layer 4 Utility Optimizer (WP-RT-1015)

`L4-DEC` solves MATH-001 §4 over a pre-allocated candidate grid (NFR-008):

    U_r(a) = U(a) - λ·R(a),    a* = argmax_{a ∈ 𝒜} U_r(a)

`U(a)` = scenario-expected P&L; `R(a)` = expected shortfall over worst tail.

## Action Grid

12 actions × 2 directions (LONG/SHORT) × 3 size fractions (0.25/0.5/1.0 ×
max_position_size) × 2 stop fractions (0.4%/0.8% × spot). Plus the flat
action (direction=0, U_r=0) as the always-present safe baseline.

## Determinism

No random numbers. Tie-break is by candidate grid index. Same context +
same scenarios → identical CIO-06 (EDR-009).

## Stop Loss

Stops are enforced within `_evaluate`: if the worst intra-period adverse
move exceeds `stop_distance`, the P&L is capped at `-stop_distance × size`.
