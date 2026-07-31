"""Unit tests for RT-COMMON: config precedence, OBS-01, SYS-03, seeds, errors."""

from __future__ import annotations

import io
import json

import pytest
from afrp_runtime.common.config import (
    MISSION_PROFILES,
    ConfigLayer,
    LayeredConfig,
    apply_mission_profile,
    load_mission_profile,
)
from afrp_runtime.common.errors import ConfigurationError, StateTransitionError
from afrp_runtime.common.obslog import LogLevel, Obs01Logger, validate_obs01
from afrp_runtime.common.seeds import GLOBAL_SEED, component_rng, derive_seed
from afrp_runtime.common.statemachine import (
    OperationalState,
    OperationalStateMachine,
    legal_targets,
)


class TestEdr005ConfigPrecedence:
    def test_precedence_order(self) -> None:
        config = LayeredConfig()
        config.set_value(ConfigLayer.SUBSYSTEM, "max_spread_bps", 9.0)
        assert config.resolve("max_spread_bps") == 9.0
        config.set_value(ConfigLayer.POLICY, "max_spread_bps", 5.0)
        assert config.resolve("max_spread_bps") == 5.0
        config.set_value(ConfigLayer.MISSION, "max_spread_bps", 2.5)
        assert config.resolve("max_spread_bps") == 2.5
        config.set_value(ConfigLayer.EMERGENCY, "max_spread_bps", 0.5)
        assert config.resolve("max_spread_bps") == 0.5
        assert config.source_layer("max_spread_bps") is ConfigLayer.EMERGENCY

    def test_missing_key_faults(self) -> None:
        with pytest.raises(ConfigurationError):
            LayeredConfig().resolve("ghost")

    def test_all_five_mission_profiles_defined(self) -> None:
        assert set(MISSION_PROFILES) == {"MP-01", "MP-02", "MP-03", "MP-04", "MP-05"}
        assert MISSION_PROFILES["MP-04"].allow_trading is False  # replay profile
        assert MISSION_PROFILES["MP-05"].allow_trading is False  # observation only

    def test_profile_projection(self) -> None:
        config = LayeredConfig()
        apply_mission_profile(config, load_mission_profile("MP-02"))
        assert config.resolve("required_quorum") == 4
        assert config.resolve("allow_trading") is True

    def test_unknown_profile_faults(self) -> None:
        with pytest.raises(ConfigurationError):
            load_mission_profile("MP-99")

    def test_edr_008_secret_rejection(self) -> None:
        config = LayeredConfig()
        with pytest.raises(ConfigurationError, match="EDR-008"):
            config.set_value(ConfigLayer.SUBSYSTEM, "venue", "api_key=sk-abc123")
        with pytest.raises(ConfigurationError, match="EDR-008"):
            config.set_value(
                ConfigLayer.POLICY, "cert", "-----BEGIN PRIVATE KEY-----"
            )


class TestObs01Logging:
    def test_record_shape_and_validation(self) -> None:
        stream = io.StringIO()
        logger = Obs01Logger("L1-ING", stream, trace_id="t1", span_id="s1", cycle_id="c1")
        logger.log(LogLevel.INFO, "tick_ingested", {"seq": 7})
        line = stream.getvalue().strip()
        assert validate_obs01(line)
        parsed = json.loads(line)
        assert parsed["subsystem"] == "L1-ING"
        assert parsed["event"] == "tick_ingested"
        assert parsed["data"] == {"seq": 7}
        assert parsed["trace_id"] == "t1"

    def test_single_line_json(self) -> None:
        stream = io.StringIO()
        Obs01Logger("X", stream).log(LogLevel.ERROR, "boom", {"msg": "a\nb"})
        assert len(stream.getvalue().splitlines()) == 1

    def test_validator_rejects_garbage(self) -> None:
        assert not validate_obs01("not json")
        assert not validate_obs01(json.dumps({"level": "INFO"}))
        assert not validate_obs01(json.dumps(
            {"ts_ns": 1, "level": "LOUD", "subsystem": "x", "event": "y"}
        ))


class TestSys03StateMachine:
    def test_boot_to_normal(self) -> None:
        machine = OperationalStateMachine()
        machine.transition(OperationalState.NORMAL, "boot verified")
        assert machine.trading_permitted

    def test_full_degradation_and_recovery_cycle(self) -> None:
        machine = OperationalStateMachine()
        machine.transition(OperationalState.NORMAL, "boot")
        machine.transition(OperationalState.OBSERVATION, "anomaly")
        machine.transition(OperationalState.DEGRADED, "quorum loss")
        machine.transition(OperationalState.RECOVERY, "rebuilding")
        machine.transition(OperationalState.NORMAL, "validated")
        assert machine.trading_permitted
        assert len(machine.history) == 6

    def test_every_live_state_reaches_emergency_stop(self) -> None:
        for path in (
            [OperationalState.NORMAL],
            [OperationalState.NORMAL, OperationalState.OBSERVATION],
            [OperationalState.NORMAL, OperationalState.OBSERVATION, OperationalState.DEGRADED],
            [
                OperationalState.NORMAL,
                OperationalState.OBSERVATION,
                OperationalState.DEGRADED,
                OperationalState.RECOVERY,
            ],
        ):
            machine = OperationalStateMachine()
            for state in path:
                machine.transition(state, "step")
            machine.transition(OperationalState.EMERGENCY_STOP, "critical breach")
            assert machine.state is OperationalState.EMERGENCY_STOP
            assert not machine.trading_permitted

    def test_initializing_cannot_estop_directly(self) -> None:
        machine = OperationalStateMachine()
        with pytest.raises(StateTransitionError):
            machine.transition(OperationalState.EMERGENCY_STOP, "premature")

    def test_estop_is_terminal_without_operator(self) -> None:
        assert legal_targets(OperationalState.EMERGENCY_STOP) == ()

    def test_manual_reset_requires_estop_and_operator(self) -> None:
        machine = OperationalStateMachine()
        machine.transition(OperationalState.NORMAL, "boot")
        with pytest.raises(StateTransitionError):
            machine.manual_reset("op-1")  # not in EMERGENCY_STOP
        machine.transition(OperationalState.EMERGENCY_STOP, "breach")
        with pytest.raises(StateTransitionError):
            machine.manual_reset("")  # missing operator id
        machine.manual_reset("op-1")
        assert machine.state is OperationalState.INITIALIZING

    def test_illegal_shortcuts_rejected(self) -> None:
        machine = OperationalStateMachine()
        machine.transition(OperationalState.NORMAL, "boot")
        with pytest.raises(StateTransitionError):
            machine.transition(OperationalState.RECOVERY, "skip")
        with pytest.raises(StateTransitionError):
            machine.transition(OperationalState.DEGRADED, "skip")


class TestSeedDiscipline:
    def test_global_seed_is_42(self) -> None:
        assert GLOBAL_SEED == 42

    def test_derivation_is_stable(self) -> None:
        assert derive_seed("L3-SIM", 5) == derive_seed("L3-SIM", 5)

    def test_substreams_are_independent(self) -> None:
        assert derive_seed("L3-SIM") != derive_seed("L2-MAC")
        assert derive_seed("L3-SIM", 1) != derive_seed("L3-SIM", 2)

    def test_rng_reproducibility(self) -> None:
        first = [component_rng("L3-SIM", 9).random() for _ in range(3)]
        second = [component_rng("L3-SIM", 9).random() for _ in range(3)]
        assert first == second
