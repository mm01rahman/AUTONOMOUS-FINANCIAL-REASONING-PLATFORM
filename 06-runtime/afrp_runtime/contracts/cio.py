"""CIO-01..CIO-12 in-process bindings (ADR-0003, REF-001 §2).

Frozen dataclasses mirroring ``proto/afrp/v1/cio.proto`` field-for-field.
Field numbers are documented inline; the proto remains the wire truth.
DSmT masses use canonical D^Theta focal labels: singletons ("BULL", "BEAR",
"RANGE"), unions ("BULL|BEAR"), intersections ("BULL&BEAR"), and "THETA"
for total ignorance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.envelope import Envelope

THETA = "THETA"
MASS_TOLERANCE = 1e-9


class ObservationKind(IntEnum):
    """Mirrors afrp.v1.ObservationKind."""

    UNSPECIFIED = 0
    TRADE = 1
    QUOTE = 2
    ORACLE = 3
    MACRO = 4


class AuthorizationVerdict(IntEnum):
    """Mirrors afrp.v1.AuthorizationVerdict."""

    UNSPECIFIED = 0
    AUTHORIZED = 1
    PROJECTED = 2
    NULL_TRADE = 3
    REJECTED = 4


class OrderState(IntEnum):
    """Mirrors afrp.v1.OrderState."""

    UNSPECIFIED = 0
    NEW = 1
    SUBMITTED = 2
    ACKNOWLEDGED = 3
    PARTIALLY_FILLED = 4
    FILLED = 5
    CANCELLED = 6
    REJECTED = 7
    EXPIRED = 8


class ExecutionEventKind(IntEnum):
    """Mirrors afrp.v1.ExecutionEventKind."""

    UNSPECIFIED = 0
    ACK = 1
    PARTIAL_FILL = 2
    FILL = 3
    CANCEL = 4
    REJECT = 5
    EXPIRE = 6


@dataclass(frozen=True)
class RawObservation:
    """CIO-01 (L1-ING)."""

    envelope: Envelope  # 1
    instrument: str  # 2
    kind: ObservationKind  # 3
    price: float  # 4
    bid: float  # 5
    ask: float  # 6
    size: float  # 7
    venue: str  # 8
    ingest_sequence: int  # 9
    event_at_ns: int  # 10


@dataclass(frozen=True)
class StandardFeature:
    """CIO-02 (L1-FST)."""

    envelope: Envelope  # 1
    feature_id: str  # 2
    instrument: str  # 3
    value: float  # 4
    window_seconds: int  # 5
    quality: float  # 6
    source_sequence: int  # 7


@dataclass(frozen=True)
class DomainBelief:
    """CIO-03 (L2 agents): DSmT basic belief assignment over D^Theta."""

    envelope: Envelope  # 1
    agent_id: str  # 2
    instrument: str  # 3
    masses: dict[str, float]  # 4
    reliability: float  # 5
    degraded: bool  # 6

    def validate(self) -> None:
        """Assert BBA well-formedness: non-negative masses summing to 1.

        Raises:
            ContractViolationError: masses are negative or do not sum to one.
        """
        if not self.masses:
            raise ContractViolationError("CIO-03", "empty mass assignment")
        negative = {k: v for k, v in self.masses.items() if v < 0.0}
        if negative:
            raise ContractViolationError("CIO-03", f"negative masses: {negative}")
        total = sum(self.masses.values())
        if abs(total - 1.0) > MASS_TOLERANCE:
            raise ContractViolationError("CIO-03", f"masses sum to {total!r}, not 1.0")


@dataclass(frozen=True)
class WorldStateVector:
    """CIO-04 (L3-WRM): fused global market state S_t."""

    envelope: Envelope  # 1
    instrument: str  # 2
    fused_masses: dict[str, float]  # 3
    epistemic_uncertainty: float  # 4
    conflict_mass: float  # 5
    regime_context: str  # 6
    active_hypotheses: tuple[str, ...]  # 7
    agent_quorum: int  # 8
    fusion_trace: tuple[str, ...]  # 9


@dataclass(frozen=True)
class Scenario:
    """Nested afrp.v1.ScenarioSet.Scenario."""

    scenario_id: str  # 1
    probability: float  # 2
    terminal_price: float  # 3
    max_drawdown: float  # 4
    max_runup: float  # 5


@dataclass(frozen=True)
class ScenarioSet:
    """CIO-05A (L3-SIM)."""

    envelope: Envelope  # 1
    instrument: str  # 2
    scenarios: tuple[Scenario, ...]  # 3
    differential_entropy: float  # 4
    horizon_seconds: int  # 5
    random_seed: int  # 6

    def validate(self) -> None:
        """Assert the scenario measure is a probability distribution.

        Raises:
            ContractViolationError: probabilities negative or not summing to one.
        """
        if not self.scenarios:
            raise ContractViolationError("CIO-05A", "empty scenario set")
        if any(s.probability < 0.0 for s in self.scenarios):
            raise ContractViolationError("CIO-05A", "negative scenario probability")
        total = sum(s.probability for s in self.scenarios)
        if abs(total - 1.0) > MASS_TOLERANCE:
            raise ContractViolationError("CIO-05A", f"probabilities sum to {total!r}")


@dataclass(frozen=True)
class DecisionContext:
    """CIO-05B (L4-FUS)."""

    envelope: Envelope  # 1
    instrument: str  # 2
    world_state_id: str  # 3
    scenario_set_id: str  # 4
    portfolio_state_id: str  # 5
    risk_aversion_lambda: float  # 6
    max_position_size: float  # 7
    available_cash: float  # 8


@dataclass(frozen=True)
class ExecutionCandidate:
    """CIO-06 (L4-DEC): a* = argmax U_r."""

    envelope: Envelope  # 1
    instrument: str  # 2
    direction: float  # 3
    size: float  # 4
    entry_price: float  # 5
    stop_price: float  # 6
    target_price: float  # 7
    expected_utility: float  # 8
    expected_risk: float  # 9
    risk_adjusted_utility: float  # 10


@dataclass(frozen=True)
class AuthorizedAction:
    """CIO-07 (L4-VAL): a_e = Pi_C(a*) with a_null fallback."""

    envelope: Envelope  # 1
    candidate_id: str  # 2
    verdict: AuthorizationVerdict  # 3
    instrument: str  # 4
    direction: float  # 5
    size: float  # 6
    entry_price: float  # 7
    stop_price: float  # 8
    mission_profile_id: str  # 9
    constraint_diagnostics: tuple[str, ...]  # 10
    hmac_signature: bytes  # 11


@dataclass(frozen=True)
class ExecutionIntent:
    """CIO-08 (L5-EXE)."""

    envelope: Envelope  # 1
    order_id: str  # 2
    authorized_action_id: str  # 3
    state: OrderState  # 4
    instrument: str  # 5
    direction: float  # 6
    quantity: float  # 7
    limit_price: float  # 8


@dataclass(frozen=True)
class ExecutionReport:
    """CIO-09 (L5-EXE)."""

    envelope: Envelope  # 1
    order_id: str  # 2
    event: ExecutionEventKind  # 3
    fill_quantity: float  # 4
    fill_price: float  # 5
    venue: str  # 6
    venue_at_ns: int  # 7
    reason: str  # 8


@dataclass(frozen=True)
class Position:
    """Nested afrp.v1.PortfolioState.Position."""

    instrument: str  # 1
    quantity: float  # 2
    average_price: float  # 3
    unrealized_pnl: float  # 4


@dataclass(frozen=True)
class PortfolioState:
    """CIO-10 (L5-EXE)."""

    envelope: Envelope  # 1
    positions: tuple[Position, ...]  # 2
    cash: float  # 3
    equity: float  # 4
    gross_exposure: float  # 5
    reconciled_at_ns: int  # 6


@dataclass(frozen=True)
class CalibrationWeights:
    """CIO-11 (L6-OPT)."""

    envelope: Envelope  # 1
    agent_weights: dict[str, float]  # 2
    brier_scores: dict[str, float]  # 3
    window_cycles: int  # 4


@dataclass(frozen=True)
class EpisodicEmbedding:
    """CIO-12 (L6-OPT)."""

    envelope: Envelope  # 1
    instrument: str  # 2
    vector: tuple[float, ...]  # 3
    regime_label: str  # 4
    window_start_ns: int  # 5
    window_end_ns: int  # 6
