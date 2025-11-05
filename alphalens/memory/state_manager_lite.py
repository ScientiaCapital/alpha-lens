"""
Lightweight state manager using in-memory storage.

For testing without Redis/PostgreSQL.
"""

import json
from typing import Any, Dict, Optional, List
from datetime import datetime
from loguru import logger


class LiteStateManager:
    """
    In-memory state manager for testing.

    Provides same interface as StateManager but stores everything in memory.
    """

    def __init__(self, config):
        """Initialize with in-memory storage."""
        self.config = config
        self._storage = {}
        self._history = {}
        logger.info("LiteStateManager initialized (in-memory mode)")

    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            persist: bool = True, metadata: Optional[Dict] = None) -> None:
        """Set a state value in memory."""
        self._storage[key] = {
            "value": value,
            "metadata": metadata,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Store in history
        if key not in self._history:
            self._history[key] = []
        self._history[key].append({
            "value": value,
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata
        })

        logger.debug(f"State set: {key}")

    def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """Get a state value from memory."""
        if key in self._storage:
            return self._storage[key]["value"]
        return default

    def delete(self, key: str) -> None:
        """Delete a state value."""
        if key in self._storage:
            del self._storage[key]
        logger.debug(f"State deleted: {key}")

    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all state values."""
        return {k: v["value"] for k, v in self._storage.items()}

    def get_history(self, key: str, limit: int = 100) -> List[Dict]:
        """Get historical values."""
        if key in self._history:
            return self._history[key][-limit:]
        return []

    def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a counter."""
        current = self.get(key, 0)
        new_value = current + amount
        self.set(key, new_value)
        return new_value

    def expire(self, key: str, seconds: int) -> None:
        """Set expiration (no-op in lite mode)."""
        pass

    def get_global_state(self) -> Dict[str, Any]:
        """Get global system state."""
        return self.get("global_state", default={
            "current_regime": "unknown",
            "active_factors": [],
            "portfolio": {},
            "cash": self.config.trading.initial_capital,
            "risk_metrics": {},
            "last_updated": datetime.utcnow().isoformat()
        })

    def set_global_state(self, state: Dict[str, Any]) -> None:
        """Update global system state."""
        state["last_updated"] = datetime.utcnow().isoformat()
        self.set("global_state", state, persist=True)

    def get_agent_state(self, agent_name: str) -> Dict[str, Any]:
        """Get agent state."""
        return self.get(f"agent:{agent_name}", default={})

    def set_agent_state(self, agent_name: str, state: Dict[str, Any]) -> None:
        """Set agent state."""
        self.set(f"agent:{agent_name}", state, persist=True)

    def health_check(self) -> Dict[str, bool]:
        """Health check."""
        return {
            "redis": True,  # Always healthy in lite mode
            "postgres": True
        }

    def close(self) -> None:
        """Close (no-op in lite mode)."""
        logger.info("LiteStateManager closed")
