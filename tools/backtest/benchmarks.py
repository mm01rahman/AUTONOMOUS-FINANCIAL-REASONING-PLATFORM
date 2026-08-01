"""Baseline benchmark strategies for comparison against AFRP."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from tools.backtest.costs import POINT_VALUE, ExecutionCosts
from tools.backtest.engine import (
    BacktestConfig,
    BacktestResult,
    Trade,
    _calc_trade_pnl,
    _compute_checksum,
    _size_lots,
    _synthetic_ohlcv,
)
from tools.backtest.metrics import compute_metrics

logger = logging.getLogger(__name__)


# ── Base strategy ─────────────────────────────────────────────────────────────


class BaseStrategy(ABC):
    """Abstract base for benchmark strategies."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self._costs = ExecutionCosts(
            spread_pips=self.config.spread_pips,
            slippage_pips=self.config.slippage_pips,
            commission_per_lot=self.config.commission_per_lot,
        )

    @abstractmethod
    def generate_signal(
        self, bars: pd.DataFrame, idx: int
    ) -> tuple[str, float]:  # (action, confidence)
        """Return (action, confidence) for bar at *idx*."""

    def run(
        self,
        data: pd.DataFrame,
        regime: str = "full",
        dataset: str = "xauusd_daily",
    ) -> BacktestResult:
        """Execute the strategy over *data* and return a :class:`BacktestResult`."""
        cfg = self.config
        equity = cfg.initial_capital
        realized_pnl = 0.0
        position: str = "flat"
        open_trade: Trade | None = None
        closed_trades: list[Trade] = []
        equity_curve: list[float] = []
        timestamps: list[datetime] = []
        trade_counter = 0

        for idx in range(len(data)):
            row = data.iloc[idx]
            bar_close = float(row["close"])
            ts_raw: Any = data.index[idx]
            if isinstance(ts_raw, pd.Timestamp):
                bar_ts = ts_raw.to_pydatetime().replace(tzinfo=UTC)
            else:
                bar_ts = datetime(2000, 1, 1, tzinfo=UTC)

            action, confidence = self.generate_signal(data, idx)

            # Close trade on direction change or exit signal
            if open_trade is not None and (action == "flat" or action != position):
                exit_price = self._costs.apply_to_price(
                    bar_close, open_trade.direction, "exit"
                )
                holding = max(1, idx - int(open_trade.id.split("_")[1]))
                g, n, com, slip, spr = _calc_trade_pnl(
                    open_trade.direction,
                    open_trade.entry_price,
                    exit_price,
                    open_trade.lots,
                    self._costs,
                )
                closed_trades.append(
                    Trade(
                        id=open_trade.id,
                        entry_time=open_trade.entry_time,
                        exit_time=bar_ts,
                        direction=open_trade.direction,
                        entry_price=open_trade.entry_price,
                        exit_price=exit_price,
                        lots=open_trade.lots,
                        gross_pnl=g,
                        net_pnl=n,
                        commission=com,
                        slippage_cost=slip,
                        spread_cost=spr,
                        confidence=open_trade.confidence,
                        utility=0.5,
                        holding_bars=holding,
                    )
                )
                realized_pnl += n
                equity = cfg.initial_capital + realized_pnl
                open_trade = None
                position = "flat"

            # Open new trade
            if open_trade is None and action in ("long", "short"):
                entry_price = self._costs.apply_to_price(bar_close, action, "entry")
                lots = _size_lots(equity, entry_price, cfg)
                trade_counter += 1
                open_trade = Trade(
                    id=f"T_{idx:06d}_{trade_counter:04d}",
                    entry_time=bar_ts,
                    exit_time=None,
                    direction=action,
                    entry_price=entry_price,
                    exit_price=None,
                    lots=lots,
                    gross_pnl=0.0,
                    net_pnl=0.0,
                    commission=0.0,
                    slippage_cost=0.0,
                    spread_cost=0.0,
                    confidence=confidence,
                    utility=0.5,
                    holding_bars=0,
                )
                position = action

            # Mark-to-market
            unrealised = 0.0
            if open_trade is not None:
                sign = 1.0 if open_trade.direction == "long" else -1.0
                unrealised = (
                    sign
                    * (bar_close - open_trade.entry_price)
                    * open_trade.lots
                    * POINT_VALUE
                )

            equity_curve.append(cfg.initial_capital + realized_pnl + unrealised)
            timestamps.append(bar_ts)

        # Force close at end
        if open_trade is not None and len(data) > 0:
            final_close = float(data.iloc[-1]["close"])
            exit_price = self._costs.apply_to_price(
                final_close, open_trade.direction, "exit"
            )
            holding = max(1, len(data) - int(open_trade.id.split("_")[1]))
            g, n, com, slip, spr = _calc_trade_pnl(
                open_trade.direction,
                open_trade.entry_price,
                exit_price,
                open_trade.lots,
                self._costs,
            )
            closed_trades.append(
                Trade(
                    id=open_trade.id,
                    entry_time=open_trade.entry_time,
                    exit_time=timestamps[-1] if timestamps else datetime.now(UTC),
                    direction=open_trade.direction,
                    entry_price=open_trade.entry_price,
                    exit_price=exit_price,
                    lots=open_trade.lots,
                    gross_pnl=g,
                    net_pnl=n,
                    commission=com,
                    slippage_cost=slip,
                    spread_cost=spr,
                    confidence=open_trade.confidence,
                    utility=0.5,
                    holding_bars=holding,
                )
            )
            realized_pnl += n
            if equity_curve:
                equity_curve[-1] = cfg.initial_capital + realized_pnl

        net_pnls = [t.net_pnl for t in closed_trades]
        m = compute_metrics(equity_curve, net_pnls, cfg.risk_free_rate, cfg.bars_per_year)
        return BacktestResult(
            config=cfg,
            trades=closed_trades,
            equity_curve=equity_curve,
            timestamps=timestamps,
            regime=regime,
            dataset=dataset,
            total_return=m["total_return"],
            cagr=m["cagr"],
            sharpe=m["sharpe"],
            sortino=m["sortino"],
            calmar=m["calmar"],
            max_drawdown=m["max_drawdown"],
            win_rate=m["win_rate"],
            profit_factor=m["profit_factor"],
            expectancy=m["expectancy"],
            total_trades=len(closed_trades),
            checksum=_compute_checksum(closed_trades),
        )


