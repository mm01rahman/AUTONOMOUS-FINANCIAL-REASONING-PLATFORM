"""Deterministic research backtest harness (Product 3, WP-IMP-0031).

The harness consumes immutable CIO-01 trade observations, delegates target
position selection to a replaceable Strategy protocol (EDR-001), executes at
deterministic spread/slippage/fee assumptions, and emits reproducible metrics
plus a SHA256 replay checksum (Article VI, NFR-004).
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from dataclasses import asdict, dataclass
from typing import Protocol

from afrp_runtime.common.errors import ContractViolationError
from afrp_runtime.contracts.cio import ObservationKind, RawObservation


class Strategy(Protocol):
    """Replaceable deterministic target-position policy."""

    def target_position(
        self, prices: tuple[float, ...], current_position: float
    ) -> float:
        """Return desired position units after observing ``prices``."""


@dataclass(frozen=True)
class BacktestConfig:
    """Execution and portfolio assumptions."""

    initial_cash: float = 100_000.0
    fee_bps: float = 0.2
    slippage_bps: float = 0.5
    max_position: float = 1.0
    annualization_periods: int = 252
    seed: int = 42

    def validate(self) -> None:
        """Validate financial and deterministic bounds."""
        if self.initial_cash <= 0.0:
            raise ContractViolationError("RESEARCH", "initial_cash must be positive")
        if self.fee_bps < 0.0 or self.slippage_bps < 0.0:
            raise ContractViolationError("RESEARCH", "costs must be non-negative")
        if self.max_position <= 0.0:
            raise ContractViolationError("RESEARCH", "max_position must be positive")
        if self.annualization_periods <= 0:
            raise ContractViolationError(
                "RESEARCH", "annualization_periods must be positive"
            )
        if self.seed != 42:
            raise ContractViolationError("RESEARCH", "AFRP deterministic seed must be 42")


@dataclass(frozen=True)
class Trade:
    """One simulated position adjustment."""

    sequence: int
    event_at_ns: int
    quantity: float
    execution_price: float
    fee: float
    resulting_position: float


@dataclass(frozen=True)
class BacktestResult:
    """Immutable research result and replay fingerprint."""

    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    annualized_sharpe: float
    trades: tuple[Trade, ...]
    equity_curve: tuple[float, ...]
    replay_checksum: str
    seed: int


@dataclass(frozen=True)
class MovingAverageCross:
    """Simple replaceable baseline strategy for harness verification."""

    short_window: int = 3
    long_window: int = 8
    target_units: float = 1.0

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= self.short_window:
            raise ContractViolationError(
                "RESEARCH", "require 0 < short_window < long_window"
            )
        if self.target_units <= 0.0:
            raise ContractViolationError("RESEARCH", "target_units must be positive")

    def target_position(
        self, prices: tuple[float, ...], current_position: float
    ) -> float:
        """Long above the slow mean, short below, flat until warm."""
        if len(prices) < self.long_window:
            return 0.0
        fast = sum(prices[-self.short_window :]) / self.short_window
        slow = sum(prices[-self.long_window :]) / self.long_window
        if fast > slow:
            return self.target_units
        if fast < slow:
            return -self.target_units
        return current_position


@dataclass(frozen=True)
class BuyAndHold:
    """Long-only harness control strategy."""

    target_units: float = 1.0

    def target_position(
        self, prices: tuple[float, ...], current_position: float
    ) -> float:
        del prices, current_position
        return self.target_units


class BacktestEngine:
    """Cost-aware deterministic event replay."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self.config.validate()

    def run(
        self, observations: list[RawObservation], strategy: Strategy
    ) -> BacktestResult:
        """Replay trade observations and liquidate at the final price.

        Raises:
            ContractViolationError: stream is empty, out of order, contains
                non-trades, or invalid prices.
        """
        self._validate_stream(observations)
        prices: list[float] = []
        cash = self.config.initial_cash
        position = 0.0
        trades: list[Trade] = []
        equity_curve: list[float] = []

        for observation in observations:
            prices.append(observation.price)
            requested = strategy.target_position(tuple(prices), position)
            target = max(
                -self.config.max_position,
                min(self.config.max_position, requested),
            )
            delta = target - position
            if abs(delta) > 1e-12:
                execution_price, fee = self._execution(delta, observation.price)
                cash -= delta * execution_price + fee
                position = target
                trades.append(
                    Trade(
                        sequence=observation.ingest_sequence,
                        event_at_ns=observation.event_at_ns,
                        quantity=delta,
                        execution_price=execution_price,
                        fee=fee,
                        resulting_position=position,
                    )
                )
            equity_curve.append(cash + position * observation.price)

        final_observation = observations[-1]
        if abs(position) > 1e-12:
            delta = -position
            execution_price, fee = self._execution(delta, final_observation.price)
            cash -= delta * execution_price + fee
            position = 0.0
            trades.append(
                Trade(
                    sequence=final_observation.ingest_sequence,
                    event_at_ns=final_observation.event_at_ns,
                    quantity=delta,
                    execution_price=execution_price,
                    fee=fee,
                    resulting_position=position,
                )
            )
            equity_curve[-1] = cash

        final_equity = equity_curve[-1]
        total_return = final_equity / self.config.initial_cash - 1.0
        max_drawdown = _max_drawdown(equity_curve)
        sharpe = _annualized_sharpe(
            equity_curve, self.config.annualization_periods
        )
        checksum = _checksum(self.config, trades, equity_curve)
        return BacktestResult(
            initial_equity=self.config.initial_cash,
            final_equity=final_equity,
            total_return=total_return,
            max_drawdown=max_drawdown,
            annualized_sharpe=sharpe,
            trades=tuple(trades),
            equity_curve=tuple(equity_curve),
            replay_checksum=checksum,
            seed=self.config.seed,
        )

    def _execution(self, delta: float, mid_price: float) -> tuple[float, float]:
        side = 1.0 if delta > 0.0 else -1.0
        execution = mid_price * (
            1.0 + side * self.config.slippage_bps / 10_000.0
        )
        fee = abs(delta) * execution * self.config.fee_bps / 10_000.0
        return execution, fee

    @staticmethod
    def _validate_stream(observations: list[RawObservation]) -> None:
        if not observations:
            raise ContractViolationError("RESEARCH", "empty observation stream")
        previous_sequence = 0
        previous_time = -1
        for observation in observations:
            if observation.kind is not ObservationKind.TRADE:
                raise ContractViolationError(
                    "RESEARCH", "backtest stream must contain CIO-01 trades only"
                )
            if observation.price <= 0.0:
                raise ContractViolationError("RESEARCH", "prices must be positive")
            if observation.ingest_sequence <= previous_sequence:
                raise ContractViolationError(
                    "RESEARCH", "ingest_sequence must be strictly increasing"
                )
            if observation.event_at_ns < previous_time:
                raise ContractViolationError(
                    "RESEARCH", "event timestamps must be monotonic"
                )
            previous_sequence = observation.ingest_sequence
            previous_time = observation.event_at_ns


def _max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    worst = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        drawdown = equity / peak - 1.0
        worst = min(worst, drawdown)
    return worst


def _annualized_sharpe(equity_curve: list[float], periods: int) -> float:
    if len(equity_curve) < 2:
        return 0.0
    returns = [
        equity_curve[index] / equity_curve[index - 1] - 1.0
        for index in range(1, len(equity_curve))
        if equity_curve[index - 1] != 0.0
    ]
    if len(returns) < 2:
        return 0.0
    volatility = statistics.stdev(returns)
    if volatility == 0.0:
        return 0.0
    return statistics.mean(returns) / volatility * math.sqrt(periods)


def _checksum(
    config: BacktestConfig, trades: list[Trade], equity_curve: list[float]
) -> str:
    payload = {
        "config": asdict(config),
        "trades": [asdict(trade) for trade in trades],
        "equity_curve": equity_curve,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
