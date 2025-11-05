"""
Learning Memory - Stores and retrieves learnings from backtests and trading.

Uses vector embeddings for semantic search over strategy learnings.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from sqlalchemy import create_engine, Column, String, Float, JSON, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from alphalens.agents.config import SystemConfig

Base = declarative_base()


class StrategyLearning(Base):
    """SQLAlchemy model for strategy learnings."""
    __tablename__ = 'strategy_learnings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String, index=True, nullable=False)
    strategy_type = Column(String, index=True, nullable=False)  # e.g., "factor", "multi_factor", "hedge"

    # Strategy details
    description = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=False)

    # Performance metrics
    sharpe_ratio = Column(Float, nullable=True)
    annual_return = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    information_coefficient = Column(Float, nullable=True)

    # Context
    market_regime = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Outcome
    outcome = Column(String, nullable=False)  # "success", "failure", "mixed"
    confidence_score = Column(Float, nullable=False)

    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # For semantic search (to be used with vector DB)
    embedding_id = Column(String, nullable=True)


class FactorPerformance(Base):
    """SQLAlchemy model for factor performance history."""
    __tablename__ = 'factor_performance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_name = Column(String, index=True, nullable=False)
    factor_formula = Column(Text, nullable=False)

    # Performance metrics
    ic_mean = Column(Float, nullable=True)
    ic_std = Column(Float, nullable=True)
    returns_1d = Column(Float, nullable=True)
    returns_5d = Column(Float, nullable=True)
    returns_10d = Column(Float, nullable=True)
    turnover = Column(Float, nullable=True)

    # Context
    market_regime = Column(String, nullable=True)
    test_period_start = Column(DateTime, nullable=False)
    test_period_end = Column(DateTime, nullable=False)

    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskEvent(Base):
    """SQLAlchemy model for risk events."""
    __tablename__ = 'risk_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, index=True, nullable=False)  # e.g., "drawdown", "loss_limit", "correlation_breach"
    severity = Column(String, nullable=False)  # "low", "medium", "high", "critical"

    # Event details
    description = Column(Text, nullable=False)
    metrics = Column(JSON, nullable=False)

    # Response
    action_taken = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)

    # Timing
    occurred_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearningMemory:
    """
    Manages long-term learning memory for the system.

    Stores and retrieves:
    - Strategy learnings
    - Factor performance history
    - Risk events
    - Market regime patterns
    """

    def __init__(self, config: SystemConfig):
        """
        Initialize learning memory.

        Args:
            config: System configuration
        """
        self.config = config

        # PostgreSQL connection
        self.engine = create_engine(config.postgres.connection_string)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        logger.info("LearningMemory initialized")

    def store_strategy_learning(
        self,
        strategy_id: str,
        strategy_type: str,
        description: str,
        parameters: Dict[str, Any],
        performance_metrics: Dict[str, float],
        market_regime: str,
        outcome: str,
        confidence_score: float,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store a strategy learning.

        Args:
            strategy_id: Unique identifier for the strategy
            strategy_type: Type of strategy (e.g., "factor", "multi_factor")
            description: Human-readable description
            parameters: Strategy parameters
            performance_metrics: Dictionary of performance metrics
            market_regime: Market regime during testing
            outcome: "success", "failure", or "mixed"
            confidence_score: Confidence in this learning (0-1)
            metadata: Additional metadata

        Returns:
            Learning record ID
        """
        learning = StrategyLearning(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            description=description,
            parameters=parameters,
            sharpe_ratio=performance_metrics.get("sharpe_ratio"),
            annual_return=performance_metrics.get("annual_return"),
            max_drawdown=performance_metrics.get("max_drawdown"),
            win_rate=performance_metrics.get("win_rate"),
            information_coefficient=performance_metrics.get("information_coefficient"),
            market_regime=market_regime,
            outcome=outcome,
            confidence_score=confidence_score,
            metadata=metadata
        )

        self.session.add(learning)
        self.session.commit()

        logger.info(f"Stored strategy learning: {strategy_id} ({outcome})")
        return learning.id

    def get_successful_strategies(
        self,
        strategy_type: Optional[str] = None,
        market_regime: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 50
    ) -> List[Dict]:
        """
        Retrieve successful strategy learnings.

        Args:
            strategy_type: Filter by strategy type
            market_regime: Filter by market regime
            min_confidence: Minimum confidence score
            limit: Maximum number of results

        Returns:
            List of successful strategies
        """
        query = self.session.query(StrategyLearning)\
            .filter(StrategyLearning.outcome == "success")\
            .filter(StrategyLearning.confidence_score >= min_confidence)

        if strategy_type:
            query = query.filter(StrategyLearning.strategy_type == strategy_type)

        if market_regime:
            query = query.filter(StrategyLearning.market_regime == market_regime)

        results = query.order_by(StrategyLearning.sharpe_ratio.desc())\
            .limit(limit)\
            .all()

        return [self._learning_to_dict(r) for r in results]

    def store_factor_performance(
        self,
        factor_name: str,
        factor_formula: str,
        metrics: Dict[str, float],
        market_regime: str,
        test_period_start: datetime,
        test_period_end: datetime,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store factor performance data.

        Args:
            factor_name: Name of the factor
            factor_formula: Formula or description
            metrics: Performance metrics
            market_regime: Market regime during test
            test_period_start: Start of test period
            test_period_end: End of test period
            metadata: Additional metadata

        Returns:
            Record ID
        """
        performance = FactorPerformance(
            factor_name=factor_name,
            factor_formula=factor_formula,
            ic_mean=metrics.get("ic_mean"),
            ic_std=metrics.get("ic_std"),
            returns_1d=metrics.get("returns_1d"),
            returns_5d=metrics.get("returns_5d"),
            returns_10d=metrics.get("returns_10d"),
            turnover=metrics.get("turnover"),
            market_regime=market_regime,
            test_period_start=test_period_start,
            test_period_end=test_period_end,
            metadata=metadata
        )

        self.session.add(performance)
        self.session.commit()

        logger.info(f"Stored factor performance: {factor_name}")
        return performance.id

    def get_factor_performance_history(
        self,
        factor_name: Optional[str] = None,
        market_regime: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve factor performance history.

        Args:
            factor_name: Filter by factor name
            market_regime: Filter by market regime
            limit: Maximum number of results

        Returns:
            List of factor performance records
        """
        query = self.session.query(FactorPerformance)

        if factor_name:
            query = query.filter(FactorPerformance.factor_name == factor_name)

        if market_regime:
            query = query.filter(FactorPerformance.market_regime == market_regime)

        results = query.order_by(FactorPerformance.created_at.desc())\
            .limit(limit)\
            .all()

        return [self._factor_perf_to_dict(r) for r in results]

    def store_risk_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        metrics: Dict[str, Any],
        action_taken: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Store a risk event.

        Args:
            event_type: Type of risk event
            severity: "low", "medium", "high", "critical"
            description: Description of the event
            metrics: Relevant metrics
            action_taken: Action taken in response
            metadata: Additional metadata

        Returns:
            Event ID
        """
        event = RiskEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            metrics=metrics,
            action_taken=action_taken,
            occurred_at=datetime.utcnow(),
            metadata=metadata
        )

        self.session.add(event)
        self.session.commit()

        logger.warning(f"Risk event stored: {event_type} ({severity})")
        return event.id

    def get_risk_events(
        self,
        event_type: Optional[str] = None,
        min_severity: str = "low",
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve risk events.

        Args:
            event_type: Filter by event type
            min_severity: Minimum severity level
            limit: Maximum number of results

        Returns:
            List of risk events
        """
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity_level = severity_order.get(min_severity, 0)

        query = self.session.query(RiskEvent)

        if event_type:
            query = query.filter(RiskEvent.event_type == event_type)

        results = query.order_by(RiskEvent.occurred_at.desc())\
            .limit(limit)\
            .all()

        # Filter by severity
        filtered_results = [
            r for r in results
            if severity_order.get(r.severity, 0) >= min_severity_level
        ]

        return [self._risk_event_to_dict(r) for r in filtered_results]

    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all learnings.

        Returns:
            Summary statistics
        """
        total_strategies = self.session.query(StrategyLearning).count()
        successful_strategies = self.session.query(StrategyLearning)\
            .filter(StrategyLearning.outcome == "success").count()

        total_factors = self.session.query(FactorPerformance).count()
        total_risk_events = self.session.query(RiskEvent).count()

        # Average Sharpe ratio of successful strategies
        avg_sharpe = self.session.query(StrategyLearning.sharpe_ratio)\
            .filter(StrategyLearning.outcome == "success")\
            .filter(StrategyLearning.sharpe_ratio.isnot(None))

        sharpe_values = [r[0] for r in avg_sharpe.all()]
        avg_sharpe_ratio = np.mean(sharpe_values) if sharpe_values else None

        return {
            "total_strategies_tested": total_strategies,
            "successful_strategies": successful_strategies,
            "success_rate": successful_strategies / total_strategies if total_strategies > 0 else 0,
            "total_factors_tested": total_factors,
            "total_risk_events": total_risk_events,
            "avg_successful_sharpe_ratio": avg_sharpe_ratio
        }

    @staticmethod
    def _learning_to_dict(learning: StrategyLearning) -> Dict:
        """Convert StrategyLearning to dictionary."""
        return {
            "id": learning.id,
            "strategy_id": learning.strategy_id,
            "strategy_type": learning.strategy_type,
            "description": learning.description,
            "parameters": learning.parameters,
            "sharpe_ratio": learning.sharpe_ratio,
            "annual_return": learning.annual_return,
            "max_drawdown": learning.max_drawdown,
            "win_rate": learning.win_rate,
            "information_coefficient": learning.information_coefficient,
            "market_regime": learning.market_regime,
            "outcome": learning.outcome,
            "confidence_score": learning.confidence_score,
            "metadata": learning.metadata,
            "created_at": learning.created_at.isoformat()
        }

    @staticmethod
    def _factor_perf_to_dict(perf: FactorPerformance) -> Dict:
        """Convert FactorPerformance to dictionary."""
        return {
            "id": perf.id,
            "factor_name": perf.factor_name,
            "factor_formula": perf.factor_formula,
            "ic_mean": perf.ic_mean,
            "ic_std": perf.ic_std,
            "returns_1d": perf.returns_1d,
            "returns_5d": perf.returns_5d,
            "returns_10d": perf.returns_10d,
            "turnover": perf.turnover,
            "market_regime": perf.market_regime,
            "test_period_start": perf.test_period_start.isoformat(),
            "test_period_end": perf.test_period_end.isoformat(),
            "metadata": perf.metadata,
            "created_at": perf.created_at.isoformat()
        }

    @staticmethod
    def _risk_event_to_dict(event: RiskEvent) -> Dict:
        """Convert RiskEvent to dictionary."""
        return {
            "id": event.id,
            "event_type": event.event_type,
            "severity": event.severity,
            "description": event.description,
            "metrics": event.metrics,
            "action_taken": event.action_taken,
            "resolution": event.resolution,
            "occurred_at": event.occurred_at.isoformat(),
            "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat()
        }

    def close(self) -> None:
        """Close database connection."""
        self.session.close()
        logger.info("LearningMemory connection closed")