# ── Concrete strategies ───────────────────────────────────────────────────────


class BuyAndHold(BaseStrategy):
    """Buy on the first bar and hold to the end."""

    def generate_signal(self, bars: pd.DataFrame, idx: int) -> tuple[str, float]:
        return "long", 1.0


class SMAcrossover(BaseStrategy):
    """SMA fast/slow crossover strategy."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        fast: int = 20,
        slow: int = 50,
    ) -> None:
        super().__init__(config)
        self.fast = fast
        self.slow = slow

    def generate_signal(self, bars: pd.DataFrame, idx: int) -> tuple[str, float]:
        if idx < self.slow:
            return "flat", 0.5
        fast_w = bars["close"].iloc[max(0, idx - self.fast + 1) : idx + 1]
        slow_w = bars["close"].iloc[max(0, idx - self.slow + 1) : idx + 1]
        fast_ma = float(fast_w.mean())
        slow_ma = float(slow_w.mean())
        if fast_ma > slow_ma:
            return "long", 0.7
        if fast_ma < slow_ma:
            return "short", 0.7
        return "flat", 0.5


class EMACrossover(BaseStrategy):
    """EMA fast/slow crossover strategy."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        fast: int = 12,
        slow: int = 26,
    ) -> None:
        super().__init__(config)
        self.fast = fast
        self.slow = slow

    def generate_signal(self, bars: pd.DataFrame, idx: int) -> tuple[str, float]:
        if idx < self.slow:
            return "flat", 0.5
        closes = bars["close"].iloc[: idx + 1]
        fast_ema = float(closes.ewm(span=self.fast, adjust=False).mean().iloc[-1])
        slow_ema = float(closes.ewm(span=self.slow, adjust=False).mean().iloc[-1])
        if fast_ema > slow_ema:
            return "long", 0.7
        if fast_ema < slow_ema:
            return "short", 0.7
        return "flat", 0.5


