"""Unit tests for the AFRP backtesting engine (WP-C1)."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from tools.backtest.costs import PIP_VALUE_PER_LOT, POINT_VALUE, ExecutionCosts
from tools.backtest.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestResult,
    Trade,
    _calc_trade_pnl,
    _compute_checksum,
    _rule_based_signal,
    _size_lots,
    _synthetic_ohlcv,
    build_features,
    load_ohlcv,
)
from tools.backtest.metrics import compute_metrics
from tools.backtest.regimes import REGIMES, filter_by_dates

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def small_df() -> pd.DataFrame:
    """50 bars of synthetic OHLCV data."""
    return _synthetic_ohlcv("2024-01-01", 50, base_price=2000.0)


@pytest.fixture
def large_df() -> pd.DataFrame:
    """300 bars of synthetic OHLCV data."""
    return _synthetic_ohlcv("2022-01-01", 300, base_price=1900.0)


@pytest.fixture
def default_config() -> BacktestConfig:
    return BacktestConfig()


@pytest.fixture
def default_costs() -> ExecutionCosts:
    return ExecutionCosts(spread_pips=0.3, slippage_pips=0.1, commission_per_lot=7.0)


@pytest.fixture
def sample_trade() -> Trade:
    return Trade(
        id="T_000001_0001",
        entry_time=datetime(2024, 1, 2, tzinfo=UTC),
        exit_time=datetime(2024, 1, 10, tzinfo=UTC),
        direction="long",
        entry_price=2000.0,
        exit_price=2050.0,
        lots=0.1,
        gross_pnl=500.0,
        net_pnl=480.0,
        commission=1.4,
        slippage_cost=0.2,
        spread_cost=0.03,
        confidence=0.75,
        utility=0.6,
        holding_bars=8,
    )


# ── 1. BacktestConfig defaults ────────────────────────────────────────────────


def test_config_defaults() -> None:
    cfg = BacktestConfig()
    assert cfg.initial_capital == 100_000.0
    assert cfg.leverage == 1.0
    assert cfg.spread_pips == 0.3
    assert cfg.slippage_pips == 0.1
    assert cfg.commission_per_lot == 7.0
    assert cfg.execution_latency_ms == 50
    assert cfg.lot_size == 100_000.0
    assert cfg.risk_per_trade == 0.01
    assert cfg.bars_per_year == 252.0
    assert cfg.risk_free_rate == 0.04


def test_config_custom_values() -> None:
    cfg = BacktestConfig(initial_capital=50_000.0, risk_per_trade=0.02, leverage=2.0)
    assert cfg.initial_capital == 50_000.0
    assert cfg.risk_per_trade == 0.02
    assert cfg.leverage == 2.0


# ── 2. ExecutionCosts ─────────────────────────────────────────────────────────


def test_costs_round_trip(default_costs: ExecutionCosts) -> None:
    cost = default_costs.total_round_trip_cost(1.0)
    assert cost > 0.0
    # Expected: spread=0.3, slippage=0.1*2=0.2, commission=7*2=14
    expected = 0.3 * 1.0 + 0.1 * 1.0 * 2 + 7.0 * 1.0 * 2
    assert abs(cost - expected) < 0.001


def test_costs_scales_with_lots(default_costs: ExecutionCosts) -> None:
    cost1 = default_costs.total_round_trip_cost(0.5)
    cost2 = default_costs.total_round_trip_cost(1.0)
    assert abs(cost2 - 2 * cost1) < 0.001


def test_costs_apply_long_entry(default_costs: ExecutionCosts) -> None:
    fill = default_costs.apply_to_price(2000.0, "long", "entry")
    assert fill > 2000.0  # buy higher than mid


def test_costs_apply_long_exit(default_costs: ExecutionCosts) -> None:
    fill = default_costs.apply_to_price(2000.0, "long", "exit")
    assert fill < 2000.0  # sell lower than mid


def test_costs_apply_short_entry(default_costs: ExecutionCosts) -> None:
    fill = default_costs.apply_to_price(2000.0, "short", "entry")
    assert fill < 2000.0  # short entry sells below mid


def test_costs_apply_short_exit(default_costs: ExecutionCosts) -> None:
    fill = default_costs.apply_to_price(2000.0, "short", "exit")
    assert fill > 2000.0  # short exit buys above mid


def test_pip_value_constant() -> None:
    assert PIP_VALUE_PER_LOT == 1.0
    assert POINT_VALUE == 100.0


# ── 3. Trade PnL calculation ──────────────────────────────────────────────────


def test_long_trade_profit(default_costs: ExecutionCosts) -> None:
    g, n, com, slip, spr = _calc_trade_pnl("long", 2000.0, 2050.0, 0.1, default_costs)
    # gross = (2050 - 2000) * 0.1 * 100 = 50 * 0.1 * 100 = 500
    assert abs(g - 500.0) < 0.01
    assert n < g  # net < gross due to costs


def test_long_trade_loss(default_costs: ExecutionCosts) -> None:
    g, n, _, _, _ = _calc_trade_pnl("long", 2000.0, 1950.0, 0.1, default_costs)
    assert g < 0  # losing long trade


def test_short_trade_profit(default_costs: ExecutionCosts) -> None:
    g, n, _, _, _ = _calc_trade_pnl("short", 2050.0, 2000.0, 0.1, default_costs)
    # gross = (2050 - 2000) * 0.1 * 100 = 500
    assert abs(g - 500.0) < 0.01
    assert n < g


def test_short_trade_loss(default_costs: ExecutionCosts) -> None:
    g, _, _, _, _ = _calc_trade_pnl("short", 2000.0, 2050.0, 0.1, default_costs)
    assert g < 0


def test_trade_costs_components(default_costs: ExecutionCosts) -> None:
    g, n, com, slip, spr = _calc_trade_pnl("long", 2000.0, 2100.0, 1.0, default_costs)
    assert com == pytest.approx(14.0)  # 7.0 * 1.0 * 2
    assert slip == pytest.approx(0.2)  # 0.1 * 1.0 * 2
    assert spr == pytest.approx(0.3)  # 0.3 * 1.0


# ── 4. Feature vector construction ───────────────────────────────────────────


def test_build_features_keys(small_df: pd.DataFrame) -> None:
    features = build_features(small_df, 30)
    required_keys = {
        "price", "returns", "sma20", "price_vs_sma20", "volatility_14", "high_low_range",
    }
    assert required_keys.issubset(set(features.keys()))


def test_build_features_first_bar(small_df: pd.DataFrame) -> None:
    features = build_features(small_df, 0)
    assert features["returns"] == 0.0
    assert features["price_vs_sma20"] == 0.0


def test_build_features_types(small_df: pd.DataFrame) -> None:
    features = build_features(small_df, 25)
    for k, v in features.items():
        assert isinstance(v, float), f"Feature '{k}' is not float: {type(v)}"


def test_build_features_price_normalized(small_df: pd.DataFrame) -> None:
    features = build_features(small_df, 25)
    assert 0.0 < features["price_normalized"] <= 1.0


# ── 5. Rule-based signal ──────────────────────────────────────────────────────


def test_rule_signal_flat_on_zero_bias() -> None:
    features = {
        "price_vs_sma20": 0.0, "returns": 0.0,
        "volatility_14": 0.01, "high_low_range": 0.005,
    }
    sig = _rule_based_signal(features)
    assert sig.action == "flat"
    assert not sig.authorized


def test_rule_signal_long_on_positive_momentum() -> None:
    features = {
        "price_vs_sma20": 0.02, "returns": 0.005,
        "volatility_14": 0.01, "high_low_range": 0.005,
    }
    sig = _rule_based_signal(features)
    assert sig.action == "long"
    assert sig.authorized


def test_rule_signal_short_on_negative_momentum() -> None:
    features = {
        "price_vs_sma20": -0.02, "returns": -0.005,
        "volatility_14": 0.01, "high_low_range": 0.005,
    }
    sig = _rule_based_signal(features)
    assert sig.action == "short"
    assert sig.authorized


def test_rule_signal_no_auth_high_vol() -> None:
    features = {
        "price_vs_sma20": 0.02, "returns": 0.01,
        "volatility_14": 0.10, "high_low_range": 0.01,
    }
    sig = _rule_based_signal(features)
    # High volatility should suppress authorisation
    assert not sig.authorized


# ── 6. Lot sizing ─────────────────────────────────────────────────────────────


def test_lot_sizing_bounded() -> None:
    cfg = BacktestConfig(initial_capital=100_000.0, risk_per_trade=0.01)
    lots = _size_lots(100_000.0, 2000.0, cfg)
    assert 0.01 <= lots <= 1.0


def test_lot_sizing_scales_with_equity() -> None:
    cfg = BacktestConfig(initial_capital=100_000.0, risk_per_trade=0.01)
    lots_small = _size_lots(10_000.0, 2000.0, cfg)
    lots_large = _size_lots(100_000.0, 2000.0, cfg)
    assert lots_large >= lots_small


# ── 7. Regime filtering ───────────────────────────────────────────────────────


def test_all_regimes_defined() -> None:
    required = {
        "gfc_2008", "gold_bull_2011", "gold_collapse_2013",
        "covid_2020", "inflation_2022", "rate_cycle_2024",
        "historical_2025", "available_2026",
    }
    assert required.issubset(set(REGIMES.keys()))


def test_filter_by_regime_returns_subset(large_df: pd.DataFrame) -> None:
    # Use a date range that overlaps with the synthetic data
    full_len = len(large_df)
    for _key, meta in REGIMES.items():
        filtered = filter_by_dates(large_df, meta["start"], meta["end"])
        assert len(filtered) <= full_len


def test_filter_by_dates_narrows_data(large_df: pd.DataFrame) -> None:
    filtered = filter_by_dates(large_df, "2022-06-01", "2022-09-30")
    assert len(filtered) <= len(large_df)


# ── 8. Checksum reproducibility ──────────────────────────────────────────────


def test_checksum_is_hex_string(sample_trade: Trade) -> None:
    checksum = _compute_checksum([sample_trade])
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)


def test_checksum_deterministic(sample_trade: Trade) -> None:
    c1 = _compute_checksum([sample_trade])
    c2 = _compute_checksum([sample_trade])
    assert c1 == c2


def test_checksum_changes_with_trade() -> None:
    t1 = Trade(
        id="T1", entry_time=datetime(2024, 1, 1, tzinfo=UTC),
        exit_time=None, direction="long", entry_price=2000.0,
        exit_price=None, lots=0.1, gross_pnl=100.0, net_pnl=90.0,
        commission=1.4, slippage_cost=0.2, spread_cost=0.03,
        confidence=0.7, utility=0.5, holding_bars=5,
    )
    t2 = Trade(
        id="T2", entry_time=datetime(2024, 1, 1, tzinfo=UTC),
        exit_time=None, direction="short", entry_price=2000.0,
        exit_price=None, lots=0.1, gross_pnl=-100.0, net_pnl=-110.0,
        commission=1.4, slippage_cost=0.2, spread_cost=0.03,
        confidence=0.7, utility=0.5, holding_bars=5,
    )
    assert _compute_checksum([t1]) != _compute_checksum([t2])


# ── 9. Metrics computation ────────────────────────────────────────────────────


def test_metrics_empty() -> None:
    m = compute_metrics([], [], 0.04, 252.0)
    assert m["total_return"] == 0.0
    assert m["sharpe"] == 0.0


def test_metrics_flat_equity() -> None:
    equity = [100_000.0] * 100
    m = compute_metrics(equity, [], 0.04, 252.0)
    assert m["max_drawdown"] == 0.0
    assert m["total_return"] == 0.0


def test_metrics_positive_return() -> None:
    equity = [100_000.0 + i * 100 for i in range(252)]
    m = compute_metrics(equity, [100.0] * 20, 0.04, 252.0)
    assert m["total_return"] > 0
    assert m["win_rate"] == 1.0


def test_metrics_max_drawdown() -> None:
    equity = [100_000.0, 110_000.0, 90_000.0, 95_000.0]
    m = compute_metrics(equity, [], 0.04, 252.0)
    # From peak 110k to trough 90k = ~18.2% drawdown
    assert m["max_drawdown"] > 0.1


def test_metrics_profit_factor() -> None:
    pnls = [100.0, -50.0, 200.0, -30.0]
    m = compute_metrics([100_000.0] * 4, pnls, 0.04, 252.0)
    assert m["profit_factor"] == pytest.approx(300.0 / 80.0, rel=0.01)


def test_metrics_win_rate() -> None:
    pnls = [100.0, -50.0, 200.0, -30.0, 10.0]
    m = compute_metrics([100_000.0] * 5, pnls, 0.04, 252.0)
    assert m["win_rate"] == pytest.approx(3.0 / 5.0, rel=0.01)


# ── 10. BacktestEngine integration ────────────────────────────────────────────


def test_engine_runs_without_error(small_df: pd.DataFrame) -> None:
    engine = BacktestEngine()
    result = engine.run(small_df, regime="test")
    assert isinstance(result, BacktestResult)


def test_engine_result_has_equity_curve(small_df: pd.DataFrame) -> None:
    engine = BacktestEngine()
    result = engine.run(small_df)
    assert len(result.equity_curve) == len(small_df)


def test_engine_result_checksum_valid(small_df: pd.DataFrame) -> None:
    engine = BacktestEngine()
    result = engine.run(small_df)
    assert len(result.checksum) == 64


def test_engine_reproducible(small_df: pd.DataFrame) -> None:
    engine = BacktestEngine()
    r1 = engine.run(small_df, regime="test")
    r2 = engine.run(small_df, regime="test")
    assert r1.checksum == r2.checksum


def test_engine_empty_df() -> None:
    empty = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    engine = BacktestEngine()
    result = engine.run(empty)
    assert result.total_trades == 0
    assert result.equity_curve == []


def test_engine_single_bar() -> None:
    df = _synthetic_ohlcv("2024-01-01", 1, base_price=2000.0)
    engine = BacktestEngine()
    result = engine.run(df)
    assert isinstance(result, BacktestResult)


def test_engine_all_loss_scenario() -> None:
    """Ensure graceful handling when equity drops severely."""
    rng = np.random.default_rng(99)
    dates = pd.date_range("2024-01-01", periods=100, freq="D", tz="UTC")
    prices = 2000.0 * np.cumprod(1.0 - rng.uniform(0.001, 0.005, 100))
    df = pd.DataFrame(
        {
            "open": prices,
            "high": prices * 1.002,
            "low": prices * 0.998,
            "close": prices,
            "volume": 10000.0,
        },
        index=dates,
    )
    engine = BacktestEngine()
    result = engine.run(df)
    assert isinstance(result, BacktestResult)
    assert result.max_drawdown >= 0.0


# ── 11. Synthetic data generation ────────────────────────────────────────────


def test_synthetic_ohlcv_shape() -> None:
    df = _synthetic_ohlcv("2020-01-01", 100)
    assert df.shape == (100, 5)
    assert set(df.columns) == {"open", "high", "low", "close", "volume"}


def test_synthetic_ohlcv_prices_positive() -> None:
    df = _synthetic_ohlcv("2020-01-01", 50)
    assert (df["close"] > 0).all()
    assert (df["high"] >= df["low"]).all()


def test_load_ohlcv_returns_dataframe() -> None:
    df = load_ohlcv("xauusd_daily")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert {"open", "high", "low", "close"}.issubset(set(df.columns))
