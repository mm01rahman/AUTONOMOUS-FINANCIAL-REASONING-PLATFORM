"""L1-FST — feature store (SLS-100, WP-IMP-0014).

Consumes CIO-01 observations and emits CIO-02 :class:`StandardFeature`
values: mid price, spread (bps), windowed log return, and EWM volatility.
Features are immutable once computed and cached by
``(feature_id, instrument, source_sequence)``.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind, RawObservation, StandardFeature
from afrp_runtime.contracts.envelope import make_envelope

SUBSYSTEM_ID = "L1-FST"

FEATURE_MID = "mid_price"
FEATURE_SPREAD_BPS = "spread_bps"
FEATURE_LOG_RETURN = "log_return"
FEATURE_EWM_VOL = "ewm_volatility"

_EWM_ALPHA = 0.2


@dataclass
class FeatureStore:
    """Deterministic CIO-02 producer with an immutable feature cache."""

    mission_profile_id: str
    window_seconds: int = 60
    cognitive_cycle_id: str = "cycle-0"
    _prices: dict[str, deque[tuple[int, float]]] = field(default_factory=dict)
    _ewm_var: dict[str, float] = field(default_factory=dict)
    _cache: dict[tuple[str, str, int], StandardFeature] = field(default_factory=dict)
    _processed: dict[tuple[str, int], list[StandardFeature]] = field(default_factory=dict)

    def _emit(
        self,
        observation: RawObservation,
        feature_id: str,
        value: float,
        quality: float,
    ) -> StandardFeature:
        key = (feature_id, observation.instrument, observation.ingest_sequence)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        envelope = make_envelope(
            producer_subsystem_id=SUBSYSTEM_ID,
            cognitive_cycle_id=self.cognitive_cycle_id,
            mission_profile_id=self.mission_profile_id,
            payload_repr=f"{feature_id}:{observation.instrument}:{value!r}",
            parent_cio_ids=(observation.envelope.message_id,),
            trace_id=observation.envelope.trace_id,
            generated_at_ns=observation.event_at_ns,
        )
        feature = StandardFeature(
            envelope=envelope,
            feature_id=feature_id,
            instrument=observation.instrument,
            value=value,
            window_seconds=self.window_seconds,
            quality=quality,
            source_sequence=observation.ingest_sequence,
        )
        self._cache[key] = feature
        return feature

    def update(self, observation: RawObservation) -> list[StandardFeature]:
        """Fold one observation into state and emit derivable features.

        Re-delivery of an already-processed observation is idempotent: the
        original emissions are returned and state is not folded twice
        (FIT-008 replay safety).

        Raises:
            ContractViolationError: the observation kind is unsupported.
        """
        replay_key = (observation.instrument, observation.ingest_sequence)
        already = self._processed.get(replay_key)
        if already is not None:
            return list(already)

        if observation.kind not in (
            ObservationKind.TRADE,
            ObservationKind.QUOTE,
            ObservationKind.ORACLE,
            ObservationKind.MACRO,
        ):
            raise ContractViolationError("CIO-02", f"unsupported kind {observation.kind}")

        features: list[StandardFeature] = []
        if observation.kind is ObservationKind.QUOTE:
            mid = (observation.bid + observation.ask) / 2.0
            spread_bps = (observation.ask - observation.bid) / mid * 10_000.0
            features.append(self._emit(observation, FEATURE_MID, mid, 1.0))
            features.append(self._emit(observation, FEATURE_SPREAD_BPS, spread_bps, 1.0))
            reference_price = mid
        elif observation.kind is ObservationKind.TRADE:
            reference_price = observation.price
            features.append(self._emit(observation, FEATURE_MID, reference_price, 0.9))
        else:
            self._processed[replay_key] = list(features)
            return features  # oracle/macro folded by dedicated agents downstream

        history = self._prices.setdefault(observation.instrument, deque(maxlen=4096))
        cutoff = observation.event_at_ns - self.window_seconds * 1_000_000_000
        while history and history[0][0] < cutoff:
            history.popleft()

        if history:
            _, base_price = history[0]
            log_return = math.log(reference_price / base_price)
            features.append(
                self._emit(
                    observation,
                    FEATURE_LOG_RETURN,
                    log_return,
                    min(1.0, len(history) / 8.0),
                )
            )
            previous_var = self._ewm_var.get(observation.instrument, 0.0)
            step_return = math.log(reference_price / history[-1][1]) if history else 0.0
            variance = (1 - _EWM_ALPHA) * previous_var + _EWM_ALPHA * step_return**2
            self._ewm_var[observation.instrument] = variance
            features.append(
                self._emit(
                    observation,
                    FEATURE_EWM_VOL,
                    math.sqrt(variance),
                    min(1.0, len(history) / 16.0),
                )
            )
        history.append((observation.event_at_ns, reference_price))
        self._processed[replay_key] = list(features)
        return features

    def latest(self, instrument: str) -> dict[str, StandardFeature]:
        """Latest feature per feature_id for ``instrument`` (highest sequence)."""
        latest: dict[str, StandardFeature] = {}
        for (feature_id, feat_instrument, _seq), feature in self._cache.items():
            if feat_instrument != instrument:
                continue
            current = latest.get(feature_id)
            if current is None or feature.source_sequence > current.source_sequence:
                latest[feature_id] = feature
        return latest
