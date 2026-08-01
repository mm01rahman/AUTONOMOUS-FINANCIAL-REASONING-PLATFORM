"""Unit tests for AFRP Phase D paper trading modules."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools.paper_trading.dashboard import render_dashboard, write_dashboard
from tools.paper_trading.decision_log import (
    DecisionLogWriter,
    DecisionRecord,
    compute_file_checksum,
)
from tools.paper_trading.gateway import FeedAdapter, FeedEvent, LiveMarketDataGateway
from tools.paper_trading.monitoring import compute_performance, period_summaries
from tools.paper_trading.portfolio import VirtualPortfolio
from tools.paper_trading.reporting import write_reports
from tools.paper_trading.risk import RiskLimits, RiskMonitor, alerts_to_dict
from tools.paper_trading.shadow_execution import (
    ExecutionConfig,
    OrderRequest,
    ShadowExecutionEngine,
)


class FailingAdapter:
    name = "xauusd"

    def poll(self, when: datetime) -> list[FeedEvent]:
        raise RuntimeError("simulated feed failure")


def test_gateway_poll_cycle_contains_required_sources() -> None:
    gateway = LiveMarketDataGateway()
    events = gateway.poll_cycle(datetime(2026, 1, 1, tzinfo=UTC))
    sources = {event.source for event in events}
    assert {"xauusd", "dxy", "ust10y", "econ_calendar", "geopolitical"}.issubset(sources)


def test_gateway_snapshot_has_mode() -> None:
    gateway = LiveMarketDataGateway()
    snapshot = gateway.build_snapshot(datetime(2026, 1, 1, tzinfo=UTC))
    assert snapshot["mode"] == "provider-interface-live-sim"


def test_gateway_heartbeat_status_transitions() -> None:
    gateway = LiveMarketDataGateway(heartbeat_timeout_seconds=1)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    gateway.poll_cycle(now)
    healthy = gateway.heartbeat_status(now)
    assert healthy["xauusd"] == "healthy"
    stale = gateway.heartbeat_status(datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC))
    assert stale["xauusd"] == "stale"


def test_feed_event_naive_timestamp() -> None:
    event = FeedEvent(
        source="xauusd",
        timestamp=datetime(2026, 1, 1),
        metric="price",
        value=1.0,
        payload={},
        heartbeat_ts=datetime(2026, 1, 1),
        sequence=1,
    )
    assert event.timestamp.tzinfo is None


def test_gateway_missing_heartbeat_for_absent_feed() -> None:
    gateway = LiveMarketDataGateway(adapters={})
    status = gateway.heartbeat_status(datetime(2026, 1, 1, tzinfo=UTC))
    assert status["xauusd"] == "missing"


def test_gateway_reconnect_backoff() -> None:
    adapters: dict[str, FeedAdapter] = {"xauusd": FailingAdapter()}
    gateway = LiveMarketDataGateway(adapters=adapters, reconnect_backoff_seconds=10)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    events = gateway.poll_cycle(now)
    assert events == []
    events_soon = gateway.poll_cycle(now)
    assert events_soon == []


def test_execution_rejects_invalid_quantity() -> None:
    engine = ShadowExecutionEngine()
    order = OrderRequest("o1", "XAUUSD", "buy", 0.0, 0.7)
    result = engine.execute(order, 2300.0, datetime(2026, 1, 1, tzinfo=UTC))
    assert result.status == "rejected"


def test_execution_can_fail_deterministically() -> None:
    engine = ShadowExecutionEngine(ExecutionConfig(failure_probability=1.0, random_seed=1))
    order = OrderRequest("o1", "XAUUSD", "buy", 1.0, 0.7)
    result = engine.execute(order, 2300.0, datetime(2026, 1, 1, tzinfo=UTC))
    assert result.status == "failed"


def test_execution_fill_summary_has_simulated_only() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.0)
    )
    order = OrderRequest("o1", "XAUUSD", "buy", 1.0, 0.7)
    result = engine.execute(order, 2300.0, datetime(2026, 1, 1, tzinfo=UTC))
    summary = engine.summarize(result)
    assert summary["simulated_only"] is True


def test_execution_partial_fill_path() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(partial_fill_probability=1.0, failure_probability=0.0, random_seed=2)
    )
    order = OrderRequest("o1", "XAUUSD", "buy", 1.0, 0.7)
    result = engine.execute(order, 2300.0, datetime(2026, 1, 1, tzinfo=UTC))
    assert result.status == "partial"
    assert len(result.fills) == 2


def test_execution_buy_price_above_mid() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.0, random_seed=42)
    )
    order = OrderRequest("o2", "XAUUSD", "buy", 1.0, 0.7)
    result = engine.execute(order, 100.0, datetime(2026, 1, 1, tzinfo=UTC))
    assert result.fills[0].price > 100.0


def test_execution_sell_price_below_mid() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.0, random_seed=42)
    )
    order = OrderRequest("o3", "XAUUSD", "sell", 1.0, 0.7)
    result = engine.execute(order, 100.0, datetime(2026, 1, 1, tzinfo=UTC))
    assert result.fills[0].price < 100.0


def test_execution_latency_within_range() -> None:
    cfg = ExecutionConfig(
        base_latency_ms=10,
        latency_jitter_ms=5,
        failure_probability=0.0,
        partial_fill_probability=0.0,
    )
    engine = ShadowExecutionEngine(cfg)
    order = OrderRequest("o4", "XAUUSD", "buy", 1.0, 0.7)
    result = engine.execute(order, 100.0, datetime(2026, 1, 1, tzinfo=UTC))
    assert 10 <= result.fills[0].latency_ms <= 15


def test_virtual_portfolio_buy_updates_state() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.0)
    )
    portfolio = VirtualPortfolio(1000.0)
    fill = engine.execute(
        OrderRequest("o1", "XAUUSD", "buy", 1.0, 0.7), 100.0, datetime(2026, 1, 1, tzinfo=UTC)
    ).fills[0]
    portfolio.apply_fill(fill)
    portfolio.update_market_price("XAUUSD", 101.0)
    state = portfolio.state()
    assert state["gross_exposure"] > 0


def test_virtual_portfolio_sell_closes_position() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.0)
    )
    portfolio = VirtualPortfolio(1000.0)
    buy_fill = engine.execute(
        OrderRequest("o1", "XAUUSD", "buy", 1.0, 0.7), 100.0, datetime(2026, 1, 1, tzinfo=UTC)
    ).fills[0]
    sell_fill = engine.execute(
        OrderRequest("o2", "XAUUSD", "sell", 1.0, 0.7), 110.0, datetime(2026, 1, 1, tzinfo=UTC)
    ).fills[0]
    portfolio.apply_fill(buy_fill)
    portfolio.apply_fill(sell_fill)
    portfolio.update_market_price("XAUUSD", 110.0)
    assert portfolio.positions["XAUUSD"].quantity == pytest.approx(0.0)


def test_virtual_portfolio_mark_records_series() -> None:
    portfolio = VirtualPortfolio(1000.0)
    marker = portfolio.mark(datetime(2026, 1, 1, tzinfo=UTC))
    assert marker["equity"] == 1000.0
    assert len(portfolio.equity_series) == 1


def test_virtual_portfolio_drawdown_non_negative() -> None:
    portfolio = VirtualPortfolio(1000.0)
    portfolio.mark(datetime(2026, 1, 1, tzinfo=UTC))
    portfolio.cash = 900.0
    state = portfolio.mark(datetime(2026, 1, 2, tzinfo=UTC))
    assert float(state["drawdown"]) >= 0


def test_portfolio_to_dict_structure() -> None:
    portfolio = VirtualPortfolio(1000.0)
    payload = portfolio.to_dict()
    assert "state" in payload
    assert "positions" in payload


def test_portfolio_leverage_when_zero_equity() -> None:
    portfolio = VirtualPortfolio(1000.0)
    portfolio.cash = 0.0
    state = portfolio.state()
    assert "leverage" in state


def test_portfolio_unrealized_tracks_market() -> None:
    engine = ShadowExecutionEngine(
        ExecutionConfig(failure_probability=0.0, partial_fill_probability=0.0)
    )
    portfolio = VirtualPortfolio(1000.0)
    fill = engine.execute(
        OrderRequest("o1", "XAUUSD", "buy", 1.0, 0.7), 100.0, datetime(2026, 1, 1, tzinfo=UTC)
    ).fills[0]
    portfolio.apply_fill(fill)
    portfolio.update_market_price("XAUUSD", 120.0)
    assert portfolio.state()["unrealized_pnl"] != 0.0


def test_decision_log_writer_writes_required_fields(tmp_path: Path) -> None:
    writer = DecisionLogWriter(tmp_path / "log.jsonl")
    record = DecisionRecord(
        sequence=1,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        market_snapshot={"x": 1},
        world_model={"a": 1},
        decision_context={"b": 2},
        utility={"c": 3},
        policy_outcome={"d": 4},
        execution_simulation={"e": 5},
        portfolio_state={"f": 6},
        learning_outputs={"g": 7},
    )
    writer.write(record)
    digest = writer.finalize()
    assert digest["records"] == 1


def test_decision_log_file_checksum(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    path.write_text('{"x":1}\n', encoding="utf-8")
    checksum = compute_file_checksum(path)
    assert len(checksum) == 64


def test_decision_log_deterministic_encoding(tmp_path: Path) -> None:
    writer = DecisionLogWriter(tmp_path / "log.jsonl")
    record = DecisionRecord(
        sequence=1,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        market_snapshot={"x": 1},
        world_model={"a": 1},
        decision_context={"b": 2},
        utility={"c": 3},
        policy_outcome={"d": 4},
        execution_simulation={"e": 5},
        portfolio_state={"f": 6},
        learning_outputs={"g": 7},
    )
    writer.write(record)
    writer.write(record)
    lines = (tmp_path / "log.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert lines[0] == lines[1]


def test_decision_log_writer_truncates_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "log.jsonl"
    path.write_text('{"stale":true}\n', encoding="utf-8")
    writer = DecisionLogWriter(path)
    record = DecisionRecord(
        sequence=1,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        market_snapshot={"x": 1},
        world_model={"a": 1},
        decision_context={"b": 2},
        utility={"c": 3},
        policy_outcome={"d": 4},
        execution_simulation={"e": 5},
        portfolio_state={"f": 6},
        learning_outputs={"g": 7},
    )
    writer.write(record)
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert "stale" not in lines[0]


def test_compute_performance_for_rising_equity() -> None:
    perf = compute_performance([100, 102, 104], [1, 2, 3], [10, 12, 14])
    assert perf.total_return > 0


def test_compute_performance_empty_inputs() -> None:
    perf = compute_performance([], [], [])
    assert perf.total_return == 0.0


def test_compute_performance_profit_factor_infinite() -> None:
    perf = compute_performance([100, 101], [1.0], [10.0])
    assert perf.profit_factor == float("inf")


def test_compute_performance_drawdown() -> None:
    perf = compute_performance([100, 120, 90], [1, -2], [10, 10, 10])
    assert perf.max_drawdown > 0


def test_period_summaries_structure() -> None:
    timeline = [
        {"timestamp": "2026-01-01T00:00:00+00:00", "equity": 100.0},
        {"timestamp": "2026-01-01T01:00:00+00:00", "equity": 101.0},
        {"timestamp": "2026-01-08T01:00:00+00:00", "equity": 102.0},
    ]
    summaries = period_summaries(timeline)
    assert "daily" in summaries
    assert "weekly" in summaries
    assert "monthly" in summaries


def test_period_summaries_empty() -> None:
    summaries = period_summaries([])
    assert summaries["daily"] == {}


def test_risk_monitor_position_alert() -> None:
    monitor = RiskMonitor(RiskLimits(max_position_notional=1.0))
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100.0,
            "gross_exposure": 10.0,
            "net_exposure": 9.0,
            "leverage": 0.2,
            "drawdown": 0.0,
        },
        position_notional=10.0,
        confidence_values=[0.5, 0.8],
        volatility=0.01,
    )
    assert any(alert.code == "RISK-POSITION" for alert in alerts)


def test_risk_monitor_drawdown_alert() -> None:
    monitor = RiskMonitor(RiskLimits(max_drawdown=0.01))
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100.0,
            "gross_exposure": 10.0,
            "net_exposure": 9.0,
            "leverage": 0.2,
            "drawdown": 0.2,
        },
        position_notional=0.0,
        confidence_values=[],
        volatility=0.01,
    )
    assert any(alert.code == "RISK-DRAWDOWN" for alert in alerts)


def test_risk_monitor_volatility_alert() -> None:
    monitor = RiskMonitor(RiskLimits(max_volatility=0.001))
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100.0,
            "gross_exposure": 10.0,
            "net_exposure": 9.0,
            "leverage": 0.2,
            "drawdown": 0.0,
        },
        position_notional=0.0,
        confidence_values=[0.5],
        volatility=0.02,
    )
    assert any(alert.code == "RISK-VOLATILITY" for alert in alerts)


def test_risk_monitor_confidence_drift_alert() -> None:
    monitor = RiskMonitor(RiskLimits(max_confidence_drift=0.01))
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100.0,
            "gross_exposure": 10.0,
            "net_exposure": 9.0,
            "leverage": 0.2,
            "drawdown": 0.0,
        },
        position_notional=0.0,
        confidence_values=[0.2, 0.2, 0.2, 0.6, 0.6],
        volatility=0.001,
    )
    assert any(alert.code == "RISK-CONFIDENCE-DRIFT" for alert in alerts)


def test_alerts_to_dict_conversion() -> None:
    monitor = RiskMonitor()
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": -1.0,
            "gross_exposure": 0.0,
            "net_exposure": 0.0,
            "leverage": 0.0,
            "drawdown": 0.0,
        },
        position_notional=0.0,
        confidence_values=[],
        volatility=0.0,
    )
    rows = alerts_to_dict(alerts)
    assert isinstance(rows, list)


def test_risk_monitor_no_alerts_for_safe_state() -> None:
    monitor = RiskMonitor()
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100000.0,
            "gross_exposure": 1000.0,
            "net_exposure": 100.0,
            "leverage": 0.01,
            "drawdown": 0.001,
        },
        position_notional=100.0,
        confidence_values=[0.5, 0.51],
        volatility=0.0001,
    )
    assert alerts == []


def test_risk_monitor_skips_single_position_concentration_when_notionals_supplied() -> None:
    monitor = RiskMonitor(RiskLimits(max_concentration=0.7))
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100000.0,
            "gross_exposure": 1000.0,
            "net_exposure": 1000.0,
            "leverage": 0.01,
            "drawdown": 0.001,
        },
        position_notional=1000.0,
        confidence_values=[0.5, 0.51],
        volatility=0.0001,
        position_notionals=[1000.0],
    )
    assert not any(alert.code == "RISK-CONCENTRATION" for alert in alerts)


def test_risk_monitor_flags_multi_position_concentration_when_notionals_supplied() -> None:
    monitor = RiskMonitor(RiskLimits(max_concentration=0.7))
    alerts = monitor.evaluate(
        datetime(2026, 1, 1, tzinfo=UTC),
        portfolio_state={
            "equity": 100000.0,
            "gross_exposure": 1000.0,
            "net_exposure": 900.0,
            "leverage": 0.01,
            "drawdown": 0.001,
        },
        position_notional=900.0,
        confidence_values=[0.5, 0.51],
        volatility=0.0001,
        position_notionals=[800.0, 200.0],
    )
    assert any(alert.code == "RISK-CONCENTRATION" for alert in alerts)


def test_dashboard_render_sets_status_healthy() -> None:
    payload = render_dashboard({"equity": 1.0, "timestamp": "x"}, {"total_return": 0.1}, [])
    assert payload["status"] == "healthy"


def test_dashboard_render_sets_status_degraded() -> None:
    payload = render_dashboard(
        {"equity": 1.0, "timestamp": "x"},
        {"total_return": 0.1},
        [{"code": "A", "message": "B", "value": 1.0, "threshold": 0.5}],
    )
    assert payload["status"] == "degraded"


def test_dashboard_write_creates_files(tmp_path: Path) -> None:
    payload = render_dashboard({"equity": 1.0, "timestamp": "x"}, {"total_return": 0.1}, [])
    artifacts = write_dashboard(tmp_path, payload)
    assert Path(artifacts.json_path).exists()
    assert Path(artifacts.markdown_path).exists()
    assert Path(artifacts.html_path).exists()


def test_reporting_writes_all_outputs(tmp_path: Path) -> None:
    artifacts = write_reports(
        tmp_path,
        {"daily": {"periods": 1.0}, "weekly": {"periods": 1.0}, "monthly": {"periods": 1.0}},
        {"total_return": 0.1},
        [],
        {"checksum": "x"},
        {"loops_completed": 1},
        {"confidence_mean": 0.5},
    )
    assert Path(artifacts.daily_json).exists()
    assert Path(artifacts.weekly_json).exists()
    assert Path(artifacts.monthly_json).exists()
    assert Path(artifacts.runtime_json).exists()
    assert Path(artifacts.learning_json).exists()
    assert Path(artifacts.risk_json).exists()


def test_reporting_json_content(tmp_path: Path) -> None:
    artifacts = write_reports(
        tmp_path,
        {"daily": {"periods": 1.0}, "weekly": {"periods": 1.0}, "monthly": {"periods": 1.0}},
        {"total_return": 0.1},
        [{"code": "A"}],
        {"checksum": "x"},
        {"loops_completed": 1},
        {"confidence_mean": 0.5},
    )
    payload = json.loads(Path(artifacts.risk_json).read_text(encoding="utf-8"))
    assert payload[0]["code"] == "A"


def test_reporting_markdown_exists(tmp_path: Path) -> None:
    artifacts = write_reports(
        tmp_path,
        {"daily": {"periods": 1.0}, "weekly": {"periods": 1.0}, "monthly": {"periods": 1.0}},
        {"total_return": 0.1},
        [],
        {"checksum": "x"},
        {"loops_completed": 1},
        {"confidence_mean": 0.5},
    )
    assert Path(artifacts.daily_md).exists()
    assert Path(artifacts.weekly_md).exists()
    assert Path(artifacts.monthly_md).exists()


def test_reporting_runtime_payload_contains_performance(tmp_path: Path) -> None:
    artifacts = write_reports(
        tmp_path,
        {"daily": {"periods": 1.0}, "weekly": {"periods": 1.0}, "monthly": {"periods": 1.0}},
        {"total_return": 0.1},
        [],
        {"checksum": "x"},
        {"loops_completed": 1},
        {"confidence_mean": 0.5},
    )
    runtime = json.loads(Path(artifacts.runtime_json).read_text(encoding="utf-8"))
    assert "performance" in runtime
