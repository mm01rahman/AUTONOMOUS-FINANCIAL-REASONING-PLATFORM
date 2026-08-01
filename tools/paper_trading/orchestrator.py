"""Deterministic Phase D orchestrator for paper trading and shadow execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tools.paper_trading.dashboard import DashboardArtifacts, render_dashboard, write_dashboard
from tools.paper_trading.decision_log import DecisionLogWriter, DecisionRecord
from tools.paper_trading.gateway import LiveMarketDataGateway
from tools.paper_trading.monitoring import compute_performance, period_summaries
from tools.paper_trading.portfolio import VirtualPortfolio
from tools.paper_trading.reporting import ReportArtifacts, write_reports
from tools.paper_trading.risk import RiskMonitor, alerts_to_dict
from tools.paper_trading.shadow_execution import (
    ExecutionConfig,
    OrderRequest,
    ShadowExecutionEngine,
)


@dataclass(frozen=True)
class PaperTradingConfig:
    iterations: int = 48
    poll_interval_seconds: int = 300
    symbol: str = "XAUUSD"
    initial_cash: float = 100_000.0
    output_dir: str = "11-research/phase-d"
    random_seed: int = 42


@dataclass(frozen=True)
class RunResult:
    config: PaperTradingConfig
    dashboard: DashboardArtifacts
    reports: ReportArtifacts
    decision_log_path: str
    decision_log_checksum: str
    risk_alert_count: int
    readiness: str
    readiness_reasons: list[str]


class PaperTradingOrchestrator:
    """Continuous deterministic loop for simulated-live paper execution."""

    def __init__(self, config: PaperTradingConfig | None = None) -> None:
        self.config = config or PaperTradingConfig()
        self.gateway = LiveMarketDataGateway()
        self.execution = ShadowExecutionEngine(ExecutionConfig(random_seed=self.config.random_seed))
        self.portfolio = VirtualPortfolio(initial_cash=self.config.initial_cash)
        self.risk = RiskMonitor()

    def run(self) -> RunResult:
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        log_writer = DecisionLogWriter(out_dir / "decision_log.jsonl")
        start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

        timeline: list[dict[str, Any]] = []
        trade_pnls: list[float] = []
        exposures: list[float] = []
        confidence_history: list[float] = []
        all_alerts: list[dict[str, Any]] = []
        last_price = 2325.0

        for idx in range(self.config.iterations):
            now = start + timedelta(seconds=idx * self.config.poll_interval_seconds)
            market = self.gateway.build_snapshot(now)
            feed_price = float(market["feeds"].get("xauusd", last_price))
            momentum = feed_price - last_price
            confidence = min(0.95, max(0.5, 0.55 + abs(momentum) / 2))
            confidence_history.append(confidence)

            side = "buy" if momentum >= 0 else "sell"
            should_trade = abs(momentum) > 0.02
            result_summary: dict[str, Any] = {
                "status": "skipped",
                "reason": "no_signal",
                "fills": [],
            }

            if should_trade:
                order = OrderRequest(
                    order_id=f"ORD-{idx:06d}",
                    symbol=self.config.symbol,
                    side=side,
                    quantity=1.0,
                    decision_confidence=confidence,
                )
                execution_result = self.execution.execute(
                    order=order, mid_price=feed_price, now=now
                )
                result_summary = self.execution.summarize(execution_result)
                for fill in execution_result.fills:
                    self.portfolio.apply_fill(fill)

            self.portfolio.update_market_price(self.config.symbol, feed_price)
            state_point = self.portfolio.mark(now)
            timeline.append(state_point)
            exposures.append(float(state_point["gross_exposure"]))
            trade_pnls.append(float(state_point["total_pnl"]))

            perf = compute_performance(
                [float(point["equity"]) for point in timeline],
                trade_pnls,
                exposures,
                risk_free_rate=0.01,
            )
            state_now = self.portfolio.state()
            alerts = self.risk.evaluate(
                when=now,
                portfolio_state=state_now,
                position_notional=abs(state_now.get("net_exposure", 0.0)),
                confidence_values=confidence_history,
                volatility=abs(momentum) / max(feed_price, 1.0),
                position_notionals=[
                    abs(position.market_price * position.quantity)
                    for position in self.portfolio.positions.values()
                    if abs(position.quantity) > 1e-12
                ],
            )
            alert_dicts = alerts_to_dict(alerts)
            all_alerts.extend(alert_dicts)

            record = DecisionRecord(
                sequence=idx,
                timestamp=now,
                market_snapshot=market,
                world_model={
                    "momentum": round(momentum, 8),
                    "trend": "up" if momentum >= 0 else "down",
                },
                decision_context={
                    "signal": side,
                    "confidence": confidence,
                    "should_trade": should_trade,
                },
                utility={"score": round(confidence * (1.0 if should_trade else 0.2), 8)},
                policy_outcome={
                    "action": side if should_trade else "hold",
                    "authorized": should_trade,
                },
                execution_simulation=result_summary,
                portfolio_state=self.portfolio.to_dict(),
                learning_outputs={"recent_confidence": confidence_history[-5:]},
            )
            log_writer.write(record)
            last_price = feed_price
            _ = perf

        digest = log_writer.finalize()
        summary = period_summaries(timeline)
        final_perf = compute_performance(
            [float(point["equity"]) for point in timeline],
            trade_pnls,
            exposures,
            risk_free_rate=0.01,
        )
        perf_payload = asdict(final_perf)

        dashboard_payload = render_dashboard(
            snapshot={**timeline[-1], "timestamp": timeline[-1]["timestamp"]},
            performance=perf_payload,
            alerts=all_alerts,
        )
        dashboard = write_dashboard(out_dir, dashboard_payload)

        reports = write_reports(
            output_dir=out_dir,
            period_summary=summary,
            performance=perf_payload,
            risk_alerts=all_alerts,
            log_digest=digest,
            runtime_health={
                "loops_completed": self.config.iterations,
                "gateway_mode": "provider-interface-live-sim",
                "broker_calls": 0,
                "runtime_frozen_respected": True,
            },
            learning_summary={
                "confidence_mean": sum(confidence_history) / len(confidence_history)
                if confidence_history
                else 0.0,
                "confidence_samples": len(confidence_history),
                "deterministic_seed": self.config.random_seed,
            },
        )

        fail_reasons: list[str] = []
        if any(alert["severity"] == "warning" for alert in all_alerts):
            fail_reasons.append("warning-level risk alerts detected")
        if float(perf_payload["max_drawdown"]) > 0.20:
            fail_reasons.append("max drawdown above 20%")

        readiness = "PASS" if not fail_reasons else "FAIL"
        return RunResult(
            config=self.config,
            dashboard=dashboard,
            reports=reports,
            decision_log_path=str(out_dir / "decision_log.jsonl"),
            decision_log_checksum=str(digest["checksum"]),
            risk_alert_count=len(all_alerts),
            readiness=readiness,
            readiness_reasons=fail_reasons,
        )
