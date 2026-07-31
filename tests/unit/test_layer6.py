"""Unit tests for Layer 6 Brier calibration and episodic embeddings."""

from __future__ import annotations

import math

import pytest
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.layer6.learning import (
    BrierCalibrator,
    RegimeEmbedder,
    multiclass_brier,
)


class TestBrierScore:
    def test_perfect_forecast_scores_zero(self) -> None:
        score = multiclass_brier(
            {"BULL": 1.0, "BEAR": 0.0, "RANGE": 0.0}, "BULL"
        )
        assert score == 0.0

    def test_fully_wrong_forecast_scores_two(self) -> None:
        score = multiclass_brier(
            {"BULL": 0.0, "BEAR": 1.0, "RANGE": 0.0}, "BULL"
        )
        assert score == 2.0

    def test_uniform_oracle(self) -> None:
        score = multiclass_brier(
            {"BULL": 1 / 3, "BEAR": 1 / 3, "RANGE": 1 / 3}, "RANGE"
        )
        assert score == pytest.approx(2 / 3)

    @pytest.mark.parametrize(
        "probabilities",
        [
            {"BULL": 0.5, "BEAR": 0.5},
            {"BULL": 0.8, "BEAR": 0.3, "RANGE": -0.1},
            {"BULL": 0.8, "BEAR": 0.2, "RANGE": 0.2},
        ],
    )
    def test_malformed_distribution_rejected(
        self, probabilities: dict[str, float]
    ) -> None:
        with pytest.raises(ContractViolationError):
            multiclass_brier(probabilities, "BULL")

    def test_unknown_outcome_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            multiclass_brier(
                {"BULL": 0.3, "BEAR": 0.3, "RANGE": 0.4}, "CRASH"
            )


class TestBrierCalibrator:
    def test_perfect_agent_weight_one(self) -> None:
        calibrator = BrierCalibrator("MP-04")
        calibrator.observe(
            "L2-MAC", {"BULL": 1.0, "BEAR": 0.0, "RANGE": 0.0}, "BULL"
        )
        assert calibrator.weights()["L2-MAC"] == 1.0

    def test_bad_agent_clamped_to_floor(self) -> None:
        calibrator = BrierCalibrator("MP-04", weight_floor=0.1)
        calibrator.observe(
            "L2-MAC", {"BULL": 0.0, "BEAR": 1.0, "RANGE": 0.0}, "BULL"
        )
        assert calibrator.weights()["L2-MAC"] == pytest.approx(0.1)

    def test_rolling_window_evicts_old_score(self) -> None:
        calibrator = BrierCalibrator("MP-04", window_cycles=2)
        calibrator.observe(
            "L2-MAC", {"BULL": 0.0, "BEAR": 1.0, "RANGE": 0.0}, "BULL"
        )
        for _ in range(2):
            calibrator.observe(
                "L2-MAC", {"BULL": 1.0, "BEAR": 0.0, "RANGE": 0.0}, "BULL"
            )
        assert calibrator.mean_scores()["L2-MAC"] == 0.0
        assert calibrator.weights()["L2-MAC"] == 1.0

    def test_multiple_agents_independent(self) -> None:
        calibrator = BrierCalibrator("MP-04")
        calibrator.observe(
            "L2-MAC", {"BULL": 1.0, "BEAR": 0.0, "RANGE": 0.0}, "BULL"
        )
        calibrator.observe(
            "L2-MIC", {"BULL": 0.0, "BEAR": 1.0, "RANGE": 0.0}, "BULL"
        )
        assert calibrator.weights()["L2-MAC"] > calibrator.weights()["L2-MIC"]

    def test_emit_cio11_with_provenance(self) -> None:
        calibrator = BrierCalibrator("MP-04", window_cycles=5)
        calibrator.observe(
            "L2-MAC",
            {"BULL": 0.7, "BEAR": 0.1, "RANGE": 0.2},
            "BULL",
            parent_cio_id="fill-1",
        )
        output = calibrator.emit(generated_at_ns=99)
        assert output.window_cycles == 5
        assert set(output.agent_weights) == {"L2-MAC"}
        assert output.envelope.parent_cio_ids == ("fill-1",)
        assert output.envelope.generated_at_ns == 99

    def test_invalid_constructor_bounds(self) -> None:
        with pytest.raises(ContractViolationError):
            BrierCalibrator("MP-04", window_cycles=0)
        with pytest.raises(ContractViolationError):
            BrierCalibrator("MP-04", weight_floor=1.1)

    def test_empty_agent_id_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            BrierCalibrator("MP-04").observe(
                "", {"BULL": 1.0, "BEAR": 0.0, "RANGE": 0.0}, "BULL"
            )


class TestRegimeEmbedder:
    FEATURES = {
        "log_return": 0.004,
        "ewm_volatility": 0.002,
        "spread_bps": 1.5,
        "macro_real_yield": -0.7,
    }

    def test_fixed_dimension_and_unit_norm(self) -> None:
        vector = RegimeEmbedder(8).embed(self.FEATURES)
        assert len(vector) == 8
        assert math.sqrt(sum(value * value for value in vector)) == pytest.approx(
            1.0
        )

    def test_mapping_order_invariant(self) -> None:
        forward = RegimeEmbedder(8).embed(self.FEATURES)
        reverse = RegimeEmbedder(8).embed(dict(reversed(list(self.FEATURES.items()))))
        assert forward == reverse

    def test_same_input_deterministic(self) -> None:
        first = RegimeEmbedder(16).embed(self.FEATURES)
        second = RegimeEmbedder(16).embed(self.FEATURES)
        assert first == second

    def test_distinct_features_change_embedding(self) -> None:
        first = RegimeEmbedder(8).embed(self.FEATURES)
        changed = dict(self.FEATURES)
        changed["log_return"] = -0.004
        assert first != RegimeEmbedder(8).embed(changed)

    def test_empty_or_nonfinite_features_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            RegimeEmbedder().embed({})
        with pytest.raises(ContractViolationError):
            RegimeEmbedder().embed({"x": math.inf})

    def test_invalid_dimension_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            RegimeEmbedder(0)

    def test_emit_cio12(self) -> None:
        output = RegimeEmbedder(8).emit(
            mission_profile_id="MP-04",
            instrument="XAUUSD",
            features=self.FEATURES,
            regime_label="BULL",
            window_start_ns=10,
            window_end_ns=20,
            parent_cio_ids=("world-1", "fill-1"),
        )
        assert output.instrument == "XAUUSD"
        assert output.regime_label == "BULL"
        assert len(output.vector) == 8
        assert output.envelope.parent_cio_ids == ("world-1", "fill-1")

    def test_invalid_window_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            RegimeEmbedder().emit(
                "MP-04", "XAUUSD", self.FEATURES, "BULL", 20, 10
            )
