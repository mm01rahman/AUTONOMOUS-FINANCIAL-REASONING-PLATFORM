"""Tests for the deterministic research backtest harness."""

from __future__ import annotations

from dataclasses import replace

import pytest
from afrp_research.backtest import (
    BacktestConfig,
    BacktestEngine,
    BuyAndHold,
    MovingAverageCross,
)
from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind, RawObservation
from afrp_runtime.contracts.envelope import make_envelope


def observations(prices: list[float]) -> list[RawObservation]:
    return [
        RawObservation(
            envelope=make_envelope(
                producer_subsystem_id="L1-ING",
                cognitive_cycle_id="research",
                mission_profile_id="MP-04",
                payload_repr=f"{index}:{price}",
                generated_at_ns=index,
            ),
            instrument="XAUUSD",
            kind=ObservationKind.TRADE,
            price=price,
            bid=0.0,
            ask=0.0,
            size=1.0,
            venue="REPLAY",
            ingest_sequence=index + 1,
            event_at_ns=index,
        )
        for index, price in enumerate(prices)
    ]


class TestBacktest:
    def test_rising_buy_and_hold_profitable_without_costs(self) -> None:
        result = BacktestEngine(
            BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
        ).run(observations([100.0, 102.0, 105.0]), BuyAndHold())
        assert result.final_equity == pytest.approx(100_005.0)
        assert result.total_return > 0.0
        assert len(result.trades) == 2  # entry + forced liquidation

    def test_costs_reduce_equity(self) -> None:
        stream = observations([100.0, 102.0, 105.0])
        free = BacktestEngine(
            BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
        ).run(stream, BuyAndHold())
        costly = BacktestEngine(
            BacktestConfig(fee_bps=5.0, slippage_bps=5.0)
        ).run(stream, BuyAndHold())
        assert costly.final_equity < free.final_equity

    def test_moving_average_can_short_falling_market(self) -> None:
        result = BacktestEngine(
            BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
        ).run(
            observations([110.0, 108.0, 106.0, 104.0, 102.0, 100.0]),
            MovingAverageCross(short_window=2, long_window=3),
        )
        assert any(trade.resulting_position < 0.0 for trade in result.trades)
        assert result.final_equity > result.initial_equity

    def test_replay_is_bit_exact(self) -> None:
        stream = observations([100.0, 101.0, 99.0, 102.0, 104.0])
        engine = BacktestEngine()
        strategy = MovingAverageCross(short_window=2, long_window=3)
        first = engine.run(stream, strategy)
        second = engine.run(stream, strategy)
        assert first == second
        assert len(first.replay_checksum) == 64
        assert first.seed == 42

    def test_position_is_clamped_to_limit(self) -> None:
        result = BacktestEngine(BacktestConfig(max_position=0.5)).run(
            observations([100.0, 101.0]), BuyAndHold(target_units=5.0)
        )
        assert max(abs(trade.resulting_position) for trade in result.trades) <= 0.5

    def test_drawdown_is_nonpositive(self) -> None:
        result = BacktestEngine(
            BacktestConfig(fee_bps=0.0, slippage_bps=0.0)
        ).run(observations([100.0, 120.0, 90.0, 110.0]), BuyAndHold())
        assert result.max_drawdown < 0.0

    def test_checksum_changes_with_cost_model(self) -> None:
        stream = observations([100.0, 101.0])
        first = BacktestEngine(BacktestConfig(fee_bps=0.0)).run(
            stream, BuyAndHold()
        )
        second = BacktestEngine(BacktestConfig(fee_bps=1.0)).run(
            stream, BuyAndHold()
        )
        assert first.replay_checksum != second.replay_checksum

    def test_empty_stream_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            BacktestEngine().run([], BuyAndHold())

    def test_non_trade_rejected(self) -> None:
        stream = observations([100.0])
        stream[0] = replace(stream[0], kind=ObservationKind.QUOTE)
        with pytest.raises(ContractViolationError):
            BacktestEngine().run(stream, BuyAndHold())

    def test_bad_sequence_rejected(self) -> None:
        stream = observations([100.0, 101.0])
        stream[1] = replace(stream[1], ingest_sequence=1)
        with pytest.raises(ContractViolationError, match="strictly increasing"):
            BacktestEngine().run(stream, BuyAndHold())

    def test_time_regression_rejected(self) -> None:
        stream = observations([100.0, 101.0])
        stream[1] = replace(stream[1], event_at_ns=-1)
        with pytest.raises(ContractViolationError, match="timestamps"):
            BacktestEngine().run(stream, BuyAndHold())

    @pytest.mark.parametrize(
        "config",
        [
            BacktestConfig(initial_cash=0.0),
            BacktestConfig(fee_bps=-1.0),
            BacktestConfig(slippage_bps=-1.0),
            BacktestConfig(max_position=0.0),
            BacktestConfig(annualization_periods=0),
            BacktestConfig(seed=7),
        ],
    )
    def test_invalid_configs_rejected(self, config: BacktestConfig) -> None:
        with pytest.raises(ContractViolationError):
            BacktestEngine(config)

    def test_invalid_moving_average_windows_rejected(self) -> None:
        with pytest.raises(ContractViolationError):
            MovingAverageCross(short_window=3, long_window=3)
        with pytest.raises(ContractViolationError):
            MovingAverageCross(short_window=2, long_window=3, target_units=0.0)
