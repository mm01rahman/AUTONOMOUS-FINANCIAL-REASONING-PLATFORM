"""Deterministic paper-only shadow execution engine (no broker routing)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any


@dataclass(frozen=True)
class OrderRequest:
    order_id: str
    symbol: str
    side: str
    quantity: float
    decision_confidence: float


@dataclass(frozen=True)
class Fill:
    fill_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: datetime
    latency_ms: int
    spread_cost: float
    slippage_cost: float


@dataclass(frozen=True)
class ExecutionResult:
    order_id: str
    status: str
    fills: list[Fill]
    reason: str
    simulated_only: bool = True


@dataclass(frozen=True)
class ExecutionConfig:
    spread_bps: float = 2.0
    slippage_bps: float = 3.5
    base_latency_ms: int = 35
    latency_jitter_ms: int = 15
    partial_fill_probability: float = 0.30
    failure_probability: float = 0.10
    random_seed: int = 42


class ShadowExecutionEngine:
    """Paper-trading execution simulator with deterministic randomness."""

    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self.config = config or ExecutionConfig()
        self._rng = Random(self.config.random_seed)
        self._fill_counter = 0

    def execute(self, order: OrderRequest, mid_price: float, now: datetime) -> ExecutionResult:
        ts = now if now.tzinfo is not None else now.replace(tzinfo=UTC)
        if order.quantity <= 0:
            return ExecutionResult(
                order_id=order.order_id, status="rejected", fills=[], reason="invalid_qty"
            )

        if self._rng.random() < self.config.failure_probability:
            return ExecutionResult(
                order_id=order.order_id, status="failed", fills=[], reason="simulated_failure"
            )

        quantities = self._build_fill_quantities(order.quantity)
        fills: list[Fill] = []
        for idx, quantity in enumerate(quantities):
            fill_ts = ts + timedelta(milliseconds=self._latency_ms())
            fill_price, spread_cost, slippage_cost = self._fill_price(mid_price, order.side)
            fills.append(
                Fill(
                    fill_id=f"F{self._fill_counter:08d}",
                    order_id=order.order_id,
                    symbol=order.symbol,
                    side=order.side,
                    quantity=round(quantity, 8),
                    price=round(fill_price, 8),
                    status="partial" if idx < len(quantities) - 1 else "filled",
                    timestamp=fill_ts,
                    latency_ms=self._latency_ms(),
                    spread_cost=spread_cost,
                    slippage_cost=slippage_cost,
                )
            )
            self._fill_counter += 1

        status = "partial" if len(quantities) > 1 else "filled"
        return ExecutionResult(order_id=order.order_id, status=status, fills=fills, reason="ok")

    def _latency_ms(self) -> int:
        jitter = self._rng.randint(0, self.config.latency_jitter_ms)
        return self.config.base_latency_ms + jitter

    def _build_fill_quantities(self, quantity: float) -> list[float]:
        if self._rng.random() >= self.config.partial_fill_probability:
            return [quantity]
        ratio = 0.35 + self._rng.random() * 0.4
        first = quantity * ratio
        second = max(0.0, quantity - first)
        if second <= 1e-9:
            return [quantity]
        return [first, second]

    def _fill_price(self, mid_price: float, side: str) -> tuple[float, float, float]:
        spread_frac = self.config.spread_bps / 10_000
        slip_frac = self.config.slippage_bps / 10_000
        spread_shift = mid_price * spread_frac / 2
        slip_shift = mid_price * slip_frac * (0.6 + self._rng.random() * 0.8)
        if side == "buy":
            fill_price = mid_price + spread_shift + slip_shift
        else:
            fill_price = mid_price - spread_shift - slip_shift
        return fill_price, spread_shift, slip_shift

    @staticmethod
    def summarize(result: ExecutionResult) -> dict[str, Any]:
        return {
            "order_id": result.order_id,
            "status": result.status,
            "fill_count": len(result.fills),
            "reason": result.reason,
            "simulated_only": result.simulated_only,
            "fills": [
                {
                    "fill_id": fill.fill_id,
                    "qty": fill.quantity,
                    "price": fill.price,
                    "latency_ms": fill.latency_ms,
                    "status": fill.status,
                }
                for fill in result.fills
            ],
        }
