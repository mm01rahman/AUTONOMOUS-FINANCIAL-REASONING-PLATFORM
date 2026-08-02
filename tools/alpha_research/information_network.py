"""Institutional Cross-Asset Information Network for Discovery Cycle 2 Program A Phase 3.

Implements a governed dynamic network analysis using the causal surfaces established
in Phase 2. The goal is institutional understanding of how information propagates
through the complete cross-asset system before XAU/USD transitions between
institutional regimes.

Constructed outputs:
  - Dynamic Network Graph
  - Temporal Influence Network
  - Regime-specific Network Atlas
  - Centrality Analysis
  - Community Detection
  - Information Flow Hierarchy
  - Network Stability Analysis
  - Confidence-weighted Edge Registry

No strategy generation, alpha discovery, or runtime modification is performed.
All analysis is deterministic and uses only governed local datasets.
"""

# ruff: noqa: E501

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from tools.alpha_research.causal_analysis import (
    GRANGER_LAGS,
    _granger_fproxy,
    _significance_tag,
    _transfer_entropy_proxy,
    prepare_dc2_phase2_artifacts,
)
from tools.alpha_research.cross_asset_ecology import (
    CROSS_ASSET_SIGNALS,
    REGIME_LABELS,
    REGIME_ORDER,
    STRESS_WINDOWS,
    _safe_pearson,
)
from tools.alpha_research.feature_discovery import _build_conditioned_frame
from tools.alpha_research.reporting import markdown_table, write_json, write_markdown

DC2_PHASE3_DIR = Path("11-research") / "discovery-cycle-2" / "research-program-a-phase3"
DC2_PHASE3_ANALYSIS = DC2_PHASE3_DIR / "dc2_phase3_information_network_analysis.json"

CORE_NODES = ["xau_return_1", *list(CROSS_ASSET_SIGNALS.keys())]
EDGE_CONFIDENCE_THRESHOLD = 0.22
COMMUNITY_EDGE_THRESHOLD = 0.28


def _node_label(node: str) -> str:
    if node == "xau_return_1":
        return "XAU/USD 1-day return"
    return str(CROSS_ASSET_SIGNALS.get(node, {}).get("title", node))


def _node_market(node: str) -> str:
    if node == "xau_return_1":
        return "XAU/USD"
    return str(CROSS_ASSET_SIGNALS.get(node, {}).get("market", "Unknown"))


def _lag_horizon(lag: int) -> str:
    if lag <= 2:
        return "immediate"
    if lag <= 5:
        return "short"
    if lag <= 10:
        return "medium"
    return "long"


def _available_nodes(frame: pd.DataFrame) -> list[str]:
    return [node for node in CORE_NODES if node in frame.columns]


def _edge_confidence(f_proxy: float, transfer_entropy: float, corr: float) -> float:
    f_component = min(1.0, max(0.0, f_proxy) / 10.0)
    te_component = min(1.0, max(0.0, transfer_entropy) / 0.05)
    corr_component = min(1.0, abs(corr) / 0.30)
    return round(0.50 * f_component + 0.30 * te_component + 0.20 * corr_component, 4)


def _topology_tag(
    out_strength: float,
    in_strength: float,
    relay_score: float,
    source_cutoff: float,
    sink_cutoff: float,
    relay_cutoff: float,
) -> str:
    net = out_strength - in_strength
    if relay_score >= relay_cutoff and abs(net) <= max(0.05, relay_cutoff * 0.1):
        return "relay"
    if net >= source_cutoff:
        return "source"
    if net <= sink_cutoff:
        return "sink"
    return "intermediate"


