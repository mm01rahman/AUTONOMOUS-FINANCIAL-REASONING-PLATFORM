# Phase D Paper Trading & Live Shadow Execution

## Scope

Phase D adds a **paper-trading + live shadow execution** platform only. It does not
route orders to any broker and does not perform real-money execution.

## Package

`tools/paper_trading/`

- `gateway.py`: provider interfaces, deterministic live-sim adapters for XAU/USD,
  DXY, UST10Y, economic calendar, geopolitical sentiment; reconnect/backoff,
  heartbeat checks, UTC normalization, deterministic merge ordering.
- `shadow_execution.py`: simulated order lifecycle with fill/partial/failure,
  spread/slippage/latency modeling.
- `portfolio.py`: virtual portfolio state (cash, positions, exposure, leverage,
  drawdown, PnL).
- `decision_log.py`: deterministic JSONL decision log with required fields and
  reproducible SHA-256 checksums.
- `monitoring.py`: rolling and period metrics (daily/weekly/monthly, sharpe,
  sortino, calmar, win-rate, profit-factor, drawdown, exposure).
- `risk.py`: risk limits and alert generation (position, concentration,
  exposure, leverage, volatility, confidence drift).
- `dashboard.py`: JSON/Markdown/HTML operational dashboard outputs.
- `reporting.py`: daily/weekly/monthly reports plus runtime/learning/risk/log
  artifacts.
- `orchestrator.py`: deterministic continuous paper-trading loop.
- `cli.py`: CLI entrypoint.
- `tools/paper_trading_run.py`: top-level shim.

## Reproducibility and Audit

- All timestamps are normalized to UTC.
- Feed merge ordering is deterministic.
- Decision logs are canonical JSONL (`sort_keys=True`) with per-run checksum.
- Output artifacts are machine-readable for CI artifact upload.

## No-Broker Guarantee

`shadow_execution.py` is simulation-only and returns `simulated_only: true` on
all execution records. No broker SDKs/endpoints are used.

## Run

```bash
uv run python -m tools.paper_trading.cli --iterations 48 --output-dir 11-research/phase-d
```
