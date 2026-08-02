# Hypothesis Cards

## IKROS-HYP-20260802-0401 — Expectation-relief bull continuation

- **Research question:** When bull_trend is already active, does a constructive expectation reset allow XAU/USD continuation rather than exhaustion?
- **Economic theory:** Reserve diversification, real-yield relief, and trend-following capital can reinforce each other once the tape is already trending higher.
- **Feature set:** regime_return_60, xau_return_20, forward_expectation
- **Regime scope:** bull_trend
- **Expected direction:** UP
- **Expected horizon:** 5D
- **Holding period:** 3-5D
- **Participants:** macro funds, trend followers, reserve managers
- **Required conditions:** bull_trend remains active, forward_expectation softens rather than shocks higher, no fresh crisis dislocation overrides the trend
- **Failure modes:** late-cycle trend exhaustion, USD or rates re-acceleration, bull trend already overcrowded
- **Historical analogues:** 
- **Contradictory evidence:** Campaign 0001 rejected macro-only drift as a sufficient explanation.; Breakdown pressure can overwhelm expectation relief near trend exhaustion.
- **Validation plan:** walk_forward validation inside bull_trend windows; CPCV with regime-preserving folds; Monte Carlo path reshuffling conditioned on bull_trend membership; sensitivity to expectation-shock sign changes
- **Acceptance criteria:** directional consistency across bull_trend folds; stable effect sign after CPCV and Monte Carlo; economic narrative remains consistent with safe-haven and carry literature
- **Rejection criteria:** effect vanishes outside a narrow sample segment; forward_expectation behaves as a redundant proxy with no incremental hypothesis value; evidence collapses once trend exhaustion controls are included
- **Required evidence:** bull_trend fold attribution; expectation-shock conditioning report; counterexample review against Campaign 0001 rejection
- **Confidence prior:** 0.53
- **Priority score:** 4.21
- **Advance to Campaign 0005:** True

## IKROS-HYP-20260802-0404 — Crisis safe-haven breakout convexity

- **Research question:** Inside crisis_dislocation, do breakout expansion and intermediate trend persistence identify the subset of shocks that produce persistent safe-haven inflows rather than one-day panic noise?
- **Economic theory:** In crisis states, gold receives flow from investors seeking collateral resilience and macro hedging, but only some crises produce durable continuation rather than liquidation whipsaw.
- **Feature set:** breakout_60, trend_gap_20_120, breakdown_20
- **Regime scope:** crisis_dislocation
- **Expected direction:** UP
- **Expected horizon:** 5D
- **Holding period:** 2-5D
- **Participants:** global macro hedgers, safe-haven allocators, systematic breakout strategies
- **Required conditions:** crisis_dislocation confirmed by the taxonomy, upside breakout dominates immediate liquidation noise, intermediate trend remains supportive
- **Failure modes:** liquidation for cash overwhelms safe-haven demand, crisis shock mean-reverts immediately, breakout is news-driven but not flow-supported
- **Historical analogues:** 2011 Gold Bull Market, 2020 COVID
- **Contradictory evidence:** Campaign 0002 flagged crisis dislocation as a lower-confidence state than the calmer regimes.; Short-term liquidation can initially push gold lower before safe-haven flows arrive.
- **Validation plan:** event-window walk_forward validation around crisis episodes; bootstrap conditioned on crisis subtypes; Monte Carlo sequencing of crisis event order; stress testing versus immediate post-event reversals
- **Acceptance criteria:** breakout-led continuation remains directional across crisis episodes; trend anchor improves separation of durable vs transient shocks; historical analogues align with safe-haven flow logic
- **Rejection criteria:** continuation fails after removing a small number of crisis windows; breakout signal proves indistinguishable from generic volatility spikes; liquidation whipsaw dominates more often than continuation
- **Required evidence:** crisis event replay book; breakout vs volatility discrimination memo; counterexample log for liquidation whipsaws
- **Confidence prior:** 0.49
- **Priority score:** 4.19
- **Advance to Campaign 0005:** True

