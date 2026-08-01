"""Risk monitoring and alerts for Phase D paper execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class RiskLimits:
    max_position_notional: float = 150_000.0
    max_concentration: float = 0.70
    max_gross_exposure: float = 250_000.0
    max_leverage: float = 2.8
    max_drawdown: float = 0.20
    max_volatility: float = 0.025
    max_confidence_drift: float = 0.25


@dataclass(frozen=True)
class RiskAlert:
    timestamp: str
    severity: str
    code: str
    message: str
    metric: str
    value: float
    threshold: float


class RiskMonitor:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def evaluate(
        self,
        when: datetime,
        portfolio_state: dict[str, float],
        position_notional: float,
        confidence_values: list[float],
        volatility: float,
    ) -> list[RiskAlert]:
        ts = when if when.tzinfo is not None else when.replace(tzinfo=UTC)
        alerts: list[RiskAlert] = []

        def add_alert(code: str, message: str, metric: str, value: float, threshold: float) -> None:
            alerts.append(
                RiskAlert(
                    timestamp=ts.isoformat(),
                    severity="warning" if code.startswith("RISK") else "info",
                    code=code,
                    message=message,
                    metric=metric,
                    value=value,
                    threshold=threshold,
                )
            )

        if position_notional > self.limits.max_position_notional:
            add_alert(
                "RISK-POSITION",
                "Position notional exceeds configured limit",
                "position_notional",
                position_notional,
                self.limits.max_position_notional,
            )

        equity = portfolio_state.get("equity", 0.0)
        gross = portfolio_state.get("gross_exposure", 0.0)
        leverage = portfolio_state.get("leverage", 0.0)
        drawdown = portfolio_state.get("drawdown", 0.0)
        net = abs(portfolio_state.get("net_exposure", 0.0))

        if gross > self.limits.max_gross_exposure:
            add_alert(
                "RISK-EXPOSURE",
                "Gross exposure over limit",
                "gross_exposure",
                gross,
                self.limits.max_gross_exposure,
            )

        if leverage > self.limits.max_leverage:
            add_alert(
                "RISK-LEVERAGE",
                "Leverage over limit",
                "leverage",
                leverage,
                self.limits.max_leverage,
            )

        concentration = net / gross if gross > 0 else 0.0
        if concentration > self.limits.max_concentration:
            add_alert(
                "RISK-CONCENTRATION",
                "Net concentration exceeds limit",
                "concentration",
                concentration,
                self.limits.max_concentration,
            )

        if drawdown > self.limits.max_drawdown:
            add_alert(
                "RISK-DRAWDOWN",
                "Drawdown exceeds limit",
                "drawdown",
                drawdown,
                self.limits.max_drawdown,
            )

        if volatility > self.limits.max_volatility:
            add_alert(
                "RISK-VOLATILITY",
                "Volatility exceeds limit",
                "volatility",
                volatility,
                self.limits.max_volatility,
            )

        if confidence_values:
            baseline = confidence_values[0]
            drift = abs(mean(confidence_values[-5:]) - baseline)
            if drift > self.limits.max_confidence_drift:
                add_alert(
                    "RISK-CONFIDENCE-DRIFT",
                    "Confidence drift exceeds threshold",
                    "confidence_drift",
                    drift,
                    self.limits.max_confidence_drift,
                )

        if equity <= 0:
            add_alert("RISK-CAPITAL", "Equity depleted", "equity", equity, 0.0)

        return alerts


def alerts_to_dict(alerts: list[RiskAlert]) -> list[dict[str, Any]]:
    return [
        {
            "timestamp": alert.timestamp,
            "severity": alert.severity,
            "code": alert.code,
            "message": alert.message,
            "metric": alert.metric,
            "value": alert.value,
            "threshold": alert.threshold,
        }
        for alert in alerts
    ]
