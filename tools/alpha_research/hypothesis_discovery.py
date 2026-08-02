"""Reporting and artifact preparation for Phase G Campaign 0004 hypothesis discovery."""

# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from tools.alpha_research.feature_discovery import load_phase_g_feature_discovery_analysis
from tools.alpha_research.regime_discovery import load_phase_g_regime_discovery_analysis
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

PHASE_G_HYPOTHESIS_DISCOVERY_DIR = (
    Path("11-research") / "phase-g" / "hypothesis-discovery"
)
PHASE_G_HYPOTHESIS_DISCOVERY_ANALYSIS = (
    PHASE_G_HYPOTHESIS_DISCOVERY_DIR / "hypothesis_discovery_analysis.json"
)

HYPOTHESIS_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "identifier": "IKROS-HYP-20260802-0401",
        "research_question_id": "IKROS-RQ-20260802-0401",
        "mechanism_id": "IKROS-KO-20260802-0401",
        "title": "Expectation-relief bull continuation",
        "slug": "expectation_relief_bull_continuation",
        "research_question": "When bull_trend is already active, does a constructive expectation reset allow XAU/USD continuation rather than exhaustion?",
        "economic_theory": "Reserve diversification, real-yield relief, and trend-following capital can reinforce each other once the tape is already trending higher.",
        "feature_set": ["regime_return_60", "xau_return_20", "forward_expectation"],
        "regime_scope": ["bull_trend"],
        "expected_direction": "UP",
        "expected_horizon": "5D",
        "expected_holding_period": "3-5D",
        "market_participants": [
            "macro funds",
            "trend followers",
            "reserve managers",
        ],
        "required_market_conditions": [
            "bull_trend remains active",
            "forward_expectation softens rather than shocks higher",
            "no fresh crisis dislocation overrides the trend",
        ],
        "failure_modes": [
            "late-cycle trend exhaustion",
            "USD or rates re-acceleration",
            "bull trend already overcrowded",
        ],
        "historical_regimes": ["gold_bull_2011"],
        "contradictory_evidence": [
            "Campaign 0001 rejected macro-only drift as a sufficient explanation.",
            "Breakdown pressure can overwhelm expectation relief near trend exhaustion.",
        ],
        "validation_plan": [
            "walk_forward validation inside bull_trend windows",
            "CPCV with regime-preserving folds",
            "Monte Carlo path reshuffling conditioned on bull_trend membership",
            "sensitivity to expectation-shock sign changes",
        ],
        "acceptance_criteria": [
            "directional consistency across bull_trend folds",
            "stable effect sign after CPCV and Monte Carlo",
            "economic narrative remains consistent with safe-haven and carry literature",
        ],
        "rejection_criteria": [
            "effect vanishes outside a narrow sample segment",
            "forward_expectation behaves as a redundant proxy with no incremental hypothesis value",
            "evidence collapses once trend exhaustion controls are included",
        ],
        "required_evidence": [
            "bull_trend fold attribution",
            "expectation-shock conditioning report",
            "counterexample review against Campaign 0001 rejection",
        ],
        "confidence_prior": 0.53,
        "novelty": 3.7,
        "economic_plausibility": 4.5,
        "validation_feasibility": 4.4,
        "institutional_usefulness": 4.5,
        "expected_information_gain": 4.2,
        "alpha_capacity": 4.2,
        "explainability": 4.6,
        "advance_to_campaign_0005": True,
    },
    {
        "identifier": "IKROS-HYP-20260802-0402",
        "research_question_id": "IKROS-RQ-20260802-0402",
        "mechanism_id": "IKROS-KO-20260802-0402",
        "title": "Liquidation-pressure bear continuation",
        "slug": "liquidation_pressure_bear_continuation",
        "research_question": "Inside bear_unwind states, do persistent downside path pressure and elevated volatility continue to dominate the next five trading days?",
        "economic_theory": "Forced deleveraging and inventory reduction can sustain downside pressure before value-sensitive buyers re-enter the market.",
        "feature_set": ["xau_return_20", "regime_vol_20", "trend_gap_30_180"],
        "regime_scope": ["bear_unwind"],
        "expected_direction": "DOWN",
        "expected_horizon": "5D",
        "expected_holding_period": "3-5D",
        "market_participants": [
            "levered macro funds",
            "commodity risk desks",
            "liquidity providers reducing inventory",
        ],
        "required_market_conditions": [
            "bear_unwind remains dominant",
            "volatility remains elevated relative to calm_carry",
            "no crisis-safe-haven reversal interrupts liquidation",
        ],
        "failure_modes": [
            "policy response or central-bank demand stabilizes gold abruptly",
            "bear unwind transitions into crisis-safe-haven bid",
            "trend gap compresses too quickly",
        ],
        "historical_regimes": ["gold_collapse_2013"],
        "contradictory_evidence": [
            "Campaign 0002 showed regime transitions can quickly flip interpretation.",
            "Liquidation exhaustion can reverse downside continuation under crisis overlap.",
        ],
        "validation_plan": [
            "walk_forward validation restricted to bear_unwind segments",
            "CPCV across non-overlapping unwind episodes",
            "stress testing around major macro announcements and shock dates",
            "sensitivity to volatility deceleration",
        ],
        "acceptance_criteria": [
            "consistent downside sign in unwind folds",
            "effect survives volatility decile perturbations",
            "trend persistence remains explanatory after redundancy controls",
        ],
        "rejection_criteria": [
            "continuation fails once crisis overlap is excluded",
            "trend_gap_30_180 behaves as a weak bystander rather than a mechanism variable",
            "volatility contribution is unstable across folds",
        ],
        "required_evidence": [
            "unwind-segment validation panel",
            "volatility-decile stress report",
            "transition-overlap contradiction log",
        ],
        "confidence_prior": 0.5,
        "novelty": 3.3,
        "economic_plausibility": 4.3,
        "validation_feasibility": 4.4,
        "institutional_usefulness": 4.2,
        "expected_information_gain": 3.9,
        "alpha_capacity": 4.1,
        "explainability": 4.5,
        "advance_to_campaign_0005": True,
    },
    {
        "identifier": "IKROS-HYP-20260802-0403",
        "research_question_id": "IKROS-RQ-20260802-0403",
        "mechanism_id": "IKROS-KO-20260802-0403",
        "title": "Carry-state accumulation drift",
        "slug": "carry_state_accumulation_drift",
        "research_question": "During calm_carry conditions, does quiet accumulation create a slow positive drift in XAU/USD when macro/trend alignment remains constructive?",
        "economic_theory": "When volatility is compressed, gold can drift through reserve accumulation and low-urgency macro repricing rather than visible breakout behavior.",
        "feature_set": ["regime_return_60", "macro_trend_interaction", "regime_vol_20"],
        "regime_scope": ["calm_carry"],
        "expected_direction": "UP",
        "expected_horizon": "5-10D",
        "expected_holding_period": "5D",
        "market_participants": [
            "reserve managers",
            "asset allocators",
            "slower-frequency macro funds",
        ],
        "required_market_conditions": [
            "calm_carry remains active",
            "macro/trend interaction remains constructive",
            "volatility stays subdued",
        ],
        "failure_modes": [
            "carry regime breaks into macro_transition",
            "low-vol drift is too weak to survive execution costs later",
            "trend anchor loses explanatory value when rates reprice abruptly",
        ],
        "historical_regimes": ["rate_cycle_2024"],
        "contradictory_evidence": [
            "Low-volatility states can exhibit negligible edge amplitude.",
            "Campaign 0003 promoted macro_trend_interaction, not standalone macro pressure.",
        ],
        "validation_plan": [
            "walk_forward tests on calm_carry windows",
            "bootstrap around low-volatility subsamples",
            "sensitivity to transition breakpoints into macro_transition",
            "capacity and turnover diagnostics deferred to later campaigns",
        ],
        "acceptance_criteria": [
            "drift sign remains stable across calm_carry folds",
            "interaction term contributes incremental explanatory value over regime_return_60 alone",
            "calm_carry episodes remain economically interpretable",
        ],
        "rejection_criteria": [
            "signal disappears after transition controls",
            "volatility compression merely suppresses all directional information",
            "macro_trend_interaction proves too weak outside a single historical window",
        ],
        "required_evidence": [
            "calm_carry bootstrap report",
            "interaction ablation note",
            "transition-sensitivity contradiction review",
        ],
        "confidence_prior": 0.47,
        "novelty": 4.1,
        "economic_plausibility": 4.0,
        "validation_feasibility": 4.0,
        "institutional_usefulness": 3.9,
        "expected_information_gain": 4.0,
        "alpha_capacity": 3.7,
        "explainability": 4.4,
        "advance_to_campaign_0005": False,
    },
    {
        "identifier": "IKROS-HYP-20260802-0404",
        "research_question_id": "IKROS-RQ-20260802-0404",
        "mechanism_id": "IKROS-KO-20260802-0404",
        "title": "Crisis safe-haven breakout convexity",
        "slug": "crisis_safe_haven_breakout_convexity",
        "research_question": "Inside crisis_dislocation, do breakout expansion and intermediate trend persistence identify the subset of shocks that produce persistent safe-haven inflows rather than one-day panic noise?",
        "economic_theory": "In crisis states, gold receives flow from investors seeking collateral resilience and macro hedging, but only some crises produce durable continuation rather than liquidation whipsaw.",
        "feature_set": ["breakout_60", "trend_gap_20_120", "breakdown_20"],
        "regime_scope": ["crisis_dislocation"],
        "expected_direction": "UP",
        "expected_horizon": "5D",
        "expected_holding_period": "2-5D",
        "market_participants": [
            "global macro hedgers",
            "safe-haven allocators",
            "systematic breakout strategies",
        ],
        "required_market_conditions": [
            "crisis_dislocation confirmed by the taxonomy",
            "upside breakout dominates immediate liquidation noise",
            "intermediate trend remains supportive",
        ],
        "failure_modes": [
            "liquidation for cash overwhelms safe-haven demand",
            "crisis shock mean-reverts immediately",
            "breakout is news-driven but not flow-supported",
        ],
        "historical_regimes": ["gold_bull_2011", "covid_2020"],
        "contradictory_evidence": [
            "Campaign 0002 flagged crisis dislocation as a lower-confidence state than the calmer regimes.",
            "Short-term liquidation can initially push gold lower before safe-haven flows arrive.",
        ],
        "validation_plan": [
            "event-window walk_forward validation around crisis episodes",
            "bootstrap conditioned on crisis subtypes",
            "Monte Carlo sequencing of crisis event order",
            "stress testing versus immediate post-event reversals",
        ],
        "acceptance_criteria": [
            "breakout-led continuation remains directional across crisis episodes",
            "trend anchor improves separation of durable vs transient shocks",
            "historical analogues align with safe-haven flow logic",
        ],
        "rejection_criteria": [
            "continuation fails after removing a small number of crisis windows",
            "breakout signal proves indistinguishable from generic volatility spikes",
            "liquidation whipsaw dominates more often than continuation",
        ],
        "required_evidence": [
            "crisis event replay book",
            "breakout vs volatility discrimination memo",
            "counterexample log for liquidation whipsaws",
        ],
        "confidence_prior": 0.49,
        "novelty": 4.4,
        "economic_plausibility": 4.4,
        "validation_feasibility": 3.8,
        "institutional_usefulness": 4.5,
        "expected_information_gain": 4.6,
        "alpha_capacity": 4.0,
        "explainability": 4.5,
        "advance_to_campaign_0005": True,
    },
    {
        "identifier": "IKROS-HYP-20260802-0405",
        "research_question_id": "IKROS-RQ-20260802-0405",
        "mechanism_id": "IKROS-KO-20260802-0405",
        "title": "Policy-shock repricing continuation",
        "slug": "policy_shock_repricing_continuation",
        "research_question": "During macro_transition states, does the first-day gold reaction persist when event pressure and breakout alignment indicate a genuine regime handoff?",
        "economic_theory": "Macro announcements can reset inflation, rate, and USD expectations quickly; when the first gold response is confirmed by event pressure and directional structure, follow-through may persist for several sessions.",
        "feature_set": [
            "xau_return_1",
            "trend_breakout_interaction",
            "sessionless_event_pressure",
        ],
        "regime_scope": ["macro_transition"],
        "expected_direction": "CONTINUATION_WITH_INITIAL_SHOCK",
        "expected_horizon": "1-5D",
        "expected_holding_period": "1-3D",
        "market_participants": [
            "macro event traders",
            "policy-sensitive CTAs",
            "cross-asset discretionary desks",
        ],
        "required_market_conditions": [
            "macro_transition state confirmed",
            "non-trivial event pressure is present",
            "breakout interaction aligns with the initial shock direction",
        ],
        "failure_modes": [
            "one-day overreaction immediately mean reverts",
            "event pressure is noisy or low quality",
            "transition fails to hand off into a persistent regime",
        ],
        "historical_regimes": ["inflation_2022"],
        "contradictory_evidence": [
            "Campaign 0003 rejected standalone macro_pressure as a direct predictor.",
            "Sparse event-pressure coverage can create fragile-looking edges if not validated carefully.",
        ],
        "validation_plan": [
            "event-synchronous walk_forward splits",
            "CPCV around clustered macro-event windows",
            "sensitivity to shock sign and immediate reversal risk",
            "Monte Carlo resampling of event sequences",
        ],
        "acceptance_criteria": [
            "continuation sign remains stable across macro-transition subsets",
            "interaction terms add value beyond xau_return_1 alone",
            "event-driven narrative remains consistent with policy repricing theory",
        ],
        "rejection_criteria": [
            "edge collapses once sparse-event penalties are applied",
            "continuation is just a proxy for generic short-horizon momentum",
            "event pressure contributes no incremental explanatory power",
        ],
        "required_evidence": [
            "event-synchronous validation book",
            "interaction ablation report",
            "sparse-coverage robustness review",
        ],
        "confidence_prior": 0.48,
        "novelty": 4.6,
        "economic_plausibility": 4.3,
        "validation_feasibility": 4.1,
        "institutional_usefulness": 4.4,
        "expected_information_gain": 4.5,
        "alpha_capacity": 3.9,
        "explainability": 4.4,
        "advance_to_campaign_0005": True,
    },
    {
        "identifier": "IKROS-HYP-20260802-0406",
        "research_question_id": "IKROS-RQ-20260802-0406",
        "mechanism_id": "IKROS-KO-20260802-0406",
        "title": "Compression-state expectation fade",
        "slug": "compression_state_expectation_fade",
        "research_question": "In range_compression, do expectation shocks and constructive macro/trend context identify fade opportunities rather than trend continuation?",
        "economic_theory": "Range-bound markets often absorb macro narrative shocks without broad participation; a low-volatility environment can cause initial impulse to mean revert rather than expand.",
        "feature_set": ["macro_trend_interaction", "forward_expectation", "regime_vol_20"],
        "regime_scope": ["range_compression"],
        "expected_direction": "MEAN_REVERT_WITHIN_RANGE",
        "expected_horizon": "3-5D",
        "expected_holding_period": "2-4D",
        "market_participants": [
            "range traders",
            "options desks",
            "inventory-balancing liquidity providers",
        ],
        "required_market_conditions": [
            "range_compression remains the dominant state",
            "volatility remains suppressed",
            "no confirmed breakout follows the initial narrative shock",
        ],
        "failure_modes": [
            "compressed state resolves into a genuine breakout",
            "macro shock is large enough to invalidate the range assumption",
            "range compression has insufficient amplitude to justify future study",
        ],
        "historical_regimes": ["historical_2025", "available_2026"],
        "contradictory_evidence": [
            "Range compression was a low-signal regime in Campaign 0003.",
            "Forward expectation can behave as a cross-asset narrative proxy rather than a direct causal driver.",
        ],
        "validation_plan": [
            "walk_forward validation on compression windows only",
            "sensitivity to breakout false-positive detection",
            "bootstrap on low-volatility subsamples",
            "transition audit into macro_transition and bull_trend states",
        ],
        "acceptance_criteria": [
            "fade direction remains more stable than continuation direction",
            "range assumption survives transition diagnostics",
            "narrative shocks can be economically explained as inventory rebalancing rather than trend starts",
        ],
        "rejection_criteria": [
            "breakout contamination dominates the sample",
            "expected edge amplitude is too low for institutional usefulness",
            "forward_expectation adds no incremental explanatory value over volatility alone",
        ],
        "required_evidence": [
            "compression-window replay set",
            "breakout contamination analysis",
            "transition contradiction memo",
        ],
        "confidence_prior": 0.42,
        "novelty": 4.2,
        "economic_plausibility": 3.7,
        "validation_feasibility": 3.9,
        "institutional_usefulness": 3.5,
        "expected_information_gain": 4.0,
        "alpha_capacity": 3.0,
        "explainability": 4.1,
        "advance_to_campaign_0005": False,
    },
    {
        "identifier": "IKROS-HYP-20260802-0407",
        "research_question_id": "IKROS-RQ-20260802-0407",
        "mechanism_id": "IKROS-KO-20260802-0407",
        "title": "Liquidation-exhaustion rebound",
        "slug": "liquidation_exhaustion_rebound",
        "research_question": "After extreme selloffs in bear_unwind or crisis_dislocation, do elevated volatility and intermediate-trend stabilization identify rebound windows once forced selling exhausts itself?",
        "economic_theory": "Gold can initially be sold for liquidity during stress, then rebound sharply once balance-sheet pressure eases and safe-haven demand returns.",
        "feature_set": ["breakdown_20", "trend_gap_20_120", "regime_vol_20"],
        "regime_scope": ["bear_unwind", "crisis_dislocation"],
        "expected_direction": "UP_AFTER_EXTREME_STRESS",
        "expected_horizon": "5-10D",
        "expected_holding_period": "3-7D",
        "market_participants": [
            "forced sellers transitioning to neutral",
            "value-seeking discretionary macro desks",
            "safe-haven allocators re-entering after liquidity shock",
        ],
        "required_market_conditions": [
            "evidence of exhaustion rather than fresh breakdown acceleration",
            "volatility remains elevated but directional panic starts to stabilize",
            "state remains within bear_unwind or crisis_dislocation",
        ],
        "failure_modes": [
            "liquidation extends longer than expected",
            "intermediate trend keeps deteriorating",
            "rebound is only a one-day short covering move",
        ],
        "historical_regimes": ["gfc_2008", "covid_2020"],
        "contradictory_evidence": [
            "Campaign 0002 noted crisis states remain lower-confidence research states.",
            "Continuation and rebound can coexist, making false positives likely without strict regime controls.",
        ],
        "validation_plan": [
            "episode-based walk_forward validation around extreme selloffs",
            "Monte Carlo sequencing of stress and rebound episodes",
            "stress testing against extended liquidation paths",
            "sensitivity to rebound timing lag",
        ],
        "acceptance_criteria": [
            "rebound sign persists across multiple stress analogues",
            "exhaustion controls improve signal quality over raw breakdown alone",
            "rebound timing remains reproducible enough for scientific follow-up",
        ],
        "rejection_criteria": [
            "rebound depends on a single crisis window",
            "timing uncertainty overwhelms institutional usefulness",
            "bear continuation dominates even after exhaustion controls",
        ],
        "required_evidence": [
            "episode replay archive",
            "rebound-timing sensitivity note",
            "continuation-vs-reversal contradiction analysis",
        ],
        "confidence_prior": 0.44,
        "novelty": 4.5,
        "economic_plausibility": 4.1,
        "validation_feasibility": 3.5,
        "institutional_usefulness": 3.8,
        "expected_information_gain": 4.4,
        "alpha_capacity": 3.6,
        "explainability": 4.3,
        "advance_to_campaign_0005": False,
    },
    {
        "identifier": "IKROS-HYP-20260802-0408",
        "research_question_id": "IKROS-RQ-20260802-0408",
        "mechanism_id": "IKROS-KO-20260802-0408",
        "title": "Transition-to-trend handoff",
        "slug": "transition_to_trend_handoff",
        "research_question": "Do macro_transition shocks that align with directional breakout structure hand off into later bull_trend continuation rather than fading out?",
        "economic_theory": "Some policy and event shocks are not isolated bursts but regime-change catalysts that seed a broader trend followed by slower capital.",
        "feature_set": ["xau_return_1", "trend_breakout_interaction", "regime_return_60"],
        "regime_scope": ["macro_transition", "bull_trend"],
        "expected_direction": "UP_IF_TRANSITION_RESOLVES_CONSTRUCTIVELY",
        "expected_horizon": "5-15D",
        "expected_holding_period": "5-10D",
        "market_participants": [
            "event traders handing risk to trend followers",
            "macro allocators",
            "systematic medium-horizon strategies",
        ],
        "required_market_conditions": [
            "macro_transition shock resolves into bull_trend rather than range_compression",
            "first-day reaction remains aligned with breakout structure",
            "medium-horizon return anchor turns supportive",
        ],
        "failure_modes": [
            "transition shock mean reverts",
            "bull_trend never materializes",
            "signal is redundant with expectation-relief bull continuation",
        ],
        "historical_regimes": ["inflation_2022", "gold_bull_2011"],
        "contradictory_evidence": [
            "Transition states are noisy and sparse in Campaign 0003.",
            "Bull continuation may already be captured by H0401 without requiring a transition narrative.",
        ],
        "validation_plan": [
            "state-transition walk_forward validation",
            "CPCV preserving transition-to-bull handoff sequences",
            "sensitivity to the duration of the handoff window",
            "Monte Carlo over transition ordering",
        ],
        "acceptance_criteria": [
            "handoff cases separate cleanly from failed transitions",
            "medium-horizon anchor adds incremental value over event-only continuation",
            "cross-state mechanism remains economically coherent",
        ],
        "rejection_criteria": [
            "handoff cases are too rare for institutional follow-up",
            "signal is redundant with H0401 or H0405",
            "transition ordering uncertainty collapses reproducibility",
        ],
        "required_evidence": [
            "transition-handoff event log",
            "cross-state redundancy review",
            "sequence-sensitivity report",
        ],
        "confidence_prior": 0.45,
        "novelty": 4.7,
        "economic_plausibility": 4.0,
        "validation_feasibility": 3.7,
        "institutional_usefulness": 4.0,
        "expected_information_gain": 4.5,
        "alpha_capacity": 4.0,
        "explainability": 4.3,
        "advance_to_campaign_0005": True,
    },
]

