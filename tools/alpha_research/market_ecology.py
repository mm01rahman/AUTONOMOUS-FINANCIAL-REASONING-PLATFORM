"""Institutional Market Ecology Research Program for Discovery Cycle 2 Program B Phase 1.

Builds the first governed institutional ecology model explaining how heterogeneous
market participants collectively generate the approved cross-asset information
network and XAU/USD regime transitions.

Program B Phase 1 outputs:
  - Institutional Market Ecology Atlas
  - Participant Profiles
  - Interaction Matrix
  - Capital Flow Atlas
  - Liquidity Ecology Report
  - Adaptive Behaviour Report
  - Ecology Knowledge Graph
  - Research Recommendations

The objective is institutional understanding, not prediction or alpha generation.
"""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from tools.alpha_research.cross_asset_ecology import CROSS_ASSET_SIGNALS, REGIME_ORDER
from tools.alpha_research.information_network import prepare_dc2_phase3_artifacts
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC2_PROGRAM_B_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-b-phase1"
DC2_PROGRAM_B_ANALYSIS = DC2_PROGRAM_B_DIR / "dc2_program_b_market_ecology_analysis.json"

PARTICIPANTS: list[dict[str, Any]] = [
    {
        "participant_id": "central_banks",
        "label": "Central Banks",
        "theme": "Theme 1",
        "signals": {
            "yield_curve_10y_3m": 1.00,
            "yield_10y_change_5": 0.95,
            "fed_surprise": 1.00,
            "macro_pressure": 0.90,
        },
        "liquidity_role": "policy_anchor",
        "capital_role": "sovereign_allocator",
        "objectives": "Anchor inflation expectations, manage reserves, preserve policy credibility.",
        "constraints": "Policy mandates, political constraints, reserve adequacy, FX credibility.",
        "information": "Inflation, growth, reserve conditions, macro stress, policy transmission.",
        "reaction_function": "Reprice policy path, influence real yields and USD expectations, alter reserve demand for gold.",
        "typical_positioning": "Slow-moving reserve allocation and policy signalling rather than tactical turnover.",
        "liquidity_effects": "Can suppress or amplify gold via rates and USD channels while influencing system-wide funding conditions.",
        "historical_behaviour": "Dominant at macro turning points, inflation shocks, and policy regime shifts.",
        "failure_modes": "Policy surprise misread, reserve defense constraints, delayed response to inflation stress.",
    },
    {
        "participant_id": "commercial_hedgers",
        "label": "Commercial Hedgers",
        "theme": "Theme 2",
        "signals": {
            "forward_expectation": 0.95,
            "yield_30y_change_20": 0.70,
            "xau_return_1": 0.60,
        },
        "liquidity_role": "inventory_hedger",
        "capital_role": "physical_flow",
        "objectives": "Reduce operating PnL volatility and manage physical exposure.",
        "constraints": "Inventory cycles, hedge ratios, financing costs, production schedules.",
        "information": "Forward curve conditions, financing costs, physical supply/demand.",
        "reaction_function": "Add or reduce hedges as forwards, duration, and spot volatility alter carry economics.",
        "typical_positioning": "Structural hedging with opportunistic rebalancing around macro repricing.",
        "liquidity_effects": "Provide one-sided flow at specific maturities and dampen extreme inventory-driven price moves.",
        "historical_behaviour": "Most visible during term-structure stress and producer margin compression.",
        "failure_modes": "Under-hedging during abrupt rallies, over-hedging during supply shocks.",
    },
    {
        "participant_id": "bullion_banks",
        "label": "Bullion Banks",
        "theme": "Theme 3",
        "signals": {
            "dxy_return_1": 0.85,
            "dxy_return_5": 0.90,
            "forward_expectation": 0.95,
            "xau_return_1": 0.80,
        },
        "liquidity_role": "intermediation_core",
        "capital_role": "inventory_transformer",
        "objectives": "Warehouse flow, manage basis exposure, intermediate OTC and futures demand.",
        "constraints": "Balance sheet, funding, basis risk, client inventory, capital usage.",
        "information": "Client flow, USD funding, basis, forwards, cross-venue spreads.",
        "reaction_function": "Translate client demand into forwards, leases, spot, and futures inventory adjustments.",
        "typical_positioning": "Market-neutral inventory management with short-horizon directional spillovers.",
        "liquidity_effects": "Primary relay between policy/macro impulses and market microstructure execution.",
        "historical_behaviour": "Most important during USD and forward-basis dislocations.",
        "failure_modes": "Funding stress, basis breaks, concentrated client flow shocks.",
    },
    {
        "participant_id": "dealers",
        "label": "Dealers",
        "theme": "Theme 4",
        "signals": {
            "dxy_return_1": 0.75,
            "dxy_return_5": 0.85,
            "macro_pressure": 0.85,
            "xau_return_1": 0.80,
        },
        "liquidity_role": "balance_sheet_intermediary",
        "capital_role": "flow_matcher",
        "objectives": "Absorb client flow while preserving inventory and spread economics.",
        "constraints": "Balance sheet, VaR, inventory, client skew, funding.",
        "information": "Order flow, positioning pressure, client imbalances, macro repricing speed.",
        "reaction_function": "Widen/tighten risk transfer, internalize or externalize inventory, transmit flow to makers and banks.",
        "typical_positioning": "Inventory-buffered and reactive to crowding, volatility, and turnover.",
        "liquidity_effects": "Can become bottlenecks during stress when balance-sheet capacity shrinks.",
        "historical_behaviour": "Critical in transition phases when information must be warehoused before redistribution.",
        "failure_modes": "Inventory saturation, spread blowout, procyclical de-risking.",
    },
    {
        "participant_id": "market_makers",
        "label": "Market Makers",
        "theme": "Theme 5",
        "signals": {
            "xau_return_1": 1.00,
            "dxy_return_1": 0.65,
            "geo_severity": 0.55,
        },
        "liquidity_role": "liquidity_provider",
        "capital_role": "microstructure_provider",
        "objectives": "Earn spread, manage adverse selection, maintain quoting franchise.",
        "constraints": "Inventory, latency, volatility, adverse selection, capital limits.",
        "information": "Order-book dynamics, flow toxicity, short-horizon volatility, event shocks.",
        "reaction_function": "Adjust quotes and inventory aggressively as toxicity and macro stress rise.",
        "typical_positioning": "Very short-horizon, inventory mean-reverting, liquidity sensitive.",
        "liquidity_effects": "Directly determine immediate market depth and short-run price resilience.",
        "historical_behaviour": "Strong in calm carry/range regimes, defensive in crisis dislocation.",
        "failure_modes": "Quote withdrawal, flow toxicity misclassification, inventory air pockets.",
    },
    {
        "participant_id": "ctas",
        "label": "Commodity Trading Advisors",
        "theme": "Theme 6",
        "signals": {
            "dxy_return_20": 0.75,
            "forward_expectation": 0.70,
            "xau_return_1": 0.85,
        },
        "liquidity_role": "trend_amplifier",
        "capital_role": "systematic_flow",
        "objectives": "Exploit persistent trends and convexity in macro futures and metals.",
        "constraints": "Model rules, position limits, volatility targets, liquidity windows.",
        "information": "Trend strength, breakout persistence, correlation regimes, momentum decay.",
        "reaction_function": "Scale into persistent moves, reinforce directional flows, reverse after trend breaks.",
        "typical_positioning": "Procyclical, model-driven, medium-horizon trend follower.",
        "liquidity_effects": "Amplify established moves and can accelerate transition once trend thresholds break.",
        "historical_behaviour": "Most influential after macro transitions convert into persistent price trends.",
        "failure_modes": "Whipsaws, false breakouts, crowded trend reversals.",
    },
    {
        "participant_id": "macro_hedge_funds",
        "label": "Macro Hedge Funds",
        "theme": "Theme 7",
        "signals": {
            "dxy_return_1": 0.90,
            "yield_10y_change_5": 0.85,
            "macro_pressure": 1.00,
            "fed_surprise": 0.90,
        },
        "liquidity_role": "macro_reallocator",
        "capital_role": "tactical_allocator",
        "objectives": "Express macro theses across rates, FX, commodities, and safe-haven trades.",
        "constraints": "Risk limits, drawdown tolerance, financing, crowding, redemption risk.",
        "information": "Macro surprise, policy path, cross-asset dislocations, positioning data.",
        "reaction_function": "Rapidly reallocate across gold, USD, and rates as macro narrative changes.",
        "typical_positioning": "Cross-asset, directional, fast to medium horizon.",
        "liquidity_effects": "Fast reallocations propagate information from rates and USD into gold.",
        "historical_behaviour": "Dominant during macro transitions, inflation repricing, and policy shocks.",
        "failure_modes": "Narrative overcrowding, leverage unwind, cross-asset contagion.",
    },
    {
        "participant_id": "etf_investors",
        "label": "ETF Investors",
        "theme": "Theme 8",
        "signals": {
            "geo_severity": 0.80,
            "forward_expectation": 0.70,
            "xau_return_1": 0.75,
        },
        "liquidity_role": "allocation_flow",
        "capital_role": "investment_flow",
        "objectives": "Allocate to gold as strategic hedge, inflation diversifier, or safe haven.",
        "constraints": "Mandates, benchmark weights, client sentiment, liquidity windows.",
        "information": "Narrative shifts, safe-haven demand, macro uncertainty, performance persistence.",
        "reaction_function": "Add or withdraw exposure after narrative confirmation and stress escalation.",
        "typical_positioning": "Slower than hedge funds, faster than sovereign allocators; flow-sensitive.",
        "liquidity_effects": "Create medium-horizon demand waves and inventory pressure for market intermediaries.",
        "historical_behaviour": "Most active during fear-driven allocation cycles and inflation hedging episodes.",
        "failure_modes": "Late entry/exit, crowding with safe-haven flows, narrative lag.",
    },
    {
        "participant_id": "retail_traders",
        "label": "Retail Traders",
        "theme": "Theme 9",
        "signals": {
            "xau_return_1": 0.90,
            "geo_severity": 0.65,
        },
        "liquidity_role": "sentiment_echo",
        "capital_role": "fragmented_flow",
        "objectives": "Capture short-horizon price action or express discretionary macro sentiment.",
        "constraints": "Capital limits, leverage, information disadvantage, execution quality.",
        "information": "Headline flow, recent price momentum, social sentiment, visible volatility.",
        "reaction_function": "Chase visible price moves and safe-haven headlines after institutional flow starts.",
        "typical_positioning": "Late-cycle, short-horizon, reactive to observable price acceleration.",
        "liquidity_effects": "Can intensify late-stage directional extension but rarely initiate regime change.",
        "historical_behaviour": "Most active after public narratives become obvious and price momentum is visible.",
        "failure_modes": "Buying tops, selling troughs, liquidity chasing.",
    },
    {
        "participant_id": "safe_haven_capital_flows",
        "label": "Safe Haven Capital Flows",
        "theme": "Theme 10",
        "signals": {
            "geo_severity": 1.00,
            "macro_pressure": 0.85,
            "yield_curve_10y_3m": 0.75,
            "dxy_return_1": 0.65,
        },
        "liquidity_role": "stress_allocator",
        "capital_role": "defensive_reallocator",
        "objectives": "Protect capital under systemic uncertainty and preserve real purchasing power.",
        "constraints": "Mandate defensiveness, event uncertainty, hedging urgency, execution constraints.",
        "information": "Geopolitical stress, systemic fragility, recession risk, correlation breaks.",
        "reaction_function": "Reallocate toward gold and related safe-haven expressions when systemic stress rises.",
        "typical_positioning": "Episodic, conviction-heavy, concentrated around stress triggers.",
        "liquidity_effects": "Can overwhelm normal market-making capacity and rewire topology during stress.",
        "historical_behaviour": "Strongest in crisis dislocation and geopolitical shock regimes.",
        "failure_modes": "Crowding into same hedge, late panic allocation, reversal after stress normalization.",
    },
]

