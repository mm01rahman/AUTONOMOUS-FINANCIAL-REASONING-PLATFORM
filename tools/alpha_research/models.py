"""Dataclasses shared across Phase E research modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PromotionThresholds:
    """Governed promotion bars for Phase E candidate strategies."""

    min_expectancy: float = 0.0
    min_sharpe: float = 0.05
    min_sortino: float = 0.10
    max_drawdown: float = 0.35
    min_positive_fold_ratio: float = 0.50
    max_ruin_probability: float = 0.10
    max_overfit_gap: float = 0.35


@dataclass(frozen=True)
class ResearchConfig:
    """Global deterministic research configuration."""

    initial_equity: float = 100_000.0
    cost_bps: float = 5.0
    output_dir: str = "11-research/phase-e"
    seed: int = 42
    train_days: int = 756
    validation_days: int = 252
    test_days: int = 252
    monte_carlo_paths: int = 400
    monte_carlo_block: int = 10
    thresholds: PromotionThresholds = PromotionThresholds()


@dataclass(frozen=True)
class StrategyParameters:
    """Deterministic parameter set used by a strategy family."""

    fast_window: int = 20
    slow_window: int = 120
    lookback: int = 20
    threshold: float = 1.5
    confidence_threshold: float = 0.55
    vol_ceiling: float = 0.018
    position_scale: float = 1.0
    max_position: float = 1.0
    score_threshold: float = 0.10
    macro_weight: float = 0.35
    microstructure_weight: float = 0.15
    liquidity_weight: float = 0.15
    regime_weight: float = 0.15
    forward_weight: float = 0.10
    behavioral_weight: float = 0.10
    technical_weight: float = 0.40
    utility_weight: float = 1.0
    policy_limit: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradeRecord:
    """One deterministic synthetic trade for research evaluation."""

    entry_at: str
    exit_at: str
    direction: str
    entry_price: float
    exit_price: float
    position: float
    pnl: float
    return_pct: float
    confidence: float
    score: float
    entry_reason: str
    exit_reason: str
    components: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrategyRun:
    """Full deterministic strategy backtest result."""

    name: str
    parameters: StrategyParameters
    metrics: dict[str, float]
    daily_returns: tuple[float, ...]
    equity_curve: tuple[float, ...]
    positions: tuple[float, ...]
    trades: tuple[TradeRecord, ...]
    checksum: str
    policy_rejection_rate: float

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["trades"] = [trade.to_dict() for trade in self.trades]
        return payload


@dataclass(frozen=True)
class OptimizationTrial:
    """One deterministic parameter-search trial."""

    parameters: StrategyParameters
    train_score: float
    validation_score: float
    objective_score: float
    overfit_gap: float
    train_metrics: dict[str, float]
    validation_metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OptimizationResult:
    """Chosen parameter set and ranked trials."""

    strategy_name: str
    selected_parameters: StrategyParameters
    selected_objective: float
    overfit_gap: float
    trials: tuple[OptimizationTrial, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "selected_parameters": self.selected_parameters.to_dict(),
            "selected_objective": self.selected_objective,
            "overfit_gap": self.overfit_gap,
            "trials": [trial.to_dict() for trial in self.trials],
        }


@dataclass(frozen=True)
class WalkForwardFold:
    """One walk-forward train/validation/test fold."""

    fold_id: int
    train_start: str
    train_end: str
    validation_end: str
    test_end: str
    parameters: StrategyParameters
    test_metrics: dict[str, float]
    test_checksum: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["parameters"] = self.parameters.to_dict()
        return payload


@dataclass(frozen=True)
class WalkForwardSummary:
    """Aggregate out-of-sample walk-forward result."""

    strategy_name: str
    aggregate_metrics: dict[str, float]
    positive_fold_ratio: float
    fold_count: int
    daily_returns: tuple[float, ...]
    folds: tuple[WalkForwardFold, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "aggregate_metrics": self.aggregate_metrics,
            "positive_fold_ratio": self.positive_fold_ratio,
            "fold_count": self.fold_count,
            "daily_returns": list(self.daily_returns),
            "folds": [fold.to_dict() for fold in self.folds],
        }


@dataclass(frozen=True)
class FeatureImportanceRecord:
    """One feature-importance/risk-of-use summary row."""

    feature: str
    mutual_information: float
    correlation_mean: float
    correlation_stability: float
    drift_score: float
    redundancy_score: float
    permutation_importance: float
    classification: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromotionDecision:
    """Promotion assessment for one candidate strategy."""

    strategy_name: str
    promote: bool
    reasons: tuple[str, ...]
    full_sample_metrics: dict[str, float]
    walk_forward_metrics: dict[str, float]
    positive_fold_ratio: float
    ruin_probability: float
    overfit_gap: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