MECHANISM_ATLAS: list[dict[str, Any]] = [
    {
        "identifier": "IKROS-MECH-20260802-0401",
        "name": "Trend-following continuation",
        "description": "Persistent medium-horizon path dependence is reinforced by expectation relief and slower capital participation.",
        "supporting_hypotheses": ["IKROS-HYP-20260802-0401", "IKROS-HYP-20260802-0408"],
        "participants": ["trend followers", "macro allocators", "reserve managers"],
    },
    {
        "identifier": "IKROS-MECH-20260802-0402",
        "name": "Liquidation reflexivity",
        "description": "Forced deleveraging can create downside continuation before exhaustion and rebound dynamics appear.",
        "supporting_hypotheses": ["IKROS-HYP-20260802-0402", "IKROS-HYP-20260802-0407"],
        "participants": ["levered funds", "risk desks", "liquidity providers"],
    },
    {
        "identifier": "IKROS-MECH-20260802-0403",
        "name": "Safe-haven convexity",
        "description": "Shock states selectively transform into durable safe-haven flow when breakout and trend structure align.",
        "supporting_hypotheses": ["IKROS-HYP-20260802-0404", "IKROS-HYP-20260802-0407"],
        "participants": ["hedgers", "safe-haven allocators", "global macro desks"],
    },
    {
        "identifier": "IKROS-MECH-20260802-0404",
        "name": "Policy repricing handoff",
        "description": "Macro-event repricing transitions from short-horizon response into broader directional participation.",
        "supporting_hypotheses": ["IKROS-HYP-20260802-0405", "IKROS-HYP-20260802-0408"],
        "participants": ["event traders", "CTAs", "cross-asset discretionary desks"],
    },
    {
        "identifier": "IKROS-MECH-20260802-0405",
        "name": "Low-volatility accumulation",
        "description": "Quiet reserve and macro accumulation can generate drift before the crowd recognizes a new trend.",
        "supporting_hypotheses": ["IKROS-HYP-20260802-0403"],
        "participants": ["reserve managers", "slow-frequency macro capital"],
    },
    {
        "identifier": "IKROS-MECH-20260802-0406",
        "name": "Compression-state mean reversion",
        "description": "Narrative shocks can fade in compressed states when participation is too shallow to create expansion.",
        "supporting_hypotheses": ["IKROS-HYP-20260802-0406"],
        "participants": ["range traders", "options desks", "inventory balancers"],
    },
]

