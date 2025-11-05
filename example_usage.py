"""
Example usage of the Alphalens Autonomous Trading System.

This script demonstrates how to:
1. Initialize the system
2. Run a single iteration
3. Monitor the results
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

from alphalens.agents.config import SystemConfig
from alphalens.orchestrator import TradingOrchestrator

# Configure logging
logger.add("logs/example_{time}.log", rotation="1 day")


def generate_sample_data(n_stocks=100, n_days=252):
    """
    Generate sample market data for testing.

    Args:
        n_stocks: Number of stocks
        n_days: Number of trading days

    Returns:
        DataFrame with price data
    """
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='B')
    tickers = [f"STOCK_{i:03d}" for i in range(n_stocks)]

    # Generate random walk prices
    np.random.seed(42)
    prices = np.exp(np.random.randn(n_days, n_stocks).cumsum(axis=0) * 0.01 + 4.6)

    df = pd.DataFrame(prices, index=dates, columns=tickers)
    return df


def main():
    """Main example function."""

    logger.info("=" * 60)
    logger.info("Alphalens Autonomous Trading System - Example")
    logger.info("=" * 60)

    # Load configuration
    logger.info("Loading configuration...")
    config = SystemConfig.from_yaml("config.yaml")

    # Override for paper trading mode
    config.trading.mode = "paper"
    config.orchestrator.enable_auto_trading = False  # Safety: don't auto-trade in example

    logger.info(f"Trading mode: {config.trading.mode}")
    logger.info(f"Initial capital: ${config.trading.initial_capital:,.2f}")

    # Initialize orchestrator
    logger.info("Initializing orchestrator...")
    orchestrator = TradingOrchestrator(config)

    # Generate sample market data
    logger.info("Generating sample market data...")
    market_data = generate_sample_data(n_stocks=100, n_days=252)
    logger.info(f"Market data shape: {market_data.shape}")

    # Perform health check
    logger.info("Performing health check...")
    health = orchestrator.health_check()
    logger.info(f"System health: {health}")

    # Run one iteration of the trading system
    logger.info("\n" + "=" * 60)
    logger.info("Running orchestrator iteration...")
    logger.info("=" * 60)

    try:
        final_state = orchestrator.start(market_data=market_data)

        logger.info("\n" + "=" * 60)
        logger.info("Iteration Results:")
        logger.info("=" * 60)

        logger.info(f"Stage completed: {final_state.get('stage')}")
        logger.info(f"Current regime: {final_state.get('current_regime')}")
        logger.info(f"Factors discovered: {len(final_state.get('discovered_factors', []))}")
        logger.info(f"Successful factors: {len(final_state.get('successful_factors', []))}")
        logger.info(f"Trading decisions made: {len(final_state.get('trading_decisions', []))}")
        logger.info(f"Trades executed: {len(final_state.get('executed_trades', []))}")
        logger.info(f"Errors: {len(final_state.get('errors', []))}")

        if final_state.get('errors'):
            logger.warning("Errors encountered:")
            for error in final_state['errors']:
                logger.warning(f"  - {error}")

        # Display successful factors
        if final_state.get('successful_factors'):
            logger.info("\nSuccessful Factors:")
            for i, factor in enumerate(final_state['successful_factors'][:5], 1):
                logger.info(f"\n  {i}. {factor.get('name')}")
                logger.info(f"     Category: {factor.get('category')}")
                logger.info(f"     Expected IC: {factor.get('expected_ic', 0):.4f}")
                logger.info(f"     Rationale: {factor.get('rationale', 'N/A')[:100]}...")

        # Display risk assessment
        risk = final_state.get('risk_assessment', {})
        if risk:
            logger.info("\nRisk Assessment:")
            logger.info(f"  Portfolio Value: ${risk.get('portfolio_value', 0):,.2f}")
            logger.info(f"  Leverage: {risk.get('leverage', 0):.2f}x")
            logger.info(f"  Risk Score: {risk.get('overall_risk_score', 0):.2f}")
            logger.info(f"  Violations: {len(final_state.get('risk_violations', []))}")

        # Get performance summary
        logger.info("\n" + "=" * 60)
        logger.info("Performance Summary:")
        logger.info("=" * 60)

        performance = orchestrator.get_performance()
        logger.info(f"Total iterations: {performance.get('iterations', 0)}")
        logger.info(f"Successful factors found: {performance.get('successful_factors', 0)}")
        logger.info(f"Total trades: {performance.get('total_trades', 0)}")

        learning_summary = performance.get('learning_summary', {})
        if learning_summary:
            logger.info(f"\nLearning Summary:")
            logger.info(f"  Strategies tested: {learning_summary.get('total_strategies_tested', 0)}")
            logger.info(f"  Success rate: {learning_summary.get('success_rate', 0):.1%}")

    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        logger.info("\n" + "=" * 60)
        logger.info("Shutting down orchestrator...")
        orchestrator.close()
        logger.info("Done!")


if __name__ == "__main__":
    main()