## IKROS-HYP-20260802-0405 — Policy-shock repricing continuation

- **Research question:** During macro_transition states, does the first-day gold reaction persist when event pressure and breakout alignment indicate a genuine regime handoff?
- **Economic theory:** Macro announcements can reset inflation, rate, and USD expectations quickly; when the first gold response is confirmed by event pressure and directional structure, follow-through may persist for several sessions.
- **Feature set:** xau_return_1, trend_breakout_interaction, sessionless_event_pressure
- **Regime scope:** macro_transition
- **Expected direction:** CONTINUATION_WITH_INITIAL_SHOCK
- **Expected horizon:** 1-5D
- **Holding period:** 1-3D
- **Participants:** macro event traders, policy-sensitive CTAs, cross-asset discretionary desks
- **Required conditions:** macro_transition state confirmed, non-trivial event pressure is present, breakout interaction aligns with the initial shock direction
- **Failure modes:** one-day overreaction immediately mean reverts, event pressure is noisy or low quality, transition fails to hand off into a persistent regime
- **Historical analogues:** 
- **Contradictory evidence:** Campaign 0003 rejected standalone macro_pressure as a direct predictor.; Sparse event-pressure coverage can create fragile-looking edges if not validated carefully.
- **Validation plan:** event-synchronous walk_forward splits; CPCV around clustered macro-event windows; sensitivity to shock sign and immediate reversal risk; Monte Carlo resampling of event sequences
- **Acceptance criteria:** continuation sign remains stable across macro-transition subsets; interaction terms add value beyond xau_return_1 alone; event-driven narrative remains consistent with policy repricing theory
- **Rejection criteria:** edge collapses once sparse-event penalties are applied; continuation is just a proxy for generic short-horizon momentum; event pressure contributes no incremental explanatory power
- **Required evidence:** event-synchronous validation book; interaction ablation report; sparse-coverage robustness review
- **Confidence prior:** 0.48
- **Priority score:** 4.15
- **Advance to Campaign 0005:** True

## IKROS-HYP-20260802-0402 — Liquidation-pressure bear continuation

- **Research question:** Inside bear_unwind states, do persistent downside path pressure and elevated volatility continue to dominate the next five trading days?
- **Economic theory:** Forced deleveraging and inventory reduction can sustain downside pressure before value-sensitive buyers re-enter the market.
- **Feature set:** xau_return_20, regime_vol_20, trend_gap_30_180
- **Regime scope:** bear_unwind
- **Expected direction:** DOWN
- **Expected horizon:** 5D
- **Holding period:** 3-5D
- **Participants:** levered macro funds, commodity risk desks, liquidity providers reducing inventory
- **Required conditions:** bear_unwind remains dominant, volatility remains elevated relative to calm_carry, no crisis-safe-haven reversal interrupts liquidation
- **Failure modes:** policy response or central-bank demand stabilizes gold abruptly, bear unwind transitions into crisis-safe-haven bid, trend gap compresses too quickly
- **Historical analogues:** 2013 Gold Collapse
- **Contradictory evidence:** Campaign 0002 showed regime transitions can quickly flip interpretation.; Liquidation exhaustion can reverse downside continuation under crisis overlap.
- **Validation plan:** walk_forward validation restricted to bear_unwind segments; CPCV across non-overlapping unwind episodes; stress testing around major macro announcements and shock dates; sensitivity to volatility deceleration
- **Acceptance criteria:** consistent downside sign in unwind folds; effect survives volatility decile perturbations; trend persistence remains explanatory after redundancy controls
- **Rejection criteria:** continuation fails once crisis overlap is excluded; trend_gap_30_180 behaves as a weak bystander rather than a mechanism variable; volatility contribution is unstable across folds
- **Required evidence:** unwind-segment validation panel; volatility-decile stress report; transition-overlap contradiction log
- **Confidence prior:** 0.50
- **Priority score:** 4.01
- **Advance to Campaign 0005:** True

## IKROS-HYP-20260802-0408 — Transition-to-trend handoff

