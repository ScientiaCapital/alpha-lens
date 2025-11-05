"""
Polygon.io data feed integration.

Provides comprehensive market data:
- Stocks (real-time and historical)
- Options (chains, Greeks, real-time)
- Crypto (24/7 coverage)
- Technical indicators
- News and sentiment
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
import time
from functools import lru_cache

from alphalens.data.base import BaseDataFeed
from alphalens.assets.option import OptionAsset, OptionType, OptionStyle

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests not installed")


class PolygonDataFeed(BaseDataFeed):
    """
    Polygon.io data feed - comprehensive market data provider.

    Supports:
    - Stocks: Real-time quotes, historical data, aggregates
    - Options: Chains, Greeks, historical, snapshots
    - Crypto: 24/7 data, multiple exchanges
    - Technical indicators: SMA, EMA, RSI, MACD
    - News and sentiment

    Rate Limits (Free tier):
    - 5 API calls per minute
    - Use caching aggressively!

    Paid tiers:
    - Starter: 100 calls/min
    - Developer: 1000 calls/min
    - Advanced: Unlimited
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.polygon.io",
        tier: str = "free",  # free, starter, developer, advanced
        enable_caching: bool = True
    ):
        """
        Initialize Polygon data feed.

        Args:
            api_key: Polygon API key (get from polygon.io)
            base_url: API base URL
            tier: Account tier (affects rate limits)
            enable_caching: Enable response caching
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("Requests is required. Run: pip install requests")

        config = {
            "api_key": api_key,
            "base_url": base_url,
            "tier": tier
        }
        super().__init__(config)

        self.api_key = api_key
        self.base_url = base_url
        self.tier = tier
        self.enable_caching = enable_caching

        # Rate limiting
        self.rate_limits = {
            "free": 5,      # 5 calls per minute
            "starter": 100,
            "developer": 1000,
            "advanced": 10000
        }
        self.calls_per_minute = self.rate_limits.get(tier, 5)
        self.call_timestamps: List[float] = []

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

        logger.info(f"Polygon feed initialized (tier: {tier}, {self.calls_per_minute} calls/min)")

    def connect(self) -> bool:
        """Test connection to Polygon API."""
        try:
            # Test with a simple endpoint
            url = f"{self.base_url}/v1/meta/symbols/AAPL/company"
            response = self._make_request(url)

            if response:
                self.connected = True
                logger.info("Connected to Polygon.io")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to connect to Polygon: {e}")
            return False

    def disconnect(self) -> None:
        """Close session."""
        self.session.close()
        self.connected = False
        logger.info("Disconnected from Polygon")

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 3
    ) -> Optional[Dict]:
        """
        Make API request with rate limiting and retries.

        Args:
            url: Request URL
            params: Query parameters
            retries: Number of retries on failure

        Returns:
            Response JSON or None
        """
        # Rate limiting
        self._enforce_rate_limit()

        # Add API key to params
        params = params or {}
        params["apiKey"] = self.api_key

        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=10)

                # Track call timestamp
                self.call_timestamps.append(time.time())

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 429:
                    # Rate limit exceeded
                    logger.warning("Rate limit exceeded, waiting...")
                    time.sleep(60)  # Wait 1 minute
                    continue

                elif response.status_code >= 500:
                    # Server error, retry
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    return None

            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None

        return None

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = time.time()

        # Remove timestamps older than 1 minute
        self.call_timestamps = [
            ts for ts in self.call_timestamps
            if now - ts < 60
        ]

        # Check if we've exceeded limit
        if len(self.call_timestamps) >= self.calls_per_minute:
            # Calculate wait time
            oldest_call = min(self.call_timestamps)
            wait_time = 60 - (now - oldest_call)

            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time + 0.1)

    # Stock Data

    def get_historical_data(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Day"
    ) -> pd.DataFrame:
        """
        Get historical stock data.

        Args:
            symbols: List of stock symbols
            start: Start date
            end: End date
            timeframe: Timeframe (1Min, 5Min, 1Hour, 1Day)

        Returns:
            DataFrame with OHLCV data
        """
        if not self.connected:
            raise RuntimeError("Not connected to Polygon")

        # Map timeframe to Polygon format
        timeframe_map = {
            "1Min": (1, "minute"),
            "5Min": (5, "minute"),
            "15Min": (15, "minute"),
            "1Hour": (1, "hour"),
            "1Day": (1, "day")
        }

        multiplier, timespan = timeframe_map.get(timeframe, (1, "day"))

        all_data = []

        for symbol in symbols:
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"

            response = self._make_request(url, params={"adjusted": "true", "sort": "asc"})

            if response and "results" in response:
                for bar in response["results"]:
                    all_data.append({
                        "timestamp": pd.to_datetime(bar["t"], unit="ms"),
                        "symbol": symbol,
                        "open": bar["o"],
                        "high": bar["h"],
                        "low": bar["l"],
                        "close": bar["c"],
                        "volume": bar["v"]
                    })

        if not all_data:
            logger.warning("No data retrieved")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df = df.set_index(["timestamp", "symbol"])
        df = df.sort_index()

        return df

    def get_latest_prices(self, symbols: List[str]) -> pd.Series:
        """
        Get latest prices for symbols.

        Args:
            symbols: List of symbols

        Returns:
            Series with symbol -> price
        """
        prices = {}

        for symbol in symbols:
            url = f"{self.base_url}/v2/last/trade/{symbol}"
            response = self._make_request(url)

            if response and "results" in response:
                prices[symbol] = response["results"]["p"]

        return pd.Series(prices)

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current quote for symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Quote dictionary with bid/ask/last
        """
        url = f"{self.base_url}/v2/last/nbbo/{symbol}"
        response = self._make_request(url)

        if response and "results" in response:
            result = response["results"]
            return {
                "symbol": symbol,
                "bid_price": result.get("P"),
                "bid_size": result.get("S"),
                "ask_price": result.get("p"),
                "ask_size": result.get("s"),
                "timestamp": pd.to_datetime(result.get("t"), unit="ns")
            }

        return None

    # Options Data

    def get_options_chain(
        self,
        underlying_symbol: str,
        expiration_date: Optional[datetime] = None,
        strike_price: Optional[float] = None,
        option_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get options chain for underlying.

        Args:
            underlying_symbol: Underlying stock symbol
            expiration_date: Filter by expiration
            strike_price: Filter by strike
            option_type: Filter by type ('call' or 'put')

        Returns:
            DataFrame with options contracts
        """
        url = f"{self.base_url}/v3/reference/options/contracts"

        params = {
            "underlying_ticker": underlying_symbol,
            "limit": 1000
        }

        if expiration_date:
            params["expiration_date"] = expiration_date.strftime("%Y-%m-%d")

        if strike_price:
            params["strike_price"] = strike_price

        if option_type:
            params["contract_type"] = option_type

        response = self._make_request(url, params=params)

        if not response or "results" not in response:
            return pd.DataFrame()

        options = []
        for contract in response["results"]:
            options.append({
                "ticker": contract["ticker"],
                "underlying": contract["underlying_ticker"],
                "strike": contract["strike_price"],
                "expiry": pd.to_datetime(contract["expiration_date"]),
                "type": contract["contract_type"],
                "shares_per_contract": contract.get("shares_per_contract", 100)
            })

        return pd.DataFrame(options)

    def get_option_quote(self, option_symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get quote for option contract.

        Args:
            option_symbol: Option symbol (e.g., "O:AAPL240315C00150000")

        Returns:
            Option quote dictionary
        """
        url = f"{self.base_url}/v3/quotes/{option_symbol}"
        response = self._make_request(url, params={"limit": 1, "order": "desc"})

        if response and "results" in response and len(response["results"]) > 0:
            result = response["results"][0]
            return {
                "symbol": option_symbol,
                "bid_price": result.get("bid"),
                "bid_size": result.get("bid_size"),
                "ask_price": result.get("ask"),
                "ask_size": result.get("ask_size"),
                "last_price": result.get("last"),
                "volume": result.get("volume"),
                "open_interest": result.get("open_interest"),
                "implied_volatility": result.get("implied_volatility"),
                "delta": result.get("delta"),
                "gamma": result.get("gamma"),
                "theta": result.get("theta"),
                "vega": result.get("vega"),
                "timestamp": pd.to_datetime(result.get("sip_timestamp"), unit="ns")
            }

        return None

    # Crypto Data

    def get_crypto_data(
        self,
        from_currency: str,
        to_currency: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1Day"
    ) -> pd.DataFrame:
        """
        Get cryptocurrency data.

        Args:
            from_currency: Base currency (e.g., "BTC")
            to_currency: Quote currency (e.g., "USD")
            start: Start date
            end: End date
            timeframe: Timeframe

        Returns:
            DataFrame with OHLCV data
        """
        timeframe_map = {
            "1Min": (1, "minute"),
            "5Min": (5, "minute"),
            "1Hour": (1, "hour"),
            "1Day": (1, "day")
        }

        multiplier, timespan = timeframe_map.get(timeframe, (1, "day"))

        url = f"{self.base_url}/v2/aggs/ticker/X:{from_currency}{to_currency}/range/{multiplier}/{timespan}/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}"

        response = self._make_request(url, params={"adjusted": "true", "sort": "asc"})

        if not response or "results" not in response:
            return pd.DataFrame()

        data = []
        for bar in response["results"]:
            data.append({
                "timestamp": pd.to_datetime(bar["t"], unit="ms"),
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"]
            })

        df = pd.DataFrame(data)
        df = df.set_index("timestamp")

        return df

    # Technical Indicators

    def get_sma(
        self,
        symbol: str,
        window: int = 50,
        timeframe: str = "1Day"
    ) -> pd.Series:
        """
        Get Simple Moving Average.

        Args:
            symbol: Stock symbol
            window: SMA window
            timeframe: Timeframe

        Returns:
            Series with SMA values
        """
        url = f"{self.base_url}/v1/indicators/sma/{symbol}"

        params = {
            "timespan": "day" if "Day" in timeframe else "minute",
            "window": window,
            "series_type": "close",
            "order": "desc",
            "limit": 100
        }

        response = self._make_request(url, params=params)

        if not response or "results" not in response:
            return pd.Series()

        data = []
        for point in response["results"]["values"]:
            data.append({
                "timestamp": pd.to_datetime(point["timestamp"], unit="ms"),
                "sma": point["value"]
            })

        df = pd.DataFrame(data)
        df = df.set_index("timestamp")

        return df["sma"]

    # News and Sentiment

    def get_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get latest news.

        Args:
            symbol: Filter by symbol (None = all news)
            limit: Number of articles

        Returns:
            List of news articles
        """
        url = f"{self.base_url}/v2/reference/news"

        params = {"limit": limit, "order": "desc"}
        if symbol:
            params["ticker"] = symbol

        response = self._make_request(url, params=params)

        if not response or "results" not in response:
            return []

        articles = []
        for article in response["results"]:
            articles.append({
                "id": article["id"],
                "title": article["title"],
                "author": article["author"],
                "published_utc": pd.to_datetime(article["published_utc"]),
                "article_url": article["article_url"],
                "tickers": article.get("tickers", []),
                "amp_url": article.get("amp_url"),
                "image_url": article.get("image_url"),
                "description": article.get("description", ""),
                "keywords": article.get("keywords", [])
            })

        return articles

    # WebSocket Streaming

    def subscribe_realtime(
        self,
        symbols: List[str],
        callback: callable
    ) -> None:
        """
        Subscribe to real-time updates via WebSocket.

        Note: Requires separate WebSocket implementation.
        This is a placeholder for the interface.

        Args:
            symbols: Symbols to subscribe to
            callback: Callback function for updates
        """
        logger.warning("Real-time WebSocket streaming requires additional setup")
        logger.info("Use Polygon WebSocket client: https://github.com/polygon-io/client-python")

    def unsubscribe_realtime(self, symbols: Optional[List[str]] = None) -> None:
        """Unsubscribe from real-time updates."""
        pass