class Momentum(BaseStrategy):
    """Buy when price > N-day high, sell when below N-day low."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        lookback: int = 20,
    ) -> None:
        super().__init__(config)
        self.lookback = lookback

    def generate_signal(self, bars: pd.DataFrame, idx: int) -> tuple[str, float]:
        if idx < self.lookback:
            return "flat", 0.5
        window = bars["close"].iloc[max(0, idx - self.lookback) : idx]
        n_high = float(window.max())
        n_low = float(window.min())
        close = float(bars["close"].iloc[idx])
        if close > n_high:
            return "long", 0.65
        if close < n_low:
            return "short", 0.65
        return "flat", 0.5


class MeanReversion(BaseStrategy):
    """Fade extreme z-score moves."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        lookback: int = 20,
        z_threshold: float = 2.0,
    ) -> None:
        super().__init__(config)
        self.lookback = lookback
        self.z_threshold = z_threshold

    def generate_signal(self, bars: pd.DataFrame, idx: int) -> tuple[str, float]:
        if idx < self.lookback:
            return "flat", 0.5
        window = bars["close"].iloc[max(0, idx - self.lookback) : idx + 1]
        mean = float(window.mean())
        std = float(window.std())
        if std == 0:
            return "flat", 0.5
        close = float(bars["close"].iloc[idx])
        z = (close - mean) / std
        if z < -self.z_threshold:
            return "long", 0.70
        if z > self.z_threshold:
            return "short", 0.70
        return "flat", 0.5


class Breakout(BaseStrategy):
    """Donchian channel breakout."""

    def __init__(
        self,
        config: BacktestConfig | None = None,
        channel: int = 20,
    ) -> None:
        super().__init__(config)
        self.channel = channel

    def generate_signal(self, bars: pd.DataFrame, idx: int) -> tuple[str, float]:
        if idx < self.channel:
            return "flat", 0.5
        window = bars.iloc[max(0, idx - self.channel) : idx]
        upper = float(window["high"].max())
        lower = float(window["low"].min())
        close = float(bars["close"].iloc[idx])
        if close > upper:
            return "long", 0.68
        if close < lower:
            return "short", 0.68
        return "flat", 0.5


# ── Factory ───────────────────────────────────────────────────────────────────


def all_benchmarks(config: BacktestConfig | None = None) -> dict[str, BaseStrategy]:
    """Return one instance of each benchmark strategy."""
    cfg = config or BacktestConfig()
    return {
        "buy_and_hold": BuyAndHold(config=cfg),
        "sma_crossover": SMAcrossover(config=cfg),
        "ema_crossover": EMACrossover(config=cfg),
        "momentum": Momentum(config=cfg),
        "mean_reversion": MeanReversion(config=cfg),
        "breakout": Breakout(config=cfg),
    }


def run_all_benchmarks(
    data: pd.DataFrame,
    config: BacktestConfig | None = None,
    regime: str = "full",
    dataset: str = "xauusd_daily",
) -> dict[str, BacktestResult]:
    """Run all benchmark strategies and return named results."""
    results: dict[str, BacktestResult] = {}
    for name, strategy in all_benchmarks(config).items():
        try:
            results[name] = strategy.run(data, regime=regime, dataset=dataset)
            logger.info(
                "Benchmark '%s' complete: %.4f total return",
                name, results[name].total_return,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Benchmark '%s' failed: %s", name, exc)
            # Return empty result on failure
            synthetic = _synthetic_ohlcv("2020-01-01", 10)
            results[name] = strategy.run(synthetic, regime=regime, dataset="synthetic")
    return results
