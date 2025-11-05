"""
Backtesting Agent - Tests strategies and learns from results.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

from alphalens.agents.base import BaseAgent
from alphalens.agents.config import SystemConfig
from alphalens.memory.memory_store import MemoryStore

# Import Alphalens for factor analysis
import alphalens as al
import alphalens.performance as perf
import alphalens.utils as utils


class BacktestingAgent(BaseAgent):
    """
    Tests strategies through backtesting and learns from results.

    Implements the self-learning loop:
    1. Run backtest on factor/strategy
    2. Analyze performance metrics
    3. Compare to historical results
    4. Update factor scoring model
    5. Store learnings
    """

    def __init__(self, config: SystemConfig, memory: MemoryStore):
        super().__init__(
            name="backtesting",
            config=config,
            memory=memory,
            description="an expert quantitative analyst specializing in strategy backtesting and performance analysis"
        )

    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize backtesting agent state."""
        return {
            "backtests_run": 0,
            "strategies_tested": 0,
            "successful_strategies": 0,
            "avg_sharpe_ratio": 0.0,
            "best_strategy": None,
            "learning_rate": self.config.learning.learning_rate,
            "factor_weights": {},  # Learned weights for different factor types
            "action_history": []
        }

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute backtesting on a factor or strategy.

        Args:
            context: Must contain:
                - factor: Factor data or factor definition
                - prices: Price data for backtesting
                - forward_returns: Optional pre-computed forward returns
                - factor_name: Name of the factor being tested

        Returns:
            Dictionary with:
                - backtest_results: Full backtest results
                - performance_metrics: Key performance metrics
                - decision: Whether to use this factor/strategy
                - confidence: Confidence score (0-1)
        """
        logger.info(f"Agent {self.name} executing backtest")

        factor = context.get("factor")
        prices = context.get("prices")
        factor_name = context.get("factor_name", "unnamed_factor")

        if factor is None or prices is None:
            logger.warning("Missing required data for backtesting")
            return self._empty_result()

        # Run the backtest
        backtest_results = self._run_backtest(factor, prices, factor_name)

        # Analyze results
        analysis = self._analyze_results(backtest_results, factor_name)

        # Make decision based on results
        decision, confidence = self._make_decision(analysis)

        # Learn from the results
        self._learn_from_backtest(factor_name, analysis, decision)

        # Update state
        self.update_state({
            "backtests_run": self.get_state("backtests_run") + 1,
            "strategies_tested": self.get_state("strategies_tested") + 1
        })

        if decision == "use":
            self.update_state({
                "successful_strategies": self.get_state("successful_strategies") + 1
            })

        self.log_action("backtest_completed", {
            "factor": factor_name,
            "decision": decision,
            "confidence": confidence,
            "sharpe_ratio": analysis.get("sharpe_ratio")
        })

        return {
            "backtest_results": backtest_results,
            "performance_metrics": analysis,
            "decision": decision,
            "confidence": confidence
        }

    def _run_backtest(
        self,
        factor: pd.Series,
        prices: pd.DataFrame,
        factor_name: str
    ) -> Dict[str, Any]:
        """
        Run backtest using Alphalens.

        Args:
            factor: Factor values (MultiIndex with date and asset)
            prices: Price data
            factor_name: Name of the factor

        Returns:
            Backtest results dictionary
        """
        try:
            # Prepare factor data using Alphalens
            factor_data = utils.get_clean_factor_and_forward_returns(
                factor=factor,
                prices=prices,
                quantiles=self.config.trading.factor_quantiles,
                periods=(1, 5, 10),
                filter_zscore=20
            )

            # Calculate performance metrics
            mean_return_by_q = perf.mean_return_by_quantile(factor_data)
            ic = perf.factor_information_coefficient(factor_data)
            turnover = perf.quantile_turnover(factor_data[['factor_quantile']], quantile=5)

            # Calculate returns for each quantile
            quantile_returns = perf.mean_return_by_quantile(
                factor_data,
                by_date=True,
                demeaned=True
            )[0]  # Get mean returns

            results = {
                "factor_data": factor_data,
                "mean_return_by_quantile": mean_return_by_q,
                "ic": ic,
                "turnover": turnover,
                "quantile_returns": quantile_returns,
                "status": "success"
            }

            logger.info(f"Backtest completed successfully for {factor_name}")
            return results

        except Exception as e:
            logger.error(f"Backtest failed for {factor_name}: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _analyze_results(
        self,
        backtest_results: Dict[str, Any],
        factor_name: str
    ) -> Dict[str, Any]:
        """
        Analyze backtest results and extract key metrics.

        Args:
            backtest_results: Results from backtest
            factor_name: Name of the factor

        Returns:
            Analysis dictionary with metrics
        """
        if backtest_results.get("status") == "failed":
            return {
                "factor_name": factor_name,
                "status": "failed",
                "usable": False
            }

        try:
            ic = backtest_results["ic"]
            mean_ic = ic.mean()
            ic_std = ic.std()

            # Get returns by quantile
            mean_return_by_q = backtest_results["mean_return_by_quantile"][0]

            # Calculate spread between top and bottom quantile
            top_quantile = mean_return_by_q.max()
            bottom_quantile = mean_return_by_q.min()
            quantile_spread = top_quantile - bottom_quantile

            # Get turnover
            turnover = backtest_results["turnover"]
            avg_turnover = turnover.mean()

            # Estimate Sharpe ratio from IC (approximate)
            # Sharpe ≈ IC * sqrt(trading_frequency)
            estimated_sharpe = mean_ic * np.sqrt(252)  # Daily frequency

            # Calculate risk-adjusted metrics
            ic_sharpe = mean_ic / ic_std if ic_std > 0 else 0

            analysis = {
                "factor_name": factor_name,
                "status": "success",
                "ic_mean": float(mean_ic),
                "ic_std": float(ic_std),
                "ic_sharpe": float(ic_sharpe),
                "quantile_spread_1d": float(quantile_spread.iloc[0]) if len(quantile_spread) > 0 else 0,
                "quantile_spread_5d": float(quantile_spread.iloc[1]) if len(quantile_spread) > 1 else 0,
                "quantile_spread_10d": float(quantile_spread.iloc[2]) if len(quantile_spread) > 2 else 0,
                "turnover": float(avg_turnover),
                "estimated_sharpe": float(estimated_sharpe),
                "usable": self._is_factor_usable(mean_ic, ic_std, avg_turnover)
            }

            return analysis

        except Exception as e:
            logger.error(f"Analysis failed for {factor_name}: {e}")
            return {
                "factor_name": factor_name,
                "status": "failed",
                "usable": False,
                "error": str(e)
            }

    def _is_factor_usable(self, ic_mean: float, ic_std: float, turnover: float) -> bool:
        """
        Determine if a factor is usable based on metrics.

        Args:
            ic_mean: Mean information coefficient
            ic_std: IC standard deviation
            turnover: Average turnover

        Returns:
            True if factor meets minimum criteria
        """
        # Minimum IC threshold
        if ic_mean < 0.02:
            return False

        # IC should be stable (low relative std)
        if ic_std / abs(ic_mean) > 3.0:
            return False

        # Turnover should be reasonable (not too high)
        if turnover > 0.8:  # More than 80% turnover might be too costly
            return False

        return True

    def _make_decision(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """
        Make decision on whether to use this factor.

        Args:
            analysis: Analysis results

        Returns:
            Tuple of (decision, confidence)
            - decision: "use", "reject", or "uncertain"
            - confidence: 0-1 score
        """
        if not analysis.get("usable"):
            return "reject", 0.9

        ic_mean = analysis.get("ic_mean", 0)
        ic_sharpe = analysis.get("ic_sharpe", 0)
        turnover = analysis.get("turnover", 1.0)

        # Score the factor
        score = 0.0

        # IC contribution (0-0.4)
        score += min(ic_mean / 0.05, 1.0) * 0.4

        # IC Sharpe contribution (0-0.3)
        score += min(ic_sharpe / 2.0, 1.0) * 0.3

        # Turnover penalty (0-0.3, lower is better)
        score += (1.0 - min(turnover, 1.0)) * 0.3

        # Decision thresholds
        if score >= self.config.learning.confidence_threshold:
            decision = "use"
            confidence = score
        elif score >= 0.4:
            decision = "uncertain"
            confidence = score
        else:
            decision = "reject"
            confidence = 1.0 - score  # High confidence in rejection

        # Use Claude for complex cases
        if decision == "uncertain":
            decision, confidence = self._claude_decision(analysis)

        return decision, confidence

    def _claude_decision(self, analysis: Dict[str, Any]) -> Tuple[str, float]:
        """
        Use Claude to make decision on uncertain cases.

        Args:
            analysis: Analysis results

        Returns:
            Tuple of (decision, confidence)
        """
        prompt = f"""You are analyzing a trading factor's backtest results. The quantitative metrics are inconclusive.

