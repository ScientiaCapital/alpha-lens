"""
State definitions for the trading orchestrator.
"""

from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from datetime import datetime


class TradingState(TypedDict):
    """
    State for the trading orchestrator state machine.

    This represents the complete state as the system moves through
    different stages of the trading workflow.
    """

    # Current stage
    stage: str  # idle, discovering, backtesting, risk_analysis, deciding, executing, learning

    # Market data
    market_data: Optional[Any]
    current_regime: str

    # Factor discovery
    discovered_factors: List[Dict[str, Any]]
    factors_to_test: List[Dict[str, Any]]

    # Backtesting
    backtest_results: Dict[str, Any]
    successful_factors: List[Dict[str, Any]]

    # Risk management
    risk_assessment: Dict[str, Any]
    risk_violations: List[str]

    # Decision making
    trading_decisions: List[Dict[str, Any]]
    approved_trades: List[Dict[str, Any]]

    # Execution
    executed_trades: List[Dict[str, Any]]
    execution_results: Dict[str, Any]

    # Learning
    learnings: List[Dict[str, Any]]

    # Portfolio state
    portfolio: Dict[str, Any]

    # Metadata
    iteration: int
    last_update: str
    errors: List[str]


def create_initial_state() -> TradingState:
    """Create initial state for the orchestrator."""
    return TradingState(
        stage="idle",
        market_data=None,
        current_regime="unknown",
        discovered_factors=[],
        factors_to_test=[],
        backtest_results={},
        successful_factors=[],
        risk_assessment={},
        risk_violations=[],
        trading_decisions=[],
        approved_trades=[],
        executed_trades=[],
        execution_results={},
        learnings=[],
        portfolio={
            "cash": 1_000_000,
            "positions": {},
            "total_value": 1_000_000
        },
        iteration=0,
        last_update=datetime.utcnow().isoformat(),
        errors=[]
    )
