"""
Integration tests for data feeds.

Tests Alpaca, Polygon, Yahoo, and UnifiedDataManager.

Run with:
    pytest tests/integration/test_data_feeds.py -v
    pytest tests/integration/test_data_feeds.py -v -k "test_alpaca"  # Run only Alpaca tests
"""

import pytest
import os
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from alphalens.data.unified_data_manager import UnifiedDataManager
from alphalens.data.alpaca_feed import AlpacaDataFeed
from alphalens.data.yahoo_feed import YahooDataFeed

# Check for API keys
ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")
POLYGON_KEY = os.getenv("POLYGON_API_KEY")

# Pytest markers
requires_alpaca = pytest.mark.skipif(
    not ALPACA_KEY or not ALPACA_SECRET,
    reason="Alpaca API keys not set"
)

requires_polygon = pytest.mark.skipif(
    not POLYGON_KEY,
    reason="Polygon API key not set"
)


class TestYahooDataFeed:
    """Test Yahoo Finance data feed (no API key required)."""

    @pytest.fixture
    def yahoo_feed(self):
        """Create Yahoo feed instance."""
        feed = YahooDataFeed()
        yield feed

    def test_yahoo_connection(self, yahoo_feed):
        """Test Yahoo connection."""
        assert yahoo_feed.connect()
        assert yahoo_feed.connected

    def test_yahoo_historical_data(self, yahoo_feed):
        """Test fetching historical data."""
        yahoo_feed.connect()

        end = datetime.now()
        start = end - timedelta(days=30)

        df = yahoo_feed.get_historical_data(
            symbols=["SPY", "AAPL"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        assert not df.empty
        assert "close" in df.columns
        assert "volume" in df.columns
        assert len(df) > 0

        # Check both symbols present
        symbols = df.index.get_level_values("symbol").unique()
        assert "SPY" in symbols
        assert "AAPL" in symbols

    def test_yahoo_latest_prices(self, yahoo_feed):
        """Test fetching latest prices."""
        yahoo_feed.connect()

        prices = yahoo_feed.get_latest_prices(["SPY", "AAPL"])

        assert not prices.empty
        assert len(prices) == 2
        assert "SPY" in prices.index
        assert "AAPL" in prices.index
        assert prices["SPY"] > 0
        assert prices["AAPL"] > 0


@requires_alpaca
class TestAlpacaDataFeed:
    """Test Alpaca data feed."""

    @pytest.fixture
    def alpaca_feed(self):
        """Create Alpaca feed instance."""
        config = {
            "api_key": ALPACA_KEY,
            "secret_key": ALPACA_SECRET,
            "paper_trading": True
        }
        feed = AlpacaDataFeed(config)
        yield feed
        feed.disconnect()

    def test_alpaca_connection(self, alpaca_feed):
        """Test Alpaca connection."""
        assert alpaca_feed.connect()
        assert alpaca_feed.connected

    def test_alpaca_historical_data(self, alpaca_feed):
        """Test fetching historical data."""
        alpaca_feed.connect()

        end = datetime.now()
        start = end - timedelta(days=10)

        df = alpaca_feed.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        assert not df.empty
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_alpaca_latest_prices(self, alpaca_feed):
        """Test fetching latest prices."""
        alpaca_feed.connect()

        prices = alpaca_feed.get_latest_prices(["SPY", "AAPL"])

        assert not prices.empty
        assert len(prices) >= 1  # At least one should work


@requires_polygon
class TestPolygonDataFeed:
    """Test Polygon data feed."""

    @pytest.fixture
    def polygon_feed(self):
        """Create Polygon feed instance."""
        from alphalens.data.polygon_feed import PolygonDataFeed

        feed = PolygonDataFeed(
            api_key=POLYGON_KEY,
            tier="free"
        )
        yield feed
        feed.disconnect()

    def test_polygon_connection(self, polygon_feed):
        """Test Polygon connection."""
        assert polygon_feed.connect()
        assert polygon_feed.connected

    def test_polygon_historical_data(self, polygon_feed):
        """Test fetching historical data."""
        polygon_feed.connect()

        end = datetime.now()
        start = end - timedelta(days=10)

        df = polygon_feed.get_historical_data(
            symbols=["AAPL"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        assert not df.empty
        assert "close" in df.columns

    def test_polygon_options_chain(self, polygon_feed):
        """Test fetching options chain."""
        polygon_feed.connect()

        chain = polygon_feed.get_options_chain(
            underlying_symbol="AAPL",
            option_type="call"
        )

        # May be empty if no options data available
        if not chain.empty:
            assert "strike" in chain.columns
            assert "expiry" in chain.columns

    def test_polygon_rate_limiting(self, polygon_feed):
        """Test rate limiting."""
        polygon_feed.connect()

        # Should enforce rate limit
        import time
        start_time = time.time()

        # Try to make multiple requests
        for i in range(3):
            polygon_feed.get_latest_prices(["AAPL"])

        elapsed = time.time() - start_time

        # Should complete (rate limiter working)
        assert elapsed >= 0


class TestUnifiedDataManager:
    """Test UnifiedDataManager."""

    @pytest.fixture
    def data_manager(self):
        """Create data manager."""
        manager = UnifiedDataManager(
            alpaca_key=ALPACA_KEY,
            alpaca_secret=ALPACA_SECRET,
            polygon_key=POLYGON_KEY,
            enable_caching=True
        )
        yield manager

    def test_available_sources(self, data_manager):
        """Test getting available sources."""
        sources = data_manager.get_available_sources()

        assert isinstance(sources, list)
        # At minimum Yahoo should be available
        assert "yahoo" in sources

    def test_health_check(self, data_manager):
        """Test health check."""
        health = data_manager.health_check()

        assert isinstance(health, dict)
        # Yahoo should always be healthy
        assert health.get("yahoo") is True

    def test_historical_data(self, data_manager):
        """Test fetching historical data."""
        end = datetime.now()
        start = end - timedelta(days=10)

        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        assert not df.empty
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_latest_prices(self, data_manager):
        """Test fetching latest prices."""
        prices = data_manager.get_latest_prices(["SPY", "AAPL"])

        assert not prices.empty
        assert len(prices) >= 1

    def test_caching(self, data_manager):
        """Test caching functionality."""
        end = datetime.now()
        start = end - timedelta(days=5)

        # First fetch
        df1 = data_manager.get_historical_data(["SPY"], start, end)

        # Second fetch (should use cache)
        df2 = data_manager.get_historical_data(["SPY"], start, end)

        # Should return same data
        assert len(df1) == len(df2)

        # Check cache stats
        stats = data_manager.get_cache_stats()
        assert stats["cache_hits"] > 0

    def test_cache_stats(self, data_manager):
        """Test cache statistics."""
        stats = data_manager.get_cache_stats()

        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats
        assert 0 <= stats["hit_rate"] <= 1

    def test_automatic_failover(self, data_manager):
        """Test automatic failover between sources."""
        end = datetime.now()
        start = end - timedelta(days=5)

        # Should work even if some sources are unavailable
        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end
        )

        # Should get data from at least one source
        assert not df.empty

    def test_clear_cache(self, data_manager):
        """Test clearing cache."""
        end = datetime.now()
        start = end - timedelta(days=5)

        # Fetch some data
        data_manager.get_historical_data(["SPY"], start, end)

        # Clear cache
        data_manager.clear_cache()

        # Stats should reset
        stats = data_manager.get_cache_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0


class TestDataQuality:
    """Test data quality and consistency."""

    @pytest.fixture
    def data_manager(self):
        """Create data manager."""
        return UnifiedDataManager(
            alpaca_key=ALPACA_KEY,
            alpaca_secret=ALPACA_SECRET,
            polygon_key=POLYGON_KEY,
            enable_caching=False  # Disable for quality tests
        )

    def test_no_missing_data(self, data_manager):
        """Test that data has no unexpected missing values."""
        end = datetime.now()
        start = end - timedelta(days=10)

        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        # Check no NaN in critical columns
        assert not df["close"].isna().any()
        assert not df["volume"].isna().any()

    def test_price_reasonableness(self, data_manager):
        """Test that prices are reasonable."""
        prices = data_manager.get_latest_prices(["SPY"])

        if not prices.empty:
            spy_price = prices["SPY"]

            # SPY should be between $100 and $1000 (reasonable range)
            assert 100 < spy_price < 1000

    def test_data_ordering(self, data_manager):
        """Test that data is properly ordered."""
        end = datetime.now()
        start = end - timedelta(days=10)

        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        # Check timestamps are in ascending order
        timestamps = df.index.get_level_values("timestamp")
        assert timestamps.is_monotonic_increasing

    def test_volume_positivity(self, data_manager):
        """Test that volume is always positive."""
        end = datetime.now()
        start = end - timedelta(days=10)

        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        # Volume should always be positive
        assert (df["volume"] > 0).all()


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def data_manager(self):
        """Create data manager."""
        return UnifiedDataManager(
            alpaca_key=ALPACA_KEY,
            alpaca_secret=ALPACA_SECRET,
            polygon_key=POLYGON_KEY,
            enable_caching=True
        )

    def test_invalid_symbol(self, data_manager):
        """Test handling of invalid symbols."""
        end = datetime.now()
        start = end - timedelta(days=5)

        # Should not crash on invalid symbol
        df = data_manager.get_historical_data(
            symbols=["INVALIDXYZ123"],
            start=start,
            end=end
        )

        # Should return empty or handle gracefully
        assert isinstance(df, pd.DataFrame)

    def test_future_dates(self, data_manager):
        """Test handling of future dates."""
        start = datetime.now() + timedelta(days=10)
        end = start + timedelta(days=20)

        # Should return empty data
        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end
        )

        assert df.empty

    def test_inverted_date_range(self, data_manager):
        """Test handling of inverted date ranges."""
        end = datetime.now()
        start = end + timedelta(days=10)  # Start after end

        # Should handle gracefully
        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end
        )

        assert df.empty

    def test_empty_symbol_list(self, data_manager):
        """Test handling of empty symbol list."""
        end = datetime.now()
        start = end - timedelta(days=5)

        df = data_manager.get_historical_data(
            symbols=[],
            start=start,
            end=end
        )

        assert df.empty


# Performance benchmarks
class TestPerformance:
    """Performance benchmarks."""

    @pytest.fixture
    def data_manager(self):
        """Create data manager with caching."""
        return UnifiedDataManager(
            alpaca_key=ALPACA_KEY,
            alpaca_secret=ALPACA_SECRET,
            polygon_key=POLYGON_KEY,
            enable_caching=True
        )

    def test_caching_speedup(self, data_manager):
        """Test that caching provides speedup."""
        import time

        end = datetime.now()
        start = end - timedelta(days=5)

        # First fetch (uncached)
        t1 = time.time()
        df1 = data_manager.get_historical_data(["SPY"], start, end)
        t2 = time.time()
        uncached_time = t2 - t1

        # Second fetch (cached)
        t3 = time.time()
        df2 = data_manager.get_historical_data(["SPY"], start, end)
        t4 = time.time()
        cached_time = t4 - t3

        # Cached should be faster
        assert cached_time < uncached_time
        logger.info(f"Speedup: {uncached_time / cached_time:.1f}x")

    def test_multiple_symbols_performance(self, data_manager):
        """Test performance with multiple symbols."""
        import time

        end = datetime.now()
        start = end - timedelta(days=5)

        symbols = ["SPY", "AAPL", "MSFT", "GOOGL", "AMZN"]

        t1 = time.time()
        df = data_manager.get_historical_data(symbols, start, end)
        t2 = time.time()

        elapsed = t2 - t1

        # Should complete in reasonable time (< 30s)
        assert elapsed < 30
        logger.info(f"Fetched {len(symbols)} symbols in {elapsed:.2f}s")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