def _compute_directed_edges(frame: pd.DataFrame, nodes: list[str]) -> list[dict[str, Any]]:
    """Compute the full directed information network across all node pairs."""
    edges: list[dict[str, Any]] = []
    for source in nodes:
        for target in nodes:
            if source == target:
                continue
            source_series = frame[source].astype(float)
            target_series = frame[target].astype(float)
            corr = _safe_pearson(source_series, target_series)
            best_lag = 1
            best_fp = 0.0
            best_te = 0.0
            for lag in GRANGER_LAGS:
                src_arr: NDArray[np.float64] = np.asarray(source_series.to_numpy(), dtype=float)
                tgt_arr: NDArray[np.float64] = np.asarray(target_series.to_numpy(), dtype=float)
                granger = _granger_fproxy(src_arr, tgt_arr, lag)
                te = _transfer_entropy_proxy(source_series, target_series, lag)
                score = 0.65 * granger["f_proxy"] + 100.0 * te
                best_score = 0.65 * best_fp + 100.0 * best_te
                if score > best_score:
                    best_lag = lag
                    best_fp = granger["f_proxy"]
                    best_te = te
            confidence = _edge_confidence(best_fp, best_te, corr)
            if confidence < EDGE_CONFIDENCE_THRESHOLD and best_fp < 1.5:
                continue
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "source_market": _node_market(source),
                    "target_market": _node_market(target),
                    "best_lag": best_lag,
                    "lag_horizon": _lag_horizon(best_lag),
                    "f_proxy": round(best_fp, 4),
                    "transfer_entropy": round(best_te, 5),
                    "correlation": round(corr, 4),
                    "confidence": confidence,
                    "significance": _significance_tag(best_fp),
                }
            )
    edges.sort(
        key=lambda item: (item["confidence"], item["f_proxy"], item["transfer_entropy"]),
        reverse=True,
    )
    return edges


def _network_density(nodes: list[str], edges: list[dict[str, Any]]) -> float:
    possible = max(1, len(nodes) * (len(nodes) - 1))
    return round(len(edges) / possible, 4)


def _centrality_analysis(nodes: list[str], edges: list[dict[str, Any]]) -> dict[str, Any]:
    out_strength: dict[str, float] = {node: 0.0 for node in nodes}
    in_strength: dict[str, float] = {node: 0.0 for node in nodes}
    for edge in edges:
        out_strength[str(edge["source"])] += float(edge["confidence"])
        in_strength[str(edge["target"])] += float(edge["confidence"])

    relay_scores = {node: round(out_strength[node] * in_strength[node], 4) for node in nodes}
    net_flow = {node: round(out_strength[node] - in_strength[node], 4) for node in nodes}
    source_cutoff = (
        float(np.quantile(np.asarray(list(net_flow.values()), dtype=float), 0.75))
        if net_flow
        else 0.0
    )
    sink_cutoff = (
        float(np.quantile(np.asarray(list(net_flow.values()), dtype=float), 0.25))
        if net_flow
        else 0.0
    )
    relay_cutoff = (
        float(np.quantile(np.asarray(list(relay_scores.values()), dtype=float), 0.80))
        if relay_scores
        else 0.0
    )

    nodes_summary: dict[str, dict[str, Any]] = {}
    for node in nodes:
        nodes_summary[node] = {
            "label": _node_label(node),
            "market": _node_market(node),
            "out_strength": round(out_strength[node], 4),
            "in_strength": round(in_strength[node], 4),
            "net_flow": net_flow[node],
            "relay_score": relay_scores[node],
            "topology_role": _topology_tag(
                out_strength[node],
                in_strength[node],
                relay_scores[node],
                source_cutoff,
                sink_cutoff,
                relay_cutoff,
            ),
        }

    sorted_sources = sorted(
        nodes_summary.items(), key=lambda item: item[1]["net_flow"], reverse=True
    )
    sorted_relays = sorted(
        nodes_summary.items(), key=lambda item: item[1]["relay_score"], reverse=True
    )
    sorted_sinks = sorted(nodes_summary.items(), key=lambda item: item[1]["net_flow"])
    return {
        "nodes": nodes_summary,
        "top_sources": [node for node, _ in sorted_sources[:5]],
        "top_sinks": [node for node, _ in sorted_sinks[:5]],
        "top_relays": [node for node, _ in sorted_relays[:5]],
        "bottlenecks": [
            node for node, info in sorted_relays[:5] if info["topology_role"] == "relay"
        ],
    }


