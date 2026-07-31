"""L3-SIM — Equilibrium World Model scenario simulator (SLS-301, WP-IMP-0025).

Samples price trajectories under the belief-conditioned measure, constrains
them to the equilibrium manifold ℰ (MATH-001 §3):

    Σ_EWM(τ) = P_raw(τ | S_t, a) / Z   if τ ∈ ℰ, else 0

and evaluates aleatory dispersion via the differential Shannon entropy of the
admitted terminal distribution (Gaussian closure):

    H = ½ · ln(2πe·σ²)

Deterministic under seed 42 substreams (EDR-009/NFR-004).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.common.seeds import component_rng
from afrp_runtime.contracts.cio import Scenario, ScenarioSet, WorldStateVector
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.dsmt import pignistic

SUBSYSTEM_ID = "L3-SIM"

_STEPS = 24


@dataclass
class ScenarioSimulator:
    """Seeded Monte-Carlo trajectory generator on the equilibrium manifold."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"
    n_paths: int = 256
    horizon_seconds: int = 3600
    max_abs_log_move: float = 0.05  # ℰ boundary: |ln(S_T/S_0)| bound
    drift_scale: float = 0.004
    base_volatility: float = 0.008

    def simulate(
        self,
        world_state: WorldStateVector,
        spot_price: float,
        cycle: int = 0,
    ) -> ScenarioSet:
        """Generate CIO-05A from the fused world state.

        Raises:
            ContractViolationError: non-positive spot or no admissible path.
        """
        if spot_price <= 0.0:
            raise ContractViolationError("CIO-05A", f"spot must be positive: {spot_price}")

        betp = pignistic(world_state.fused_masses)
        direction_tilt = betp.get("BULL", 0.0) - betp.get("BEAR", 0.0)
        confidence = 1.0 - world_state.epistemic_uncertainty
        drift = direction_tilt * self.drift_scale * confidence
        sigma = self.base_volatility * (1.0 + world_state.epistemic_uncertainty)

        rng = component_rng(SUBSYSTEM_ID, cycle)
        dt = 1.0 / _STEPS
        admitted: list[tuple[float, float, float]] = []  # (terminal, drawdown, runup)

        for _ in range(self.n_paths):
            log_price = 0.0
            low = 0.0
            high = 0.0
            inside = True
            for _ in range(_STEPS):
                shock = rng.gauss(0.0, 1.0)
                log_price += (drift - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * shock
                low = min(low, log_price)
                high = max(high, log_price)
                if abs(log_price) > self.max_abs_log_move:
                    inside = False  # τ ∉ ℰ — measure assigns zero
                    break
            if inside:
                admitted.append((log_price, low, high))

        if not admitted:
            raise ContractViolationError(
                "CIO-05A", "no trajectory admitted by the equilibrium manifold"
            )

        probability = 1.0 / len(admitted)  # P_raw/Z equal-weight normalization
        scenarios = tuple(
            Scenario(
                scenario_id=f"s{index:04d}",
                probability=probability,
                terminal_price=spot_price * math.exp(terminal),
                max_drawdown=spot_price * (math.exp(low) - 1.0),
                max_runup=spot_price * (math.exp(high) - 1.0),
            )
            for index, (terminal, low, high) in enumerate(admitted)
        )

        terminals = [t for t, _, _ in admitted]
        mean = sum(terminals) / len(terminals)
        variance = sum((t - mean) ** 2 for t in terminals) / max(1, len(terminals) - 1)
        entropy = 0.5 * math.log(2.0 * math.pi * math.e * max(variance, 1e-18))

        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{world_state.instrument}:{len(scenarios)}:{cycle}",
            parent_cio_ids=(world_state.envelope.message_id,),
            trace_id=world_state.envelope.trace_id,
        )
        scenario_set = ScenarioSet(
            envelope=envelope,
            instrument=world_state.instrument,
            scenarios=scenarios,
            differential_entropy=entropy,
            horizon_seconds=self.horizon_seconds,
            random_seed=42,
        )
        scenario_set.validate()
        return scenario_set
