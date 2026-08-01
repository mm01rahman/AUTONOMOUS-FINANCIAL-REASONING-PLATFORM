"""CLI entry point for the AFRP backtesting campaign."""

from __future__ import annotations

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


def main() -> None:
    """Run the full Phase C backtesting campaign and print a summary."""
    from tools.backtest.campaign import ResearchCampaign

    logger = logging.getLogger(__name__)
    logger.info("Starting AFRP Phase C Backtesting Campaign...")

    campaign = ResearchCampaign()
    try:
        result = campaign.run()
    except Exception as exc:  # noqa: BLE001
        logger.error("Campaign failed: %s", exc)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  AFRP Phase C — Backtesting Campaign Complete")
    print("=" * 60)
    print(f"  Regimes evaluated:    {len(result.regime_results)}")
    print(f"  Benchmarks run:       {len(result.benchmark_results)}")
    print(f"  Robustness scenarios: {len(result.robustness_results)}")
    print(f"  Reports generated:    {len(result.reports)}")
    print(f"  JSON exports:         {len(result.json_exports)}")
    print("=" * 60 + "\n")

    if result.regime_results:
        print("Regime Results:")
        for key, r in result.regime_results.items():
            print(
                f"  {key:25s}  return={r.total_return:+.4f}"
                f"  sharpe={r.sharpe:.4f}  trades={r.total_trades}"
            )

    if result.benchmark_results:
        print("\nBenchmark Results (full dataset):")
        for name, r in result.benchmark_results.items():
            print(
                f"  {name:25s}  return={r.total_return:+.4f}"
                f"  sharpe={r.sharpe:.4f}  trades={r.total_trades}"
            )

    print("\nReports written to 11-research/")


if __name__ == "__main__":
    main()
