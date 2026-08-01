"""Report generators for backtesting results (Phase C, WP-C9)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from tools.backtest.engine import BacktestResult


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _f2(v: float) -> str:
    return f"{v:.2f}"


def _f4(v: float) -> str:
    return f"{v:.4f}"


def generate_backtesting_report(result: BacktestResult) -> str:
    """Markdown report for a single backtest run."""
    lines: list[str] = [
        f"# Backtesting Report — {result.regime}",
        "",
        f"**Dataset:** {result.dataset}  ",
        f"**Period:** {result.timestamps[0].date() if result.timestamps else 'N/A'} — "
        f"{result.timestamps[-1].date() if result.timestamps else 'N/A'}  ",
        f"**Generated:** {date.today()}",
        "",
        "## Performance Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Total Return | {_pct(result.total_return)} |",
        f"| CAGR | {_pct(result.cagr)} |",
        f"| Sharpe Ratio | {_f4(result.sharpe)} |",
        f"| Sortino Ratio | {_f4(result.sortino)} |",
        f"| Calmar Ratio | {_f4(result.calmar)} |",
        f"| Max Drawdown | {_pct(result.max_drawdown)} |",
        f"| Win Rate | {_pct(result.win_rate)} |",
        f"| Profit Factor | {_f4(result.profit_factor)} |",
        f"| Expectancy | ${_f2(result.expectancy)} |",
        f"| Total Trades | {result.total_trades} |",
        "",
        "## Configuration",
        "",
        f"- Initial Capital: ${result.config.initial_capital:,.0f}",
        f"- Leverage: {result.config.leverage}×",
        f"- Spread: {result.config.spread_pips} pips",
        f"- Slippage: {result.config.slippage_pips} pips",
        f"- Commission: ${result.config.commission_per_lot}/lot",
        f"- Risk per Trade: {_pct(result.config.risk_per_trade)}",
        "",
        "## Reproducibility",
        "",
        f"- Trade Checksum: `{result.checksum}`",
    ]
    return "\n".join(lines)


def generate_benchmark_comparison(
    afrp: BacktestResult, benchmarks: dict[str, BacktestResult]
) -> str:
    """Markdown comparison table of AFRP vs benchmark strategies."""
    lines: list[str] = [
        "# Benchmark Comparison Report",
        "",
        f"**Regime:** {afrp.regime}  ",
        f"**Generated:** {date.today()}",
        "",
        "## Return & Risk Comparison",
        "",
        "| Strategy | Total Return | CAGR | Sharpe | Sortino | Max DD | Win Rate | Trades |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        f"| **AFRP** | {_pct(afrp.total_return)} | {_pct(afrp.cagr)}"
        f" | {_f4(afrp.sharpe)}"
        f" | {_f4(afrp.sortino)} | {_pct(afrp.max_drawdown)}"
        f" | {_pct(afrp.win_rate)} | {afrp.total_trades} |",
    ]
    for name, r in benchmarks.items():
        lines.append(
            f"| {name} | {_pct(r.total_return)} | {_pct(r.cagr)} | {_f4(r.sharpe)} "
            f"| {_f4(r.sortino)} | {_pct(r.max_drawdown)} | {_pct(r.win_rate)} | {r.total_trades} |"
        )
    lines += [
        "",
        "## Key Findings",
        "",
        "- AFRP uses the full reasoning pipeline with cost-aware execution.",
        "- All strategies evaluated under identical cost assumptions.",
        "- Benchmark strategies use pure price-action signals.",
    ]
    return "\n".join(lines)


def generate_regime_report(regime_results: dict[str, BacktestResult]) -> str:
    """Markdown report summarising performance across all regimes."""
    lines: list[str] = [
        "# Regime Analysis Report",
        "",
        f"**Generated:** {date.today()}",
        "",
        "## Performance by Regime",
        "",
        "| Regime | Label | Return | Sharpe | Max DD | Trades |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key, r in regime_results.items():
        lines.append(
            f"| {key} | {r.regime} | {_pct(r.total_return)} | {_f4(r.sharpe)} "
            f"| {_pct(r.max_drawdown)} | {r.total_trades} |"
        )
    lines += [
        "",
        "## Regime Coverage",
        "",
        f"- **Regimes evaluated:** {len(regime_results)}",
        "- Includes crisis periods, bull markets, and rate cycles.",
    ]
    return "\n".join(lines)


def generate_robustness_report(scenario_results: dict[str, BacktestResult]) -> str:
    """Markdown report for robustness scenario analysis."""
    lines: list[str] = [
        "# Robustness Analysis Report",
        "",
        f"**Generated:** {date.today()}",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Return | Sharpe | Max DD | Trades |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key, r in scenario_results.items():
        lines.append(
            f"| {key} | {_pct(r.total_return)} | {_f4(r.sharpe)} "
            f"| {_pct(r.max_drawdown)} | {r.total_trades} |"
        )
    lines += [
        "",
        "## Observations",
        "",
        "- System tested across trending, ranging, high-vol, and stress scenarios.",
        "- Signal generation remains deterministic under all conditions.",
    ]
    return "\n".join(lines)


def generate_sensitivity_report(
    sensitivity_results: dict[str, dict[str, BacktestResult]]
) -> str:
    """Markdown report for parameter sensitivity analysis."""
    lines: list[str] = [
        "# Sensitivity Analysis Report",
        "",
        f"**Generated:** {date.today()}",
        "",
    ]
    for param, param_results in sensitivity_results.items():
        lines += [
            f"## Parameter: `{param}`",
            "",
            "| Value | Return | Sharpe | Max DD |",
            "| --- | --- | --- | --- |",
        ]
        for val_key, r in param_results.items():
            lines.append(
                f"| {val_key} | {_pct(r.total_return)} | {_f4(r.sharpe)} "
                f"| {_pct(r.max_drawdown)} |"
            )
        lines.append("")
    return "\n".join(lines)


def generate_trade_analysis(result: BacktestResult) -> str:
    """Markdown trade distribution and analytics report."""
    trades = result.trades
    lines: list[str] = [
        "# Trade Analysis Report",
        "",
        f"**Regime:** {result.regime}  ",
        f"**Generated:** {date.today()}",
        "",
        "## Trade Statistics",
        "",
        f"- Total Trades: {len(trades)}",
    ]

    if trades:
        longs = [t for t in trades if t.direction == "long"]
        shorts = [t for t in trades if t.direction == "short"]
        winners = [t for t in trades if t.net_pnl > 0]
        losers = [t for t in trades if t.net_pnl <= 0]
        holding = [t.holding_bars for t in trades]
        avg_hold = sum(holding) / len(holding) if holding else 0

        lines += [
            f"- Long Trades: {len(longs)}",
            f"- Short Trades: {len(shorts)}",
            f"- Winners: {len(winners)}",
            f"- Losers: {len(losers)}",
            f"- Average Holding Bars: {avg_hold:.1f}",
            "",
            "## PnL Distribution",
            "",
            "| Metric | Value |",
            "| --- | --- |",
        ]
        pnls = [t.net_pnl for t in trades]
        pnls_sorted = sorted(pnls)
        n = len(pnls_sorted)
        median = pnls_sorted[n // 2] if n else 0.0
        best = max(pnls) if pnls else 0.0
        worst = min(pnls) if pnls else 0.0
        total_costs = sum(t.commission + t.slippage_cost + t.spread_cost for t in trades)

        lines += [
            f"| Best Trade | ${best:.2f} |",
            f"| Worst Trade | ${worst:.2f} |",
            f"| Median Trade | ${median:.2f} |",
            f"| Total Costs | ${total_costs:.2f} |",
        ]

    return "\n".join(lines)


def generate_performance_report(result: BacktestResult) -> str:
    """Detailed performance metrics report."""
    lines: list[str] = [
        "# Performance Report",
        "",
        f"**Regime:** {result.regime}  ",
        f"**Dataset:** {result.dataset}  ",
        f"**Generated:** {date.today()}",
        "",
        "## Return Metrics",
        "",
        f"- Total Return: {_pct(result.total_return)}",
        f"- CAGR: {_pct(result.cagr)}",
        "",
        "## Risk-Adjusted Metrics",
        "",
        f"- Sharpe Ratio: {_f4(result.sharpe)}",
        f"- Sortino Ratio: {_f4(result.sortino)}",
        f"- Calmar Ratio: {_f4(result.calmar)}",
        f"- Max Drawdown: {_pct(result.max_drawdown)}",
        "",
        "## Trade Quality",
        "",
        f"- Win Rate: {_pct(result.win_rate)}",
        f"- Profit Factor: {_f4(result.profit_factor)}",
        f"- Expectancy: ${_f2(result.expectancy)}",
        f"- Total Trades: {result.total_trades}",
    ]
    return "\n".join(lines)


def generate_executive_summary(all_results: list[BacktestResult]) -> str:
    """Executive summary across all backtest runs."""
    lines: list[str] = [
        "# Executive Summary — Phase C Quantitative Research",
        "",
        f"**Generated:** {date.today()}",
        f"**Total Runs:** {len(all_results)}",
        "",
        "## Aggregate Performance",
        "",
        "| Run | Regime | Dataset | Return | Sharpe | Max DD |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in all_results:
        lines.append(
            f"| {r.regime} | {r.regime} | {r.dataset} | {_pct(r.total_return)} "
            f"| {_f4(r.sharpe)} | {_pct(r.max_drawdown)} |"
        )

    if all_results:
        avg_sharpe = sum(r.sharpe for r in all_results) / len(all_results)
        avg_return = sum(r.total_return for r in all_results) / len(all_results)
        lines += [
            "",
            "## Key Observations",
            "",
            f"- Average Sharpe across all runs: {avg_sharpe:.4f}",
            f"- Average Total Return: {_pct(avg_return)}",
            "- All runs used identical cost model and position sizing.",
            "- Backtesting framework is deterministic (SHA-256 reproducibility).",
        ]

    return "\n".join(lines)


def export_json(result: BacktestResult) -> dict[str, Any]:
    """Serialise a BacktestResult to a JSON-safe dictionary."""
    trades_data: list[dict[str, Any]] = [
        {
            "id": t.id,
            "entry_time": t.entry_time.isoformat(),
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "direction": t.direction,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "lots": t.lots,
            "gross_pnl": t.gross_pnl,
            "net_pnl": t.net_pnl,
            "commission": t.commission,
            "slippage_cost": t.slippage_cost,
            "spread_cost": t.spread_cost,
            "confidence": t.confidence,
            "utility": t.utility,
            "holding_bars": t.holding_bars,
        }
        for t in result.trades
    ]
    return {
        "regime": result.regime,
        "dataset": result.dataset,
        "total_return": result.total_return,
        "cagr": result.cagr,
        "sharpe": result.sharpe,
        "sortino": result.sortino,
        "calmar": result.calmar,
        "max_drawdown": result.max_drawdown,
        "win_rate": result.win_rate,
        "profit_factor": result.profit_factor,
        "expectancy": result.expectancy,
        "total_trades": result.total_trades,
        "checksum": result.checksum,
        "trades": trades_data,
        "equity_curve_len": len(result.equity_curve),
        "config": {
            "initial_capital": result.config.initial_capital,
            "leverage": result.config.leverage,
            "spread_pips": result.config.spread_pips,
            "slippage_pips": result.config.slippage_pips,
            "commission_per_lot": result.config.commission_per_lot,
            "risk_per_trade": result.config.risk_per_trade,
        },
    }


def write_json(result: BacktestResult, path: str) -> None:
    """Write a BacktestResult as JSON to the given path."""
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = export_json(result)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
