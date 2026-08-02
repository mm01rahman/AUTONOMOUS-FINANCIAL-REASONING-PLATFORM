"""CLI for Phase D paper trading and reporting."""

from __future__ import annotations

import argparse
import json
import sys

from tools.paper_trading.orchestrator import PaperTradingConfig, PaperTradingOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AFRP Phase D paper trading loop")
    parser.add_argument("--iterations", type=int, default=48)
    parser.add_argument("--poll-seconds", type=int, default=300)
    parser.add_argument("--output-dir", type=str, default="11-research/phase-d")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--strict-readiness", action="store_true")
    args = parser.parse_args()

    config = PaperTradingConfig(
        iterations=args.iterations,
        poll_interval_seconds=args.poll_seconds,
        output_dir=args.output_dir,
        random_seed=args.seed,
    )
    result = PaperTradingOrchestrator(config).run()

    summary = {
        "readiness": result.readiness,
        "risk_alert_count": result.risk_alert_count,
        "decision_log": result.decision_log_path,
        "decision_log_checksum": result.decision_log_checksum,
        "dashboard": {
            "json": result.dashboard.json_path,
            "md": result.dashboard.markdown_path,
            "html": result.dashboard.html_path,
        },
        "reports": {
            "daily_json": result.reports.daily_json,
            "weekly_json": result.reports.weekly_json,
            "monthly_json": result.reports.monthly_json,
            "runtime_json": result.reports.runtime_json,
            "learning_json": result.reports.learning_json,
            "risk_json": result.reports.risk_json,
            "log_digest_json": result.reports.log_digest_json,
        },
        "reasons": result.readiness_reasons,
    }
    print(json.dumps(summary, indent=2))

    if args.strict_readiness and result.readiness == "FAIL":
        sys.exit(2)


if __name__ == "__main__":
    main()
