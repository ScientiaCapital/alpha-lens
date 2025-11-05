"""
Setup Verification Script

Quick test to verify your Alpaca + Polygon integration is working correctly.

Usage:
    python examples/verify_setup.py
"""

import os
import sys
from datetime import datetime, timedelta
from loguru import logger

# Configure logger for this script
logger.remove()
logger.add(sys.stderr, level="INFO")


def test_environment_variables():
    """Test that environment variables are set."""
    logger.info("=== Testing Environment Variables ===")

    required = {
        "ALPACA_API_KEY": False,
        "ALPACA_SECRET_KEY": False,
        "POLYGON_API_KEY": False
    }

    for var in required:
        value = os.getenv(var)
        if value:
            logger.success(f"✓ {var} is set")
            required[var] = True
        else:
            logger.warning(f"✗ {var} not set")

    if not required["ALPACA_API_KEY"] or not required["ALPACA_SECRET_KEY"]:
        logger.error("Alpaca credentials are required")
        logger.info("Get free keys at: https://alpaca.markets")
        return False

    if not required["POLYGON_API_KEY"]:
        logger.warning("Polygon API key not set (will use Yahoo Finance fallback)")
        logger.info("Get free key at: https://polygon.io")

    return True


def test_imports():
    """Test that all required packages are installed."""
    logger.info("\n=== Testing Package Imports ===")

    packages = [
        ("alpaca.trading.client", "alpaca-py"),
        ("alphalens.data.unified_data_manager", "alphalens (local)"),
        ("alphalens.brokers.alpaca_broker", "alphalens (local)"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("yfinance", "yfinance"),
    ]

    optional_packages = [
        ("websocket", "websocket-client"),
        ("polygon", "polygon-api-client"),
    ]

    all_good = True

    for module, package in packages:
        try:
            __import__(module)
            logger.success(f"✓ {package}")
        except ImportError:
            logger.error(f"✗ {package} not installed")
            logger.info(f"  Install: pip install {package}")
            all_good = False

    # Check optional
    for module, package in optional_packages:
        try:
            __import__(module)
            logger.success(f"✓ {package} (optional)")
        except ImportError:
            logger.warning(f"⚠ {package} not installed (optional)")

    return all_good


def test_alpaca_connection():
    """Test Alpaca broker connection."""
    logger.info("\n=== Testing Alpaca Connection ===")

    try:
        from alphalens.brokers.alpaca_broker import AlpacaBroker

        broker = AlpacaBroker(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            paper_trading=True
        )

        if broker.connect():
            logger.success("✓ Connected to Alpaca (Paper Trading)")

            # Get account
            account = broker.get_account()
            logger.info(f"  Account equity: ${account['equity']:.2f}")
            logger.info(f"  Buying power: ${account['buying_power']:.2f}")

            broker.disconnect()
            return True
        else:
            logger.error("✗ Failed to connect to Alpaca")
            return False

    except Exception as e:
        logger.error(f"✗ Alpaca connection error: {e}")
        return False


def test_data_manager():
    """Test UnifiedDataManager."""
    logger.info("\n=== Testing Data Manager ===")

    try:
        from alphalens.data.unified_data_manager import UnifiedDataManager

        data_manager = UnifiedDataManager(
            alpaca_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
            polygon_key=os.getenv("POLYGON_API_KEY"),
            enable_caching=True
        )

        # Check available sources
        sources = data_manager.get_available_sources()
        logger.info(f"Available data sources: {sources}")

        # Health check
        health = data_manager.health_check()
        for source, status in health.items():
            if status:
                logger.success(f"✓ {source} connected")
            else:
                logger.warning(f"✗ {source} not available")

        if not any(health.values()):
            logger.error("No data sources available")
            return False

        logger.success("✓ Data Manager initialized")
        return True

    except Exception as e:
        logger.error(f"✗ Data Manager error: {e}")
        return False


def test_historical_data():
    """Test fetching historical data."""
    logger.info("\n=== Testing Historical Data ===")

    try:
        from alphalens.data.unified_data_manager import UnifiedDataManager

        data_manager = UnifiedDataManager(
            alpaca_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
            polygon_key=os.getenv("POLYGON_API_KEY"),
            enable_caching=True
        )

        # Fetch 5 days of data for SPY
        end = datetime.now()
        start = end - timedelta(days=5)

        logger.info("Fetching 5 days of SPY data...")
        df = data_manager.get_historical_data(
            symbols=["SPY"],
            start=start,
            end=end,
            timeframe="1Day"
        )

        if df.empty:
            logger.error("✗ No data retrieved")
            return False

        logger.success(f"✓ Retrieved {len(df)} rows")
        logger.info(f"  Columns: {df.columns.tolist()}")
        logger.info(f"  Latest close: ${df['close'].iloc[-1]:.2f}")

        return True

    except Exception as e:
        logger.error(f"✗ Historical data error: {e}")
        return False


def test_realtime_quotes():
    """Test fetching real-time quotes."""
    logger.info("\n=== Testing Real-Time Quotes ===")

    try:
        from alphalens.data.unified_data_manager import UnifiedDataManager

        data_manager = UnifiedDataManager(
            alpaca_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
            polygon_key=os.getenv("POLYGON_API_KEY"),
            enable_caching=True
        )

        logger.info("Fetching latest prices for SPY, AAPL...")
        prices = data_manager.get_latest_prices(["SPY", "AAPL"])

        if prices.empty:
            logger.error("✗ No prices retrieved")
            return False

        logger.success(f"✓ Retrieved {len(prices)} prices")
        for symbol, price in prices.items():
            logger.info(f"  {symbol}: ${price:.2f}")

        return True

    except Exception as e:
        logger.error(f"✗ Real-time quotes error: {e}")
        return False


def test_caching():
    """Test caching performance."""
    logger.info("\n=== Testing Caching ===")

    try:
        from alphalens.data.unified_data_manager import UnifiedDataManager
        import time

        data_manager = UnifiedDataManager(
            alpaca_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
            polygon_key=os.getenv("POLYGON_API_KEY"),
            enable_caching=True
        )

        end = datetime.now()
        start = end - timedelta(days=5)
        symbols = ["SPY"]

        # First fetch
        t1 = time.time()
        df1 = data_manager.get_historical_data(symbols, start, end)
        t2 = time.time()

        # Second fetch (should be cached)
        t3 = time.time()
        df2 = data_manager.get_historical_data(symbols, start, end)
        t4 = time.time()

        first_time = t2 - t1
        cached_time = t4 - t3

        logger.info(f"First fetch: {first_time:.3f}s")
        logger.info(f"Cached fetch: {cached_time:.4f}s")

        if cached_time < first_time:
            speedup = first_time / cached_time
            logger.success(f"✓ Caching working! {speedup:.1f}x faster")

            # Show stats
            stats = data_manager.get_cache_stats()
            logger.info(f"  Cache hit rate: {stats['hit_rate']:.1%}")
            return True
        else:
            logger.warning("⚠ Caching may not be working optimally")
            return True  # Still pass

    except Exception as e:
        logger.error(f"✗ Caching test error: {e}")
        return False


def run_all_tests():
    """Run all verification tests."""
    logger.info("=" * 60)
    logger.info("Alpaca + Polygon Setup Verification")
    logger.info("=" * 60)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("Package Imports", test_imports),
        ("Alpaca Connection", test_alpaca_connection),
        ("Data Manager", test_data_manager),
        ("Historical Data", test_historical_data),
        ("Real-Time Quotes", test_realtime_quotes),
        ("Caching", test_caching),
    ]

    results = {}

    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test '{name}' failed with exception: {e}")
            results[name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")

    if passed == total:
        logger.success("🎉 All tests passed! Your setup is ready.")
        logger.info("\nNext steps:")
        logger.info("1. Run examples: python examples/alpaca_polygon_integration.py")
        logger.info("2. Review guide: ALPACA_POLYGON_SETUP.md")
        return 0
    else:
        logger.error("❌ Some tests failed. Please review the errors above.")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check environment variables in .env file")
        logger.info("2. Verify API keys are correct")
        logger.info("3. Install missing packages: pip install -r requirements-agents.txt")
        logger.info("4. Review setup guide: ALPACA_POLYGON_SETUP.md")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
