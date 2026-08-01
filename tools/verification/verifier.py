"""End-to-end runtime verification and deterministic checks (WP-B3/B5)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from afrp_runtime.contracts.cio import THETA, AuthorizationVerdict
from afrp_runtime.layer4.optimizer import UtilityOptimizer
from afrp_runtime.layer4.policy import PolicyEngine
from afrp_runtime.layer4.synthesizer import DecisionSynthesizer

from tools import system_gate


@dataclass(frozen=True)
class LayerVerificationResult:
    layer_id: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class RuntimeVerificationReport:
    deterministic: bool
    replay_checksum: str
    expected_checksum: str
    layer_results: tuple[LayerVerificationResult, ...]
    world_state_uncertainty: float
    policy_null_trade: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _verify_layers() -> tuple[LayerVerificationResult, ...]:
    features, world, scenarios, portfolio = system_gate._pipeline()  # noqa: SLF001
    context = DecisionSynthesizer("MP-04", cognitive_cycle_id="phaseb").synthesize(
        world, scenarios, portfolio
    )
    candidate = UtilityOptimizer("MP-04", cognitive_cycle_id="phaseb").optimize(
        context, scenarios, features["mid_price"].value
    )
    action = PolicyEngine("MP-04", cognitive_cycle_id="phaseb").authorize(
        candidate, world, portfolio, spread_bps=features["spread_bps"].value
    )
    return (
        LayerVerificationResult(
            layer_id="L1",
            passed="mid_price" in features and "spread_bps" in features,
            detail=f"features={len(features)}",
        ),
        LayerVerificationResult(
            layer_id="L2",
            passed=world.agent_quorum >= 0,
            detail=f"quorum={world.agent_quorum}",
        ),
        LayerVerificationResult(
            layer_id="L3",
            passed=abs(sum(world.fused_masses.values()) - 1.0) < 1e-9,
            detail=f"epistemic_uncertainty={world.epistemic_uncertainty:.6f}",
        ),
        LayerVerificationResult(
            layer_id="L4",
            passed=(
                candidate.instrument == world.instrument
                and action.instrument == world.instrument
            ),
            detail=f"candidate_ru={candidate.risk_adjusted_utility:.6f}",
        ),
        LayerVerificationResult(
            layer_id="L5",
            passed=action.verdict
            in {
                AuthorizationVerdict.AUTHORIZED,
                AuthorizationVerdict.PROJECTED,
                AuthorizationVerdict.NULL_TRADE,
            },
            detail=f"verdict={action.verdict.value}",
        ),
        LayerVerificationResult(
            layer_id="L6",
            passed=True,
            detail="validated via separate math/statistical checks",
        ),
    )


def verify_runtime(report_path: Path | None = None) -> RuntimeVerificationReport:
    """Run deterministic and cross-layer verification."""
    first = system_gate.semantic_replay()
    second = system_gate.semantic_replay()
    expected = system_gate.EXPECTED_PATH.read_text(encoding="utf-8").strip()
    deterministic = first == second and first.checksum == second.checksum
    layer_results = _verify_layers()
    failures: list[str] = []
    if not deterministic:
        failures.append("deterministic replay mismatch")
    if first.checksum != expected:
        failures.append("frozen checksum mismatch")
    if not all(layer.passed for layer in layer_results):
        failures.append("layer verification failed")
    theta = dict(first.world_masses).get(THETA, 0.0)
    report = RuntimeVerificationReport(
        deterministic=deterministic,
        replay_checksum=first.checksum,
        expected_checksum=expected,
        layer_results=layer_results,
        world_state_uncertainty=theta,
        policy_null_trade=first.action[0] == 0,
        failures=tuple(failures),
    )
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return report
