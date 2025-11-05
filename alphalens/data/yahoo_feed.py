"""
Yahoo Finance data feed (free historical data).
"""

from typing import List, Optional, Callable
from datetime import datetime
import pandas as pd
from loguru import logger

from alphalens.data.base import BaseDataFeed

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class YahooDataFeed(BaseDataFeed):
    """Yahoo Finance data feed (historical data only)."""

    def __init__(self):
        """Initialize Yahoo Finance data feed."""
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance not installed. Run: pip install yfinance")

        super().__init__({})

    def connect(self) -> bool:
        """Connect (no-op for Yahoo Finance)."""
        self.connected = True
        logger.info("Yahoo Finance data feed ready")
        return True

    def disconnect(self) -> None:
        """Disconnect (no-op)."""
        self.connected = False

    def get_historical_data(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Day"
    ) -> pd.DataFrame:
        """Get historical data from Yahoo Finance."""
        if not self.connected:
            raise RuntimeError("Not connected to data feed")

        # Map timeframe to yfinance interval
        interval_map = {
            "1Min": "1m",
            "5Min": "5m",
            "1Hour": "1h",
            "1Day": "1d"
        }
        interval = interval_map.get(timeframe, "1d")

        # Download data for all symbols
        data = yf.download(
            tickers=symbols,
            start=start,
            end=end,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            progress=False
        )

        # Reshape to MultiIndex format (timestamp, symbol)
        if len(symbols) == 1:
            # Single symbol - add symbol level
            data = data.stack().swaplevel()
            data.index.names = ['timestamp', 'symbol']
        else:
            # Multiple symbols - already has proper structure
            data = data.stack(level=0).swaplevel()
            data.index.names = ['timestamp', 'symbol']

        return data

    def get_latest_prices(self, symbols: List[str]) -> pd.Series:
        """Get latest prices."""
        if not self.connected:
            raise RuntimeError("Not connected to data feed")

        prices = {}
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            prices[symbol] = info.get('regularMarketPrice', info.get('previousClose', 0))

        return pd.Series(prices)

    def subscribe_realtime(
        self,
        symbols: List[str],
        callback: Callable[[dict], None]
    ) -> None:
        """Not supported for Yahoo Finance."""
        raise NotImplementedError("Real-time data not available from Yahoo Finance")

    def unsubscribe_realtime(self, symbols: Optional[List[str]] = None) -> None:
        """Not supported for Yahoo Finance."""
        pass