- **Research question:** Do macro_transition shocks that align with directional breakout structure hand off into later bull_trend continuation rather than fading out?
- **Economic theory:** Some policy and event shocks are not isolated bursts but regime-change catalysts that seed a broader trend followed by slower capital.
- **Feature set:** xau_return_1, trend_breakout_interaction, regime_return_60
- **Regime scope:** macro_transition, bull_trend
- **Expected direction:** UP_IF_TRANSITION_RESOLVES_CONSTRUCTIVELY
- **Expected horizon:** 5-15D
- **Holding period:** 5-10D
- **Participants:** event traders handing risk to trend followers, macro allocators, systematic medium-horizon strategies
- **Required conditions:** macro_transition shock resolves into bull_trend rather than range_compression, first-day reaction remains aligned with breakout structure, medium-horizon return anchor turns supportive
- **Failure modes:** transition shock mean reverts, bull_trend never materializes, signal is redundant with expectation-relief bull continuation
- **Historical analogues:** 
- **Contradictory evidence:** Transition states are noisy and sparse in Campaign 0003.; Bull continuation may already be captured by H0401 without requiring a transition narrative.
- **Validation plan:** state-transition walk_forward validation; CPCV preserving transition-to-bull handoff sequences; sensitivity to the duration of the handoff window; Monte Carlo over transition ordering
- **Acceptance criteria:** handoff cases separate cleanly from failed transitions; medium-horizon anchor adds incremental value over event-only continuation; cross-state mechanism remains economically coherent
- **Rejection criteria:** handoff cases are too rare for institutional follow-up; signal is redundant with H0401 or H0405; transition ordering uncertainty collapses reproducibility
- **Required evidence:** transition-handoff event log; cross-state redundancy review; sequence-sensitivity report
- **Confidence prior:** 0.45
- **Priority score:** 4.00
- **Advance to Campaign 0005:** True

## IKROS-HYP-20260802-0407 — Liquidation-exhaustion rebound

- **Research question:** After extreme selloffs in bear_unwind or crisis_dislocation, do elevated volatility and intermediate-trend stabilization identify rebound windows once forced selling exhausts itself?
- **Economic theory:** Gold can initially be sold for liquidity during stress, then rebound sharply once balance-sheet pressure eases and safe-haven demand returns.
- **Feature set:** breakdown_20, trend_gap_20_120, regime_vol_20
- **Regime scope:** bear_unwind, crisis_dislocation
- **Expected direction:** UP_AFTER_EXTREME_STRESS
- **Expected horizon:** 5-10D
- **Holding period:** 3-7D
- **Participants:** forced sellers transitioning to neutral, value-seeking discretionary macro desks, safe-haven allocators re-entering after liquidity shock
- **Required conditions:** evidence of exhaustion rather than fresh breakdown acceleration, volatility remains elevated but directional panic starts to stabilize, state remains within bear_unwind or crisis_dislocation
- **Failure modes:** liquidation extends longer than expected, intermediate trend keeps deteriorating, rebound is only a one-day short covering move
- **Historical analogues:** 2013 Gold Collapse, 2011 Gold Bull Market, 2020 COVID
- **Contradictory evidence:** Campaign 0002 noted crisis states remain lower-confidence research states.; Continuation and rebound can coexist, making false positives likely without strict regime controls.
- **Validation plan:** episode-based walk_forward validation around extreme selloffs; Monte Carlo sequencing of stress and rebound episodes; stress testing against extended liquidation paths; sensitivity to rebound timing lag
- **Acceptance criteria:** rebound sign persists across multiple stress analogues; exhaustion controls improve signal quality over raw breakdown alone; rebound timing remains reproducible enough for scientific follow-up
- **Rejection criteria:** rebound depends on a single crisis window; timing uncertainty overwhelms institutional usefulness; bear continuation dominates even after exhaustion controls
- **Required evidence:** episode replay archive; rebound-timing sensitivity note; continuation-vs-reversal contradiction analysis
- **Confidence prior:** 0.44
- **Priority score:** 3.89
- **Advance to Campaign 0005:** False

