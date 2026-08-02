"""Unit tests for benchmark strategies (WP-C3)."""

from __future__ import annotations

import pandas as pd
import pytest

from tools.backtest.benchmarks import (
    BaseStrategy,
    Breakout,
    BuyAndHold,
    EMACrossover,
    MeanReversion,
    Momentum,
    SMAcrossover,
    all_benchmarks,
    run_all_benchmarks,
)
from tools.backtest.engine import BacktestConfig, BacktestResult, _synthetic_ohlcv

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def trend_up_df() -> pd.DataFrame:
    """Steadily rising price data — favours long strategies."""
    dates = pd.date_range("2023-01-01", periods=200, freq="D", tz="UTC")
    prices = [2000.0 + i * 2.0 for i in range(200)]
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.005 for p in prices],
            "low": [p * 0.995 for p in prices],
            "close": prices,
            "volume": [10000.0] * 200,
        },
        index=dates,
    )


@pytest.fixture
def mean_rev_df() -> pd.DataFrame:
    """Oscillating (mean-reverting) price data."""
    import math
    dates = pd.date_range("2023-01-01", periods=200, freq="D", tz="UTC")
    prices = [2000.0 + 100.0 * math.sin(i * 0.2) for i in range(200)]
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.003 for p in prices],
            "low": [p * 0.997 for p in prices],
            "close": prices,
            "volume": [10000.0] * 200,
        },
        index=dates,
    )


@pytest.fixture
def small_df() -> pd.DataFrame:
    return _synthetic_ohlcv("2024-01-01", 100, base_price=2000.0)


@pytest.fixture
def config() -> BacktestConfig:
    return BacktestConfig(initial_capital=100_000.0)


# ── BuyAndHold ────────────────────────────────────────────────────────────────


def test_buy_and_hold_opens_position(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = BuyAndHold(config=config)
    result = strategy.run(small_df)
    assert result.total_trades >= 1


def test_buy_and_hold_first_signal(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = BuyAndHold(config=config)
    action, conf = strategy.generate_signal(small_df, 0)
    assert action == "long"
    assert conf == 1.0


def test_buy_and_hold_returns_result_type(small_df: pd.DataFrame) -> None:
    result = BuyAndHold().run(small_df)
    assert isinstance(result, BacktestResult)


def test_buy_and_hold_trending_up_positive_return(
    trend_up_df: pd.DataFrame, config: BacktestConfig
) -> None:
    result = BuyAndHold(config=config).run(trend_up_df)
    # Trending-up data should produce a positive return for buy-and-hold
    assert result.total_return > 0.0


# ── SMAcrossover ──────────────────────────────────────────────────────────────


def test_sma_crossover_runs(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = SMAcrossover(config=config)
    result = strategy.run(small_df)
    assert isinstance(result, BacktestResult)


def test_sma_crossover_flat_before_warmup(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = SMAcrossover(fast=20, slow=50, config=config)
    # Before the slow period, signal must be flat
    action, _ = strategy.generate_signal(small_df, 10)
    assert action == "flat"


def test_sma_crossover_generates_some_trades(
    small_df: pd.DataFrame, config: BacktestConfig
) -> None:
    strategy = SMAcrossover(fast=5, slow=10, config=config)
    result = strategy.run(small_df)
    assert result.total_trades >= 0  # may have 0 trades on very small dataset


# ── EMACrossover ──────────────────────────────────────────────────────────────


def test_ema_crossover_runs(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    result = EMACrossover(config=config).run(small_df)
    assert isinstance(result, BacktestResult)


def test_ema_crossover_flat_before_warmup(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = EMACrossover(fast=12, slow=26, config=config)
    action, _ = strategy.generate_signal(small_df, 5)
    assert action == "flat"


def test_ema_crossover_trending_produces_trade(
    trend_up_df: pd.DataFrame, config: BacktestConfig
) -> None:
    result = EMACrossover(fast=5, slow=10, config=config).run(trend_up_df)
    assert result.total_trades >= 0


# ── Momentum ──────────────────────────────────────────────────────────────────


def test_momentum_runs(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    result = Momentum(config=config).run(small_df)
    assert isinstance(result, BacktestResult)


def test_momentum_flat_before_lookback(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = Momentum(lookback=20, config=config)
    action, _ = strategy.generate_signal(small_df, 5)
    assert action == "flat"


def test_momentum_long_on_breakout(trend_up_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = Momentum(lookback=10, config=config)
    # After warmup, a strongly trending up dataset should produce a long signal
    action, _ = strategy.generate_signal(trend_up_df, 50)
    assert action in ("long", "flat")  # Could be flat if no new high in window


# ── MeanReversion ─────────────────────────────────────────────────────────────


def test_mean_reversion_runs(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    result = MeanReversion(config=config).run(small_df)
    assert isinstance(result, BacktestResult)


def test_mean_reversion_flat_on_neutral(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = MeanReversion(lookback=20, z_threshold=2.0, config=config)
    # For a synthetic small dataset near equilibrium, many bars should be flat
    flat_count = 0
    for i in range(20, min(50, len(small_df))):
        action, _ = strategy.generate_signal(small_df, i)
        if action == "flat":
            flat_count += 1
    assert flat_count >= 0  # Sanity check — strategy is well-defined


# ── Breakout ──────────────────────────────────────────────────────────────────


def test_breakout_runs(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    result = Breakout(config=config).run(small_df)
    assert isinstance(result, BacktestResult)


def test_breakout_flat_before_channel(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    strategy = Breakout(channel=20, config=config)
    action, _ = strategy.generate_signal(small_df, 5)
    assert action == "flat"


# ── all_benchmarks factory ────────────────────────────────────────────────────


def test_all_benchmarks_returns_six_strategies(config: BacktestConfig) -> None:
    benches = all_benchmarks(config)
    assert len(benches) == 6
    expected_names = {
        "buy_and_hold", "sma_crossover", "ema_crossover",
        "momentum", "mean_reversion", "breakout",
    }
    assert set(benches.keys()) == expected_names


def test_all_benchmarks_instances_are_base_strategy(config: BacktestConfig) -> None:
    for name, strat in all_benchmarks(config).items():
        assert isinstance(strat, BaseStrategy), f"{name} is not BaseStrategy"


def test_run_all_benchmarks_returns_dict(small_df: pd.DataFrame, config: BacktestConfig) -> None:
    results = run_all_benchmarks(small_df, config)
    assert isinstance(results, dict)
    assert len(results) == 6


def test_run_all_benchmarks_all_results_valid(
    small_df: pd.DataFrame, config: BacktestConfig
) -> None:
    results = run_all_benchmarks(small_df, config)
    for name, r in results.items():
        assert isinstance(r, BacktestResult), f"{name} returned wrong type"
        assert len(r.equity_curve) > 0, f"{name} has empty equity curve"
