# AFRP Phase B — Verification & Validation Framework

Phase B adds a deterministic, reproducible V&V framework without redesigning Runtime.

## Components

- `tools/verification/replay.py`: replay scheduler, timeline events, deterministic clock, replay controller.
- `tools/verification/scenarios.py`: permanent scenario library loader and required scenario checks.
- `tools/verification/verifier.py`: end-to-end cross-layer verification (L1→L6) and deterministic replay checks.
- `tools/verification/math_checks.py`: PCR5, mass conservation, calibration and replay invariant checks.
- `tools/verification/statistical.py`: Sharpe/Sortino/Calmar/profit-factor/drawdown and calibration metrics.
- `tools/verification/stress.py`: missing data/feed loss, long replay, latency stress checks.
- `tools/verification/performance.py`: replay throughput and p99 decision latency benchmarks.
- `tools/verification/regression.py`: regression orchestration across replay/math/stress/performance/statistics.
- `tools/verification/dashboard.py`: Markdown, JSON, HTML, and GitHub summary rendering.
- `tools/verification/cli.py`: end-to-end runner.

## Scenario Library

Scenarios live in `09-validation/scenarios/` and include:

- FOMC
- CPI
- Core CPI
- PPI
- NFP
- Flash Crash
- COVID
- Banking Crisis
- Weekend Gap
- Liquidity Vacuum
- Strong Trend
- Range Market
- High Volatility
- Low Volatility

## Usage

```bash
uv run python -m tools.phaseb_validation
uv run python -m tools.phaseb_validation --github-summary
```

Reports are emitted under `09-validation/reports/`:

- `runtime_verification.json`
- `mathematical_verification.json`
- `stress_report.json`
- `performance_report.json`
- `statistical_report.json`
- `regression_report.json`
- `validation_dashboard.json`
- `validation_dashboard.md`
- `validation_dashboard.html`

## CI Integration

Workflow: `.github/workflows/phaseb-validation.yml`

- Runs on pull requests and pushes to `main`
- Executes full Phase B validation runner
- Uploads reports as artifacts
