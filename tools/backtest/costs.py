"""Execution cost model for XAU/USD backtesting."""

from __future__ import annotations

from dataclasses import dataclass

# XAU/USD: 1 standard lot = 100 oz; 1 pip = $0.01/oz → $1/lot
PIP_VALUE_PER_LOT: float = 1.0
POINT_VALUE: float = 100.0  # $/lot per $1 price change (100 oz × $1/oz)


@dataclass
class ExecutionCosts:
    """Round-trip execution cost model for XAU/USD."""

    spread_pips: float
    slippage_pips: float
    commission_per_lot: float
    pip_value: float = PIP_VALUE_PER_LOT

    def total_round_trip_cost(self, lots: float) -> float:
        """Compute total cost in USD for a round-trip trade of *lots* size."""
        spread_cost = self.spread_pips * self.pip_value * lots
        slippage_cost = self.slippage_pips * self.pip_value * lots * 2
        commission = self.commission_per_lot * lots * 2
        return spread_cost + slippage_cost + commission

    def apply_to_price(self, price: float, direction: str, side: str) -> float:
        """Return the effective fill price after spread and slippage.

        Args:
            price: Mid-market price.
            direction: ``"long"`` or ``"short"``.
            side: ``"entry"`` or ``"exit"``.
        """
        pip_size = 0.01  # $0.01 per oz per pip
        half_spread = (self.spread_pips / 2) * pip_size
        slip = self.slippage_pips * pip_size

        if direction == "long":
            return price + half_spread + slip if side == "entry" else price - half_spread - slip
        # short
        return price - half_spread - slip if side == "entry" else price + half_spread + slip
