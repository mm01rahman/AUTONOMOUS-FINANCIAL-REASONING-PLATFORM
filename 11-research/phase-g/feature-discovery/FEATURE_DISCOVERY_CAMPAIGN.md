# Campaign 0003 - Institutional Feature Discovery Within the Six-State Market Taxonomy

## Research question

Which features exhibit stable predictive power after conditioning on the
Institutional Six-State Overlay Taxonomy v1?

## Economic rationale

Campaign 0002 established that XAU/USD behavior must be interpreted through the
accepted institutional state model. Campaign 0003 therefore asks which
information channels remain useful *inside* each regime instead of assuming that
global feature rankings survive unchanged across bull, unwind, crisis, and
transition states.

## Supporting literature

1. Regime-conditioned return predictability and state-dependent market
   efficiency literature
2. Commodity safe-haven and crisis transmission literature
3. Feature stability, redundancy, and information-content selection literature
4. Adaptive markets and regime-specific explanatory-variable selection

## Governed datasets

- Frozen AFRP XAU/USD daily research frame
- Phase E canonical feature matrix
- Campaign 0002 institutional six-state taxonomy artifacts
- Existing event, macro, and cross-asset proxy series already governed by AFRP

## Candidate feature sources

- Existing AFRP Feature Registry
- Macro variables
- Volatility and trend variables
- Cross-asset return and expectation proxies
- Event proximity and geopolitical severity variables
- Bounded deterministic interaction terms constructed inside the campaign only

## Hypotheses

1. Regime conditioning will materially reduce the approved feature set relative
   to the global Phase E ranking.
2. A small cross-regime anchor set will survive in most states.
3. Interaction features will add value only in macro-transition and
   crisis-adjacent states.
4. Several intuitive standalone macro and event features will remain useful as
   context variables but fail promotion as direct predictive features.

## Experiment design

1. Recompute the governed feature matrix on the frozen research frame.
2. Condition every candidate feature on the accepted six-state taxonomy.
3. Evaluate mutual information, correlation stability, bootstrap sign
   consistency, drift, redundancy, and bounded interaction usefulness.
4. Promote only features that remain statistically and economically usable after
   redundancy pruning.
5. Register promoted and rejected outcomes into IKROS with full lineage.

## Validation methodology

- Walk-forward reasoning via temporal correlation slices
- Combinatorial purged cross-validation proxy through regime-conditioned
  subsample stability
- Bootstrap sign consistency
- Monte Carlo-style resampling through repeated deterministic bootstrap draws
- Sensitivity through redundancy and drift penalties
- Temporal stability and regime stability checks
- Out-of-sample replay interpretation through the accepted taxonomy

## Acceptance criteria

- Non-trivial mutual information inside at least one approved regime
- Stable sign under bootstrap resampling
- Acceptable temporal stability after conditioning
- Clear economic rationale
- Redundancy controlled below institutional tolerance after pruning
- Reproducible on the frozen stack

## Failure criteria

- Feature utility disappears after regime conditioning
- Feature duplicates a stronger approved variable
- Sparse event coverage prevents stable validation
- Interaction complexity adds instability without incremental information

## Required evidence

- Regime feature matrix
- Feature stability report
- Feature interaction matrix
- Redundancy analysis
- Promoted and rejected feature registries
- Final ARB recommendation
