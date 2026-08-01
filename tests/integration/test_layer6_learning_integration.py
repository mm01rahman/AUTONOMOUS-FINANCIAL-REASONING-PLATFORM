"""WP-RT-1018 integration tests for the Layer 6 learning pipeline."""

from __future__ import annotations

import math

import pytest
from afrp_runtime.contracts.cio import CalibrationWeights, EpisodicEmbedding
from afrp_runtime.layer6.learning import BrierCalibrator, RegimeEmbedder

_FEATURES = {
    "log_return": 0.003,
    "ewm_volatility": 0.0015,
    "spread_bps": 1.2,
    "macro_real_yield": -0.5,
    "momentum_5d": 0.002,
}

_PROBS_BULL = {"BULL": 0.7, "BEAR": 0.1, "RANGE": 0.2}
_PROBS_BEAR = {"BULL": 0.1, "BEAR": 0.8, "RANGE": 0.1}
_PROBS_UNIFORM = {"BULL": 1 / 3, "BEAR": 1 / 3, "RANGE": 1 / 3}


class TestCalibrationPipeline:
    """CIO-11 emission from historical observation history."""

    def test_full_observation_to_cio11_emission(self) -> None:
        calibrator = BrierCalibrator("MP-02", window_cycles=10)

        # Simulate 5 rounds for two agents with mixed outcomes
        for i in range(5):
            outcome = "BULL" if i % 2 == 0 else "BEAR"
            calibrator.observe("L2-MAC", _PROBS_BULL, outcome, parent_cio_id=f"fill-{i}")
            calibrator.observe("L2-MIC", _PROBS_BEAR, outcome, parent_cio_id=f"fill-{i}")

        cio11: CalibrationWeights = calibrator.emit(generated_at_ns=1_000_000)

        # Schema valid
        assert isinstance(cio11.envelope.message_id, str) and len(cio11.envelope.message_id) > 0
        assert cio11.window_cycles == 10
        assert set(cio11.agent_weights.keys()) == {"L2-MAC", "L2-MIC"}
        assert set(cio11.brier_scores.keys()) == {"L2-MAC", "L2-MIC"}

        # Weights are bounded
        for w in cio11.agent_weights.values():
            assert 0.05 <= w <= 1.0

        # The agent that got BULL right more often should have higher weight
        assert cio11.agent_weights["L2-MAC"] > cio11.agent_weights["L2-MIC"]

        # Provenance
        assert "fill-0" in cio11.envelope.parent_cio_ids
        assert cio11.envelope.generated_at_ns == 1_000_000
        assert cio11.envelope.producer_subsystem_id == "L6-OPT"

    def test_rolling_window_converges_after_recovery(self) -> None:
        """After bad initial observations, perfect forecasts should recover weight to 1.0."""
        calibrator = BrierCalibrator("MP-02", window_cycles=3)
        # 1 bad observation
        calibrator.observe("AGENT", {"BULL": 0.0, "BEAR": 1.0, "RANGE": 0.0}, "BULL")
        # 3 perfect observations — evicts the bad one
        for _ in range(3):
            calibrator.observe("AGENT", {"BULL": 1.0, "BEAR": 0.0, "RANGE": 0.0}, "BULL")
        assert calibrator.weights()["AGENT"] == pytest.approx(1.0)

    def test_emission_is_reproducible_for_same_history(self) -> None:
        """Two calibrators with the same observation history must emit identical weights."""
        def _build_calibrator() -> BrierCalibrator:
            cal = BrierCalibrator("MP-02", window_cycles=5)
            for outcome in ("BULL", "BEAR", "RANGE", "BULL", "BULL"):
                cal.observe("L2-MAC", _PROBS_BULL, outcome)
            return cal

        c1 = _build_calibrator()
        c2 = _build_calibrator()
        assert c1.weights() == c2.weights()
        assert c1.mean_scores() == c2.mean_scores()

    def test_out_of_band_path_does_not_produce_authorized_action(self) -> None:
        """CIO-11 is a calibration weight, not an authorization — must not carry hmac_signature."""
        calibrator = BrierCalibrator("MP-02")
        calibrator.observe("L2-MAC", _PROBS_BULL, "BULL")
        cio11 = calibrator.emit(generated_at_ns=1)
        assert isinstance(cio11, CalibrationWeights)
        # CalibrationWeights has no hmac_signature field — verified by absence
        assert not hasattr(cio11, "hmac_signature")


