"""
Trading Orchestrator - Central coordinator using LangGraph state machine.
"""

from typing import Dict, Any, Callable
from datetime import datetime
from loguru import logger
from langgraph.graph import StateGraph, END

from alphalens.agents.config import SystemConfig
from alphalens.memory.memory_store import MemoryStore
from alphalens.orchestrator.state import TradingState, create_initial_state

# Import agents
from alphalens.agents.factor_discovery import FactorDiscoveryAgent
from alphalens.agents.backtesting import BacktestingAgent
from alphalens.agents.risk_management import RiskManagementAgent
from alphalens.agents.execution import ExecutionAgent
from alphalens.agents.market_regime import MarketRegimeAgent


class TradingOrchestrator:
    """
    Central orchestrator that coordinates all agents using a LangGraph state machine.

    State transitions:
    idle -> regime_detection -> factor_discovery -> backtesting -> risk_analysis
    -> decision_making -> execution -> learning -> idle
    """

    def __init__(self, config: SystemConfig):
        """
        Initialize the orchestrator.

        Args:
            config: System configuration
        """
        self.config = config
        self.memory = MemoryStore(config)

        # Initialize all agents
        self.agents = {
            "factor_discovery": FactorDiscoveryAgent(config, self.memory),
            "backtesting": BacktestingAgent(config, self.memory),
            "risk_management": RiskManagementAgent(config, self.memory),
            "execution": ExecutionAgent(config, self.memory),
            "market_regime": MarketRegimeAgent(config, self.memory)
        }

        # Build the state machine
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

        # Orchestrator state
        self.current_state = create_initial_state()
        self.is_running = False
        self.is_paused = False

        logger.info("TradingOrchestrator initialized")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.

        Returns:
            Configured state graph
        """
        # Create state graph
        workflow = StateGraph(TradingState)

        # Add nodes (each represents an agent or decision point)
        workflow.add_node("detect_regime", self._detect_regime)
        workflow.add_node("discover_factors", self._discover_factors)
        workflow.add_node("backtest_factors", self._backtest_factors)
        workflow.add_node("assess_risk", self._assess_risk)
        workflow.add_node("make_decisions", self._make_decisions)
        workflow.add_node("execute_trades", self._execute_trades)
        workflow.add_node("learn", self._learn)

        # Define edges (transitions)
        workflow.set_entry_point("detect_regime")

        workflow.add_edge("detect_regime", "discover_factors")
        workflow.add_edge("discover_factors", "backtest_factors")
        workflow.add_edge("backtest_factors", "assess_risk")
        workflow.add_conditional_edges(
            "assess_risk",
            self._should_trade,
            {
                "make_decisions": "make_decisions",
                "learn": "learn",  # Skip trading if risk too high
            }
        )
        workflow.add_edge("make_decisions", "execute_trades")
        workflow.add_edge("execute_trades", "learn")
        workflow.add_edge("learn", END)

        logger.info("LangGraph state machine built")
        return workflow

    # Node functions - each corresponds to a stage in the workflow

    def _detect_regime(self, state: TradingState) -> TradingState:
        """Detect market regime."""
        logger.info("Stage: Detecting market regime")

        try:
            result = self.agents["market_regime"].execute({
                "market_data": state["market_data"]
            })

            state["current_regime"] = result["regime"]
            state["stage"] = "regime_detected"

        except Exception as e:
            logger.error(f"Regime detection failed: {e}")
            state["errors"].append(str(e))

        return state

    def _discover_factors(self, state: TradingState) -> TradingState:
        """Discover new factors."""
        logger.info("Stage: Discovering factors")

        if not self.config.orchestrator.enable_factor_discovery:
            logger.info("Factor discovery disabled")
            return state

        try:
            result = self.agents["factor_discovery"].execute({
                "market_data": state["market_data"],
                "existing_factors": state.get("successful_factors", [])
            })

            state["discovered_factors"] = result["new_factors"]
            state["factors_to_test"] = result["new_factors"]
            state["stage"] = "factors_discovered"

        except Exception as e:
            logger.error(f"Factor discovery failed: {e}")
            state["errors"].append(str(e))

        return state

    def _backtest_factors(self, state: TradingState) -> TradingState:
        """Backtest discovered factors."""
        logger.info("Stage: Backtesting factors")

        backtest_results = []
        successful_factors = []

        for factor in state.get("factors_to_test", []):
            try:
                # Note: In production, you'd pass actual factor data and prices
                result = self.agents["backtesting"].execute({
                    "factor": factor.get("formula"),
                    "prices": state.get("market_data"),
                    "factor_name": factor.get("name", "unnamed")
                })

                backtest_results.append(result)

                if result["decision"] == "use":
                    successful_factors.append({
                        **factor,
                        "backtest_metrics": result["performance_metrics"]
                    })

            except Exception as e:
                logger.error(f"Backtest failed for {factor.get('name')}: {e}")
                state["errors"].append(str(e))

        state["backtest_results"] = {"results": backtest_results}
        state["successful_factors"] = successful_factors
        state["stage"] = "backtesting_complete"

        return state

    def _assess_risk(self, state: TradingState) -> TradingState:
        """Assess portfolio risk."""
        logger.info("Stage: Assessing risk")

        try:
            result = self.agents["risk_management"].execute({
                "portfolio": state["portfolio"],
                "market_data": state["market_data"]
            })

            state["risk_assessment"] = result["risk_assessment"]
            state["risk_violations"] = result["violations"]
            state["stage"] = "risk_assessed"

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            state["errors"].append(str(e))

        return state

    def _make_decisions(self, state: TradingState) -> TradingState:
        """Make trading decisions based on successful factors."""
        logger.info("Stage: Making trading decisions")

        decisions = []

        for factor in state.get("successful_factors", []):
            # Simple decision logic - in production, use Claude for complex reasoning
            decision = {
                "action": "buy",
                "factor": factor["name"],
                "confidence": factor.get("backtest_metrics", {}).get("confidence", 0.5),
                "size": 0.05,  # 5% of portfolio
                "timestamp": datetime.utcnow().isoformat()
            }
            decisions.append(decision)

        state["trading_decisions"] = decisions
        state["approved_trades"] = decisions  # Simplified - normally go through risk approval
        state["stage"] = "decisions_made"

        return state

    def _execute_trades(self, state: TradingState) -> TradingState:
        """Execute approved trades."""
        logger.info("Stage: Executing trades")

        if not self.config.orchestrator.enable_auto_trading:
            logger.info("Auto-trading disabled, skipping execution")
            state["stage"] = "execution_skipped"
            return state

        try:
            result = self.agents["execution"].execute({
                "orders": state.get("approved_trades", []),
                "market_data": state["market_data"]
            })

            state["execution_results"] = result
            state["executed_trades"] = state.get("approved_trades", [])
            state["stage"] = "trades_executed"

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            state["errors"].append(str(e))

        return state

    def _learn(self, state: TradingState) -> TradingState:
        """Learn from the iteration."""
        logger.info("Stage: Learning from results")

        if not self.config.orchestrator.enable_learning:
            logger.info("Learning disabled")
            return state

        # Store learnings
        learnings = []

        for factor in state.get("successful_factors", []):
            learning = {
                "factor": factor["name"],
                "performance": factor.get("backtest_metrics", {}),
                "regime": state["current_regime"],
                "timestamp": datetime.utcnow().isoformat()
            }
            learnings.append(learning)

        state["learnings"] = learnings
        state["iteration"] += 1
        state["stage"] = "learning_complete"

        logger.info(f"Iteration {state['iteration']} complete")
        return state

    def _should_trade(self, state: TradingState) -> str:
        """
        Conditional edge function to determine if trading should proceed.

        Args:
            state: Current state

        Returns:
            Next node name
        """
        violations = state.get("risk_violations", [])

        if violations:
            logger.warning(f"Risk violations detected, skipping trading: {violations}")
            return "learn"

        if not state.get("successful_factors"):
            logger.info("No successful factors, skipping trading")
            return "learn"

        return "make_decisions"

    # Public API methods

    def start(self, market_data: Any = None) -> Dict[str, Any]:
        """
        Start the orchestrator for one iteration.

        Args:
            market_data: Market data to process

        Returns:
            Final state after iteration
        """
        logger.info("Starting orchestrator iteration")
        self.is_running = True

        # Reset state for new iteration
        self.current_state = create_initial_state()
        self.current_state["market_data"] = market_data

        try:
            # Run the state machine
            final_state = self.compiled_graph.invoke(self.current_state)

            logger.info("Orchestrator iteration complete")
            return final_state

        except Exception as e:
            logger.error(f"Orchestrator failed: {e}")
            return {"error": str(e), "state": self.current_state}

        finally:
            self.is_running = False

    def pause(self) -> None:
        """Pause the orchestrator."""
        self.is_paused = True
        logger.info("Orchestrator paused")

    def resume(self) -> None:
        """Resume the orchestrator."""
        self.is_paused = False
        logger.info("Orchestrator resumed")

    def emergency_stop(self) -> None:
        """Emergency stop - halt all operations."""
        self.is_running = False
        self.is_paused = True
        logger.critical("EMERGENCY STOP TRIGGERED")

        # Store emergency stop event
        self.memory.store_risk_event(
            event_type="emergency_stop",
            severity="critical",
            description="Manual emergency stop triggered",
            metrics={"timestamp": datetime.utcnow().isoformat()}
        )

    def get_state(self) -> Dict[str, Any]:
        """Get current orchestrator state."""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_state": self.current_state,
            "agents_status": {name: agent.health_check() for name, agent in self.agents.items()}
        }

    def get_performance(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            "portfolio": self.current_state.get("portfolio"),
            "iterations": self.current_state.get("iteration", 0),
            "successful_factors": len(self.current_state.get("successful_factors", [])),
            "total_trades": len(self.current_state.get("executed_trades", [])),
            "learning_summary": self.memory.get_learning_summary()
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        return {
            "orchestrator": "healthy" if not self.is_paused else "paused",
            "memory": self.memory.health_check(),
            "agents": {name: agent.health_check() for name, agent in self.agents.items()}
        }

    def close(self) -> None:
        """Shutdown the orchestrator and clean up resources."""
        logger.info("Shutting down orchestrator")
        self.emergency_stop()
        self.memory.close()
