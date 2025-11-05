"""
Configuration management for the autonomous trading system.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class ClaudeConfig(BaseModel):
    """Configuration for Claude SDK."""
    api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = Field(default="claude-3-5-sonnet-20241022")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.7)


class RedisConfig(BaseModel):
    """Configuration for Redis cache."""
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: Optional[str] = Field(default=None)
    decode_responses: bool = Field(default=True)


class PostgresConfig(BaseModel):
    """Configuration for PostgreSQL database."""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="alphalens_agents")
    user: str = Field(default="postgres")
    password: str = Field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class VectorDBConfig(BaseModel):
    """Configuration for Vector Database (Weaviate)."""
    url: str = Field(default="http://localhost:8080")
    api_key: Optional[str] = Field(default=None)


class RiskLimits(BaseModel):
    """Risk management limits and guardrails."""
    max_daily_loss_pct: float = Field(default=2.0, description="Maximum daily loss as % of portfolio")
    max_position_size_pct: float = Field(default=10.0, description="Maximum single position size as % of portfolio")
    max_leverage: float = Field(default=1.0, description="Maximum portfolio leverage")
    max_drawdown_pct: float = Field(default=20.0, description="Maximum cumulative drawdown before emergency stop")
    max_sector_exposure_pct: float = Field(default=30.0, description="Maximum exposure to any single sector")
    max_correlation_threshold: float = Field(default=0.7, description="Maximum correlation between positions")

    # Position sizing
    min_position_size_usd: float = Field(default=1000.0)
    max_position_size_usd: float = Field(default=100000.0)

    # Stop losses
    stop_loss_pct: float = Field(default=5.0, description="Stop loss as % from entry")
    trailing_stop_pct: float = Field(default=3.0, description="Trailing stop as % from peak")


class TradingConfig(BaseModel):
    """Trading system configuration."""
    mode: str = Field(default="paper", description="Trading mode: paper, live, backtest")
    initial_capital: float = Field(default=1_000_000.0)
    commission_rate: float = Field(default=0.001, description="Commission as % of trade value")
    slippage_bps: float = Field(default=5.0, description="Slippage in basis points")

    # Backtesting
    backtest_start_date: Optional[str] = Field(default=None)
    backtest_end_date: Optional[str] = Field(default=None)

    # Rebalancing
    rebalance_frequency: str = Field(default="daily", description="daily, weekly, monthly")

    # Factor settings
    factor_lookback_days: int = Field(default=252, description="Days of history for factor analysis")
    factor_quantiles: int = Field(default=5, description="Number of quantiles for factor analysis")


class LearningConfig(BaseModel):
    """Configuration for self-learning system."""
    learning_rate: float = Field(default=0.01)
    exploration_rate: float = Field(default=0.2, description="Exploration vs exploitation balance")
    min_backtest_samples: int = Field(default=100, description="Minimum samples before trusting backtest")
    confidence_threshold: float = Field(default=0.6, description="Minimum confidence to act on strategy")

    # Memory settings
    max_memory_items: int = Field(default=10000)
    memory_retention_days: int = Field(default=730, description="How long to keep learnings")

    # Strategy adaptation
    strategy_update_frequency: str = Field(default="weekly")
    performance_lookback_days: int = Field(default=30)


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator."""
    enable_auto_trading: bool = Field(default=False, description="Enable autonomous trading without human approval")
    enable_learning: bool = Field(default=True)
    enable_factor_discovery: bool = Field(default=True)

    # Agent execution frequency
    factor_discovery_interval_hours: int = Field(default=24)
    backtesting_interval_hours: int = Field(default=6)
    risk_check_interval_minutes: int = Field(default=5)
    regime_check_interval_hours: int = Field(default=1)

    # Logging
    log_level: str = Field(default="INFO")
    log_to_file: bool = Field(default=True)
    log_file_path: str = Field(default="logs/orchestrator.log")


class SystemConfig(BaseModel):
    """Master configuration for the entire system."""
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    risk_limits: RiskLimits = Field(default_factory=RiskLimits)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SystemConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SystemConfig":
        """Load configuration from YAML file."""
        import yaml
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()

    def to_yaml(self, yaml_path: str) -> None:
        """Save configuration to YAML file."""
        import yaml
        with open(yaml_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


# Default configuration instance
DEFAULT_CONFIG = SystemConfig()
