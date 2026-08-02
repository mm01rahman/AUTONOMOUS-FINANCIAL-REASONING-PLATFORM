"""Research campaign orchestrator — WP-C1 through WP-C9."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from tools.backtest.benchmarks import run_all_benchmarks
from tools.backtest.engine import BacktestConfig, BacktestEngine, BacktestResult, load_ohlcv
from tools.backtest.regimes import REGIMES, ROBUSTNESS_SCENARIOS, filter_by_dates
from tools.backtest.reports import (
    export_json,
    generate_backtesting_report,
    generate_benchmark_comparison,
    generate_executive_summary,
    generate_performance_report,
    generate_regime_report,
    generate_robustness_report,
    generate_sensitivity_report,
    generate_trade_analysis,
)

logger = logging.getLogger(__name__)

RESEARCH_DIR = Path(__file__).resolve().parents[2] / "11-research"
RESULTS_DIR = RESEARCH_DIR / "results"


@dataclass
class CampaignResult:
    """Aggregated results from all Phase C work packages."""

    regime_results: dict[str, BacktestResult]
    benchmark_results: dict[str, BacktestResult]
    robustness_results: dict[str, BacktestResult]
    sensitivity_results: dict[str, dict[str, BacktestResult]]
    reports: dict[str, str]
    json_exports: list[str] = field(default_factory=list)


class ResearchCampaign:
    """Orchestrates WP-C1 through WP-C9 in sequence."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self.config = config or BacktestConfig()
        self.engine = BacktestEngine(self.config)

    # ── WP-C2: Regime evaluations ─────────────────────────────────────────

    def _run_regimes(self, full_data: object) -> dict[str, BacktestResult]:
        import pandas as pd

        if not isinstance(full_data, pd.DataFrame):
            raise TypeError("full_data must be a DataFrame")

        results: dict[str, BacktestResult] = {}
        for key, meta in REGIMES.items():
            try:
                regime_data = filter_by_dates(full_data, meta["start"], meta["end"])
                if len(regime_data) < 5:
                    logger.warning("Regime %s has only %d bars, skipping", key, len(regime_data))
                    continue
                result = self.engine.run(regime_data, regime=meta["label"], dataset="xauusd_daily")
                results[key] = result
                logger.info(
                    "Regime %s: %.4f return, %d trades",
                    key, result.total_return, result.total_trades,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Regime %s failed: %s", key, exc)
        return results

    # ── WP-C3: Benchmarks ─────────────────────────────────────────────────

    def _run_benchmarks(self, full_data: object) -> dict[str, BacktestResult]:
        import pandas as pd

        if not isinstance(full_data, pd.DataFrame):
            raise TypeError("full_data must be a DataFrame")

        return run_all_benchmarks(full_data, self.config, regime="full", dataset="xauusd_daily")

    # ── WP-C6: Robustness ─────────────────────────────────────────────────

    def _run_robustness(self, full_data: object) -> dict[str, BacktestResult]:
        import pandas as pd

        if not isinstance(full_data, pd.DataFrame):
            raise TypeError("full_data must be a DataFrame")

        results: dict[str, BacktestResult] = {}
        for key, meta in ROBUSTNESS_SCENARIOS.items():
            try:
                scenario_data = filter_by_dates(full_data, meta["start"], meta["end"])
                if len(scenario_data) < 3:
                    continue
                result = self.engine.run(
                    scenario_data, regime=meta["label"], dataset="xauusd_daily"
                )
                results[key] = result
            except Exception as exc:  # noqa: BLE001
                logger.warning("Scenario %s failed: %s", key, exc)
        return results

    # ── WP-C7: Sensitivity ────────────────────────────────────────────────

    def _run_sensitivity(
        self, sample_data: object
    ) -> dict[str, dict[str, BacktestResult]]:
        import pandas as pd

        if not isinstance(sample_data, pd.DataFrame):
            raise TypeError("sample_data must be a DataFrame")

        results: dict[str, dict[str, BacktestResult]] = {}

        # Spread sensitivity
        spread_runs: dict[str, BacktestResult] = {}
        for spread in (0.1, 0.3, 0.5, 1.0, 2.0):
            cfg = BacktestConfig(spread_pips=spread)
            eng = BacktestEngine(cfg)
            try:
                spread_runs[str(spread)] = eng.run(
                    sample_data, regime="sensitivity", dataset="xauusd_daily"
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Spread sensitivity %s failed: %s", spread, exc)
        results["spread_pips"] = spread_runs

        # Risk per trade sensitivity
        risk_runs: dict[str, BacktestResult] = {}
        for risk in (0.005, 0.01, 0.02, 0.03):
            cfg = BacktestConfig(risk_per_trade=risk)
            eng = BacktestEngine(cfg)
            try:
                risk_runs[str(risk)] = eng.run(
                    sample_data, regime="sensitivity", dataset="xauusd_daily"
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Risk sensitivity %s failed: %s", risk, exc)
        results["risk_per_trade"] = risk_runs

        return results

    # ── Full campaign ─────────────────────────────────────────────────────

    def run(self) -> CampaignResult:
        """Execute all Phase C work packages in sequence."""
        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("Loading OHLCV data...")
        full_data = load_ohlcv("xauusd_daily")

        # Select a 2-year sample for sensitivity (faster)
        sample_data = filter_by_dates(full_data, "2023-01-01", "2024-12-31")
        if len(sample_data) < 10:
            sample_data = full_data.iloc[-500:].copy()

        # WP-C2: Regime evaluations
        logger.info("WP-C2: Running regime evaluations...")
        regime_results = self._run_regimes(full_data)

        # WP-C3: Benchmark strategies
        logger.info("WP-C3: Running benchmark strategies...")
        benchmark_results = self._run_benchmarks(full_data)

        # AFRP full run for benchmark comparison
        afrp_full = self.engine.run(full_data, regime="full", dataset="xauusd_daily")

        # WP-C6: Robustness
        logger.info("WP-C6: Running robustness scenarios...")
        robustness_results = self._run_robustness(full_data)

        # WP-C7: Sensitivity
        logger.info("WP-C7: Running sensitivity analysis...")
        sensitivity_results = self._run_sensitivity(sample_data)

        # WP-C9: Generate all reports
        logger.info("WP-C9: Generating reports...")
        reports: dict[str, str] = {}

        # Backtesting report (full run)
        reports["backtesting_report"] = generate_backtesting_report(afrp_full)

        # Benchmark comparison
        reports["benchmark_comparison"] = generate_benchmark_comparison(
            afrp_full, benchmark_results
        )

        # Regime analysis
        reports["regime_analysis"] = generate_regime_report(regime_results)

        # Robustness report
        reports["robustness_report"] = generate_robustness_report(robustness_results)

        # Sensitivity report
        reports["sensitivity_report"] = generate_sensitivity_report(sensitivity_results)

        # Trade analysis
        reports["trade_analysis"] = generate_trade_analysis(afrp_full)

        # Performance report
        reports["performance_report"] = generate_performance_report(afrp_full)

        # Executive summary
        all_results = [afrp_full, *list(regime_results.values())]
        reports["executive_summary"] = generate_executive_summary(all_results)

        # Write reports to 11-research/
        for name, content in reports.items():
            report_path = RESEARCH_DIR / f"{name}.md"
            report_path.write_text(content, encoding="utf-8")
            logger.info("Wrote %s", report_path)

        # Write JSON exports to 11-research/results/
        json_exports: list[str] = []
        for key, result in regime_results.items():
            path = str(RESULTS_DIR / f"{key}_result.json")
            data = export_json(result)
            Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
            json_exports.append(path)

        afrp_vs_benchmarks = {
            "afrp": export_json(afrp_full),
            "benchmarks": {k: export_json(v) for k, v in benchmark_results.items()},
        }
        bmark_path = RESULTS_DIR / "afrp_vs_benchmarks.json"
        bmark_path.write_text(json.dumps(afrp_vs_benchmarks, indent=2), encoding="utf-8")
        json_exports.append(str(bmark_path))

        return CampaignResult(
            regime_results=regime_results,
            benchmark_results=benchmark_results,
            robustness_results=robustness_results,
            sensitivity_results=sensitivity_results,
            reports=reports,
            json_exports=json_exports,
        )