REGIME_BEHAVIOR_MAP: dict[str, dict[str, str]] = {
    "bull_trend": {
        "central_banks": "Policy stance matters less than persistent investor and CTA trend reinforcement.",
        "commercial_hedgers": "Increase tactical hedging as upside persists.",
        "bullion_banks": "Warehouse trend-following demand and manage forward inventory.",
        "dealers": "Distribute directional client demand while protecting inventory.",
        "market_makers": "Provide liquidity but shorten quote horizons.",
        "ctas": "Scale into trend continuation and amplify directional persistence.",
        "macro_hedge_funds": "Express pro-gold macro thesis via cross-asset allocations.",
        "etf_investors": "Increase strategic allocations after confirmation.",
        "retail_traders": "Join once momentum is visible.",
        "safe_haven_capital_flows": "Less dominant unless trend is fear-driven.",
    },
    "bear_unwind": {
        "central_banks": "Higher real-rate pressure dominates reserve demand.",
        "commercial_hedgers": "Reduce hedges or monetize prior protection.",
        "bullion_banks": "Unwind inventories and funding-sensitive structures.",
        "dealers": "Transmit de-risking across client channels.",
        "market_makers": "Tighten risk, manage adverse flow imbalances.",
        "ctas": "Reverse long exposure and accelerate unwind.",
        "macro_hedge_funds": "Rotate toward USD/rates expressions over gold.",
        "etf_investors": "Redeem exposure after thesis deterioration.",
        "retail_traders": "Late liquidation after visible breakdown.",
        "safe_haven_capital_flows": "Retreat as stress premium falls.",
    },
    "calm_carry": {
        "central_banks": "Steady policy backdrop suppresses urgent gold demand.",
        "commercial_hedgers": "Optimize carry and financing through forward structures.",
        "bullion_banks": "Monetize stable basis conditions.",
        "dealers": "Warehouse balanced two-way flow efficiently.",
        "market_makers": "Deepest liquidity and narrowest spreads.",
        "ctas": "Lower participation because trends are muted.",
        "macro_hedge_funds": "Prefer relative-value expressions.",
        "etf_investors": "Strategic flows dominate over tactical changes.",
        "retail_traders": "Attention fades without visible volatility.",
        "safe_haven_capital_flows": "Remain dormant.",
    },
    "crisis_dislocation": {
        "central_banks": "Policy and reserve credibility become central network anchors.",
        "commercial_hedgers": "Prioritize balance-sheet protection over optimization.",
        "bullion_banks": "Funding and basis stress make them critical relays.",
        "dealers": "Become bottlenecks as balance-sheet capacity shrinks.",
        "market_makers": "Withdraw liquidity and widen spreads sharply.",
        "ctas": "Can reinforce both crash and rebound once trend rules trigger.",
        "macro_hedge_funds": "Aggressively reallocate across gold, USD, and rates.",
        "etf_investors": "Add to safe-haven positions after stress confirmation.",
        "retail_traders": "Chase fear-driven moves late in the cycle.",
        "safe_haven_capital_flows": "Most dominant participant during systemic stress.",
    },
    "macro_transition": {
        "central_banks": "Primary drivers through policy-path repricing.",
        "commercial_hedgers": "Re-evaluate hedge structures as macro carry changes.",
        "bullion_banks": "Translate macro repricing into forward/spot market structure.",
        "dealers": "Intermediate rapid portfolio reallocation across participants.",
        "market_makers": "Adjust depth as information arrival accelerates.",
        "ctas": "Join after directional persistence is established.",
        "macro_hedge_funds": "Fastest tactical reallocators at narrative turning points.",
        "etf_investors": "Respond after thesis gains institutional legitimacy.",
        "retail_traders": "Mostly reactive, not initiators.",
        "safe_haven_capital_flows": "Rise when macro transition overlaps with systemic fear.",
    },
    "range_compression": {
        "central_banks": "Policy uncertainty is low and participant interactions are muted.",
        "commercial_hedgers": "Maintain baseline hedges with little directional urgency.",
        "bullion_banks": "Optimize balance sheet rather than directional expression.",
        "dealers": "Facilitate mean-reverting two-way flow.",
        "market_makers": "Dominate microstructure with deepest continuous liquidity.",
        "ctas": "Low engagement because breakout signals are absent.",
        "macro_hedge_funds": "Wait for cleaner macro asymmetry.",
        "etf_investors": "Strategic but inactive.",
        "retail_traders": "Fade visibility due to low excitement.",
        "safe_haven_capital_flows": "Inactive in absence of stress.",
    },
}