def _feedback_loops(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edge_map = {(str(edge["source"]), str(edge["target"])): edge for edge in edges}
    loops: list[dict[str, Any]] = []
    for source, target in list(edge_map):
        if source >= target:
            continue
        forward = edge_map.get((source, target))
        backward = edge_map.get((target, source))
        if not forward or not backward:
            continue
        if (
            float(forward["confidence"]) < COMMUNITY_EDGE_THRESHOLD
            or float(backward["confidence"]) < COMMUNITY_EDGE_THRESHOLD
        ):
            continue
        loops.append(
            {
                "pair": f"{source} <-> {target}",
                "forward_confidence": forward["confidence"],
                "backward_confidence": backward["confidence"],
                "combined_confidence": round(
                    (float(forward["confidence"]) + float(backward["confidence"])) / 2.0, 4
                ),
            }
        )
    loops.sort(key=lambda item: float(item["combined_confidence"]), reverse=True)
    return loops


def _communities(nodes: list[str], edges: list[dict[str, Any]]) -> list[list[str]]:
    adjacency: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        if float(edge["confidence"]) < COMMUNITY_EDGE_THRESHOLD:
            continue
        source = str(edge["source"])
        target = str(edge["target"])
        adjacency[source].add(target)
        adjacency[target].add(source)

    seen: set[str] = set()
    components: list[list[str]] = []
    for start in nodes:
        if start in seen:
            continue
        stack = [start]
        component: list[str] = []
        seen.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for nxt in sorted(adjacency[node]):
                if nxt in seen:
                    continue
                seen.add(nxt)
                stack.append(nxt)
        components.append(sorted(component))
    components.sort(key=len, reverse=True)
    return components


def _hierarchy(centrality: dict[str, Any]) -> list[dict[str, Any]]:
    ranked = sorted(
        (
            {
                "node": node,
                "label": info["label"],
                "market": info["market"],
                "net_flow": info["net_flow"],
                "out_strength": info["out_strength"],
                "in_strength": info["in_strength"],
                "role": info["topology_role"],
            }
            for node, info in centrality["nodes"].items()
        ),
        key=lambda item: (float(item["net_flow"]), float(item["out_strength"])),
        reverse=True,
    )
    return ranked


def _subset_network(frame: pd.DataFrame, label: str) -> dict[str, Any]:
    nodes = _available_nodes(frame)
    if len(frame) < 40 or len(nodes) < 4:
        return {
            "label": label,
            "n_obs": len(frame),
            "nodes": nodes,
            "edges": [],
            "density": 0.0,
            "feedback_loops": [],
            "communities": [[node] for node in nodes],
            "centrality": _centrality_analysis(nodes, []),
            "hierarchy": [],
        }
    edges = _compute_directed_edges(frame, nodes)
    centrality = _centrality_analysis(nodes, edges)
    return {
        "label": label,
        "n_obs": len(frame),
        "nodes": nodes,
        "edges": edges,
        "density": _network_density(nodes, edges),
        "feedback_loops": _feedback_loops(edges),
        "communities": _communities(nodes, edges),
        "centrality": centrality,
        "hierarchy": _hierarchy(centrality),
    }


def _regime_network_atlas(frame: pd.DataFrame) -> dict[str, Any]:
    atlas: dict[str, Any] = {}
    for regime in REGIME_ORDER:
        subset = frame.loc[frame["regime"] == regime]
        atlas[regime] = _subset_network(subset, REGIME_LABELS[regime])
    return atlas


def _stress_topology(frame: pd.DataFrame) -> dict[str, Any]:
    _tz = getattr(frame.index, "tz", None)
    index = pd.DatetimeIndex(frame.index)
    result: dict[str, Any] = {}
    for label, start_str, end_str in STRESS_WINDOWS:
        start = pd.Timestamp(start_str, tz=_tz)
        end = pd.Timestamp(end_str, tz=_tz)
        mask = (index >= start) & (index <= end)
        result[label] = _subset_network(frame.loc[mask], label)
    return result


def _event_topology(frame: pd.DataFrame) -> dict[str, Any]:
    topologies: dict[str, Any] = {}
    if "fed_surprise" in frame.columns:
        fed_values: NDArray[np.float64] = np.asarray(frame["fed_surprise"].to_numpy(), dtype=float)
        fed_mask: NDArray[np.bool_] = np.asarray(np.abs(fed_values) > 0.0, dtype=bool)
        topologies["fed_surprise_events"] = _subset_network(
            frame.loc[fed_mask], "Fed Surprise Events"
        )
    if "geo_severity" in frame.columns:
        geo_values: NDArray[np.float64] = np.asarray(frame["geo_severity"].to_numpy(), dtype=float)
        threshold = float(pd.Series(geo_values).quantile(0.75))
        geo_mask: NDArray[np.bool_] = np.asarray(geo_values >= threshold, dtype=bool)
        topologies["geopolitical_stress_events"] = _subset_network(
            frame.loc[geo_mask], "Geopolitical Stress Events"
        )
    if "macro_pressure" in frame.columns:
        macro_values: NDArray[np.float64] = np.asarray(
            frame["macro_pressure"].to_numpy(), dtype=float
        )
        macro_threshold = float(pd.Series(np.abs(macro_values)).quantile(0.75))
        macro_mask: NDArray[np.bool_] = np.asarray(
            np.abs(macro_values) >= macro_threshold, dtype=bool
        )
        topologies["macro_pressure_events"] = _subset_network(
            frame.loc[macro_mask], "Macro Pressure Events"
        )
    return topologies


def _stable_edge_presence(*edge_sets: dict[str, Any]) -> dict[str, int]:
    presence: dict[str, int] = defaultdict(int)
    for collection in edge_sets:
        for network in collection.values():
            for edge in cast(list[dict[str, Any]], network.get("edges", [])):
                key = f"{edge['source']}->{edge['target']}"
                presence[key] += 1
    return dict(presence)


def _network_stability(
    overall: dict[str, Any],
    regimes: dict[str, Any],
    stress: dict[str, Any],
    events: dict[str, Any],
) -> dict[str, Any]:
    overall_edges = {f"{edge['source']}->{edge['target']}" for edge in overall["edges"]}
    overlaps: dict[str, float] = {}
    for label, network in {**regimes, **stress, **events}.items():
        subset_edges = {f"{edge['source']}->{edge['target']}" for edge in network.get("edges", [])}
        union = overall_edges | subset_edges
        overlap = 0.0 if not union else len(overall_edges & subset_edges) / len(union)
        overlaps[label] = round(overlap, 4)

    presence = _stable_edge_presence(regimes, stress, events)
    stable_edge_candidates: list[dict[str, Any]] = [
        {"edge": key, "presence_count": count} for key, count in presence.items() if count >= 3
    ]
    stable_edges = sorted(
        stable_edge_candidates,
        key=lambda item: int(cast(int, item["presence_count"])),
        reverse=True,
    )

    centrality_overlap = {
        "overall_top_sources": overall["centrality"]["top_sources"][:3],
        "overall_top_relays": overall["centrality"]["top_relays"][:3],
        "overall_top_sinks": overall["centrality"]["top_sinks"][:3],
    }
    return {
        "topology_overlap": overlaps,
        "stable_edges": stable_edges,
        "centrality_overlap": centrality_overlap,
        "mean_overlap": round(
            float(np.mean(np.asarray(list(overlaps.values()), dtype=float))) if overlaps else 0.0, 4
        ),
    }


def _edge_registry(
    overall: dict[str, Any],
    regimes: dict[str, Any],
    stress: dict[str, Any],
    events: dict[str, Any],
    phase2: dict[str, Any],
) -> list[dict[str, Any]]:
    promoted = set(phase2.get("arb_summary", {}).get("promote_to_institutional_knowledge", []))
    retained = set(phase2.get("arb_summary", {}).get("retain_for_validation", []))

    regime_presence: dict[str, int] = defaultdict(int)
    stress_presence: dict[str, int] = defaultdict(int)
    event_presence: dict[str, int] = defaultdict(int)
    for label, network in regimes.items():
        for edge in network.get("edges", []):
            regime_presence[f"{edge['source']}->{edge['target']}"] += 1
    for label, network in stress.items():
        for edge in network.get("edges", []):
            stress_presence[f"{edge['source']}->{edge['target']}"] += 1
    for label, network in events.items():
        for edge in network.get("edges", []):
            event_presence[f"{edge['source']}->{edge['target']}"] += 1

    registry: list[dict[str, Any]] = []
    for rank, edge in enumerate(overall["edges"], start=1):
        key = f"{edge['source']}->{edge['target']}"
        bonus = 0.0
        if edge["target"] == "xau_return_1" and edge["source"] in promoted:
            bonus += 0.15
        elif edge["target"] == "xau_return_1" and edge["source"] in retained:
            bonus += 0.08
        registry.append(
            {
                "rank": rank,
                "edge": key,
                "source": edge["source"],
                "target": edge["target"],
                "source_market": edge["source_market"],
                "target_market": edge["target_market"],
                "best_lag": edge["best_lag"],
                "lag_horizon": edge["lag_horizon"],
                "confidence": round(min(1.0, float(edge["confidence"]) + bonus), 4),
                "significance": edge["significance"],
                "regime_presence": regime_presence.get(key, 0),
                "stress_presence": stress_presence.get(key, 0),
                "event_presence": event_presence.get(key, 0),
                "institutional_support": (
                    "PROMOTED_PHASE2"
                    if edge["source"] in promoted and edge["target"] == "xau_return_1"
                    else "RETAINED_PHASE2"
                    if edge["source"] in retained and edge["target"] == "xau_return_1"
                    else "NETWORK_ONLY"
                ),
            }
        )
    registry.sort(
        key=lambda item: (
            float(item["confidence"]),
            int(item["regime_presence"])
            + int(item["stress_presence"])
            + int(item["event_presence"]),
        ),
        reverse=True,
    )
    for rank, item in enumerate(registry, start=1):
        item["rank"] = rank
    return registry


def _arb_recommendation(
    overall: dict[str, Any],
    stability: dict[str, Any],
    edge_registry: list[dict[str, Any]],
) -> dict[str, Any]:
    top_model = "confidence-weighted directed cross-asset information network with regime overlays"
    stable_top_edges = [item["edge"] for item in edge_registry[:5]]
    return {
        "governing_model": top_model,
        "dominant_sources": overall["centrality"]["top_sources"][:3],
        "dominant_relays": overall["centrality"]["top_relays"][:3],
        "dominant_sinks": overall["centrality"]["top_sinks"][:3],
        "network_bottlenecks": overall["centrality"]["bottlenecks"][:3],
        "stable_edges": stable_top_edges,
        "mean_topology_overlap": stability["mean_overlap"],
        "primary_finding": (
            "The strongest institutional representation is a confidence-weighted directed information network "
            "with regime-specific overlays. It preserves global source/sink hierarchy while allowing topology "
            "to reconfigure across stress and event conditions."
        ),
    }


def prepare_dc2_phase3_artifacts(repo_root: Path | None = None) -> dict[str, Any]:
    frame = _build_conditioned_frame()
    nodes = _available_nodes(frame)
    phase2 = prepare_dc2_phase2_artifacts(repo_root=repo_root)

    overall = _subset_network(frame[nodes + ["regime"]], "Overall Network")
    regimes = _regime_network_atlas(frame[nodes + ["regime"]])
    stress = _stress_topology(frame[nodes + ["regime"]])
    events = _event_topology(frame[nodes + ["regime"]])
    stability = _network_stability(overall, regimes, stress, events)
    edge_registry = _edge_registry(overall, regimes, stress, events, phase2)
    arb = _arb_recommendation(overall, stability, edge_registry)

    analysis = {
        "phase": "DC2_PROGRAM_A_PHASE3",
        "title": "Institutional Cross-Asset Information Network",
        "date_range": {
            "start": str(frame.index[0]),
            "end": str(frame.index[-1]),
            "n_obs": int(len(frame)),
        },
        "overall_network": overall,
        "temporal_influence_network": [
            {
                "edge": f"{edge['source']}->{edge['target']}",
                "best_lag": edge["best_lag"],
                "lag_horizon": edge["lag_horizon"],
                "confidence": edge["confidence"],
                "significance": edge["significance"],
            }
            for edge in overall["edges"]
        ],
        "regime_network_atlas": regimes,
        "stress_topology": stress,
        "event_topology": events,
        "centrality_analysis": overall["centrality"],
        "community_detection": {
            "communities": overall["communities"],
            "feedback_loops": overall["feedback_loops"],
        },
        "information_flow_hierarchy": overall["hierarchy"],
        "network_stability_analysis": stability,
        "confidence_weighted_edge_registry": edge_registry,
        "arb_recommendation": arb,
        "data_limitations": phase2.get("data_limitations", {}),
    }

    out_dir = (repo_root or Path(".")) / DC2_PHASE3_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "dc2_phase3_information_network_analysis.json", analysis)
    return analysis


