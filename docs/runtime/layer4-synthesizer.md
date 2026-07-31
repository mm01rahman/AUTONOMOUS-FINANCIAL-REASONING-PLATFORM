# Layer 4 Decision Synthesizer (WP-RT-1014)

`L4-FUS` combines `CIO-04` (`WorldStateVector`), `CIO-05A` (`ScenarioSet`),
and `CIO-10` (`PortfolioState`) into a `CIO-05B` `DecisionContext` optimization
payload.

## Algorithm

Risk aversion λ is derived from the mission profile risk tolerance (EDR-005):

    λ = BASE_LAMBDA / max(risk_tolerance, 0.25)

Higher tolerance → lower λ → optimizer takes more aggressive positions.

| Profile | risk_tolerance | λ |
|---|---|---|
| MP-01 | 0.5 | 4.0 |
| MP-02 | 1.0 | 2.0 |
| MP-03 | 1.5 | 1.33 |

## Provenance

The CIO-05B envelope records three parent CIO IDs (world state, scenario set,
portfolio) and inherits the CIO-04 trace_id, preserving full audit lineage.