INTERACTION_BIAS: dict[tuple[str, str], float] = {
    ("central_banks", "macro_hedge_funds"): 0.25,
    ("central_banks", "bullion_banks"): 0.18,
    ("central_banks", "safe_haven_capital_flows"): 0.12,
    ("commercial_hedgers", "bullion_banks"): 0.22,
    ("commercial_hedgers", "dealers"): 0.18,
    ("bullion_banks", "dealers"): 0.26,
    ("dealers", "market_makers"): 0.28,
    ("macro_hedge_funds", "ctas"): 0.20,
    ("macro_hedge_funds", "etf_investors"): 0.10,
    ("safe_haven_capital_flows", "etf_investors"): 0.24,
    ("safe_haven_capital_flows", "market_makers"): -0.08,
    ("retail_traders", "market_makers"): -0.05,
}


def _phase3_node_stats(phase3: dict[str, Any]) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for node, info in phase3["centrality_analysis"]["nodes"].items():
        stats[node] = {
            "out_strength": float(info["out_strength"]),
            "in_strength": float(info["in_strength"]),
            "net_flow": float(info["net_flow"]),
            "relay_score": float(info["relay_score"]),
        }
    return stats


def _participant_profiles(phase3: dict[str, Any]) -> dict[str, dict[str, Any]]:
    node_stats = _phase3_node_stats(phase3)
    profiles: dict[str, dict[str, Any]] = {}
    for participant in PARTICIPANTS:
        pid = str(participant["participant_id"])
        signals = dict(participant["signals"])
        source_exposure = 0.0
        sink_exposure = 0.0
        relay_exposure = 0.0
        net_influence = 0.0
        leverage_channels: list[str] = []
        for signal, weight in signals.items():
            if signal not in node_stats:
                continue
            leverage_channels.append(signal)
            source_exposure += float(weight) * max(0.0, node_stats[signal]["net_flow"])
            sink_exposure += float(weight) * max(0.0, -node_stats[signal]["net_flow"])
            relay_exposure += float(weight) * node_stats[signal]["relay_score"]
            net_influence += float(weight) * (
                node_stats[signal]["out_strength"] - 0.5 * node_stats[signal]["in_strength"]
            )
        aggregate_score = round(net_influence + 0.5 * relay_exposure, 4)
        if aggregate_score > 1.9:
            ecology_role = "ecology_driver"
        elif relay_exposure > 0.6:
            ecology_role = "ecology_relay"
        elif sink_exposure > source_exposure:
            ecology_role = "ecology_sink"
        else:
            ecology_role = "ecology_adapter"
        profiles[pid] = {
            "participant_id": pid,
            "label": participant["label"],
            "theme": participant["theme"],
            "objectives": participant["objectives"],
            "constraints": participant["constraints"],
            "information": participant["information"],
            "reaction_function": participant["reaction_function"],
            "typical_positioning": participant["typical_positioning"],
            "liquidity_effects": participant["liquidity_effects"],
            "historical_behaviour": participant["historical_behaviour"],
            "failure_modes": participant["failure_modes"],
            "signals": signals,
            "leveraged_channels": leverage_channels,
            "source_exposure": round(source_exposure, 4),
            "sink_exposure": round(sink_exposure, 4),
            "relay_exposure": round(relay_exposure, 4),
            "net_influence_score": round(net_influence, 4),
            "aggregate_ecology_score": aggregate_score,
            "liquidity_role": participant["liquidity_role"],
            "capital_role": participant["capital_role"],
            "ecology_role": ecology_role,
            "expected_behaviour_by_regime": {
                regime: REGIME_BEHAVIOR_MAP[regime][pid] for regime in REGIME_ORDER
            },
        }
    return profiles


