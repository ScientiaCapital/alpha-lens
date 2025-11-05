"""
Base data feed interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable
from datetime import datetime
import pandas as pd
from loguru import logger


class BaseDataFeed(ABC):
    """
    Abstract base class for data feeds.
    """

    def __init__(self, config: dict):
        """
        Initialize data feed.

        Args:
            config: Data feed configuration
        """
        self.config = config
        self.connected = False
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def connect(self) -> bool:
        """Connect to data source."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from data source."""
        pass

    @abstractmethod
    def get_historical_data(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Day"
    ) -> pd.DataFrame:
        """
        Get historical data.

        Args:
            symbols: List of symbols
            start: Start datetime
            end: End datetime
            timeframe: Data timeframe

        Returns:
            DataFrame with MultiIndex (timestamp, symbol)
        """
        pass

    @abstractmethod
    def get_latest_prices(self, symbols: List[str]) -> pd.Series:
        """
        Get latest prices for symbols.

        Args:
            symbols: List of symbols

        Returns:
            Series with symbol as index, price as value
        """
        pass

    @abstractmethod
    def subscribe_realtime(
        self,
        symbols: List[str],
        callback: Callable[[dict], None]
    ) -> None:
        """
        Subscribe to real-time data updates.

        Args:
            symbols: List of symbols to subscribe to
            callback: Function to call with each update
        """
        pass

    @abstractmethod
    def unsubscribe_realtime(self, symbols: Optional[List[str]] = None) -> None:
        """
        Unsubscribe from real-time data.

        Args:
            symbols: Symbols to unsubscribe (None = all)
        """
        pass
