"""
Lightweight configuration for testing without PostgreSQL/Redis.

Uses SQLite and in-memory storage for quick testing.
"""

from alphalens.agents.config import SystemConfig, PostgresConfig, RedisConfig
import tempfile
import os


def create_lite_config(api_key: str = None) -> SystemConfig:
    """
    Create a lightweight configuration for testing.

    Uses:
    - SQLite instead of PostgreSQL
    - In-memory dict instead of Redis
    - Local file storage

    Args:
        api_key: Anthropic API key (or will use environment variable)

    Returns:
        SystemConfig configured for lightweight testing
    """

    # Create temp directory for SQLite database
    temp_dir = tempfile.gettempdir()
    sqlite_path = os.path.join(temp_dir, "alphalens_agents_lite.db")

    config = SystemConfig()

    # Use SQLite connection string
    config.postgres.host = ""
    config.postgres.port = 0
    config.postgres.database = sqlite_path
    config.postgres.user = ""
    config.postgres.password = ""

    # Disable Redis (will use in-memory fallback)
    config.redis.host = "disabled"

    # Set API key
    if api_key:
        config.claude.api_key = api_key

    # Safe defaults for testing
    config.trading.mode = "paper"
    config.orchestrator.enable_auto_trading = False
    config.orchestrator.enable_learning = True
    config.orchestrator.enable_factor_discovery = True

    return config
