"""
Base asset class and common types.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
from loguru import logger


class AssetType(Enum):
    """Asset type enumeration."""
    EQUITY = "equity"
    OPTION = "option"
    CRYPTO = "crypto"
    FUTURE = "future"
    FOREX = "forex"


@dataclass
class PriceData:
    """Price data for an asset."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None


@dataclass
class RiskMetrics:
    """Risk metrics for an asset."""
    volatility: float  # Annualized volatility
    beta: Optional[float] = None  # Beta to market
    var_95: Optional[float] = None  # 95% Value at Risk
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None


class BaseAsset(ABC):
    """
    Abstract base class for all tradeable assets.

    All asset types (equity, options, crypto, futures) inherit from this.
    """

    def __init__(
        self,
        symbol: str,
        asset_type: AssetType,
        exchange: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base asset.

        Args:
            symbol: Asset symbol/ticker
            asset_type: Type of asset
            exchange: Exchange where asset trades
            metadata: Additional asset metadata
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.exchange = exchange
        self.metadata = metadata or {}

        self._price_history: Optional[pd.DataFrame] = None
        self._current_price: Optional[float] = None
        self._risk_metrics: Optional[RiskMetrics] = None

        logger.debug(f"Asset created: {self}")

    @abstractmethod
    def get_identifier(self) -> str:
        """
        Get unique identifier for this asset.

        Returns:
            Unique string identifier
        """
        pass

    @abstractmethod
    def is_tradeable(self) -> bool:
        """
        Check if asset is currently tradeable.

        Returns:
            True if asset can be traded
        """
        pass

    @abstractmethod
    def get_lot_size(self) -> float:
        """
        Get minimum tradeable lot size.

        Returns:
            Minimum quantity for orders
        """
        pass

    @abstractmethod
    def calculate_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate value of a position.

        Args:
            quantity: Number of units
            price: Price per unit (current price if None)

        Returns:
            Total value
        """
        pass

    def set_price_history(self, price_history: pd.DataFrame) -> None:
        """Set historical price data."""
        self._price_history = price_history

    def get_price_history(self) -> Optional[pd.DataFrame]:
        """Get historical price data."""
        return self._price_history

    def set_current_price(self, price: float) -> None:
        """Set current market price."""
        self._current_price = price

    def get_current_price(self) -> Optional[float]:
        """Get current market price."""
        return self._current_price

    def calculate_returns(self, period: int = 1) -> Optional[pd.Series]:
        """
        Calculate returns over specified period.

        Args:
            period: Number of periods for return calculation

        Returns:
            Series of returns or None if no price history
        """
        if self._price_history is None:
            return None

        if 'close' not in self._price_history.columns:
            return None

        returns = self._price_history['close'].pct_change(period)
        return returns

    def calculate_volatility(self, periods: int = 252) -> Optional[float]:
        """
        Calculate annualized volatility.

        Args:
            periods: Number of periods to use (default 252 for daily data)

        Returns:
            Annualized volatility or None
        """
        returns = self.calculate_returns()
        if returns is None:
            return None

        recent_returns = returns.tail(periods)
        daily_vol = recent_returns.std()

        # Annualize (assuming 252 trading days)
        annual_vol = daily_vol * (252 ** 0.5)

        return annual_vol

    def update_risk_metrics(self) -> None:
        """Update risk metrics based on current data."""
        if self._price_history is None:
            return

        volatility = self.calculate_volatility()
        if volatility is None:
            return

        # Calculate max drawdown
        if 'close' in self._price_history.columns:
            prices = self._price_history['close']
            cumulative = (1 + prices.pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
        else:
            max_drawdown = None

        # Calculate Sharpe (assuming risk-free rate of 2%)
        returns = self.calculate_returns()
        if returns is not None:
            excess_returns = returns.mean() * 252 - 0.02  # Annualized
            sharpe_ratio = excess_returns / volatility if volatility > 0 else None
        else:
            sharpe_ratio = None

        self._risk_metrics = RiskMetrics(
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio
        )

    def get_risk_metrics(self) -> Optional[RiskMetrics]:
        """Get risk metrics (calculate if not available)."""
        if self._risk_metrics is None:
            self.update_risk_metrics()
        return self._risk_metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to dictionary representation."""
        return {
            "symbol": self.symbol,
            "asset_type": self.asset_type.value,
            "exchange": self.exchange,
            "current_price": self._current_price,
            "identifier": self.get_identifier(),
            "tradeable": self.is_tradeable(),
            "lot_size": self.get_lot_size(),
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(symbol='{self.symbol}', type={self.asset_type.value})>"

    def __str__(self) -> str:
        return self.get_identifier()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BaseAsset):
            return False
        return self.get_identifier() == other.get_identifier()

    def __hash__(self) -> int:
        return hash(self.get_identifier())
