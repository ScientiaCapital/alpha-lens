"""
Risk Management Agent - Monitors and manages portfolio risk.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger

from alphalens.agents.base import BaseAgent
from alphalens.agents.config import SystemConfig
from alphalens.memory.memory_store import MemoryStore


class RiskManagementAgent(BaseAgent):
    """
    Manages portfolio risk and enforces safety limits.

    Monitors:
    - Portfolio drawdown
    - Position sizing
    - Exposure limits
    - Correlation risks
    - Volatility
    """

    def __init__(self, config: SystemConfig, memory: MemoryStore):
        super().__init__(
            name="risk_management",
            config=config,
            memory=memory,
            description="a risk management specialist focused on portfolio protection and optimal position sizing"
        )

    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize risk management agent state."""
        return {
            "risk_checks_performed": 0,
            "violations_detected": 0,
            "emergency_stops_triggered": 0,
            "current_risk_score": 0.0,
            "max_drawdown_seen": 0.0,
            "action_history": []
        }

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute risk management checks.

        Args:
            context: Must contain:
                - portfolio: Current portfolio positions
                - proposed_trade: Optional proposed trade to evaluate
                - market_data: Current market data

        Returns:
            Dictionary with:
                - risk_assessment: Overall risk assessment
                - violations: List of any limit violations
                - action_required: Emergency action if needed
                - position_sizes: Recommended position sizes
        """
        logger.info(f"Agent {self.name} performing risk assessment")

        portfolio = context.get("portfolio", {})
        proposed_trade = context.get("proposed_trade")
        market_data = context.get("market_data")

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(portfolio, market_data)

        # Check for violations
        violations = self._check_violations(risk_metrics, portfolio)

        # Assess proposed trade if provided
        trade_approval = None
        if proposed_trade:
            trade_approval = self._evaluate_trade(proposed_trade, portfolio, risk_metrics)

        # Determine if action is required
        action_required = self._determine_action(violations)

        # Calculate optimal position sizes
        position_sizes = self._calculate_position_sizes(portfolio, risk_metrics)

        # Update state
        self.update_state({
            "risk_checks_performed": self.get_state("risk_checks_performed") + 1,
            "violations_detected": self.get_state("violations_detected") + len(violations),
            "current_risk_score": risk_metrics.get("overall_risk_score", 0)
        })

        if action_required == "emergency_stop":
            self.update_state({
                "emergency_stops_triggered": self.get_state("emergency_stops_triggered") + 1
            })

            # Store risk event
            self.memory.store_risk_event(
                event_type="emergency_stop",
                severity="critical",
                description=f"Emergency stop triggered due to: {', '.join(violations)}",
                metrics=risk_metrics
            )

        self.log_action("risk_assessment", {
            "violations": len(violations),
            "action_required": action_required,
            "risk_score": risk_metrics.get("overall_risk_score")
        })

        return {
            "risk_assessment": risk_metrics,
            "violations": violations,
            "action_required": action_required,
            "position_sizes": position_sizes,
            "trade_approval": trade_approval
        }

    def _calculate_risk_metrics(
        self,
        portfolio: Dict[str, Any],
        market_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate comprehensive risk metrics."""
        # Placeholder implementation
        return {
            "portfolio_value": portfolio.get("total_value", 0),
            "cash": portfolio.get("cash", 0),
            "leverage": 1.0,
            "var_95": 0.02,  # 2% VaR
            "current_drawdown": 0.0,
            "volatility": 0.15,
            "beta": 1.0,
            "concentration": 0.1,
            "overall_risk_score": 0.3  # 0-1, lower is better
        }

    def _check_violations(
        self,
        risk_metrics: Dict[str, float],
        portfolio: Dict[str, Any]
    ) -> List[str]:
        """Check for risk limit violations."""
        violations = []
        limits = self.config.risk_limits

        # Check drawdown
        if risk_metrics.get("current_drawdown", 0) > limits.max_drawdown_pct / 100:
            violations.append(f"Drawdown exceeds limit: {risk_metrics['current_drawdown']:.1%}")

        # Check leverage
        if risk_metrics.get("leverage", 0) > limits.max_leverage:
            violations.append(f"Leverage exceeds limit: {risk_metrics['leverage']:.2f}")

        # Check concentration
        if risk_metrics.get("concentration", 0) > limits.max_position_size_pct / 100:
            violations.append(f"Position concentration too high: {risk_metrics['concentration']:.1%}")

        return violations

    def _evaluate_trade(
        self,
        proposed_trade: Dict[str, Any],
        portfolio: Dict[str, Any],
        risk_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Evaluate if a proposed trade is acceptable."""
        # Simple approval logic
        if len(self._check_violations(risk_metrics, portfolio)) > 0:
            return {
                "approved": False,
                "reason": "Existing risk violations",
                "suggested_size": 0
            }

        return {
            "approved": True,
            "reason": "Within risk limits",
            "suggested_size": proposed_trade.get("size", 0)
        }

    def _determine_action(self, violations: List[str]) -> str:
        """Determine what action is required based on violations."""
        if not violations:
            return "none"

        # Check for critical violations
        critical_keywords = ["drawdown", "leverage"]
        for violation in violations:
            for keyword in critical_keywords:
                if keyword in violation.lower():
                    return "emergency_stop"

        return "reduce_exposure"

    def _calculate_position_sizes(
        self,
        portfolio: Dict[str, Any],
        risk_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate optimal position sizes using risk parity or Kelly criterion."""
        # Placeholder - would implement Kelly criterion or risk parity
        return {
            "max_position_size": self.config.risk_limits.max_position_size_pct / 100,
            "recommended_leverage": min(risk_metrics.get("leverage", 1.0), self.config.risk_limits.max_leverage)
        }
