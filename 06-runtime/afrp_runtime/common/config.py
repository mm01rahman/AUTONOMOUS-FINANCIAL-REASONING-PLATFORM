"""Layered configuration with EDR-005 precedence (RT-COMMON).

Precedence (highest wins):
Emergency Overrides > Mission Profile > Policy Bundle > Subsystem Config.

Mission Profiles MP-01..MP-05 (GLOSS-001 item 11) fix risk tolerances, spread
limits and agent quorum requirements. EDR-008: values resembling embedded
secrets are rejected outright.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from afrp_runtime.common.errors import ConfigurationError

_SECRET_PATTERN = re.compile(
    r"(?:api[_-]?key|secret|password|token)\s*[:=]|-----BEGIN|aws_[a-z_]*key",
    re.IGNORECASE,
)

ConfigValue = str | int | float | bool


class ConfigLayer(StrEnum):
    """EDR-005 layers, ordered weakest to strongest."""

    SUBSYSTEM = "SUBSYSTEM"
    POLICY = "POLICY"
    MISSION = "MISSION"
    EMERGENCY = "EMERGENCY"


_PRECEDENCE = (
    ConfigLayer.SUBSYSTEM,
    ConfigLayer.POLICY,
    ConfigLayer.MISSION,
    ConfigLayer.EMERGENCY,
)


@dataclass(frozen=True)
class MissionProfile:
    """Operational risk configuration profile (MP-01..MP-05)."""

    profile_id: str
    description: str
    risk_tolerance: float  # utility lambda multiplier input
    max_spread_bps: float
    required_quorum: int
    allow_trading: bool
    max_position_size: float


MISSION_PROFILES: dict[str, MissionProfile] = {
    "MP-01": MissionProfile(
        "MP-01", "Conservative live trading", 0.5, 1.5, 5, True, 1.0
    ),
    "MP-02": MissionProfile(
        "MP-02", "Standard live trading", 1.0, 2.5, 4, True, 2.0
    ),
    "MP-03": MissionProfile(
        "MP-03", "Aggressive live trading", 1.5, 4.0, 4, True, 3.0
    ),
    "MP-04": MissionProfile(
        "MP-04", "Deterministic replay / backtest", 1.0, 10.0, 1, False, 2.0
    ),
    "MP-05": MissionProfile(
        "MP-05", "Observation only — no trading", 0.0, 0.0, 3, False, 0.0
    ),
}


def _screen_secret(key: str, value: ConfigValue) -> None:
    if isinstance(value, str) and _SECRET_PATTERN.search(value):
        raise ConfigurationError(key, "embedded secret material rejected (EDR-008)")


@dataclass
class LayeredConfig:
    """Mutable configuration store resolving keys by EDR-005 precedence."""

    layers: dict[ConfigLayer, dict[str, ConfigValue]] = field(
        default_factory=lambda: {layer: {} for layer in ConfigLayer}
    )

    def set_value(self, layer: ConfigLayer, key: str, value: ConfigValue) -> None:
        """Set ``key`` in ``layer`` after EDR-008 screening."""
        _screen_secret(key, value)
        self.layers[layer][key] = value

    def resolve(self, key: str) -> ConfigValue:
        """Resolve ``key`` by precedence.

        Raises:
            ConfigurationError: the key is defined in no layer.
        """
        for layer in reversed(_PRECEDENCE):
            if key in self.layers[layer]:
                return self.layers[layer][key]
        raise ConfigurationError(key, "not defined in any configuration layer")

    def source_layer(self, key: str) -> ConfigLayer:
        """The layer that currently supplies ``key``."""
        for layer in reversed(_PRECEDENCE):
            if key in self.layers[layer]:
                return layer
        raise ConfigurationError(key, "not defined in any configuration layer")


def load_mission_profile(profile_id: str) -> MissionProfile:
    """Look up a mission profile.

    Raises:
        ConfigurationError: unknown profile id.
    """
    try:
        return MISSION_PROFILES[profile_id]
    except KeyError as exc:
        raise ConfigurationError("mission_profile_id", f"unknown profile {profile_id!r}") from exc


def apply_mission_profile(config: LayeredConfig, profile: MissionProfile) -> None:
    """Project a mission profile into the MISSION layer."""
    config.set_value(ConfigLayer.MISSION, "risk_tolerance", profile.risk_tolerance)
    config.set_value(ConfigLayer.MISSION, "max_spread_bps", profile.max_spread_bps)
    config.set_value(ConfigLayer.MISSION, "required_quorum", profile.required_quorum)
    config.set_value(ConfigLayer.MISSION, "allow_trading", profile.allow_trading)
    config.set_value(ConfigLayer.MISSION, "max_position_size", profile.max_position_size)