## IKROS-HYP-20260802-0403 — Carry-state accumulation drift

- **Research question:** During calm_carry conditions, does quiet accumulation create a slow positive drift in XAU/USD when macro/trend alignment remains constructive?
- **Economic theory:** When volatility is compressed, gold can drift through reserve accumulation and low-urgency macro repricing rather than visible breakout behavior.
- **Feature set:** regime_return_60, macro_trend_interaction, regime_vol_20
- **Regime scope:** calm_carry
- **Expected direction:** UP
- **Expected horizon:** 5-10D
- **Holding period:** 5D
- **Participants:** reserve managers, asset allocators, slower-frequency macro funds
- **Required conditions:** calm_carry remains active, macro/trend interaction remains constructive, volatility stays subdued
- **Failure modes:** carry regime breaks into macro_transition, low-vol drift is too weak to survive execution costs later, trend anchor loses explanatory value when rates reprice abruptly
- **Historical analogues:** 
- **Contradictory evidence:** Low-volatility states can exhibit negligible edge amplitude.; Campaign 0003 promoted macro_trend_interaction, not standalone macro pressure.
- **Validation plan:** walk_forward tests on calm_carry windows; bootstrap around low-volatility subsamples; sensitivity to transition breakpoints into macro_transition; capacity and turnover diagnostics deferred to later campaigns
- **Acceptance criteria:** drift sign remains stable across calm_carry folds; interaction term contributes incremental explanatory value over regime_return_60 alone; calm_carry episodes remain economically interpretable
- **Rejection criteria:** signal disappears after transition controls; volatility compression merely suppresses all directional information; macro_trend_interaction proves too weak outside a single historical window
- **Required evidence:** calm_carry bootstrap report; interaction ablation note; transition-sensitivity contradiction review
- **Confidence prior:** 0.47
- **Priority score:** 3.88
- **Advance to Campaign 0005:** False

## IKROS-HYP-20260802-0406 — Compression-state expectation fade

- **Research question:** In range_compression, do expectation shocks and constructive macro/trend context identify fade opportunities rather than trend continuation?
- **Economic theory:** Range-bound markets often absorb macro narrative shocks without broad participation; a low-volatility environment can cause initial impulse to mean revert rather than expand.
- **Feature set:** macro_trend_interaction, forward_expectation, regime_vol_20
- **Regime scope:** range_compression
- **Expected direction:** MEAN_REVERT_WITHIN_RANGE
- **Expected horizon:** 3-5D
- **Holding period:** 2-4D
- **Participants:** range traders, options desks, inventory-balancing liquidity providers
- **Required conditions:** range_compression remains the dominant state, volatility remains suppressed, no confirmed breakout follows the initial narrative shock
- **Failure modes:** compressed state resolves into a genuine breakout, macro shock is large enough to invalidate the range assumption, range compression has insufficient amplitude to justify future study
- **Historical analogues:** 2008 Financial Crisis, 2022 Inflation Cycle, 2024 Rate Cycle
- **Contradictory evidence:** Range compression was a low-signal regime in Campaign 0003.; Forward expectation can behave as a cross-asset narrative proxy rather than a direct causal driver.
- **Validation plan:** walk_forward validation on compression windows only; sensitivity to breakout false-positive detection; bootstrap on low-volatility subsamples; transition audit into macro_transition and bull_trend states
- **Acceptance criteria:** fade direction remains more stable than continuation direction; range assumption survives transition diagnostics; narrative shocks can be economically explained as inventory rebalancing rather than trend starts
- **Rejection criteria:** breakout contamination dominates the sample; expected edge amplitude is too low for institutional usefulness; forward_expectation adds no incremental explanatory value over volatility alone
- **Required evidence:** compression-window replay set; breakout contamination analysis; transition contradiction memo
- **Confidence prior:** 0.42
- **Priority score:** 3.64
- **Advance to Campaign 0005:** False
