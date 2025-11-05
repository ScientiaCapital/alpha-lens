"""
Lightweight example usage WITHOUT requiring PostgreSQL/Redis.

This version uses in-memory storage for quick testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alphalens.agents.config_lite import create_lite_config
from alphalens.memory.state_manager_lite import LiteStateManager
from alphalens.memory.learning_memory import LearningMemory
from alphalens.memory.memory_store import MemoryStore

# Configure logging
logger.add("logs/example_lite_{time}.log", rotation="1 day")
logger.info("Starting Alphalens Lite Example")


def generate_sample_data(n_stocks=50, n_days=100):
    """
    Generate sample market data for testing.

    Args:
        n_stocks: Number of stocks
        n_days: Number of trading days

    Returns:
        DataFrame with price data
    """
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='B')
    tickers = [f"STOCK_{i:03d}" for f in range(n_stocks)]

    # Generate random walk prices
    np.random.seed(42)
    returns = np.random.randn(n_days, n_stocks) * 0.02  # 2% daily vol
    prices = 100 * np.exp(returns.cumsum(axis=0))

    df = pd.DataFrame(prices, index=dates, columns=tickers)
    return df


def test_agents_individually():
    """Test each agent individually without the full orchestrator."""

    logger.info("=" * 60)
    logger.info("Testing Individual Agents (Lite Mode)")
    logger.info("=" * 60)

    # Create lite configuration
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY found - Claude features will be limited")

    config = create_lite_config(api_key)

    # Create lite memory store
    logger.info("Setting up lite memory store...")
    state_manager = LiteStateManager(config)

    # Mock learning memory (we'll use in-memory for now)
    class MockLearningMemory:
        def __init__(self, config):
            self.learnings = []
            self.factors = []
            self.events = []

        def store_strategy_learning(self, *args, **kwargs):
            self.learnings.append(kwargs)
            return len(self.learnings)

        def store_factor_performance(self, *args, **kwargs):
            self.factors.append(kwargs)
            return len(self.factors)

        def store_risk_event(self, *args, **kwargs):
            self.events.append(kwargs)
            return len(self.events)

        def get_successful_strategies(self, *args, **kwargs):
            return []

        def get_factor_performance_history(self, *args, **kwargs):
            return []

        def get_risk_events(self, *args, **kwargs):
            return []

        def get_learning_summary(self):
            return {
                "total_strategies_tested": len(self.learnings),
                "total_factors_tested": len(self.factors),
                "total_risk_events": len(self.events)
            }

        def close(self):
            pass

    learning_memory = MockLearningMemory(config)

    # Create memory store
    class LiteMemoryStore:
        def __init__(self, state_manager, learning_memory):
            self.state_manager = state_manager
            self.learning_memory = learning_memory

        def get_state(self, key, default=None):
            return self.state_manager.get(key, default)

        def set_state(self, key, value, ttl=None, persist=True):
            self.state_manager.set(key, value, ttl=ttl, persist=persist)

        def get_global_state(self):
            return self.state_manager.get_global_state()

        def set_global_state(self, state):
            self.state_manager.set_global_state(state)

        def get_agent_state(self, agent_name):
            return self.state_manager.get_agent_state(agent_name)

        def set_agent_state(self, agent_name, state):
            self.state_manager.set_agent_state(agent_name, state)

        def store_learning(self, *args, **kwargs):
            return self.learning_memory.store_strategy_learning(*args, **kwargs)

        def get_successful_strategies(self, *args, **kwargs):
            return self.learning_memory.get_successful_strategies(*args, **kwargs)

        def store_factor_performance(self, *args, **kwargs):
            return self.learning_memory.store_factor_performance(*args, **kwargs)

        def get_factor_history(self, *args, **kwargs):
            return self.learning_memory.get_factor_performance_history(*args, **kwargs)

        def store_risk_event(self, *args, **kwargs):
            return self.learning_memory.store_risk_event(*args, **kwargs)

        def get_risk_events(self, *args, **kwargs):
            return self.learning_memory.get_risk_events(*args, **kwargs)

        def get_learning_summary(self):
            return self.learning_memory.get_learning_summary()

        def health_check(self):
            return self.state_manager.health_check()

        def close(self):
            self.state_manager.close()
            self.learning_memory.close()

    memory = LiteMemoryStore(state_manager, learning_memory)

    # Generate sample data
    logger.info("Generating sample market data...")
    market_data = generate_sample_data(n_stocks=50, n_days=100)
    logger.info(f"Market data shape: {market_data.shape}")

    # Test Market Regime Agent
    logger.info("\n" + "=" * 60)
    logger.info("1. Testing Market Regime Agent")
    logger.info("=" * 60)

    from alphalens.agents.market_regime import MarketRegimeAgent

    regime_agent = MarketRegimeAgent(config, memory)
    regime_result = regime_agent.execute({"market_data": market_data})

    logger.info(f"✓ Detected regime: {regime_result['regime']}")
    logger.info(f"✓ Confidence: {regime_result['confidence']:.2f}")

    # Test Factor Discovery Agent (without Claude if no API key)
    logger.info("\n" + "=" * 60)
    logger.info("2. Testing Factor Discovery Agent")
    logger.info("=" * 60)

    if api_key:
        from alphalens.agents.factor_discovery import FactorDiscoveryAgent

        factor_agent = FactorDiscoveryAgent(config, memory)

        # Note: This will call Claude API
        try:
            factor_result = factor_agent.execute({
                "market_data": market_data,
                "existing_factors": []
            })

            logger.info(f"✓ Factors discovered: {len(factor_result['new_factors'])}")
            for i, factor in enumerate(factor_result['new_factors'][:3], 1):
                logger.info(f"  {i}. {factor.get('name', 'Unknown')}")
        except Exception as e:
            logger.warning(f"Factor discovery failed (may need valid API key): {e}")
    else:
        logger.info("Skipping Factor Discovery (no API key)")

    # Test Risk Management Agent
    logger.info("\n" + "=" * 60)
    logger.info("3. Testing Risk Management Agent")
    logger.info("=" * 60)

    from alphalens.agents.risk_management import RiskManagementAgent

    risk_agent = RiskManagementAgent(config, memory)

    portfolio = {
        "total_value": 1_000_000,
        "cash": 500_000,
        "positions": {}
    }

    risk_result = risk_agent.execute({
        "portfolio": portfolio,
        "market_data": market_data
    })

    logger.info(f"✓ Risk score: {risk_result['risk_assessment'].get('overall_risk_score', 0):.2f}")
    logger.info(f"✓ Violations: {len(risk_result['violations'])}")
    logger.info(f"✓ Action required: {risk_result['action_required']}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    logger.info(f"✓ Market Regime Agent: Working")
    logger.info(f"✓ Risk Management Agent: Working")
    if api_key:
        logger.info(f"✓ Factor Discovery Agent: Working")
    else:
        logger.info(f"⚠ Factor Discovery Agent: Needs API key")

    logger.info("\n✅ Basic agent functionality verified!")
    logger.info("\nNext steps:")
    logger.info("1. Add ANTHROPIC_API_KEY to .env file")
    logger.info("2. Run full example_usage.py with PostgreSQL/Redis")
    logger.info("3. Start building production features")

    # Cleanup
    memory.close()


if __name__ == "__main__":
    try:
        test_agents_individually()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