**Factor Performance:**
- IC Mean: {analysis.get('ic_mean', 0):.4f}
- IC Sharpe: {analysis.get('ic_sharpe', 0):.4f}
- Turnover: {analysis.get('turnover', 0):.2%}
- Estimated Sharpe Ratio: {analysis.get('estimated_sharpe', 0):.4f}

**Decision Criteria:**
- Minimum IC for use: 0.02
- Desired IC Sharpe: > 1.0
- Maximum acceptable turnover: 80%

**Market Context:**
- Current regime: {self.get_global_state().get('current_regime', 'unknown')}

Should this factor be used in production? Consider:
1. Economic intuition behind the metrics
2. Risk vs. reward tradeoff
3. Implementation costs from turnover
4. Market regime suitability

Respond with:
DECISION: [use/reject/test_more]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
"""

        response = self.reason(prompt)

        # Parse response
        decision = "reject"
        confidence = 0.5

        for line in response.split('\n'):
            if line.startswith('DECISION:'):
                decision_text = line.replace('DECISION:', '').strip().lower()
                if 'use' in decision_text:
                    decision = "use"
                elif 'reject' in decision_text:
                    decision = "reject"
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                except:
                    confidence = 0.5

        return decision, confidence

    def _learn_from_backtest(
        self,
        factor_name: str,
        analysis: Dict[str, Any],
        decision: str
    ) -> None:
        """
        Learn from backtest results and update models.

        Args:
            factor_name: Name of the factor
            analysis: Analysis results
            decision: Decision made (use/reject/uncertain)
        """
        # Store in learning memory
        if analysis.get("status") == "success":
            outcome = "success" if decision == "use" else "failure"

            self.memory.store_factor_performance(
                factor_name=factor_name,
                factor_formula=analysis.get("factor_formula", "N/A"),
                metrics={
                    "ic_mean": analysis.get("ic_mean"),
                    "ic_std": analysis.get("ic_std"),
                    "returns_1d": analysis.get("quantile_spread_1d"),
                    "returns_5d": analysis.get("quantile_spread_5d"),
                    "returns_10d": analysis.get("quantile_spread_10d"),
                    "turnover": analysis.get("turnover")
                },
                market_regime=self.get_global_state().get("current_regime", "unknown"),
                test_period_start=datetime.utcnow() - timedelta(days=365),
                test_period_end=datetime.utcnow()
            )

        # Update factor weights (simple learning)
        factor_category = analysis.get("category", "unknown")
        current_weight = self.get_state("factor_weights").get(factor_category, 0.5)

        if decision == "use":
            # Increase weight for this category
            new_weight = current_weight + self.get_state("learning_rate")
        else:
            # Decrease weight
            new_weight = current_weight - self.get_state("learning_rate")

        # Clip to [0, 1]
        new_weight = max(0.0, min(1.0, new_weight))

        factor_weights = self.get_state("factor_weights") or {}
        factor_weights[factor_category] = new_weight
        self.set_state("factor_weights", factor_weights)

        logger.info(f"Updated weight for {factor_category}: {new_weight:.3f}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of backtesting performance.

        Returns:
            Summary dictionary
        """
        return {
            "backtests_run": self.get_state("backtests_run"),
            "strategies_tested": self.get_state("strategies_tested"),
            "successful_strategies": self.get_state("successful_strategies"),
            "success_rate": (
                self.get_state("successful_strategies") / self.get_state("strategies_tested")
                if self.get_state("strategies_tested") > 0 else 0
            ),
            "factor_weights": self.get_state("factor_weights"),
            "best_strategy": self.get_state("best_strategy")
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result for failed backtests."""
        return {
            "backtest_results": {},
            "performance_metrics": {},
            "decision": "reject",
            "confidence": 0.0
        }
