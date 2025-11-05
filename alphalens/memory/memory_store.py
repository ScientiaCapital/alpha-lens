"""
Memory Store - High-level interface for all memory operations.

Combines StateManager and LearningMemory into a unified interface.
"""

from typing import Any, Dict, List, Optional
from alphalens.memory.state_manager import StateManager
from alphalens.memory.learning_memory import LearningMemory
from alphalens.agents.config import SystemConfig
from loguru import logger


class MemoryStore:
    """
    Unified interface for all memory operations.

    Provides access to both state management and learning memory.
    """

    def __init__(self, config: SystemConfig):
        """
        Initialize memory store.

        Args:
            config: System configuration
        """
        self.config = config
        self.state_manager = StateManager(config)
        self.learning_memory = LearningMemory(config)

        logger.info("MemoryStore initialized")

    # State management methods
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self.state_manager.get(key, default)

    def set_state(self, key: str, value: Any, ttl: Optional[int] = None, persist: bool = True) -> None:
        """Set a state value."""
        self.state_manager.set(key, value, ttl=ttl, persist=persist)

    def get_global_state(self) -> Dict[str, Any]:
        """Get the global system state."""
        return self.state_manager.get_global_state()

    def set_global_state(self, state: Dict[str, Any]) -> None:
        """Set the global system state."""
        self.state_manager.set_global_state(state)

    def get_agent_state(self, agent_name: str) -> Dict[str, Any]:
        """Get state for a specific agent."""
        return self.state_manager.get_agent_state(agent_name)

    def set_agent_state(self, agent_name: str, state: Dict[str, Any]) -> None:
        """Set state for a specific agent."""
        self.state_manager.set_agent_state(agent_name, state)

    # Learning memory methods
    def store_learning(self, *args, **kwargs) -> int:
        """Store a strategy learning."""
        return self.learning_memory.store_strategy_learning(*args, **kwargs)

    def get_successful_strategies(self, *args, **kwargs) -> List[Dict]:
        """Get successful strategies."""
        return self.learning_memory.get_successful_strategies(*args, **kwargs)

    def store_factor_performance(self, *args, **kwargs) -> int:
        """Store factor performance."""
        return self.learning_memory.store_factor_performance(*args, **kwargs)

    def get_factor_history(self, *args, **kwargs) -> List[Dict]:
        """Get factor performance history."""
        return self.learning_memory.get_factor_performance_history(*args, **kwargs)

    def store_risk_event(self, *args, **kwargs) -> int:
        """Store a risk event."""
        return self.learning_memory.store_risk_event(*args, **kwargs)

    def get_risk_events(self, *args, **kwargs) -> List[Dict]:
        """Get risk events."""
        return self.learning_memory.get_risk_events(*args, **kwargs)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get learning summary statistics."""
        return self.learning_memory.get_learning_summary()

    def health_check(self) -> Dict[str, bool]:
        """Check health of all storage backends."""
        return self.state_manager.health_check()

    def close(self) -> None:
        """Close all connections."""
        self.state_manager.close()
        self.learning_memory.close()
        logger.info("MemoryStore closed")
