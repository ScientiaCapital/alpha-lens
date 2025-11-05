"""
State Manager - Handles shared state across all agents.

Provides both persistent storage (PostgreSQL) and fast in-memory cache (Redis).
"""

import json
import redis
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from alphalens.agents.config import SystemConfig

Base = declarative_base()


class StateRecord(Base):
    """SQLAlchemy model for persistent state storage."""
    __tablename__ = 'agent_states'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, nullable=True)


class StateManager:
    """
    Manages state for all agents with two-tier storage:
    - Redis: Fast in-memory cache for real-time state
    - PostgreSQL: Persistent storage for historical state
    """

    def __init__(self, config: SystemConfig):
        """
        Initialize state manager with Redis and PostgreSQL connections.

        Args:
            config: System configuration
        """
        self.config = config

        # Redis connection for fast cache
        self.redis_client = redis.Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            decode_responses=config.redis.decode_responses
        )

        # PostgreSQL connection for persistent storage
        self.engine = create_engine(config.postgres.connection_string)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        logger.info("StateManager initialized with Redis and PostgreSQL")

    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            persist: bool = True, metadata: Optional[Dict] = None) -> None:
        """
        Set a state value.

        Args:
            key: State key
            value: State value (will be JSON serialized)
            ttl: Time to live in seconds for Redis cache (None = no expiration)
            persist: Whether to persist to PostgreSQL
            metadata: Additional metadata to store with the value
        """
        # Serialize value
        serialized = json.dumps(value)

        # Store in Redis cache
        if ttl:
            self.redis_client.setex(key, ttl, serialized)
        else:
            self.redis_client.set(key, serialized)

        # Store in PostgreSQL if persist=True
        if persist:
            state_record = self.session.query(StateRecord).filter_by(key=key).first()
            if state_record:
                state_record.value = value
                state_record.updated_at = datetime.utcnow()
                state_record.metadata = metadata
            else:
                state_record = StateRecord(
                    key=key,
                    value=value,
                    metadata=metadata
                )
                self.session.add(state_record)

            self.session.commit()

        logger.debug(f"State set: {key}")

    def get(self, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        Get a state value.

        Args:
            key: State key
            default: Default value if key not found
            use_cache: Whether to check Redis cache first

        Returns:
            State value or default if not found
        """
        # Try Redis cache first
        if use_cache:
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"State retrieved from cache: {key}")
                return json.loads(cached)

        # Fall back to PostgreSQL
        state_record = self.session.query(StateRecord).filter_by(key=key).first()
        if state_record:
            value = state_record.value

            # Update Redis cache
            if use_cache:
                self.redis_client.set(key, json.dumps(value))

            logger.debug(f"State retrieved from DB: {key}")
            return value

        logger.debug(f"State not found: {key}, returning default")
        return default

    def delete(self, key: str) -> None:
        """
        Delete a state value from both cache and persistent storage.

        Args:
            key: State key
        """
        # Delete from Redis
        self.redis_client.delete(key)

        # Delete from PostgreSQL
        self.session.query(StateRecord).filter_by(key=key).delete()
        self.session.commit()

        logger.debug(f"State deleted: {key}")

    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """
        Get all state values matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "agent:*")

        Returns:
            Dictionary of key-value pairs
        """
        result = {}

        # Get keys matching pattern from Redis
        keys = self.redis_client.keys(pattern)
        for key in keys:
            try:
                value = self.redis_client.get(key)
                if value:
                    result[key] = json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON for key: {key}")

        return result

    def get_history(self, key: str, limit: int = 100) -> List[Dict]:
        """
        Get historical values for a key from PostgreSQL.

        Args:
            key: State key
            limit: Maximum number of records to retrieve

        Returns:
            List of historical records
        """
        records = self.session.query(StateRecord).filter_by(key=key)\
            .order_by(StateRecord.updated_at.desc())\
            .limit(limit)\
            .all()

        return [
            {
                "value": r.value,
                "updated_at": r.updated_at.isoformat(),
                "metadata": r.metadata
            }
            for r in records
        ]

    def increment(self, key: str, amount: int = 1) -> int:
        """
        Atomically increment a counter.

        Args:
            key: Counter key
            amount: Amount to increment by

        Returns:
            New counter value
        """
        new_value = self.redis_client.incr(key, amount)
        logger.debug(f"Counter incremented: {key} = {new_value}")
        return new_value

    def expire(self, key: str, seconds: int) -> None:
        """
        Set expiration on a key.

        Args:
            key: State key
            seconds: Expiration time in seconds
        """
        self.redis_client.expire(key, seconds)

    def get_global_state(self) -> Dict[str, Any]:
        """
        Get the global system state.

        Returns:
            Global state dictionary
        """
        return self.get("global_state", default={
            "current_regime": "unknown",
            "active_factors": [],
            "portfolio": {},
            "cash": self.config.trading.initial_capital,
            "risk_metrics": {},
            "last_updated": datetime.utcnow().isoformat()
        })

    def set_global_state(self, state: Dict[str, Any]) -> None:
        """
        Update the global system state.

        Args:
            state: Global state dictionary
        """
        state["last_updated"] = datetime.utcnow().isoformat()
        self.set("global_state", state, persist=True)

    def get_agent_state(self, agent_name: str) -> Dict[str, Any]:
        """
        Get state for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent state dictionary
        """
        return self.get(f"agent:{agent_name}", default={})

    def set_agent_state(self, agent_name: str, state: Dict[str, Any]) -> None:
        """
        Update state for a specific agent.

        Args:
            agent_name: Name of the agent
            state: Agent state dictionary
        """
        self.set(f"agent:{agent_name}", state, persist=True)

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of storage backends.

        Returns:
            Dictionary with health status
        """
        health = {}

        # Check Redis
        try:
            self.redis_client.ping()
            health["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            health["redis"] = False

        # Check PostgreSQL
        try:
            self.session.execute("SELECT 1")
            health["postgres"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            health["postgres"] = False

        return health

    def close(self) -> None:
        """Close all connections."""
        self.session.close()
        self.redis_client.close()
        logger.info("StateManager connections closed")