class TestEmbeddingPipeline:
    """CIO-12 emission and reproducibility tests."""

    def test_full_feature_set_to_cio12_emission(self) -> None:
        embedder = RegimeEmbedder(dimension=16)
        cio12: EpisodicEmbedding = embedder.emit(
            mission_profile_id="MP-02",
            instrument="XAUUSD",
            features=_FEATURES,
            regime_label="BULL",
            window_start_ns=1_000,
            window_end_ns=2_000,
            parent_cio_ids=("world-state-1", "fill-1"),
        )

        # Schema valid
        assert cio12.instrument == "XAUUSD"
        assert cio12.regime_label == "BULL"
        assert cio12.window_start_ns == 1_000
        assert cio12.window_end_ns == 2_000
        assert len(cio12.vector) == 16
        assert cio12.envelope.producer_subsystem_id == "L6-OPT"
        assert cio12.envelope.parent_cio_ids == ("world-state-1", "fill-1")

        # Unit norm
        norm = math.sqrt(sum(v * v for v in cio12.vector))
        assert norm == pytest.approx(1.0, abs=1e-9)

    def test_embedding_replay_reproducibility(self) -> None:
        """Embedding must be bit-for-bit identical across separate emit() calls."""
        embedder = RegimeEmbedder(dimension=16)
        kwargs = dict(
            mission_profile_id="MP-02",
            instrument="XAUUSD",
            features=_FEATURES,
            regime_label="RANGE",
            window_start_ns=500,
            window_end_ns=1_000,
        )
        first = embedder.emit(**kwargs)  # type: ignore[arg-type]
        second = embedder.emit(**kwargs)  # type: ignore[arg-type]
        assert first.vector == second.vector

    def test_different_regime_labels_produce_different_envelopes(self) -> None:
        """Different regime labels must produce different payload hashes."""
        embedder = RegimeEmbedder(dimension=8)
        bull = embedder.emit("MP-02", "XAUUSD", _FEATURES, "BULL", 0, 100)
        bear = embedder.emit("MP-02", "XAUUSD", _FEATURES, "BEAR", 0, 100)
        assert bull.regime_label != bear.regime_label
        assert bull.envelope.payload_hash != bear.envelope.payload_hash

    def test_insert_order_invariant_across_instruments(self) -> None:
        """Sorted feature iteration ensures embedding is order-independent."""
        embedder = RegimeEmbedder(dimension=8)
        fwd = embedder.embed(_FEATURES)
        rev = embedder.embed(dict(reversed(list(_FEATURES.items()))))
        assert fwd == rev


class TestCrossLayerOutOfBand:
    """Verify L6-OPT is strictly out-of-band — no bypass of L4-VAL policy."""

    def test_calibration_weights_do_not_authorize_trades(self) -> None:
        """CIO-11 carries no verdict field — it cannot authorize execution."""
        from afrp_runtime.contracts.cio import AuthorizationVerdict

        calibrator = BrierCalibrator("MP-02")
        calibrator.observe("L2-MAC", _PROBS_BULL, "BULL")
        cio11 = calibrator.emit(generated_at_ns=1)

        # CIO-11 has no verdict — cannot be cast to or confused with CIO-07
        assert not hasattr(cio11, "verdict")
        assert not hasattr(cio11, "authorized")
        # The CalibrationWeights type is distinct from AuthorizationVerdict values
        assert not isinstance(cio11, type(AuthorizationVerdict))

    def test_embedding_does_not_carry_policy_approval(self) -> None:
        """CIO-12 carries no verdict — policy re-validation is always required."""
        embedder = RegimeEmbedder(8)
        cio12 = embedder.emit("MP-02", "XAUUSD", _FEATURES, "BULL", 0, 1)
        assert not hasattr(cio12, "verdict")
        assert not hasattr(cio12, "hmac_signature")