DEPENDENCY_EDGES: list[dict[str, str]] = [
    {
        "from": "IKROS-HYP-20260802-0405",
        "to": "IKROS-HYP-20260802-0408",
        "reason": "event-driven repricing can seed a later trend handoff",
    },
    {
        "from": "IKROS-HYP-20260802-0408",
        "to": "IKROS-HYP-20260802-0401",
        "reason": "successful transition handoff can mature into bull continuation",
    },
    {
        "from": "IKROS-HYP-20260802-0402",
        "to": "IKROS-HYP-20260802-0407",
        "reason": "continued liquidation is the precursor state for an exhaustion rebound",
    },
    {
        "from": "IKROS-HYP-20260802-0406",
        "to": "IKROS-HYP-20260802-0405",
        "reason": "range compression can break into macro transition when narrative shocks persist",
    },
    {
        "from": "IKROS-HYP-20260802-0404",
        "to": "IKROS-HYP-20260802-0407",
        "reason": "crisis continuation and crisis exhaustion share the same shock domain but opposite outcomes",
    },
]


def prepare_phase_g_hypothesis_discovery_artifacts(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    regime_analysis = load_phase_g_regime_discovery_analysis(repo_root)
    feature_analysis = load_phase_g_feature_discovery_analysis(repo_root)
    promoted_map = {
        item["feature"]: item for item in feature_analysis["promoted_feature_registry"]
    }
    atlas_by_regime = _atlas_by_regime(regime_analysis["historical_atlas"])

    hypotheses = [
        _build_hypothesis_record(item, promoted_map, atlas_by_regime)
        for item in HYPOTHESIS_BLUEPRINTS
    ]
    hypotheses.sort(key=lambda item: float(item["priority_score"]), reverse=True)
    recommended = [
        item["identifier"] for item in hypotheses if bool(item["advance_to_campaign_0005"])
    ][:5]

    analysis = {
        "campaign": {
            "title": "Campaign 0004 Hypothesis Discovery",
            "accepted_taxonomy": regime_analysis["accepted_taxonomy"]["name"],
            "approved_catalogue": feature_analysis["campaign"]["approved_catalogue"],
            "hypothesis_catalogue": "Institutional Alpha Hypothesis Catalogue v1",
            "hypothesis_count": len(hypotheses),
            "recommended_for_campaign_0005": len(recommended),
        },
        "research_priority_matrix": [
            {
                "identifier": item["identifier"],
                "title": item["title"],
                "priority_score": item["priority_score"],
                "priority_tier": item["priority_tier"],
                "economic_plausibility": item["economic_plausibility"],
                "novelty": item["novelty"],
                "validation_feasibility": item["validation_feasibility"],
                "expected_information_gain": item["expected_information_gain"],
                "institutional_usefulness": item["institutional_usefulness"],
                "alpha_capacity": item["alpha_capacity"],
                "support_score": item["support_score"],
                "advance_to_campaign_0005": item["advance_to_campaign_0005"],
            }
            for item in hypotheses
        ],
        "expected_validation_matrix": [
            {
                "identifier": item["identifier"],
                "title": item["title"],
                "regime_scope": item["regime_scope"],
                "expected_horizon": item["expected_horizon"],
                "validation_plan": item["validation_plan"],
                "acceptance_criteria": item["acceptance_criteria"],
                "rejection_criteria": item["rejection_criteria"],
            }
            for item in hypotheses
        ],
        "economic_mechanism_atlas": MECHANISM_ATLAS,
        "hypothesis_dependency_graph": {
            "nodes": [
                {
                    "identifier": item["identifier"],
                    "title": item["title"],
                    "priority_tier": item["priority_tier"],
                }
                for item in hypotheses
            ],
            "edges": DEPENDENCY_EDGES,
        },
        "hypotheses": hypotheses,
        "recommended_hypotheses": recommended,
        "arb_recommendation": (
            "Advance the highest-priority regime-conditioned hypotheses into Campaign 0005 "
            "for scientific validation without adding new infrastructure or relaxing the "
            "approved taxonomy and feature-catalogue constraints."
        ),
    }

    analysis_path = output_dir / "hypothesis_discovery_analysis.json"
    knowledge_path = output_dir / "hypothesis_discovery_knowledge.json"
    write_json(analysis_path, analysis)
    write_json(knowledge_path, _build_knowledge_pack(analysis))

    return {
        "analysis": analysis,
        "paths": {
            "analysis": str(analysis_path),
            "knowledge": str(knowledge_path),
        },
    }


def load_phase_g_hypothesis_discovery_analysis(repo_root: Path) -> dict[str, Any]:
    analysis_path = repo_root / PHASE_G_HYPOTHESIS_DISCOVERY_ANALYSIS
    return cast(dict[str, Any], json.loads(analysis_path.read_text(encoding="utf-8")))


def emit_hypothesis_discovery_reports(
    *,
    output_dir: Path,
    analysis: dict[str, Any],
    campaign_result: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    catalogue_json = output_dir / "institutional_alpha_hypothesis_catalogue_v1.json"
    catalogue_md = output_dir / "INSTITUTIONAL_ALPHA_HYPOTHESIS_CATALOGUE_V1.md"
    cards_md = output_dir / "HYPOTHESIS_CARDS.md"
    mechanism_json = output_dir / "economic_mechanism_atlas.json"
    mechanism_md = output_dir / "ECONOMIC_MECHANISM_ATLAS.md"
    dependency_json = output_dir / "hypothesis_dependency_graph.json"
    dependency_md = output_dir / "HYPOTHESIS_DEPENDENCY_GRAPH.md"
    priority_json = output_dir / "research_priority_matrix.json"
    priority_md = output_dir / "RESEARCH_PRIORITY_MATRIX.md"
    validation_json = output_dir / "expected_validation_matrix.json"
    validation_md = output_dir / "EXPECTED_VALIDATION_MATRIX.md"
    final_report_md = output_dir / "HYPOTHESIS_DISCOVERY_FINAL_CAMPAIGN_REPORT.md"

    write_json(catalogue_json, analysis["hypotheses"])
    write_json(mechanism_json, analysis["economic_mechanism_atlas"])
    write_json(dependency_json, analysis["hypothesis_dependency_graph"])
    write_json(priority_json, analysis["research_priority_matrix"])
    write_json(validation_json, analysis["expected_validation_matrix"])

    catalogue_rows = [
        [
            item["identifier"],
            item["title"],
            ", ".join(item["regime_scope"]),
            ", ".join(item["feature_set"]),
            item["priority_tier"],
            item["advance_to_campaign_0005"],
        ]
        for item in analysis["hypotheses"]
    ]
    write_markdown(
        catalogue_md,
        f"""
# Institutional Alpha Hypothesis Catalogue v1

{markdown_table(
    ["ID", "Title", "Regime Scope", "Feature Set", "Priority", "Advance to 0005"],
    catalogue_rows,
)}
""",
    )

    card_sections: list[str] = []
    for item in analysis["hypotheses"]:
        card_sections.append(
            "\n".join(
                [
                    f"## {item['identifier']} — {item['title']}",
                    "",
                    f"- **Research question:** {item['research_question']}",
                    f"- **Economic theory:** {item['economic_theory']}",
                    f"- **Feature set:** {', '.join(item['feature_set'])}",
                    f"- **Regime scope:** {', '.join(item['regime_scope'])}",
                    f"- **Expected direction:** {item['expected_direction']}",
                    f"- **Expected horizon:** {item['expected_horizon']}",
                    f"- **Holding period:** {item['expected_holding_period']}",
                    f"- **Participants:** {', '.join(item['market_participants'])}",
                    f"- **Required conditions:** {', '.join(item['required_market_conditions'])}",
                    f"- **Failure modes:** {', '.join(item['failure_modes'])}",
                    f"- **Historical analogues:** {', '.join(item['historical_analogues'])}",
                    f"- **Contradictory evidence:** {'; '.join(item['contradictory_evidence'])}",
                    f"- **Validation plan:** {'; '.join(item['validation_plan'])}",
                    f"- **Acceptance criteria:** {'; '.join(item['acceptance_criteria'])}",
                    f"- **Rejection criteria:** {'; '.join(item['rejection_criteria'])}",
                    f"- **Required evidence:** {'; '.join(item['required_evidence'])}",
                    f"- **Confidence prior:** {item['confidence_prior']:.2f}",
                    f"- **Priority score:** {item['priority_score']:.2f}",
                    f"- **Advance to Campaign 0005:** {item['advance_to_campaign_0005']}",
                ]
            )
        )
    write_markdown(cards_md, "# Hypothesis Cards\n\n" + "\n\n".join(card_sections))

    mechanism_rows = [
        [
            item["name"],
            item["description"],
            ", ".join(item["supporting_hypotheses"]),
            ", ".join(item["participants"]),
        ]
        for item in analysis["economic_mechanism_atlas"]
    ]
    write_markdown(
        mechanism_md,
        f"""
# Economic Mechanism Atlas

{markdown_table(
    ["Mechanism", "Description", "Supporting Hypotheses", "Participants"],
    mechanism_rows,
)}
""",
    )

    edge_lines = [
        f"    {edge['from']} --> {edge['to']}"
        for edge in analysis["hypothesis_dependency_graph"]["edges"]
    ]
    write_markdown(
        dependency_md,
        "# Hypothesis Dependency Graph\n\n```mermaid\ngraph TD\n"
        + "\n".join(edge_lines)
        + "\n```",
    )

    priority_rows = [
        [
            item["identifier"],
            item["priority_score"],
            item["priority_tier"],
            item["economic_plausibility"],
            item["expected_information_gain"],
            item["validation_feasibility"],
            item["advance_to_campaign_0005"],
        ]
        for item in analysis["research_priority_matrix"]
    ]
    write_markdown(
        priority_md,
        f"""
# Research Priority Matrix

{markdown_table(
    [
        "ID",
        "Priority Score",
        "Tier",
        "Economic Plausibility",
        "Information Gain",
        "Validation Feasibility",
        "Advance",
    ],
    priority_rows,
)}
""",
    )

    validation_rows = [
        [
            item["identifier"],
            item["expected_horizon"],
            ", ".join(item["regime_scope"]),
            "; ".join(item["validation_plan"]),
        ]
        for item in analysis["expected_validation_matrix"]
    ]
    write_markdown(
        validation_md,
        f"""
# Expected Validation Matrix

{markdown_table(
    ["ID", "Expected Horizon", "Regime Scope", "Validation Plan"],
    validation_rows,
)}
""",
    )

    recommended = ", ".join(analysis["recommended_hypotheses"])
    write_markdown(
        final_report_md,
        f"""
# Hypothesis Discovery Final Campaign Report

## Outcome

Campaign 0004 completed with the recommendation to publish
**{analysis["campaign"]["hypothesis_catalogue"]}** and advance a bounded subset
of hypotheses into Campaign 0005 for scientific validation.

## Registered conclusion

- Campaign ID: `{campaign_result["campaign_id"]}`
- Completion report: `{campaign_result["report"]["report_id"]}`
- Research question: `{campaign_result["research_question"]["ikros_id"]}`
- Hypothesis: `{campaign_result["hypothesis"]["ikros_id"]}`
- Experiment: `{campaign_result["experiment"]["ikros_id"]}`
- Conclusion: `{campaign_result["catalogue_summary"]["conclusion_id"]}`

## Recommended Campaign 0005 candidates

{recommended}

## ARB recommendation

{campaign_result["catalogue_summary"]["arb_recommendation"]}
""",
    )

    return {
        "hypothesis_catalogue_json": str(catalogue_json),
        "hypothesis_catalogue_markdown": str(catalogue_md),
        "hypothesis_cards_markdown": str(cards_md),
        "economic_mechanism_json": str(mechanism_json),
        "economic_mechanism_markdown": str(mechanism_md),
        "dependency_graph_json": str(dependency_json),
        "dependency_graph_markdown": str(dependency_md),
        "priority_matrix_json": str(priority_json),
        "priority_matrix_markdown": str(priority_md),
        "validation_matrix_json": str(validation_json),
        "validation_matrix_markdown": str(validation_md),
        "final_report_markdown": str(final_report_md),
    }


def _build_hypothesis_record(
    blueprint: dict[str, Any],
    promoted_map: dict[str, dict[str, Any]],
    atlas_by_regime: dict[str, list[str]],
) -> dict[str, Any]:
    feature_refs = [promoted_map[name]["identifier"] for name in blueprint["feature_set"]]
    support_score = sum(
        float(promoted_map[name]["mean_score"]) for name in blueprint["feature_set"]
    ) / len(blueprint["feature_set"])
    historical_analogues = [
        analogue
        for regime in blueprint["regime_scope"]
        for analogue in atlas_by_regime.get(regime, [])
    ]
    priority_score = _priority_score(blueprint, support_score)
    return {
        **blueprint,
        "feature_ids": feature_refs,
        "knowledge_links": feature_refs + [blueprint["mechanism_id"]],
        "historical_analogues": list(dict.fromkeys(historical_analogues))[:3],
        "support_score": round(support_score, 4),
        "priority_score": round(priority_score, 4),
        "priority_tier": _priority_tier(priority_score),
    }


def _atlas_by_regime(historical_atlas: list[dict[str, Any]]) -> dict[str, list[str]]:
    atlas: dict[str, list[str]] = {}
    for row in historical_atlas:
        atlas.setdefault(str(row["dominant_regime"]), []).append(str(row["label"]))
    return atlas


def _priority_score(blueprint: dict[str, Any], support_score: float) -> float:
    return (
        float(blueprint["economic_plausibility"]) * 0.2
        + float(blueprint["novelty"]) * 0.1
        + float(blueprint["validation_feasibility"]) * 0.15
        + float(blueprint["institutional_usefulness"]) * 0.15
        + float(blueprint["expected_information_gain"]) * 0.15
        + float(blueprint["alpha_capacity"]) * 0.1
        + float(blueprint["explainability"]) * 0.1
        + support_score * 0.05
    )


def _priority_tier(score: float) -> str:
    if score >= 4.2:
        return "P1"
    if score >= 3.9:
        return "P2"
    return "P3"


def _build_knowledge_pack(analysis: dict[str, Any]) -> dict[str, Any]:
    hypotheses = analysis["hypotheses"]
    research_questions = [
        {
            "identifier": item["research_question_id"],
            "type": "ResearchQuestion",
            "title": item["research_question"],
            "summary": item["title"],
            "lifecycle_state": "ACTIVE",
            "confidence": item["confidence_prior"],
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
            "source_ids": [item["identifier"]],
            "motivation": item["economic_theory"],
            "scope": "HYPOTHESIS_DISCOVERY",
            "instrument": "XAU/USD",
            "time_horizon": item["expected_horizon"],
            "campaign_tag": "PHASE-G-HYPOTHESIS-004",
            "linked_hypotheses": [item["identifier"]],
            "linked_conclusions": [],
            "attributes": {
                "motivation": item["economic_theory"],
                "scope": "HYPOTHESIS_DISCOVERY",
                "instrument": "XAU/USD",
                "time_horizon": item["expected_horizon"],
                "campaign_tag": "PHASE-G-HYPOTHESIS-004",
                "linked_hypotheses": [item["identifier"]],
                "linked_conclusions": [],
                "regime_scope": item["regime_scope"],
                "feature_set": item["feature_set"],
                "expected_holding_period": item["expected_holding_period"],
            },
        }
        for item in hypotheses
    ]
    hypothesis_objects = [
        {
            "identifier": item["identifier"],
            "type": "Hypothesis",
            "title": item["title"],
            "summary": item["economic_theory"],
            "lifecycle_state": "APPROVED_FOR_TESTING",
            "confidence": item["confidence_prior"],
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
            "source_ids": [item["research_question_id"]],
            "statement": item["research_question"],
            "null_hypothesis": "The described mechanism does not produce a persistent regime-conditioned predictive relationship.",
            "alternative_hypothesis": item["economic_theory"],
            "significance_level": 0.05,
            "power": 0.8,
            "prior_confidence": item["confidence_prior"],
            "posterior_confidence": 0.0,
            "source_rq": item["research_question_id"],
            "motivating_theses": [],
            "experiments": [],
            "validations": [],
            "contradictions": [],
            "attributes": {
                "statement": item["research_question"],
                "null_hypothesis": "The described mechanism does not produce a persistent regime-conditioned predictive relationship.",
                "alternative_hypothesis": item["economic_theory"],
                "significance_level": 0.05,
                "power": 0.8,
                "prior_confidence": item["confidence_prior"],
                "posterior_confidence": 0.0,
                "source_rq": item["research_question_id"],
                "motivating_theses": [],
                "experiments": [],
                "validations": [],
                "contradictions": [],
                "research_question": item["research_question"],
                "feature_ids": item["feature_ids"],
                "feature_set": item["feature_set"],
                "regime_scope": item["regime_scope"],
                "expected_direction": item["expected_direction"],
                "expected_horizon": item["expected_horizon"],
                "expected_holding_period": item["expected_holding_period"],
                "validation_plan": item["validation_plan"],
                "acceptance_criteria": item["acceptance_criteria"],
                "rejection_criteria": item["rejection_criteria"],
                "required_evidence": item["required_evidence"],
                "knowledge_links": item["knowledge_links"],
                "priority_tier": item["priority_tier"],
                "advance_to_campaign_0005": item["advance_to_campaign_0005"],
            },
        }
        for item in hypotheses
    ]
    mechanism_objects = [
        {
            "identifier": item["identifier"],
            "type": "KnowledgeObject",
            "title": item["name"],
            "summary": item["description"],
            "lifecycle_state": "ACTIVE",
            "confidence": 0.8,
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
            "source_ids": item["supporting_hypotheses"],
            "attributes": {
                "participants": item["participants"],
                "supporting_hypotheses": item["supporting_hypotheses"],
            },
        }
        for item in analysis["economic_mechanism_atlas"]
    ]
    return {
        "metadata": {
            "source_kind": "INTERNAL_RESEARCH_REPORT",
            "title": "Campaign 0004 hypothesis discovery knowledge pack",
            "specification_refs": ["SPEC-012", "SPEC-060"],
            "evidence_refs": [
                "11-research/phase-g/hypothesis-discovery/HYPOTHESIS_DISCOVERY_CAMPAIGN.md",
                "11-research/phase-g/feature-discovery/feature_discovery_analysis.json",
                "11-research/phase-g/regime-discovery/regime_discovery_analysis.json",
            ],
        },
        "ikros_objects": [
            {
                "identifier": "IKROS-DSV-20260802-0004",
                "type": "DatasetVersion",
                "title": "Campaign 0004 hypothesis discovery dataset reference",
                "summary": "Governed dataset and feature/reference bundle used for hypothesis discovery only.",
                "lifecycle_state": "VALIDATED",
                "confidence": 0.88,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
                "attributes": {
                    "upstream_dataset_version": "IKROS-DSV-20260802-0003",
                    "taxonomy_id": "IKROS-CONCL-20260802-0002",
                    "feature_catalogue_id": "IKROS-CONCL-20260802-0003",
                    "hypothesis_count": analysis["campaign"]["hypothesis_count"],
                },
            },
            {
                "identifier": "IKROS-KO-20260802-0400",
                "type": "KnowledgeObject",
                "title": "Campaign 0004 hypothesis discovery methodology",
                "summary": "Institutional methodology for generating hypotheses from the approved taxonomy and approved feature catalogue without validating them.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.84,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/hypothesis-discovery/HYPOTHESIS_DISCOVERY_CAMPAIGN.md"],
                "attributes": {
                    "approved_taxonomy": analysis["campaign"]["accepted_taxonomy"],
                    "approved_catalogue": analysis["campaign"]["approved_catalogue"],
                    "recommended_hypotheses": analysis["recommended_hypotheses"],
                },
            },
            {
                "identifier": "IKROS-EVIDENCE-20260802-0004",
                "type": "Evidence",
                "title": "Campaign 0004 hypothesis evidence bundle",
                "summary": "Evidence bundle carrying the hypothesis catalogue, mechanism atlas, priority matrix, and validation matrix into IKROS.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.83,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
                "attributes": {
                    "recommended_hypotheses": analysis["recommended_hypotheses"],
                    "priority_matrix_size": len(analysis["research_priority_matrix"]),
                    "validation_matrix_size": len(analysis["expected_validation_matrix"]),
                },
            },
            {
                "identifier": "IKROS-CONTRA-20260802-0004",
                "type": "ContradictoryEvidence",
                "title": "Campaign 0004 contradiction log",
                "summary": "Contradictions inherited from macro-only rejection, sparse event coverage, and crisis-state uncertainty.",
                "lifecycle_state": "ACTIVE",
                "confidence": 0.74,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
                "attributes": {
                    "reasons": [
                        "macro-only mechanisms were previously rejected",
                        "transition and crisis states remain sparser than calmer regimes",
                        "range-compression hypotheses may have low institutional capacity",
                    ]
                },
            },
            {
                "identifier": "IKROS-CONCL-20260802-0004",
                "type": "ResearchConclusion",
                "title": "Publish the institutional alpha hypothesis catalogue",
                "summary": "Campaign 0004 recommends advancing only the highest-priority regime-conditioned hypotheses into Campaign 0005.",
                "lifecycle_state": "PUBLISHED",
                "confidence": 0.84,
                "specification_refs": ["SPEC-012", "SPEC-060"],
                "evidence_refs": ["11-research/phase-g/hypothesis-discovery/hypothesis_discovery_analysis.json"],
                "source_ids": ["IKROS-EVIDENCE-20260802-0004", "IKROS-CONTRA-20260802-0004"],
                "attributes": {
                    "recommended_hypotheses": analysis["recommended_hypotheses"],
                    "decision": "ADVANCE_TO_CAMPAIGN_0005",
                    "catalogue": analysis["campaign"]["hypothesis_catalogue"],
                },
            },
        ]
        + research_questions
        + hypothesis_objects
        + mechanism_objects,
    }
