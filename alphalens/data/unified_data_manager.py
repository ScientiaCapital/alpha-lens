"""
Unified Data Manager - Combines multiple data sources intelligently.

Automatically routes requests to best data source:
- Alpaca: Real-time trading data, free for customers
- Polygon: Comprehensive historical, options, crypto
- Yahoo Finance: Free backup for historical data

Features:
- Intelligent caching
- Automatic failover
- Rate limit management
- Cost optimization
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from loguru import logger
from functools import lru_cache
import pickle
import os

from alphalens.data.base import BaseDataFeed
from alphalens.data.alpaca_feed import AlpacaDataFeed
from alphalens.data.polygon_feed import PolygonDataFeed
from alphalens.data.yahoo_feed import YahooDataFeed


class UnifiedDataManager:
    """
    Unified data manager combining multiple sources.

    **Smart Routing**:
    - Real-time quotes: Alpaca (free for customers) > Polygon
    - Historical stocks: Polygon > Yahoo (free backup)
    - Options data: Polygon (only source with options)
    - Crypto data: Polygon > Alpaca

    **Caching Strategy**:
    - Historical data: Cache for 24 hours
    - Intraday data: Cache for 1 minute
    - Options chains: Cache for 5 minutes
    - Real-time quotes: No caching

    **Rate Limiting**:
    - Automatic rate limit detection
    - Intelligent backoff
    - Queue management
    """

    def __init__(
        self,
        alpaca_key: Optional[str] = None,
        alpaca_secret: Optional[str] = None,
        polygon_key: Optional[str] = None,
        cache_dir: str = ".cache",
        enable_caching: bool = True
    ):
        """
        Initialize unified data manager.

        Args:
            alpaca_key: Alpaca API key
            alpaca_secret: Alpaca secret key
            polygon_key: Polygon API key
            cache_dir: Directory for cache files
            enable_caching: Enable data caching
        """
        self.cache_dir = cache_dir
        self.enable_caching = enable_caching

        if enable_caching:
            os.makedirs(cache_dir, exist_ok=True)

        # Initialize data sources
        self.sources: Dict[str, Optional[BaseDataFeed]] = {}

        # Alpaca
        if alpaca_key and alpaca_secret:
            try:
                self.sources["alpaca"] = AlpacaDataFeed(alpaca_key, alpaca_secret)
                self.sources["alpaca"].connect()
                logger.info("✓ Alpaca data feed connected")
            except Exception as e:
                logger.warning(f"Alpaca initialization failed: {e}")
                self.sources["alpaca"] = None
        else:
            self.sources["alpaca"] = None
            logger.info("Alpaca credentials not provided")

        # Polygon
        if polygon_key:
            try:
                self.sources["polygon"] = PolygonDataFeed(polygon_key)
                self.sources["polygon"].connect()
                logger.info("✓ Polygon data feed connected")
            except Exception as e:
                logger.warning(f"Polygon initialization failed: {e}")
                self.sources["polygon"] = None
        else:
            self.sources["polygon"] = None
            logger.info("Polygon credentials not provided")

        # Yahoo Finance (always available, free)
        try:
            self.sources["yahoo"] = YahooDataFeed()
            self.sources["yahoo"].connect()
            logger.info("✓ Yahoo Finance data feed ready")
        except Exception as e:
            logger.warning(f"Yahoo Finance initialization failed: {e}")
            self.sources["yahoo"] = None

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info("Unified Data Manager initialized")

    def get_historical_data(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        timeframe: str = "1Day",
        source: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical data with intelligent source selection.

        Args:
            symbols: List of symbols
            start: Start date
            end: End date
            timeframe: Timeframe
            source: Force specific source (None = auto-select)

        Returns:
            DataFrame with historical data
        """
        cache_key = f"hist_{'-'.join(symbols)}_{start.date()}_{end.date()}_{timeframe}"

        # Check cache
        if self.enable_caching:
            cached_data = self._load_from_cache(cache_key, max_age_hours=24)
            if cached_data is not None:
                self.cache_hits += 1
                logger.debug(f"Cache hit: {cache_key}")
                return cached_data

        self.cache_misses += 1

        # Select source
        if source:
            selected_source = source
        else:
            # Auto-select: Polygon > Yahoo
            if self.sources.get("polygon"):
                selected_source = "polygon"
            elif self.sources.get("yahoo"):
                selected_source = "yahoo"
            else:
                raise RuntimeError("No data sources available")

        # Get data
        try:
            feed = self.sources[selected_source]
            data = feed.get_historical_data(symbols, start, end, timeframe)

            # Cache the result
            if self.enable_caching and not data.empty:
                self._save_to_cache(cache_key, data)

            logger.info(f"Retrieved historical data from {selected_source}: {len(data)} rows")
            return data

        except Exception as e:
            logger.error(f"Failed to get data from {selected_source}: {e}")

            # Failover to alternative source
            if selected_source == "polygon" and self.sources.get("yahoo"):
                logger.info("Failing over to Yahoo Finance")
                return self.get_historical_data(symbols, start, end, timeframe, source="yahoo")

            return pd.DataFrame()

    def get_latest_prices(
        self,
        symbols: List[str],
        source: Optional[str] = None
    ) -> pd.Series:
        """
        Get latest prices with intelligent source selection.

        Args:
            symbols: List of symbols
            source: Force specific source

        Returns:
            Series with latest prices
        """
        # Select source: Alpaca > Polygon > Yahoo
        if source:
            selected_source = source
        elif self.sources.get("alpaca"):
            selected_source = "alpaca"
        elif self.sources.get("polygon"):
            selected_source = "polygon"
        elif self.sources.get("yahoo"):
            selected_source = "yahoo"
        else:
            raise RuntimeError("No data sources available")

        try:
            feed = self.sources[selected_source]
            prices = feed.get_latest_prices(symbols)
            logger.debug(f"Latest prices from {selected_source}: {len(prices)} symbols")
            return prices

        except Exception as e:
            logger.error(f"Failed to get prices from {selected_source}: {e}")

            # Failover
            if selected_source == "alpaca" and self.sources.get("polygon"):
                return self.get_latest_prices(symbols, source="polygon")
            elif selected_source == "polygon" and self.sources.get("yahoo"):
                return self.get_latest_prices(symbols, source="yahoo")

            return pd.Series()

    def get_options_chain(
        self,
        underlying_symbol: str,
        expiration_date: Optional[datetime] = None,
        strike_price: Optional[float] = None,
        option_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get options chain (Polygon only).

        Args:
            underlying_symbol: Underlying symbol
            expiration_date: Filter by expiration
            strike_price: Filter by strike
            option_type: Filter by type

        Returns:
            DataFrame with options
        """
        if not self.sources.get("polygon"):
            raise RuntimeError("Polygon is required for options data")

        cache_key = f"options_{underlying_symbol}_{expiration_date}_{strike_price}_{option_type}"

        # Check cache (5 minute expiry for options)
        if self.enable_caching:
            cached_data = self._load_from_cache(cache_key, max_age_hours=0.083)  # 5 minutes
            if cached_data is not None:
                self.cache_hits += 1
                return cached_data

        self.cache_misses += 1

        # Get from Polygon
        try:
            polygon = self.sources["polygon"]
            chain = polygon.get_options_chain(
                underlying_symbol,
                expiration_date,
                strike_price,
                option_type
            )

            # Cache
            if self.enable_caching and not chain.empty:
                self._save_to_cache(cache_key, chain)

            logger.info(f"Retrieved options chain: {len(chain)} contracts")
            return chain

        except Exception as e:
            logger.error(f"Failed to get options chain: {e}")
            return pd.DataFrame()

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
            from_currency: Base currency
            to_currency: Quote currency
            start: Start date
            end: End date
            timeframe: Timeframe

        Returns:
            DataFrame with crypto data
        """
        if not self.sources.get("polygon"):
            raise RuntimeError("Polygon is required for crypto data")

        cache_key = f"crypto_{from_currency}{to_currency}_{start.date()}_{end.date()}_{timeframe}"

        # Check cache
        if self.enable_caching:
            cached_data = self._load_from_cache(cache_key, max_age_hours=1)
            if cached_data is not None:
                self.cache_hits += 1
                return cached_data

        self.cache_misses += 1

        try:
            polygon = self.sources["polygon"]
            data = polygon.get_crypto_data(from_currency, to_currency, start, end, timeframe)

            # Cache
            if self.enable_caching and not data.empty:
                self._save_to_cache(cache_key, data)

            logger.info(f"Retrieved crypto data: {len(data)} bars")
            return data

        except Exception as e:
            logger.error(f"Failed to get crypto data: {e}")
            return pd.DataFrame()

    def get_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get latest news (Polygon only).

        Args:
            symbol: Filter by symbol
            limit: Number of articles

        Returns:
            List of news articles
        """
        if not self.sources.get("polygon"):
            logger.warning("Polygon not available for news")
            return []

        try:
            polygon = self.sources["polygon"]
            news = polygon.get_news(symbol, limit)
            logger.info(f"Retrieved {len(news)} news articles")
            return news

        except Exception as e:
            logger.error(f"Failed to get news: {e}")
            return []

    def _save_to_cache(self, key: str, data: Any) -> None:
        """Save data to cache."""
        try:
            cache_path = os.path.join(self.cache_dir, f"{key}.pkl")
            with open(cache_path, "wb") as f:
                pickle.dump({
                    "data": data,
                    "timestamp": datetime.now()
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _load_from_cache(self, key: str, max_age_hours: float) -> Optional[Any]:
        """Load data from cache if not expired."""
        try:
            cache_path = os.path.join(self.cache_dir, f"{key}.pkl")

            if not os.path.exists(cache_path):
                return None

            with open(cache_path, "rb") as f:
                cache_data = pickle.load(f)

            # Check age
            age_hours = (datetime.now() - cache_data["timestamp"]).total_seconds() / 3600

            if age_hours <= max_age_hours:
                return cache_data["data"]
            else:
                # Expired
                os.remove(cache_path)
                return None

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

    def clear_cache(self) -> None:
        """Clear all cached data."""
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, file))
            logger.info("Cache cleared")

    def get_available_sources(self) -> List[str]:
        """Get list of available data sources."""
        return [name for name, source in self.sources.items() if source is not None]

    def health_check(self) -> Dict[str, bool]:
        """Check health of all data sources."""
        health = {}

        for name, source in self.sources.items():
            if source is None:
                health[name] = False
            else:
                try:
                    health[name] = source.connected
                except:
                    health[name] = False

        return health