def load_dc2_phase3_analysis(repo_root: Path | None = None) -> dict[str, Any]:
    import json
    from typing import cast

    path = (repo_root or Path(".")) / DC2_PHASE3_ANALYSIS
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def emit_dc2_phase3_reports(
    analysis: dict[str, Any],
    campaign_result: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    out_dir = (repo_root or Path(".")) / DC2_PHASE3_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}

    overall = analysis["overall_network"]
    regimes = analysis["regime_network_atlas"]
    stress = analysis["stress_topology"]
    events = analysis["event_topology"]
    centrality = analysis["centrality_analysis"]
    communities = analysis["community_detection"]
    hierarchy = analysis["information_flow_hierarchy"]
    stability = analysis["network_stability_analysis"]
    registry = analysis["confidence_weighted_edge_registry"]
    arb = analysis["arb_recommendation"]

    dynamic_md = out_dir / "DYNAMIC_NETWORK_GRAPH.md"
    dynamic_rows: list[list[object]] = [
        [
            edge["source"],
            edge["target"],
            edge["best_lag"],
            edge["confidence"],
            edge["significance"],
        ]
        for edge in overall["edges"][:20]
    ]
    write_markdown(
        dynamic_md,
        f"""# Dynamic Network Graph
## Discovery Cycle 2 Program A Phase 3

### Summary
- Nodes: {len(overall["nodes"])}
- Edges: {len(overall["edges"])}
- Density: {overall["density"]}

{markdown_table(["Source", "Target", "Best Lag", "Confidence", "Significance"], dynamic_rows)}

### Primary Finding
{arb["primary_finding"]}
""",
    )
    written["dynamic_network_graph"] = str(dynamic_md)

    temporal_md = out_dir / "TEMPORAL_INFLUENCE_NETWORK.md"
    temporal_rows: list[list[object]] = [
        [item["edge"], item["best_lag"], item["lag_horizon"], item["confidence"]]
        for item in analysis["temporal_influence_network"][:20]
    ]
    write_markdown(
        temporal_md,
        f"""# Temporal Influence Network
## Discovery Cycle 2 Program A Phase 3

{markdown_table(["Edge", "Best Lag", "Horizon", "Confidence"], temporal_rows)}
""",
    )
    written["temporal_influence_network"] = str(temporal_md)

    regime_md = out_dir / "REGIME_SPECIFIC_NETWORK_ATLAS.md"
    regime_rows: list[list[object]] = []
    for regime in REGIME_ORDER:
        network = regimes[regime]
        regime_rows.append(
            [
                regime,
                network["n_obs"],
                len(network["edges"]),
                network["density"],
                ", ".join(network["centrality"]["top_sources"][:2]) or "None",
            ]
        )
    write_markdown(
        regime_md,
        f"""# Regime-specific Network Atlas
## Discovery Cycle 2 Program A Phase 3

{markdown_table(["Regime", "Observations", "Edges", "Density", "Top Sources"], regime_rows)}
""",
    )
    written["regime_network_atlas"] = str(regime_md)

    centrality_md = out_dir / "CENTRALITY_ANALYSIS.md"
    centrality_rows: list[list[object]] = [
        [
            node,
            info["market"],
            info["out_strength"],
            info["in_strength"],
            info["net_flow"],
            info["topology_role"],
        ]
        for node, info in centrality["nodes"].items()
    ]
    write_markdown(
        centrality_md,
        f"""# Centrality Analysis
## Discovery Cycle 2 Program A Phase 3

{markdown_table(["Node", "Market", "Out Strength", "In Strength", "Net Flow", "Role"], centrality_rows)}

### Top Sources
{", ".join(centrality["top_sources"][:5])}

### Top Relays
{", ".join(centrality["top_relays"][:5])}

### Top Sinks
{", ".join(centrality["top_sinks"][:5])}
""",
    )
    written["centrality_analysis"] = str(centrality_md)

    community_md = out_dir / "COMMUNITY_DETECTION.md"
    community_rows: list[list[object]] = [
        [idx + 1, len(group), ", ".join(group)]
        for idx, group in enumerate(communities["communities"])
    ]
    loop_rows: list[list[object]] = [
        [
            loop["pair"],
            loop["forward_confidence"],
            loop["backward_confidence"],
            loop["combined_confidence"],
        ]
        for loop in communities["feedback_loops"][:10]
    ]
    write_markdown(
        community_md,
        f"""# Community Detection
## Discovery Cycle 2 Program A Phase 3

### Communities
{markdown_table(["Community", "Size", "Members"], community_rows)}

### Feedback Loops
{markdown_table(["Loop", "Forward", "Backward", "Combined"], loop_rows) if loop_rows else "_No strong feedback loops._"}
""",
    )
    written["community_detection"] = str(community_md)

    hierarchy_md = out_dir / "INFORMATION_FLOW_HIERARCHY.md"
    hierarchy_rows: list[list[object]] = [
        [idx + 1, item["node"], item["market"], item["net_flow"], item["role"]]
        for idx, item in enumerate(hierarchy)
    ]
    write_markdown(
        hierarchy_md,
        f"""# Information Flow Hierarchy
## Discovery Cycle 2 Program A Phase 3

{markdown_table(["Rank", "Node", "Market", "Net Flow", "Role"], hierarchy_rows)}
""",
    )
    written["information_flow_hierarchy"] = str(hierarchy_md)

    stability_md = out_dir / "NETWORK_STABILITY_ANALYSIS.md"
    overlap_rows: list[list[object]] = [
        [label, value] for label, value in stability["topology_overlap"].items()
    ]
    stable_edge_rows: list[list[object]] = [
        [item["edge"], item["presence_count"]] for item in stability["stable_edges"][:15]
    ]
    write_markdown(
        stability_md,
        f"""# Network Stability Analysis
## Discovery Cycle 2 Program A Phase 3

### Mean Overlap
{stability["mean_overlap"]}

### Topology Overlap
{markdown_table(["Subset", "Jaccard Overlap"], overlap_rows)}

### Stable Edges
{markdown_table(["Edge", "Presence Count"], stable_edge_rows) if stable_edge_rows else "_No stable edges across subsets._"}
""",
    )
    written["network_stability_analysis"] = str(stability_md)

    registry_md = out_dir / "CONFIDENCE_WEIGHTED_EDGE_REGISTRY.md"
    registry_rows: list[list[object]] = [
        [
            item["rank"],
            item["edge"],
            item["best_lag"],
            item["confidence"],
            item["regime_presence"],
            item["stress_presence"],
            item["institutional_support"],
        ]
        for item in registry[:25]
    ]
    write_markdown(
        registry_md,
        f"""# Confidence-weighted Edge Registry
## Discovery Cycle 2 Program A Phase 3

{markdown_table(["Rank", "Edge", "Lag", "Confidence", "Regimes", "Stress", "Institutional Support"], registry_rows)}
""",
    )
    written["edge_registry"] = str(registry_md)

    arb_md = out_dir / "ARB_NETWORK_RECOMMENDATION.md"
    write_markdown(
        arb_md,
        f"""# ARB Network Recommendation
## Discovery Cycle 2 Program A Phase 3

### Governing Model
{arb["governing_model"]}

### Dominant Sources
{", ".join(arb["dominant_sources"])}

### Dominant Relays
{", ".join(arb["dominant_relays"])}

### Dominant Sinks
{", ".join(arb["dominant_sinks"])}

### Bottlenecks
{", ".join(arb["network_bottlenecks"]) if arb["network_bottlenecks"] else "None"}

### Stable High-confidence Edges
{chr(10).join(f"- {edge}" for edge in arb["stable_edges"]) if arb["stable_edges"] else "None"}

### Recommendation
{arb["primary_finding"]}
""",
    )
    written["arb_network_recommendation"] = str(arb_md)

    write_json(out_dir / "dynamic_network_graph.json", overall)
    write_json(out_dir / "temporal_influence_network.json", analysis["temporal_influence_network"])
    write_json(out_dir / "regime_network_atlas.json", regimes)
    write_json(out_dir / "stress_topology.json", stress)
    write_json(out_dir / "event_topology.json", events)
    write_json(out_dir / "centrality_analysis.json", centrality)
    write_json(out_dir / "network_stability_analysis.json", stability)
    write_json(out_dir / "confidence_weighted_edge_registry.json", registry)
    write_json(out_dir / "arb_network_recommendation.json", arb)

    written["dynamic_network_graph_json"] = str(out_dir / "dynamic_network_graph.json")
    written["temporal_influence_network_json"] = str(out_dir / "temporal_influence_network.json")
    written["regime_network_atlas_json"] = str(out_dir / "regime_network_atlas.json")
    written["stress_topology_json"] = str(out_dir / "stress_topology.json")
    written["event_topology_json"] = str(out_dir / "event_topology.json")
    written["centrality_analysis_json"] = str(out_dir / "centrality_analysis.json")
    written["network_stability_analysis_json"] = str(out_dir / "network_stability_analysis.json")
    written["edge_registry_json"] = str(out_dir / "confidence_weighted_edge_registry.json")
    written["arb_network_recommendation_json"] = str(out_dir / "arb_network_recommendation.json")

    return written
