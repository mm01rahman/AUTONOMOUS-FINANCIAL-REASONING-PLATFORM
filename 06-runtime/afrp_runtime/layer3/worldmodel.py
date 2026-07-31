"""L3-WRM — World Model Kernel (SLS-300, WP-IMP-0024).

Synthesizes CIO-03 domain beliefs into the unified CIO-04
:class:`WorldStateVector` via reliability discounting and sequential PCR5
fusion. Degraded quorum operation pads missing agents with the vacuous
belief instead of failing (NFR-003).
"""

from __future__ import annotations

from dataclasses import dataclass

from afrp_runtime.contracts.cio import (
    THETA,
    CalibrationWeights,
    DomainBelief,
    WorldStateVector,
)
from afrp_runtime.contracts.envelope import make_envelope
from afrp_runtime.layer3.dsmt import combine_all, discount, pignistic

SUBSYSTEM_ID = "L3-WRM"

EXPECTED_AGENTS: tuple[str, ...] = (
    "L2-MAC",
    "L2-MIC",
    "L2-LIQ",
    "L2-REG",
    "L2-FOR",
    "L2-BEH",
)


@dataclass
class WorldModelKernel:
    """Deterministic CIO-04 producer."""

    mission_profile_id: str
    cognitive_cycle_id: str = "cycle-0"

    def fuse(
        self,
        instrument: str,
        beliefs: list[DomainBelief],
        weights: CalibrationWeights | None = None,
    ) -> WorldStateVector:
        """Fuse agent beliefs into the world state.

        Missing expected agents are padded with vacuous beliefs (m(Θ) = 1)
        and counted out of the healthy quorum (NFR-003).

        With zero healthy sources the result is the vacuous world state
        m(Θ)=1, quorum=0. L4-VAL then authorizes a_null (NFR-003/Article VIII).
        """
        by_agent = {belief.agent_id: belief for belief in beliefs}
        trace: list[str] = []
        sources: list[dict[str, float]] = []
        parents: list[str] = []
        healthy = 0

        for agent_id in EXPECTED_AGENTS:
            belief = by_agent.get(agent_id)
            if belief is None:
                sources.append({THETA: 1.0})
                trace.append(f"{agent_id}: MISSING -> vacuous m(THETA)=1 (NFR-003)")
                continue
            belief.validate()
            parents.append(belief.envelope.message_id)
            weight = belief.reliability
            if weights is not None:
                weight *= weights.agent_weights.get(agent_id, 1.0)
            weight = max(0.0, min(1.0, weight))
            masses = discount(belief.masses, weight)
            sources.append(masses)
            if belief.degraded:
                trace.append(f"{agent_id}: DEGRADED (weight {weight:.3f})")
            else:
                healthy += 1
                trace.append(f"{agent_id}: OK (weight {weight:.3f})")

        fused, conflict = combine_all(sources)
        trace.append(f"pcr5: fused {len(sources)} sources, conflict={conflict:.6f}")

        if fused.get(THETA, 0.0) >= 1.0 - 1e-9:
            hypotheses: tuple[str, ...] = ()
        else:
            betp = pignistic(fused)
            hypotheses = tuple(
                singleton
                for singleton, probability in sorted(
                    betp.items(), key=lambda item: (-item[1], item[0])
                )
                if probability > 0.15
            )

        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{instrument}:{sorted(fused.items())!r}",
            parent_cio_ids=tuple(parents),
        )
        return WorldStateVector(
            envelope=envelope,
            instrument=instrument,
            fused_masses=fused,
            epistemic_uncertainty=fused.get(THETA, 0.0),
            conflict_mass=conflict,
            regime_context=hypotheses[0] if hypotheses else THETA,
            active_hypotheses=hypotheses,
            agent_quorum=healthy,
            fusion_trace=tuple(trace),
        )
