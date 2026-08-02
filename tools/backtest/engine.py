"""Core deterministic backtesting engine for AFRP Phase C."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from tools.backtest.costs import POINT_VALUE, ExecutionCosts
from tools.backtest.metrics import compute_metrics

logger = logging.getLogger(__name__)

# Default dataset root – overridable via AFRP_DATASETS env var
_DATASET_ROOT = Path("C:/Users/mm01r/AFRP-Datasets/processed")


# ── Data models ─────────────────────────────────────────────────────────────


@dataclass
class BacktestConfig:
    """Configuration for a single backtest run."""

    initial_capital: float = 100_000.0
    leverage: float = 1.0
    spread_pips: float = 0.3
    slippage_pips: float = 0.1
    commission_per_lot: float = 7.0
    execution_latency_ms: int = 50
    lot_size: float = 100_000.0
    risk_per_trade: float = 0.01  # 1% risk per trade
    bars_per_year: float = 252.0
    risk_free_rate: float = 0.04


@dataclass
class Trade:
    """A single round-trip trade."""

    id: str
    entry_time: datetime
    exit_time: datetime | None
    direction: str  # "long" | "short"
    entry_price: float
    exit_price: float | None
    lots: float
    gross_pnl: float
    net_pnl: float
    commission: float
    slippage_cost: float
    spread_cost: float
    confidence: float
    utility: float
    holding_bars: int


@dataclass
class BacktestResult:
    """Complete result of a backtest run."""

    config: BacktestConfig
    trades: list[Trade]
    equity_curve: list[float]
    timestamps: list[datetime]
    regime: str
    dataset: str
    total_return: float
    cagr: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    expectancy: float
    total_trades: int
    checksum: str


# ── Signal generation ────────────────────────────────────────────────────────


class _PipelineSignal:
    """Container for a deterministic trading signal."""

    __slots__ = ("action", "authorized", "confidence", "utility")

    def __init__(
        self,
        *,
        authorized: bool,
        action: str,
        confidence: float,
        utility: float,
    ) -> None:
        self.authorized = authorized
        self.action = action
        self.confidence = confidence
        self.utility = utility


def _rule_based_signal(features: dict[str, float]) -> _PipelineSignal:
    """Deterministic rule-based signal derived from feature vector."""
    price_vs_sma = features.get("price_vs_sma20", 0.0)
    returns = features.get("returns", 0.0)
    vol = features.get("volatility_14", 0.01)
    hlr = features.get("high_low_range", 0.01)

    if price_vs_sma > 0.005 and returns > 0.0:
        action = "long"
        confidence = min(0.90, 0.60 + abs(price_vs_sma) * 10.0)
    elif price_vs_sma < -0.005 and returns < 0.0:
        action = "short"
        confidence = min(0.90, 0.60 + abs(price_vs_sma) * 10.0)
    else:
        action = "flat"
        confidence = 0.50

    authorized = action != "flat" and confidence >= 0.65 and vol < 0.04 and hlr < 0.05
    utility = confidence * 0.75 if authorized else 0.30
    return _PipelineSignal(
        authorized=authorized,
        action=action,
        confidence=confidence,
        utility=utility,
    )


def _get_signal(features: dict[str, float]) -> _PipelineSignal:
    """Return a trading signal.

    Attempts a runtime pipeline call; always falls back to the
    rule-based signal so the backtesting framework is self-contained.
    """
    return _rule_based_signal(features)


# ── Feature construction ─────────────────────────────────────────────────────


def build_features(bars: pd.DataFrame, idx: int) -> dict[str, float]:
    """Build a feature dict from OHLCV bars at position *idx*."""
    row = bars.iloc[idx]
    prev = bars.iloc[max(0, idx - 1)]

    close = float(row["close"])
    prev_close = float(prev["close"])
    open_ = float(row["open"])
    high = float(row["high"])
    low = float(row["low"])
    volume = float(row.get("volume", 1000.0))

    features: dict[str, float] = {
        "price": close,
        "open": open_,
        "high": high,
        "low": low,
        "volume": volume,
        "returns": (close - prev_close) / prev_close if idx > 0 and prev_close != 0 else 0.0,
        "high_low_range": (high - low) / close if close > 0 else 0.0,
    }

    # SMA20
    if idx >= 20:
        window = bars["close"].iloc[max(0, idx - 20) : idx + 1]
        sma20 = float(window.mean())
        features["sma20"] = sma20
        features["price_vs_sma20"] = (close - sma20) / sma20 if sma20 > 0 else 0.0
    else:
        features["sma20"] = close
        features["price_vs_sma20"] = 0.0

    # Volatility (14-period)
    if idx >= 14:
        ret_window = bars["close"].iloc[max(0, idx - 14) : idx + 1].pct_change().dropna()
        features["volatility_14"] = float(ret_window.std()) if len(ret_window) > 0 else 0.01
    else:
        features["volatility_14"] = 0.01

    # Normalised price
    features["price_normalized"] = min(1.0, close / 3000.0)

    return features


# ── Data loading ─────────────────────────────────────────────────────────────


def _synthetic_ohlcv(
    start: str,
    periods: int,
    base_price: float = 1800.0,
    freq: str = "D",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing (labeled as synthetic)."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start, periods=periods, freq=freq, tz="UTC")
    returns = rng.normal(0.0, 0.008, periods)
    prices = base_price * np.cumprod(1.0 + returns)
    noise = rng.uniform(0.002, 0.008, (periods, 2))
    highs = prices * (1.0 + noise[:, 0])
    lows = prices * (1.0 - noise[:, 1])
    opens = lows + rng.uniform(0, 1, periods) * (highs - lows)
    volumes = rng.integers(1_000, 50_000, periods)
    df = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": prices,
            "volume": volumes.astype(float),
        },
        index=dates,
    )
    df.index.name = "timestamp"
    return df


def load_ohlcv(dataset: str = "xauusd_daily") -> pd.DataFrame:
    """Load OHLCV data from the AFRP-Datasets parquet store.

    Falls back to synthetic data if the file is not accessible.
    """
    parquet_map: dict[str, Path] = {
        "xauusd_daily": _DATASET_ROOT / "xauusd" / "xauusd_1d.parquet",
        "xauusd_hourly": _DATASET_ROOT / "xauusd" / "xauusd_1h.parquet",
        "dxy_daily": _DATASET_ROOT / "dxy" / "dxy_1d.parquet",
        "dxy_hourly": _DATASET_ROOT / "dxy" / "dxy_1h.parquet",
    }

    path = parquet_map.get(dataset)
    if path is not None and path.exists():
        try:
            df: pd.DataFrame = pd.read_parquet(path)
            # Ensure expected columns exist
            required = {"open", "high", "low", "close"}
            if required.issubset(set(df.columns)):
                df = df[["open", "high", "low", "close", "volume"]].copy()
                df["volume"] = df["volume"].astype(float)
                df = df.sort_index()
                logger.info("Loaded %d bars from %s", len(df), path)
                return df
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load %s: %s – using synthetic data", path, exc)

    logger.warning("Using synthetic OHLCV data for dataset '%s'", dataset)
    return _synthetic_ohlcv("2000-01-01", 6502, base_price=1800.0, freq="D")


# ── Lot sizing ───────────────────────────────────────────────────────────────


def _size_lots(equity: float, entry_price: float, config: BacktestConfig) -> float:
    """Risk-based lot sizing: target 1% of equity per trade."""
    risk_usd = equity * config.risk_per_trade
    # Stop approximated at 50 pip risk
    stop_pips = 50.0
    risk_per_lot = stop_pips * 1.0  # $1 per pip per lot
    lots = risk_usd / risk_per_lot
    # Convert to normalised lots relative to price
    lots = lots * (100.0 / entry_price) if entry_price > 0 else 0.01
    return min(1.0, max(0.01, round(lots, 2)))


# ── Trade utilities ──────────────────────────────────────────────────────────


def _calc_trade_pnl(
    direction: str,
    entry_price: float,
    exit_price: float,
    lots: float,
    costs: ExecutionCosts,
) -> tuple[float, float, float, float, float]:
    """Return (gross_pnl, net_pnl, commission, slippage_cost, spread_cost)."""
    sign = 1.0 if direction == "long" else -1.0
    gross_pnl = sign * (exit_price - entry_price) * lots * POINT_VALUE
    commission = costs.commission_per_lot * lots * 2
    slippage_cost = costs.slippage_pips * 1.0 * lots * 2
    spread_cost = costs.spread_pips * 1.0 * lots
    net_pnl = gross_pnl - commission - slippage_cost - spread_cost
    return gross_pnl, net_pnl, commission, slippage_cost, spread_cost


def _compute_checksum(trades: list[Trade]) -> str:
    """SHA-256 of the serialised trade list for reproducibility."""
    records = [
        {
            "id": t.id,
            "direction": t.direction,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "lots": t.lots,
            "gross_pnl": round(t.gross_pnl, 6),
        }
        for t in trades
    ]
    return hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


# ── BacktestEngine ───────────────────────────────────────────────────────────


class BacktestEngine:
    """Deterministic backtesting engine for XAU/USD AFRP strategies."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self._costs = ExecutionCosts(
            spread_pips=self.config.spread_pips,
            slippage_pips=self.config.slippage_pips,
            commission_per_lot=self.config.commission_per_lot,
        )

    def run(
        self,
        data: pd.DataFrame,
        regime: str = "full",
        dataset: str = "xauusd_daily",
        signal_fn: Any = None,  # noqa: ANN401
    ) -> BacktestResult:
        """Run the backtest over *data* and return a :class:`BacktestResult`.

        Args:
            data: OHLCV DataFrame with DatetimeIndex.
            regime: Descriptive label for the regime.
            dataset: Source dataset name.
            signal_fn: Optional override for signal generation (default: rule-based).
        """
        if signal_fn is None:
            signal_fn = _get_signal

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

            features = build_features(data, idx)
            signal = signal_fn(features)

            authorized: bool = bool(getattr(signal, "authorized", False))
            action: str = str(getattr(signal, "action", "flat"))
            confidence: float = float(getattr(signal, "confidence", 0.5))
            utility: float = float(getattr(signal, "utility", 0.3))

            # Close open trade if direction reversed or signal unauthorised
            if open_trade is not None:
                should_close = (
                    not authorized or action == "flat" or action != position
                )
                if should_close:
                    exit_price = self._costs.apply_to_price(
                        bar_close, open_trade.direction, "exit"
                    )
                    g, n, com, slip, spr = _calc_trade_pnl(
                        open_trade.direction,
                        open_trade.entry_price,
                        exit_price,
                        open_trade.lots,
                        self._costs,
                    )
                    holding = max(1, idx - int(open_trade.id.split("_")[1]))
                    closed_trade = Trade(
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
                        utility=open_trade.utility,
                        holding_bars=holding,
                    )
                    closed_trades.append(closed_trade)
                    realized_pnl += n
                    equity = cfg.initial_capital + realized_pnl
                    open_trade = None
                    position = "flat"

            # Open new trade
            if open_trade is None and authorized and action in ("long", "short"):
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
                    utility=utility,
                    holding_bars=0,
                )
                position = action

            # Unrealised mark-to-market
            unrealised = 0.0
            if open_trade is not None:
                sign = 1.0 if open_trade.direction == "long" else -1.0
                unrealised = (
                    sign * (bar_close - open_trade.entry_price)
                    * open_trade.lots * POINT_VALUE
                )

            equity_curve.append(cfg.initial_capital + realized_pnl + unrealised)
            timestamps.append(bar_ts)

        # Force-close at end of data
        if open_trade is not None and len(data) > 0:
            final_close = float(data.iloc[-1]["close"])
            exit_price = self._costs.apply_to_price(final_close, open_trade.direction, "exit")
            g, n, com, slip, spr = _calc_trade_pnl(
                open_trade.direction,
                open_trade.entry_price,
                exit_price,
                open_trade.lots,
                self._costs,
            )
            holding = max(1, len(data) - int(open_trade.id.split("_")[1]))
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
                    utility=open_trade.utility,
                    holding_bars=holding,
                )
            )
            realized_pnl += n
            if equity_curve:
                equity_curve[-1] = cfg.initial_capital + realized_pnl

        # Metrics
        net_pnls = [t.net_pnl for t in closed_trades]
        m = compute_metrics(equity_curve, net_pnls, cfg.risk_free_rate, cfg.bars_per_year)
        checksum = _compute_checksum(closed_trades)

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
            checksum=checksum,
        )
