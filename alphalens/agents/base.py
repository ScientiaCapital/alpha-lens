"""
Base Agent - Abstract base class for all autonomous agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from anthropic import Anthropic
from loguru import logger

from alphalens.agents.config import SystemConfig
from alphalens.memory.memory_store import MemoryStore


class BaseAgent(ABC):
    """
    Abstract base class for all autonomous agents.

    Each agent has:
    - Access to Claude SDK for reasoning
    - Access to memory (state + learning)
    - Ability to execute actions
    - State persistence
    """

    def __init__(
        self,
        name: str,
        config: SystemConfig,
        memory: MemoryStore,
        description: Optional[str] = None
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name (unique identifier)
            config: System configuration
            memory: Shared memory store
            description: Optional description of agent's purpose
        """
        self.name = name
        self.config = config
        self.memory = memory
        self.description = description or f"{name} agent"

        # Initialize Claude client
        self.claude = Anthropic(api_key=config.claude.api_key)

        # Load agent state from memory
        self.state = self.memory.get_agent_state(self.name)
        if not self.state:
            self.state = self._initialize_state()
            self.memory.set_agent_state(self.name, self.state)

        logger.info(f"Agent initialized: {self.name}")

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main task.

        Args:
            context: Execution context (market data, global state, etc.)

        Returns:
            Dictionary containing execution results and any updates
        """
        pass

    @abstractmethod
    def _initialize_state(self) -> Dict[str, Any]:
        """
        Initialize the agent's state.

        Returns:
            Initial state dictionary
        """
        pass

    def reason(self, prompt: str, system: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """
        Use Claude for complex reasoning.

        Args:
            prompt: The reasoning prompt
            system: System prompt (optional)
            max_tokens: Maximum tokens in response

        Returns:
            Claude's response
        """
        try:
            response = self.claude.messages.create(
                model=self.config.claude.model,
                max_tokens=max_tokens or self.config.claude.max_tokens,
                temperature=self.config.claude.temperature,
                system=system or f"You are {self.description}. Provide clear, actionable insights based on quantitative analysis.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text from response
            result = response.content[0].text if response.content else ""

            logger.debug(f"Agent {self.name} reasoned: {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"Claude reasoning failed for {self.name}: {e}")
            return ""

    def get_state(self, key: Optional[str] = None) -> Any:
        """
        Get agent state or specific state value.

        Args:
            key: Optional key to get specific state value

        Returns:
            State value or entire state dict
        """
        if key:
            return self.state.get(key)
        return self.state

    def set_state(self, key: str, value: Any) -> None:
        """
        Update agent state.

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
        self.state["last_updated"] = datetime.utcnow().isoformat()
        self.memory.set_agent_state(self.name, self.state)

        logger.debug(f"Agent {self.name} state updated: {key}")

    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple state values at once.

        Args:
            updates: Dictionary of state updates
        """
        self.state.update(updates)
        self.state["last_updated"] = datetime.utcnow().isoformat()
        self.memory.set_agent_state(self.name, self.state)

        logger.debug(f"Agent {self.name} state updated: {len(updates)} keys")

    def get_global_state(self) -> Dict[str, Any]:
        """Get the global system state."""
        return self.memory.get_global_state()

    def update_global_state(self, updates: Dict[str, Any]) -> None:
        """
        Update the global system state.

        Args:
            updates: Dictionary of updates to merge into global state
        """
        global_state = self.get_global_state()
        global_state.update(updates)
        self.memory.set_global_state(global_state)

        logger.debug(f"Agent {self.name} updated global state")

    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """
        Log an action taken by the agent.

        Args:
            action: Action name
            details: Action details
        """
        log_entry = {
            "agent": self.name,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store in agent's action history
        action_history = self.get_state("action_history") or []
        action_history.append(log_entry)

        # Keep only last 100 actions in state
        if len(action_history) > 100:
            action_history = action_history[-100:]

        self.set_state("action_history", action_history)

        logger.info(f"Agent {self.name} action: {action}")

    def store_learning(
        self,
        strategy_id: str,
        strategy_type: str,
        description: str,
        parameters: Dict[str, Any],
        performance_metrics: Dict[str, float],
        outcome: str,
        confidence_score: float
    ) -> int:
        """
        Store a learning from this agent's execution.

        Args:
            strategy_id: Unique strategy identifier
            strategy_type: Type of strategy
            description: Description of what was learned
            parameters: Strategy parameters
            performance_metrics: Performance metrics
            outcome: "success", "failure", or "mixed"
            confidence_score: Confidence in this learning (0-1)

        Returns:
            Learning record ID
        """
        market_regime = self.get_global_state().get("current_regime", "unknown")

        learning_id = self.memory.store_learning(
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            description=description,
            parameters=parameters,
            performance_metrics=performance_metrics,
            market_regime=market_regime,
            outcome=outcome,
            confidence_score=confidence_score,
            metadata={"agent": self.name}
        )

        logger.info(f"Agent {self.name} stored learning: {strategy_id}")
        return learning_id

    def get_successful_strategies(
        self,
        strategy_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve successful strategies from learning memory.

        Args:
            strategy_type: Filter by strategy type
            limit: Maximum number of results

        Returns:
            List of successful strategies
        """
        market_regime = self.get_global_state().get("current_regime")

        return self.memory.get_successful_strategies(
            strategy_type=strategy_type,
            market_regime=market_regime,
            limit=limit
        )

    def health_check(self) -> Dict[str, Any]:
        """
        Perform agent health check.

        Returns:
            Health status dictionary
        """
        return {
            "agent": self.name,
            "status": "healthy",
            "last_updated": self.state.get("last_updated"),
            "actions_logged": len(self.get_state("action_history") or [])
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
