"""Unit tests for the CIO in-process bindings (ADR-0003 parity + validation)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts import cio
from afrp_runtime.contracts.envelope import Envelope, hash_payload, make_envelope

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = json.loads(
    (REPO_ROOT / "09-validation" / "contracts" / "afrp_v1.snapshot.json").read_text(
        encoding="utf-8"
    )
)

# dataclass -> proto message parity map (ADR-0003)
PARITY: dict[str, type] = {
    "afrp.v1.CognitiveEnvelope": Envelope,
    "afrp.v1.RawObservation": cio.RawObservation,
    "afrp.v1.StandardFeature": cio.StandardFeature,
    "afrp.v1.DomainBelief": cio.DomainBelief,
    "afrp.v1.WorldStateVector": cio.WorldStateVector,
    "afrp.v1.ScenarioSet": cio.ScenarioSet,
    "afrp.v1.ScenarioSet.Scenario": cio.Scenario,
    "afrp.v1.DecisionContext": cio.DecisionContext,
    "afrp.v1.ExecutionCandidate": cio.ExecutionCandidate,
    "afrp.v1.AuthorizedAction": cio.AuthorizedAction,
    "afrp.v1.ExecutionIntent": cio.ExecutionIntent,
    "afrp.v1.ExecutionReport": cio.ExecutionReport,
    "afrp.v1.PortfolioState": cio.PortfolioState,
    "afrp.v1.PortfolioState.Position": cio.Position,
    "afrp.v1.CalibrationWeights": cio.CalibrationWeights,
    "afrp.v1.EpisodicEmbedding": cio.EpisodicEmbedding,
}


def envelope() -> Envelope:
    return make_envelope(
        producer_subsystem_id="TEST",
        cognitive_cycle_id="cycle-1",
        mission_profile_id="MP-04",
        payload_repr="payload",
    )


class TestEnvelopeFactory:
    def test_envelope_fields_populated(self) -> None:
        env = envelope()
        assert env.message_id and env.trace_id and env.span_id
        assert env.mission_profile_id == "MP-04"
        assert env.payload_hash == hash_payload("payload")
        assert env.provenance[-1] == "TEST"

    def test_provenance_chains_parents(self) -> None:
        env = make_envelope(
            producer_subsystem_id="L3-WRM",
            cognitive_cycle_id="c",
            mission_profile_id="MP-04",
            payload_repr="p",
            parent_cio_ids=("m1", "m2"),
        )
        assert env.parent_cio_ids == ("m1", "m2")
        assert env.provenance == ("m1", "m2", "L3-WRM")

    def test_payload_hash_is_sha256(self) -> None:
        assert len(hash_payload("x")) == 32

    def test_deterministic_timestamp_injection(self) -> None:
        env = make_envelope(
            producer_subsystem_id="T",
            cognitive_cycle_id="c",
            mission_profile_id="MP-04",
            payload_repr="p",
            generated_at_ns=123456789,
        )
        assert env.generated_at_ns == 123456789


class TestProtoParity:
    """Every dataclass mirrors its proto message field-for-field (ADR-0003)."""

    @pytest.mark.parametrize("proto_name", sorted(PARITY))
    def test_field_names_match_snapshot(self, proto_name: str) -> None:
        proto_fields = SNAPSHOT["messages"][proto_name]
        expected_names = [proto_fields[num][0] for num in sorted(proto_fields, key=int)]
        binding = PARITY[proto_name]
        dataclass_fields = getattr(binding, "__dataclass_fields__")  # noqa: B009
        annotations = [name for name in dataclass_fields if name != "provenance"]
        assert annotations == expected_names, (
            f"{proto_name}: dataclass fields {annotations} != proto {expected_names}"
        )

    def test_every_snapshot_message_has_binding(self) -> None:
        # protoc synthesizes *Entry messages for map<> fields; they are not
        # standalone contracts (ADR-0003).
        real = {n for n in SNAPSHOT["messages"] if not n.endswith("Entry")}
        assert real == set(PARITY)


class TestDomainBeliefValidation:
    def test_valid_bba_passes(self) -> None:
        belief = cio.DomainBelief(
            envelope=envelope(),
            agent_id="L2-MAC",
            instrument="XAUUSD",
            masses={"BULL": 0.5, "BEAR": 0.2, "BULL|BEAR": 0.1, "THETA": 0.2},
            reliability=0.9,
            degraded=False,
        )
        belief.validate()  # must not raise

    def test_negative_mass_rejected(self) -> None:
        belief = cio.DomainBelief(
            envelope=envelope(),
            agent_id="a",
            instrument="i",
            masses={"BULL": 1.2, "BEAR": -0.2},
            reliability=1.0,
            degraded=False,
        )
        with pytest.raises(ContractViolationError, match="negative"):
            belief.validate()

    def test_non_unit_sum_rejected(self) -> None:
        belief = cio.DomainBelief(
            envelope=envelope(),
            agent_id="a",
            instrument="i",
            masses={"BULL": 0.5, "THETA": 0.4},
            reliability=1.0,
            degraded=False,
        )
        with pytest.raises(ContractViolationError, match="sum"):
            belief.validate()

    def test_empty_masses_rejected(self) -> None:
        belief = cio.DomainBelief(
            envelope=envelope(),
            agent_id="a",
            instrument="i",
            masses={},
            reliability=1.0,
            degraded=True,
        )
        with pytest.raises(ContractViolationError, match="empty"):
            belief.validate()


class TestScenarioSetValidation:
    def test_valid_distribution_passes(self) -> None:
        scenario_set = cio.ScenarioSet(
            envelope=envelope(),
            instrument="XAUUSD",
            scenarios=(
                cio.Scenario("s1", 0.6, 2400.0, -5.0, 8.0),
                cio.Scenario("s2", 0.4, 2350.0, -12.0, 3.0),
            ),
            differential_entropy=1.2,
            horizon_seconds=3600,
            random_seed=42,
        )
        scenario_set.validate()

    def test_non_unit_probability_rejected(self) -> None:
        scenario_set = cio.ScenarioSet(
            envelope=envelope(),
            instrument="XAUUSD",
            scenarios=(cio.Scenario("s1", 0.6, 2400.0, -5.0, 8.0),),
            differential_entropy=0.0,
            horizon_seconds=60,
            random_seed=42,
        )
        with pytest.raises(ContractViolationError):
            scenario_set.validate()
