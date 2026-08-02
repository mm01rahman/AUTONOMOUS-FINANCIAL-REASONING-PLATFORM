# Macro Alpha Completion Report

## Outcome

The first complete Phase G campaign is closed as a **governed rejection**.

- **Campaign ID:** `IKROS-RESEARCHCAMPAIGN-20260802-0001`
- **Completion report:** `IKROS-CAMPAIGNREPORT-20260802-0001`
- **Research question:** `IKROS-RQ-20260802-0001`
- **Hypothesis:** `IKROS-HYP-20260802-0001`
- **Experiment:** `IKROS-EXP-20260802-0001`
- **Validation artifact:** `IKROS-VAL-20260802-0001`
- **Contradictory evidence:** `IKROS-CONTRA-20260802-0001`
- **Conclusion:** `IKROS-CONCL-20260802-0001`
- **Alpha candidate:** `IKROS-ALPHACAND-20260802-0001`
- **Confidence assessments:** `ICA-20260802-0001` (hypothesis), `ICA-20260802-0002` (candidate)

## Decision

Do **not** advance the macro-only baseline.

The campaign preserved the full research chain inside IKROS and concluded that the current macro-only XAU/USD baseline is useful as contradiction-rich institutional memory, but not as an advanceable alpha candidate.

## Deterministic evidence

Key imported Phase E metrics:

| Metric | Value |
| --- | --- |
| Full-sample return | `-0.081674` |
| Full-sample Sharpe | `-2.1270` |
| Walk-forward Sharpe | `-1.9781` |
| Walk-forward total return | `0.015755` |
| Positive fold ratio | `0.0` |
| Monte Carlo ruin probability | `0.0125` |

Recorded confidence after contradiction-aware review:

| Target | Lifecycle | Overall confidence |
| --- | --- | --- |
| `IKROS-HYP-20260802-0001` | `REFUTED` | `0.2366` |
| `IKROS-ALPHACAND-20260802-0001` | `REJECTED` | `0.3163` |

## Rejection basis

1. Walk-forward out-of-sample edge was not positive.
2. Positive fold ratio remained below the governance minimum.
3. Full-sample expectancy was not positive.
4. Required Phase G validation components remain incomplete.

## Registered deliverables

The campaign is fully persisted in `data/ikros/` across registries, graph, memory, ingestion reports, orchestrator audit, completion reporting, and confidence history.

## Next research posture

Macro Alpha remains open as a program, but the **macro-only baseline** is closed as a rejected starting point. Future work should branch from regime-conditional, feature-discovery, or causal variants rather than retesting the same baseline unchanged.