def _signal_overlap(a: dict[str, float], b: dict[str, float]) -> float:
    shared = set(a) & set(b)
    return round(sum(min(float(a[s]), float(b[s])) for s in shared), 4)


def _interaction_network(profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    participants = list(profiles)
    matrix: dict[str, dict[str, float]] = {}
    edges: list[dict[str, Any]] = []
    for source in participants:
        matrix[source] = {}
        for target in participants:
            if source == target:
                matrix[source][target] = 0.0
                continue
            source_signals = cast(dict[str, float], profiles[source]["signals"])
            target_signals = cast(dict[str, float], profiles[target]["signals"])
            overlap = _signal_overlap(source_signals, target_signals)
            source_score = float(profiles[source]["aggregate_ecology_score"])
            target_score = float(profiles[target]["aggregate_ecology_score"])
            directional = max(0.0, source_score - 0.25 * target_score) * 0.05
            bias = INTERACTION_BIAS.get((source, target), 0.0)
            score = round(overlap * 0.22 + directional + bias, 4)
            matrix[source][target] = score
            if abs(score) >= 0.18:
                relation = "cooperative" if score > 0 else "competitive"
                edges.append(
                    {
                        "source": source,
                        "target": target,
                        "interaction_score": score,
                        "relation": relation,
                        "shared_channels": sorted(set(source_signals) & set(target_signals)),
                    }
                )
    edges.sort(key=lambda item: abs(float(item["interaction_score"])), reverse=True)
    return {"matrix": matrix, "edges": edges}


def _capital_flow_network(
    profiles: dict[str, dict[str, Any]], phase3: dict[str, Any]
) -> dict[str, Any]:
    centrality = phase3["centrality_analysis"]["nodes"]
    edges: list[dict[str, Any]] = []
    for pid, profile in profiles.items():
        for signal, weight in cast(dict[str, float], profile["signals"]).items():
            node = centrality.get(signal, {})
            capital_intensity = round(
                float(weight) * (0.6 + abs(float(node.get("net_flow", 0.0)))), 4
            )
            if capital_intensity < 0.35:
                continue
            edges.append(
                {
                    "participant": pid,
                    "market_node": signal,
                    "market": CROSS_ASSET_SIGNALS.get(signal, {}).get("market", "XAU/USD"),
                    "capital_intensity": capital_intensity,
                    "flow_type": str(profile["capital_role"]),
                }
            )
    edges.sort(key=lambda item: float(item["capital_intensity"]), reverse=True)
    return {"edges": edges}


def _liquidity_network(
    profiles: dict[str, dict[str, Any]], interactions: dict[str, Any]
) -> dict[str, Any]:
    provider_roles = {
        "liquidity_provider",
        "balance_sheet_intermediary",
        "intermediation_core",
        "policy_anchor",
    }
    demand_roles = {
        "trend_amplifier",
        "macro_reallocator",
        "allocation_flow",
        "fragmented_flow",
        "stress_allocator",
    }
    edges: list[dict[str, Any]] = []
    for edge in interactions["edges"]:
        source_role = str(profiles[str(edge["source"])]["liquidity_role"])
        target_role = str(profiles[str(edge["target"])]["liquidity_role"])
        if (
            source_role in provider_roles
            and target_role in demand_roles
            and float(edge["interaction_score"]) > 0
        ):
            liquidity_effect = "provision"
        elif (
            source_role in demand_roles
            and target_role in provider_roles
            and float(edge["interaction_score"]) > 0
        ):
            liquidity_effect = "withdrawal_pressure"
        elif float(edge["interaction_score"]) < 0:
            liquidity_effect = "competition"
        else:
            liquidity_effect = "balancing"
        edges.append(
            {
                "source": edge["source"],
                "target": edge["target"],
                "liquidity_effect": liquidity_effect,
                "strength": round(abs(float(edge["interaction_score"])), 4),
            }
        )
    return {"edges": edges}


def _cooperation_competition(interactions: dict[str, Any]) -> dict[str, Any]:
    cooperation = [
        edge for edge in interactions["edges"] if float(edge["interaction_score"]) > 0.22
    ]
    competition = [
        edge for edge in interactions["edges"] if float(edge["interaction_score"]) < -0.02
    ]
    return {"cooperation": cooperation, "competition": competition}


def _feedback_loops(interactions: dict[str, Any]) -> list[dict[str, Any]]:
    interaction_map = {
        (str(edge["source"]), str(edge["target"])): float(edge["interaction_score"])
        for edge in interactions["edges"]
    }
    loops: list[dict[str, Any]] = []
    for (source, target), score in interaction_map.items():
        back = interaction_map.get((target, source))
        if back is None:
            continue
        if source >= target:
            continue
        if score > 0.20 and back > 0.20:
            loops.append(
                {
                    "pair": f"{source}<->{target}",
                    "forward": round(score, 4),
                    "backward": round(back, 4),
                    "loop_type": "reinforcing",
                }
            )
        elif score < -0.02 and back < -0.02:
            loops.append(
                {
                    "pair": f"{source}<->{target}",
                    "forward": round(score, 4),
                    "backward": round(back, 4),
                    "loop_type": "competitive",
                }
            )
    loops.sort(
        key=lambda item: abs(float(item["forward"])) + abs(float(item["backward"])), reverse=True
    )
    return loops


def _adaptive_behaviour_model(
    profiles: dict[str, dict[str, Any]], phase3: dict[str, Any]
) -> dict[str, Any]:
    dominant_sources = set(phase3["arb_recommendation"]["dominant_sources"])
    dominant_relays = set(phase3["arb_recommendation"]["dominant_relays"])
    result: dict[str, Any] = {}
    for pid, profile in profiles.items():
        signals = set(cast(dict[str, float], profile["signals"]).keys())
        if signals & dominant_sources:
            trigger = "macro_source_repricing"
        elif signals & dominant_relays:
            trigger = "relay_congestion"
        else:
            trigger = "observable_price_extension"
        result[pid] = {
            "participant": pid,
            "adaptive_trigger": trigger,
            "adaptation_mode": (
                "reallocate"
                if profile["capital_role"]
                in {"tactical_allocator", "defensive_reallocator", "investment_flow"}
                else "warehouse"
                if profile["liquidity_role"]
                in {"intermediation_core", "balance_sheet_intermediary"}
                else "quote_adjust"
                if profile["liquidity_role"] == "liquidity_provider"
                else "rule_scale"
                if profile["liquidity_role"] == "trend_amplifier"
                else "hedge_rebalance"
            ),
            "regime_sensitivity": (
                "high"
                if profile["ecology_role"] in {"ecology_driver", "ecology_relay"}
                else "moderate"
            ),
        }
    return result


def _knowledge_graph_payload(
    profiles: dict[str, dict[str, Any]],
    interactions: dict[str, Any],
    capital_flows: dict[str, Any],
    liquidity: dict[str, Any],
    loops: list[dict[str, Any]],
) -> dict[str, Any]:
    participant_nodes = [
        {
            "node_id": f"IKROS-PB1-PARTICIPANT-{pid.replace('_', '-').upper()}",
            "label": profile["label"],
            "node_type": "KNOWLEDGE_OBJECT",
            "attributes": {
                "participant_id": pid,
                "theme": profile["theme"],
                "ecology_role": profile["ecology_role"],
                "capital_role": profile["capital_role"],
                "liquidity_role": profile["liquidity_role"],
            },
        }
        for pid, profile in profiles.items()
    ]
    interaction_edges = [
        {
            "source": f"IKROS-PB1-PARTICIPANT-{str(edge['source']).replace('_', '-').upper()}",
            "target": f"IKROS-PB1-PARTICIPANT-{str(edge['target']).replace('_', '-').upper()}",
            "relation": "RELATED_TO" if float(edge["interaction_score"]) > 0 else "ASSOCIATED_WITH",
            "confidence": round(abs(float(edge["interaction_score"])), 4),
            "attributes": {
                "shared_channels": edge["shared_channels"],
                "relation": edge["relation"],
            },
        }
        for edge in interactions["edges"][:30]
    ]
    factor_nodes = [
        {
            "node_id": "IKROS-PB1-FACTOR-XAU-RETURN-1",
            "label": "XAU/USD 1-day return",
            "node_type": "FACTOR",
            "attributes": {"market": "XAU/USD"},
        },
    ]
    factor_nodes.extend(
        [
            {
                "node_id": f"IKROS-PB1-FACTOR-{signal.replace('_', '-').upper()}",
                "label": CROSS_ASSET_SIGNALS.get(signal, {}).get("title", signal),
                "node_type": "FACTOR",
                "attributes": {
                    "market": CROSS_ASSET_SIGNALS.get(signal, {}).get("market", "XAU/USD"),
                },
            }
            for signal in CROSS_ASSET_SIGNALS
        ]
    )
    factor_edges = [
        {
            "source": f"IKROS-PB1-PARTICIPANT-{str(edge['participant']).replace('_', '-').upper()}",
            "target": f"IKROS-PB1-FACTOR-{str(edge['market_node']).replace('_', '-').upper()}",
            "relation": "CAUSES",
            "confidence": float(edge["capital_intensity"]),
            "attributes": {"flow_type": edge["flow_type"]},
        }
        for edge in capital_flows["edges"][:40]
    ]
    loop_edges = [
        {
            "pair": loop["pair"],
            "loop_type": loop["loop_type"],
            "forward": loop["forward"],
            "backward": loop["backward"],
        }
        for loop in loops[:10]
    ]
    return {
        "participant_nodes": participant_nodes,
        "factor_nodes": factor_nodes,
        "interaction_edges": interaction_edges,
        "factor_edges": factor_edges,
        "liquidity_edges": liquidity["edges"][:30],
        "feedback_loops": loop_edges,
    }


def _recommendations(
    profiles: dict[str, dict[str, Any]],
    interactions: dict[str, Any],
    phase3: dict[str, Any],
) -> dict[str, Any]:
    drivers = sorted(
        profiles.values(),
        key=lambda item: float(item["aggregate_ecology_score"]),
        reverse=True,
    )[:5]
    relays = [item for item in drivers if item["ecology_role"] == "ecology_relay"] or sorted(
        profiles.values(),
        key=lambda item: float(item["relay_exposure"]),
        reverse=True,
    )[:3]
    return {
        "priority_participants": [item["participant_id"] for item in drivers[:5]],
        "priority_relays": [item["participant_id"] for item in relays[:3]],
        "critical_interactions": [
            f"{edge['source']}->{edge['target']}" for edge in interactions["edges"][:8]
        ],
        "dataset_priorities": [
            "COT / commercial hedger positioning",
            "ETF flow data (GLD and related products)",
            "Bullion bank / dealer inventory and lease/basis proxies",
            "Safe-haven fund flow proxies and options positioning",
        ],
        "arb_recommendation": (
            "Adopt a participant-layer ecology model in which central banks and macro hedge funds initiate macro repricing, "
            "bullion banks and dealers relay and transform the flow, market makers provide or withdraw microstructure depth, "
            "and CTAs / ETF investors / safe-haven flows amplify or stabilize regime transitions."
        ),
        "phase3_governing_model": phase3["arb_recommendation"]["governing_model"],
    }


def prepare_dc2_program_b_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    phase3 = prepare_dc2_phase3_artifacts(repo_root=repo_root)
    profiles = _participant_profiles(phase3)
    interactions = _interaction_network(profiles)
    capital_flows = _capital_flow_network(profiles, phase3)
    liquidity = _liquidity_network(profiles, interactions)
    collaboration = _cooperation_competition(interactions)
    feedback_loops = _feedback_loops(interactions)
    adaptive = _adaptive_behaviour_model(profiles, phase3)
    knowledge_graph = _knowledge_graph_payload(
        profiles, interactions, capital_flows, liquidity, feedback_loops
    )
    recommendations = _recommendations(profiles, interactions, phase3)

    analysis = {
        "phase": "DC2_PROGRAM_B_PHASE1",
        "title": "Institutional Market Ecology Research Program",
        "date_range": phase3["date_range"],
        "participant_profiles": profiles,
        "participant_interaction_network": interactions,
        "interaction_matrix": interactions["matrix"],
        "capital_flow_network": capital_flows,
        "liquidity_network": liquidity,
        "cooperation_network": collaboration["cooperation"],
        "competition_network": collaboration["competition"],
        "feedback_loops": feedback_loops,
        "adaptive_behaviour_model": adaptive,
        "institutional_market_ecology_graph": {
            "participants": list(profiles.keys()),
            "dominant_participants": recommendations["priority_participants"],
            "critical_interactions": recommendations["critical_interactions"],
        },
        "ecology_knowledge_graph": knowledge_graph,
        "research_recommendations": recommendations,
        "program_a_foundations": phase3["arb_recommendation"],
    }

    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_B_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_program_b_market_ecology_analysis.json", analysis)
    return analysis


def emit_dc2_program_b_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PROGRAM_B_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    profiles = analysis["participant_profiles"]
    interactions = analysis["participant_interaction_network"]
    capital_flows = analysis["capital_flow_network"]
    liquidity = analysis["liquidity_network"]
    adaptive = analysis["adaptive_behaviour_model"]
    graph_payload = analysis["ecology_knowledge_graph"]
    recommendations = analysis["research_recommendations"]

    atlas_md = out_dir / "INSTITUTIONAL_MARKET_ECOLOGY_ATLAS.md"
    atlas_rows: list[list[object]] = [
        [
            pid,
            profile["ecology_role"],
            profile["aggregate_ecology_score"],
            profile["source_exposure"],
            profile["relay_exposure"],
        ]
        for pid, profile in profiles.items()
    ]
    write_markdown(
        atlas_md,
        f"""# Institutional Market Ecology Atlas
## Discovery Cycle 2 Program B Phase 1

{markdown_table(["Participant", "Ecology Role", "Ecology Score", "Source Exposure", "Relay Exposure"], atlas_rows)}

### Governing Interpretation
{recommendations["arb_recommendation"]}
""",
    )
    written["ecology_atlas"] = str(atlas_md)

    profiles_md = out_dir / "PARTICIPANT_PROFILES.md"
    profile_blocks = []
    for pid, profile in profiles.items():
        profile_blocks.append(
            f"""### {profile["label"]}
- **Objectives:** {profile["objectives"]}
- **Constraints:** {profile["constraints"]}
- **Information:** {profile["information"]}
- **Reaction Function:** {profile["reaction_function"]}
- **Typical Positioning:** {profile["typical_positioning"]}
- **Liquidity Effects:** {profile["liquidity_effects"]}
- **Historical Behaviour:** {profile["historical_behaviour"]}
- **Failure Modes:** {profile["failure_modes"]}
- **Ecology Role:** {profile["ecology_role"]}
"""
        )
    write_markdown(
        profiles_md,
        "# Participant Profiles\n## Discovery Cycle 2 Program B Phase 1\n\n"
        + "\n".join(profile_blocks),
    )
    written["participant_profiles"] = str(profiles_md)

    interaction_md = out_dir / "INTERACTION_MATRIX.md"
    participants = list(profiles.keys())
    interaction_rows: list[list[object]] = [
        [source, *[interactions["matrix"][source][target] for target in participants]]
        for source in participants
    ]
    write_markdown(
        interaction_md,
        f"""# Interaction Matrix
## Discovery Cycle 2 Program B Phase 1

{markdown_table(["Participant", *participants], interaction_rows)}
""",
    )
    written["interaction_matrix"] = str(interaction_md)

    capital_md = out_dir / "CAPITAL_FLOW_ATLAS.md"
    capital_rows: list[list[object]] = [
        [
            edge["participant"],
            edge["market_node"],
            edge["market"],
            edge["capital_intensity"],
            edge["flow_type"],
        ]
        for edge in capital_flows["edges"][:30]
    ]
    write_markdown(
        capital_md,
        f"""# Capital Flow Atlas
## Discovery Cycle 2 Program B Phase 1

{markdown_table(["Participant", "Market Node", "Market", "Capital Intensity", "Flow Type"], capital_rows)}
""",
    )
    written["capital_flow_atlas"] = str(capital_md)

    liquidity_md = out_dir / "LIQUIDITY_ECOLOGY_REPORT.md"
    liquidity_rows: list[list[object]] = [
        [edge["source"], edge["target"], edge["liquidity_effect"], edge["strength"]]
        for edge in liquidity["edges"][:30]
    ]
    write_markdown(
        liquidity_md,
        f"""# Liquidity Ecology Report
## Discovery Cycle 2 Program B Phase 1

{markdown_table(["Source", "Target", "Liquidity Effect", "Strength"], liquidity_rows)}
""",
    )
    written["liquidity_ecology"] = str(liquidity_md)

    adaptive_md = out_dir / "ADAPTIVE_BEHAVIOUR_REPORT.md"
    adaptive_rows: list[list[object]] = [
        [pid, model["adaptive_trigger"], model["adaptation_mode"], model["regime_sensitivity"]]
        for pid, model in adaptive.items()
    ]
    write_markdown(
        adaptive_md,
        f"""# Adaptive Behaviour Report
## Discovery Cycle 2 Program B Phase 1

{markdown_table(["Participant", "Adaptive Trigger", "Adaptation Mode", "Regime Sensitivity"], adaptive_rows)}
""",
    )
    written["adaptive_behaviour"] = str(adaptive_md)

    graph_md = out_dir / "ECOLOGY_KNOWLEDGE_GRAPH.md"
    interaction_rows_graph: list[list[object]] = [
        [edge["source"], edge["target"], edge["relation"], edge["confidence"]]
        for edge in graph_payload["interaction_edges"][:25]
    ]
    write_markdown(
        graph_md,
        f"""# Ecology Knowledge Graph
## Discovery Cycle 2 Program B Phase 1

### Participant Nodes
{len(graph_payload["participant_nodes"])}

### Factor Nodes
{len(graph_payload["factor_nodes"])}

### Interaction Edges
{markdown_table(["Source", "Target", "Relation", "Confidence"], interaction_rows_graph)}
""",
    )
    written["ecology_knowledge_graph"] = str(graph_md)

    rec_md = out_dir / "RESEARCH_RECOMMENDATIONS.md"
    write_markdown(
        rec_md,
        f"""# Research Recommendations
## Discovery Cycle 2 Program B Phase 1

### Priority Participants
{chr(10).join(f"- {item}" for item in recommendations["priority_participants"])}

### Priority Relays
{chr(10).join(f"- {item}" for item in recommendations["priority_relays"])}

### Critical Interactions
{chr(10).join(f"- {item}" for item in recommendations["critical_interactions"])}

### Dataset Priorities
{chr(10).join(f"- {item}" for item in recommendations["dataset_priorities"])}

### ARB Recommendation
{recommendations["arb_recommendation"]}
""",
    )
    written["research_recommendations"] = str(rec_md)

    write_json(
        out_dir / "institutional_market_ecology_graph.json",
        analysis["institutional_market_ecology_graph"],
    )
    write_json(out_dir / "participant_profiles.json", profiles)
    write_json(out_dir / "interaction_matrix.json", analysis["interaction_matrix"])
    write_json(out_dir / "capital_flow_atlas.json", capital_flows)
    write_json(out_dir / "liquidity_network.json", liquidity)
    write_json(out_dir / "adaptive_behaviour_model.json", adaptive)
    write_json(out_dir / "ecology_knowledge_graph.json", graph_payload)
    write_json(out_dir / "research_recommendations.json", recommendations)

    written["ecology_graph_json"] = str(out_dir / "institutional_market_ecology_graph.json")
    written["participant_profiles_json"] = str(out_dir / "participant_profiles.json")
    written["interaction_matrix_json"] = str(out_dir / "interaction_matrix.json")
    written["capital_flow_json"] = str(out_dir / "capital_flow_atlas.json")
    written["liquidity_network_json"] = str(out_dir / "liquidity_network.json")
    written["adaptive_behaviour_json"] = str(out_dir / "adaptive_behaviour_model.json")
    written["knowledge_graph_json"] = str(out_dir / "ecology_knowledge_graph.json")
    written["recommendations_json"] = str(out_dir / "research_recommendations.json")

    return written
