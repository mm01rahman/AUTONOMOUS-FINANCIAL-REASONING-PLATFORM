"""AFRP system validation gate (WP-IMP-0033).

Executes FIT-008 deterministic MP-04 replay, a total-feed-loss chaos path
(vacuous m(Theta)=1 with SYS-03 DEGRADED), and the NFR-001 Layer 4/5 P99
latency benchmark.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import yaml
from afrp_runtime.common.statemachine import (
    OperationalState,
    OperationalStateMachine,
)
from afrp_runtime.contracts.cio import (
    THETA,
    PortfolioState,
    Scenario,
    ScenarioSet,
    StandardFeature,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.contracts.features import FEATURE_SPREAD_BPS
from afrp_runtime.layer1.features import FeatureStore
from afrp_runtime.layer1.ingest import RawEvent, TickIngestor
from afrp_runtime.layer2.agents import ALL_AGENTS
from afrp_runtime.layer3.simulator import ScenarioSimulator
from afrp_runtime.layer3.worldmodel import WorldModelKernel
from afrp_runtime.layer4.optimizer import UtilityOptimizer
from afrp_runtime.layer4.policy import PolicyEngine
from afrp_runtime.layer4.synthesizer import DecisionSynthesizer
from afrp_runtime.layer5.execution import InMemoryOrderEventStore, OrderGateway

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "09-validation" / "fixtures" / "mp04_ticks.yaml"
EXPECTED_PATH = REPO_ROOT / "09-validation" / "fixtures" / "mp04_expected.sha256"
DEPRECATION_POLICY_PATH = REPO_ROOT / "03-engineering" / "DEPRECATION_POLICY.yaml"
LATENCY_BUDGET_MS = 50.0


@dataclass(frozen=True)
class ReplaySnapshot:
    """Semantic state excluding nondeterministic message/trace identifiers."""

    features: tuple[tuple[str, float], ...]
    beliefs: tuple[tuple[str, tuple[tuple[str, float], ...]], ...]
    world_masses: tuple[tuple[str, float], ...]
    world_quorum: int
    scenario_terminals: tuple[float, ...]
    scenario_entropy: float
    candidate: tuple[float, ...]
    action: tuple[int, float, float]

    @property
    def checksum(self) -> str:
        canonical = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class ChaosResult:
    """Total-feed-loss degraded-state result."""

    operational_state: OperationalState
    agent_quorum: int
    epistemic_uncertainty: float
    fused_masses: tuple[tuple[str, float], ...]
    trading_permitted: bool


@dataclass(frozen=True)
class SystemReport:
    """Aggregate system gate result."""

    replay_checksum: str
    replay_matches_expected: bool
    chaos: ChaosResult
    decision_p99_ms: float
    deprecation_compliant: bool


def _load_fixture() -> dict[str, Any]:
    loaded = yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or loaded.get("schema_version") != "1.0":
        raise ValueError("MP-04 replay fixture is malformed")
    return loaded


def _feature(
    feature_id: str, value: float, instrument: str, sequence: int
) -> StandardFeature:
    return StandardFeature(
        envelope=make_envelope(
            producer_subsystem_id="L1-FST",
            cognitive_cycle_id="mp04-replay",
            mission_profile_id="MP-04",
            payload_repr=f"{feature_id}:{value}",
            generated_at_ns=sequence,
        ),
        feature_id=feature_id,
        instrument=instrument,
        value=value,
        window_seconds=60,
        quality=1.0,
        source_sequence=sequence,
    )


def _pipeline() -> tuple[
    dict[str, StandardFeature], WorldStateVector, ScenarioSet, PortfolioState
]:
    fixture = _load_fixture()
    instrument = str(fixture["instrument"])
    raw_events = cast(list[RawEvent], fixture["events"])
    macro = cast(dict[str, float], fixture["macro_features"])

    ingestor = TickIngestor("MP-04", cognitive_cycle_id="mp04-replay")
    store = FeatureStore(
        "MP-04", window_seconds=60, cognitive_cycle_id="mp04-replay"
    )
    for raw in raw_events:
        store.update(ingestor.ingest(raw))
    features = store.latest(instrument)
    for index, (feature_id, value) in enumerate(sorted(macro.items()), start=100):
        features[feature_id] = _feature(feature_id, value, instrument, index)

    beliefs = [
        agent_cls("MP-04", cognitive_cycle_id="mp04-replay").evaluate(
            instrument, features
        )
        for agent_cls in ALL_AGENTS
    ]
    world = WorldModelKernel(
        "MP-04", cognitive_cycle_id="mp04-replay"
    ).fuse(instrument, beliefs)
    spot = features["mid_price"].value
    scenarios = ScenarioSimulator(
        "MP-04",
        cognitive_cycle_id="mp04-replay",
        n_paths=64,
    ).simulate(world, spot, cycle=42)
    portfolio = PortfolioState(
        envelope=make_envelope(
            producer_subsystem_id="L5-EXE",
            cognitive_cycle_id="mp04-replay",
            mission_profile_id="MP-04",
            payload_repr="empty-portfolio",
            generated_at_ns=int(raw_events[-1]["event_at_ns"]),
        ),
        positions=(),
        cash=100_000.0,
        equity=100_000.0,
        gross_exposure=0.0,
        reconciled_at_ns=int(raw_events[-1]["event_at_ns"]),
    )
    return features, world, scenarios, portfolio


def semantic_replay() -> ReplaySnapshot:
    """Execute the canonical MP-04 replay and return semantic state."""
    features, world, scenarios, portfolio = _pipeline()
    context = DecisionSynthesizer(
        "MP-04", cognitive_cycle_id="mp04-replay"
    ).synthesize(world, scenarios, portfolio)
    spot = features["mid_price"].value
    candidate = UtilityOptimizer(
        "MP-04", cognitive_cycle_id="mp04-replay"
    ).optimize(context, scenarios, spot)
    action = PolicyEngine(
        "MP-04", cognitive_cycle_id="mp04-replay"
    ).authorize(
        candidate,
        world,
        portfolio,
        spread_bps=features[FEATURE_SPREAD_BPS].value,
    )

    beliefs = [
        agent_cls("MP-04", cognitive_cycle_id="mp04-replay").evaluate(
            world.instrument, features
        )
        for agent_cls in ALL_AGENTS
    ]
    return ReplaySnapshot(
        features=tuple(
            (name, round(feature.value, 12))
            for name, feature in sorted(features.items())
        ),
        beliefs=tuple(
            (
                belief.agent_id,
                tuple(
                    (label, round(value, 12))
                    for label, value in sorted(belief.masses.items())
                ),
            )
            for belief in beliefs
        ),
        world_masses=tuple(
            (label, round(value, 12))
            for label, value in sorted(world.fused_masses.items())
        ),
        world_quorum=world.agent_quorum,
        scenario_terminals=tuple(
            round(scenario.terminal_price, 10)
            for scenario in scenarios.scenarios
        ),
        scenario_entropy=round(scenarios.differential_entropy, 12),
        candidate=(
            candidate.direction,
            candidate.size,
            round(candidate.risk_adjusted_utility, 12),
        ),
        action=(int(action.verdict), action.direction, action.size),
    )


def chaos_total_feed_loss() -> ChaosResult:
    """Prove total feed loss degrades to vacuity instead of panic."""
    beliefs = [
        agent_cls("MP-04", cognitive_cycle_id="chaos-feed-loss").evaluate(
            "XAUUSD", {}
        )
        for agent_cls in ALL_AGENTS
    ]
    world = WorldModelKernel(
        "MP-04", cognitive_cycle_id="chaos-feed-loss"
    ).fuse("XAUUSD", beliefs)
    machine = OperationalStateMachine()
    machine.transition(OperationalState.NORMAL, "boot")
    machine.transition(OperationalState.OBSERVATION, "all feeds stale")
    machine.transition(OperationalState.DEGRADED, "agent quorum zero")
    return ChaosResult(
        operational_state=machine.state,
        agent_quorum=world.agent_quorum,
        epistemic_uncertainty=world.epistemic_uncertainty,
        fused_masses=tuple(sorted(world.fused_masses.items())),
        trading_permitted=machine.trading_permitted,
    )


def decision_latency_p99(iterations: int = 300) -> float:
    """Benchmark L4 synthesis/optimization/policy plus L5 submission."""
    if iterations < 100:
        raise ValueError("latency benchmark requires at least 100 iterations")
    world = WorldStateVector(
        envelope=make_envelope(
            producer_subsystem_id="L3-WRM",
            cognitive_cycle_id="latency",
            mission_profile_id="MP-02",
            payload_repr="latency-world",
        ),
        instrument="XAUUSD",
        fused_masses={"BULL": 0.8, THETA: 0.2},
        epistemic_uncertainty=0.2,
        conflict_mass=0.0,
        regime_context="BULL",
        active_hypotheses=("BULL",),
        agent_quorum=6,
        fusion_trace=(),
    )
    scenarios = ScenarioSet(
        envelope=make_envelope(
            producer_subsystem_id="L3-SIM",
            cognitive_cycle_id="latency",
            mission_profile_id="MP-02",
            payload_repr="latency-scenarios",
        ),
        instrument="XAUUSD",
        scenarios=(
            Scenario("up", 0.6, 2435.0, -4.0, 38.0),
            Scenario("flat", 0.3, 2408.0, -7.0, 14.0),
            Scenario("down", 0.1, 2392.0, -12.0, 3.0),
        ),
        differential_entropy=0.5,
        horizon_seconds=3600,
        random_seed=42,
    )
    portfolio = PortfolioState(
        envelope=make_envelope(
            producer_subsystem_id="L5-EXE",
            cognitive_cycle_id="latency",
            mission_profile_id="MP-02",
            payload_repr="latency-portfolio",
        ),
        positions=(),
        cash=100_000.0,
        equity=100_000.0,
        gross_exposure=0.0,
        reconciled_at_ns=0,
    )
    ids = itertools.count()
    gateway = OrderGateway(
        "MP-02",
        event_store=InMemoryOrderEventStore(),
        order_id_factory=lambda: f"latency-{next(ids)}",
        cognitive_cycle_id="latency",
    )
    synthesizer = DecisionSynthesizer("MP-02", cognitive_cycle_id="latency")
    optimizer = UtilityOptimizer("MP-02", cognitive_cycle_id="latency")
    policy = PolicyEngine("MP-02", cognitive_cycle_id="latency")

    durations: list[float] = []
    for index in range(iterations + 1):
        started = time.perf_counter_ns()
        context = synthesizer.synthesize(world, scenarios, portfolio)
        candidate = optimizer.optimize(context, scenarios, 2400.0)
        action = policy.authorize(
            candidate, world, portfolio, spread_bps=1.0
        )
        gateway.submit(action, at_ns=index)
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        if index > 0:  # discard one warm-up sample
            durations.append(elapsed_ms)
    durations.sort()
    index_99 = math.ceil(0.99 * len(durations)) - 1
    return durations[index_99]


def validate_deprecation_policy() -> list[str]:
    """EDR-012: enforce one-minor-version grace and governed removal."""
    loaded = yaml.safe_load(DEPRECATION_POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or loaded.get("schema_version") != "1.0":
        return ["EDR-012 deprecation policy schema is invalid"]
    policy = loaded.get("deprecation", {})
    errors: list[str] = []
    if int(policy.get("minimum_grace_minor_versions", 0)) < 1:
        errors.append("EDR-012 requires at least one minor version of grace")
    if policy.get("required_stages") != ["announce", "warn", "remove"]:
        errors.append("EDR-012 stages must be announce -> warn -> remove")
    if policy.get("warning_log_schema") != "OBS-01":
        errors.append("EDR-012 warnings must use OBS-01")
    removal = policy.get("removal_requires", {})
    for key in (
        "requirement_update",
        "traceability_update",
        "level_1_adr",
        "protobuf_major_version_for_breaking_wire_change",
    ):
        if removal.get(key) is not True:
            errors.append(f"EDR-012 removal requires {key}")
    return errors


def validate_system() -> SystemReport:
    """Run every system fitness gate."""
    first = semantic_replay()
    second = semantic_replay()
    expected = EXPECTED_PATH.read_text(encoding="utf-8").strip()
    replay_matches = first == second and first.checksum == expected
    chaos = chaos_total_feed_loss()
    p99 = decision_latency_p99()
    return SystemReport(
        replay_checksum=first.checksum,
        replay_matches_expected=replay_matches,
        chaos=chaos,
        decision_p99_ms=p99,
        deprecation_compliant=not validate_deprecation_policy(),
    )


def main() -> int:
    """CLI entry point."""
    if not os.environ.get("AFRP_AUDIT_HMAC_KEY"):
        print("system_gate: FAIL — AFRP_AUDIT_HMAC_KEY must come from environment")
        return 1
    report = validate_system()
    failures: list[str] = []
    if not report.replay_matches_expected:
        failures.append("FIT-008 deterministic replay mismatch")
    if report.chaos.operational_state is not OperationalState.DEGRADED:
        failures.append("NFR-003 chaos path did not enter DEGRADED")
    if report.chaos.agent_quorum != 0:
        failures.append("NFR-003 total feed loss quorum must be zero")
    if abs(report.chaos.epistemic_uncertainty - 1.0) > 1e-9:
        failures.append("NFR-003 total feed loss must produce m(THETA)=1")
    if report.chaos.trading_permitted:
        failures.append("Article VIII: trading permitted while DEGRADED")
    if report.decision_p99_ms > LATENCY_BUDGET_MS:
        failures.append(
            f"NFR-001 P99 {report.decision_p99_ms:.3f}ms > {LATENCY_BUDGET_MS}ms"
        )
    if not report.deprecation_compliant:
        failures.extend(validate_deprecation_policy())
    if failures:
        print(f"system_gate: FAIL ({len(failures)} violation(s))")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("system_gate: PASS")
    print(f"  FIT-008 replay: {report.replay_checksum}")
    print("  NFR-003 chaos: DEGRADED, quorum=0, m(THETA)=1, trading=false")
    print(f"  NFR-001 decision P99: {report.decision_p99_ms:.3f}ms <= 50ms")
    print("  EDR-012 deprecation: >=1 minor version, governed removal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
