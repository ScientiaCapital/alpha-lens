"""
Mean-Variance Portfolio Optimization (Markowitz).
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Optional, Dict
from loguru import logger


class MeanVarianceOptimizer:
    """
    Mean-Variance portfolio optimizer.

    Implements Markowitz portfolio optimization to find optimal weights.
    """

    def __init__(
        self,
        risk_free_rate: float = 0.02,
        max_position: float = 0.2,
        min_position: float = 0.0
    ):
        """
        Initialize optimizer.

        Args:
            risk_free_rate: Risk-free rate for Sharpe calculation
            max_position: Maximum position size
            min_position: Minimum position size
        """
        self.risk_free_rate = risk_free_rate
        self.max_position = max_position
        self.min_position = min_position

        logger.info("Mean-Variance optimizer initialized")

    def optimize(
        self,
        returns: pd.DataFrame,
        target_return: Optional[float] = None,
        risk_aversion: float = 1.0
    ) -> Dict[str, float]:
        """
        Optimize portfolio weights.

        Args:
            returns: DataFrame of asset returns
            target_return: Target return (if None, maximize Sharpe)
            risk_aversion: Risk aversion parameter

        Returns:
            Dictionary of {asset: weight}
        """
        # Calculate expected returns and covariance
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        n_assets = len(mean_returns)

        # Objective function
        def portfolio_variance(weights):
            return weights.T @ cov_matrix @ weights

        def portfolio_return(weights):
            return weights.T @ mean_returns

        def negative_sharpe(weights):
            ret = portfolio_return(weights)
            vol = np.sqrt(portfolio_variance(weights))
            return -(ret - self.risk_free_rate) / vol if vol > 0 else 0

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]

        if target_return is not None:
            constraints.append({
                'type': 'eq',
                'fun': lambda x: portfolio_return(x) - target_return
            })

        # Bounds
        bounds = tuple((self.min_position, self.max_position) for _ in range(n_assets))

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        if target_return is None:
            # Maximize Sharpe ratio
            result = minimize(
                negative_sharpe,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
        else:
            # Minimize variance for target return
            result = minimize(
                portfolio_variance,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )

        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
            # Return equal weights
            weights = {asset: 1.0 / n_assets for asset in returns.columns}
        else:
            weights = {asset: weight for asset, weight in zip(returns.columns, result.x)}
            weights = {k: v for k, v in weights.items() if v > 0.001}  # Filter tiny weights

            logger.info("Optimization successful")

        return weights

    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        n_points: int = 50
    ) -> pd.DataFrame:
        """
        Calculate efficient frontier.

        Args:
            returns: DataFrame of asset returns
            n_points: Number of points on frontier

        Returns:
            DataFrame with returns and volatilities
        """
        mean_returns = returns.mean()
        min_ret = mean_returns.min()
        max_ret = mean_returns.max()

        target_returns = np.linspace(min_ret, max_ret, n_points)

        frontier_returns = []
        frontier_vols = []

        for target in target_returns:
            try:
                weights = self.optimize(returns, target_return=target)
                weights_array = np.array([weights.get(col, 0) for col in returns.columns])

                port_return = weights_array.T @ mean_returns
                port_vol = np.sqrt(weights_array.T @ returns.cov() @ weights_array)

                frontier_returns.append(port_return)
                frontier_vols.append(port_vol)
            except:
                pass

        return pd.DataFrame({
            'return': frontier_returns,
            'volatility': frontier_vols
        })
