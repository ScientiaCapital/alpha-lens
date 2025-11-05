"""
Alpaca data feed integration.
"""

from typing import List, Optional, Callable
from datetime import datetime
import pandas as pd
from loguru import logger

from alphalens.data.base import BaseDataFeed

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.live import StockDataStream
    from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class AlpacaDataFeed(BaseDataFeed):
    """Alpaca data feed."""

    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Alpaca data feed.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
        """
        if not ALPACA_AVAILABLE:
            raise ImportError("Alpaca SDK not installed. Run: pip install alpaca-py")

        config = {"api_key": api_key, "api_secret": api_secret}
        super().__init__(config)

        self.historical_client = None
        self.stream_client = None

    def connect(self) -> bool:
        """Connect to Alpaca data API."""
        try:
            self.historical_client = StockHistoricalDataClient(
                api_key=self.config["api_key"],
                secret_key=self.config["api_secret"]
            )

            self.stream_client = StockDataStream(
                api_key=self.config["api_key"],
                secret_key=self.config["api_secret"]
            )

            self.connected = True
            logger.info("Connected to Alpaca data feed")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Alpaca."""
        if self.stream_client:
            self.stream_client.stop()
        self.connected = False
        logger.info("Disconnected from Alpaca data feed")

    def get_historical_data(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Day"
    ) -> pd.DataFrame:
        """Get historical data from Alpaca."""
        if not self.connected:
            raise RuntimeError("Not connected to data feed")

        # Map timeframe
        tf_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, "Min"),
            "1Hour": TimeFrame.Hour,
            "1Day": TimeFrame.Day
        }
        tf = tf_map.get(timeframe, TimeFrame.Day)

        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=tf,
            start=start,
            end=end
        )

        bars = self.historical_client.get_stock_bars(request)
        df = bars.df

        return df

    def get_latest_prices(self, symbols: List[str]) -> pd.Series:
        """Get latest prices."""
        if not self.connected:
            raise RuntimeError("Not connected to data feed")

        request = StockLatestQuoteRequest(symbol_or_symbols=symbols)
        quotes = self.historical_client.get_stock_latest_quote(request)

        prices = {}
        for symbol, quote in quotes.items():
            # Use mid price
            prices[symbol] = (quote.bid_price + quote.ask_price) / 2

        return pd.Series(prices)

    def subscribe_realtime(
        self,
        symbols: List[str],
        callback: Callable[[dict], None]
    ) -> None:
        """Subscribe to real-time updates."""
        if not self.connected:
            raise RuntimeError("Not connected to data feed")

        async def handle_bar(bar):
            callback({
                "symbol": bar.symbol,
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            })

        self.stream_client.subscribe_bars(handle_bar, *symbols)
        self.stream_client.run()

    def unsubscribe_realtime(self, symbols: Optional[List[str]] = None) -> None:
        """Unsubscribe from real-time data."""
        if self.stream_client:
            self.stream_client.stop()
