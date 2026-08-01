"""Performance metrics for backtesting results."""

from __future__ import annotations

import math


def _annualised_return(equity_curve: list[float], bars_per_year: float = 252.0) -> float:
    """CAGR from equity curve (assumes daily bars by default)."""
    if len(equity_curve) < 2 or equity_curve[0] <= 0:
        return 0.0
    n_years = len(equity_curve) / bars_per_year
    final = equity_curve[-1]
    start = equity_curve[0]
    if start <= 0 or final <= 0 or n_years <= 0:
        return 0.0
    return float((final / start) ** (1.0 / n_years) - 1.0)


def _max_drawdown(equity_curve: list[float]) -> float:
    """Maximum drawdown as a positive fraction (e.g. 0.20 = 20%)."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _daily_returns(equity_curve: list[float]) -> list[float]:
    """Period-over-period returns from equity curve."""
    if len(equity_curve) < 2:
        return []
    returns = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        if prev <= 0:
            returns.append(0.0)
        else:
            returns.append((equity_curve[i] - prev) / prev)
    return returns


def _sharpe(returns: list[float], risk_free_rate: float, bars_per_year: float) -> float:
    """Annualised Sharpe ratio."""
    if not returns:
        return 0.0
    n = len(returns)
    rf_per_bar = risk_free_rate / bars_per_year
    excess = [r - rf_per_bar for r in returns]
    mean_excess = sum(excess) / n
    variance = sum((r - mean_excess) ** 2 for r in excess) / max(1, n - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return mean_excess / std * math.sqrt(bars_per_year)


def _sortino(returns: list[float], risk_free_rate: float, bars_per_year: float) -> float:
    """Annualised Sortino ratio using downside deviation."""
    if not returns:
        return 0.0
    n = len(returns)
    mean_r = sum(returns) / n
    rf_per_bar = risk_free_rate / bars_per_year
    excess_mean = mean_r - rf_per_bar
    downside = [r - rf_per_bar for r in returns if r < rf_per_bar]
    if not downside:
        return float("inf") if excess_mean > 0 else 0.0
    downside_var = sum(d**2 for d in downside) / len(downside)
    downside_std = math.sqrt(downside_var)
    if downside_std == 0:
        return 0.0
    return excess_mean / downside_std * math.sqrt(bars_per_year)


def _calmar(cagr: float, max_dd: float) -> float:
    """Calmar ratio = CAGR / max_drawdown."""
    if max_dd == 0:
        return 0.0
    return cagr / max_dd


def _win_rate(net_pnls: list[float]) -> float:
    """Fraction of trades with positive net PnL."""
    if not net_pnls:
        return 0.0
    wins = sum(1 for p in net_pnls if p > 0)
    return wins / len(net_pnls)


def _profit_factor(net_pnls: list[float]) -> float:
    """Gross profit / gross loss."""
    gross_profit = sum(p for p in net_pnls if p > 0)
    gross_loss = abs(sum(p for p in net_pnls if p < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def _expectancy(net_pnls: list[float]) -> float:
    """Average net PnL per trade."""
    if not net_pnls:
        return 0.0
    return sum(net_pnls) / len(net_pnls)


def _recovery_factor(total_return: float, max_dd: float) -> float:
    """Total return / max drawdown."""
    if max_dd == 0:
        return 0.0
    return total_return / max_dd


def compute_metrics(
    equity_curve: list[float],
    net_pnls: list[float],
    risk_free_rate: float = 0.04,
    bars_per_year: float = 252.0,
) -> dict[str, float]:
    """Compute the full performance metric suite.

    Args:
        equity_curve: Equity in USD at each bar.
        net_pnls: Net PnL for each *closed* trade.
        risk_free_rate: Annual risk-free rate (default 4%).
        bars_per_year: Trading bars per calendar year (default 252 days).

    Returns:
        Dictionary of named float metrics.
    """
    if not equity_curve:
        return {
            k: 0.0
            for k in (
                "total_return",
                "cagr",
                "sharpe",
                "sortino",
                "calmar",
                "max_drawdown",
                "win_rate",
                "profit_factor",
                "expectancy",
                "recovery_factor",
                "avg_trade",
                "trade_count",
            )
        }

    initial = equity_curve[0]
    final = equity_curve[-1]
    total_return = (final - initial) / initial if initial > 0 else 0.0
    cagr = _annualised_return(equity_curve, bars_per_year)
    max_dd = _max_drawdown(equity_curve)
    daily_rets = _daily_returns(equity_curve)
    sharpe = _sharpe(daily_rets, risk_free_rate, bars_per_year)
    sortino = _sortino(daily_rets, risk_free_rate, bars_per_year)
    calmar = _calmar(cagr, max_dd)
    win_rate = _win_rate(net_pnls)
    profit_factor = _profit_factor(net_pnls)
    expectancy = _expectancy(net_pnls)
    recovery = _recovery_factor(total_return, max_dd)
    avg_trade = sum(net_pnls) / len(net_pnls) if net_pnls else 0.0

    return {
        "total_return": round(total_return, 6),
        "cagr": round(cagr, 6),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "calmar": round(calmar, 4),
        "max_drawdown": round(max_dd, 6),
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "expectancy": round(expectancy, 4),
        "recovery_factor": round(recovery, 4),
        "avg_trade": round(avg_trade, 4),
        "trade_count": float(len(net_pnls)),
    }
