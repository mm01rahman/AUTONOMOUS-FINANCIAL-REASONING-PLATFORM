"""Virtual portfolio accounting for paper trading state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from tools.paper_trading.shadow_execution import Fill


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    market_price: float = 0.0
    realized_pnl: float = 0.0


class VirtualPortfolio:
    """Cash-and-position ledger for shadow execution fills."""

    def __init__(self, initial_cash: float, leverage_limit: float = 3.0) -> None:
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.leverage_limit = leverage_limit
        self.positions: dict[str, Position] = {}
        self._high_watermark = initial_cash
        self._equity_series: list[tuple[datetime, float]] = []

    def apply_fill(self, fill: Fill) -> None:
        position = self.positions.setdefault(fill.symbol, Position(symbol=fill.symbol))
        signed_qty = fill.quantity if fill.side == "buy" else -fill.quantity
        gross_cash_flow = fill.price * fill.quantity

        increasing = (
            position.quantity == 0
            or (position.quantity > 0 and signed_qty > 0)
            or (position.quantity < 0 and signed_qty < 0)
        )

        if increasing:
            new_qty = position.quantity + signed_qty
            if abs(new_qty) > 1e-12:
                weighted_cost = (
                    position.avg_price * abs(position.quantity) + fill.price * fill.quantity
                )
                position.avg_price = weighted_cost / abs(new_qty)
            position.quantity = new_qty
        else:
            closing_qty = min(abs(position.quantity), fill.quantity)
            pnl_sign = 1.0 if position.quantity > 0 else -1.0
            position.realized_pnl += pnl_sign * (fill.price - position.avg_price) * closing_qty
            position.quantity += signed_qty
            if abs(position.quantity) < 1e-12:
                position.quantity = 0.0
                position.avg_price = 0.0

        fees = fill.spread_cost + fill.slippage_cost
        if fill.side == "buy":
            self.cash -= gross_cash_flow + fees
        else:
            self.cash += gross_cash_flow - fees

    def update_market_price(self, symbol: str, market_price: float) -> None:
        position = self.positions.setdefault(symbol, Position(symbol=symbol))
        position.market_price = market_price

    def mark(self, when: datetime) -> dict[str, float | str]:
        ts = when if when.tzinfo is not None else when.replace(tzinfo=UTC)
        state = self.state()
        self._equity_series.append((ts, state["equity"]))
        self._high_watermark = max(self._high_watermark, state["equity"])
        return {"timestamp": ts.isoformat(), **state}

    def state(self) -> dict[str, float]:
        gross_exposure = 0.0
        net_exposure = 0.0
        unrealized = 0.0
        realized = 0.0

        for position in self.positions.values():
            notional = position.market_price * position.quantity
            gross_exposure += abs(notional)
            net_exposure += notional
            realized += position.realized_pnl
            unrealized += (position.market_price - position.avg_price) * position.quantity

        equity = self.cash + sum(p.market_price * p.quantity for p in self.positions.values())
        leverage = gross_exposure / equity if equity > 0 else float("inf")
        drawdown = (
            (self._high_watermark - equity) / self._high_watermark
            if self._high_watermark > 0
            else 0.0
        )
        total_pnl = equity - self.initial_cash
        return {
            "cash": round(self.cash, 8),
            "equity": round(equity, 8),
            "gross_exposure": round(gross_exposure, 8),
            "net_exposure": round(net_exposure, 8),
            "leverage": round(leverage, 8),
            "realized_pnl": round(realized, 8),
            "unrealized_pnl": round(unrealized, 8),
            "total_pnl": round(total_pnl, 8),
            "drawdown": round(max(0.0, drawdown), 8),
        }

    @property
    def equity_series(self) -> list[tuple[datetime, float]]:
        return list(self._equity_series)

    def to_dict(self) -> dict[str, Any]:
        positions = {
            symbol: {
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "market_price": pos.market_price,
                "realized_pnl": pos.realized_pnl,
            }
            for symbol, pos in self.positions.items()
        }
        return {"state": self.state(), "positions": positions}
