# Layer 4 Policy Engine (WP-RT-1016)

`L4-VAL` projects the unconstrained candidate a* onto the feasible constraint
set 𝒞 (MATH-001 §4): `a_e = Π_𝒞(a*)`. When projection fails, the output
defaults to a_null — "No Trade over a Poor Trade" (Article VIII).

## NULL_TRADE conditions

Any of the following produces NULL_TRADE:

1. `candidate.direction == 0` — already flat
2. `operational_state != NORMAL` (SYS-03)
3. `profile.allow_trading == False` (MP-04, MP-05)
4. `agent_quorum < profile.required_quorum`
5. `spread_bps > profile.max_spread_bps`
6. `risk_adjusted_utility <= 0` — no edge
7. `stop_price <= 0` on a sized action — no stop-loss defined
8. Position cap leaves zero headroom after Pi_C projection

## Pi_C projection

    projected_size = min(size, max_position_size, headroom)
    headroom = max_position_size - portfolio.gross_exposure

If `projected_size < size` → PROJECTED verdict with reduced size.

## HMAC audit signature (NFR-007/EDR-008)

Every CIO-07 carries a 32-byte HMAC-SHA256 signature over the payload string:

    "<candidate_id>:<verdict>:<direction>:<size>:<entry>:<stop>"

The signing key is sourced exclusively from `AFRP_AUDIT_HMAC_KEY` environment
variable (EDR-008); absent key raises ConfigurationError.
