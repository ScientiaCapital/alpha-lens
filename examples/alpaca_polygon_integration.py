"""
Complete Alpaca + Polygon Integration Example

This example demonstrates:
1. Setting up UnifiedDataManager with Alpaca and Polygon
2. Fetching historical data from Polygon (with Yahoo as fallback)
3. Getting real-time quotes
4. Retrieving options chains
5. Placing paper trades via Alpaca
6. Complete end-to-end workflow
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from alphalens.data.unified_data_manager import UnifiedDataManager
from alphalens.brokers.alpaca_broker import AlpacaBroker
from alphalens.assets.equity import EquityAsset
from alphalens.assets.option import OptionAsset, OptionType


def setup_credentials():
    """
    Set up API credentials from environment variables.

    Required environment variables:
    - ALPACA_API_KEY: Alpaca API key
    - ALPACA_SECRET_KEY: Alpaca secret key
    - POLYGON_API_KEY: Polygon.io API key (optional, but recommended)
    """
    alpaca_key = os.getenv("ALPACA_API_KEY")
    alpaca_secret = os.getenv("ALPACA_SECRET_KEY")
    polygon_key = os.getenv("POLYGON_API_KEY")

    if not alpaca_key or not alpaca_secret:
        logger.warning("Alpaca credentials not found in environment")
        logger.info("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")

    if not polygon_key:
        logger.warning("Polygon API key not found - will fall back to Yahoo Finance")
        logger.info("Get a free key at https://polygon.io/")

    return alpaca_key, alpaca_secret, polygon_key


def example_1_basic_setup():
    """Example 1: Basic setup and connection testing."""
    logger.info("=== Example 1: Basic Setup ===")

    alpaca_key, alpaca_secret, polygon_key = setup_credentials()

    # Initialize unified data manager
    data_manager = UnifiedDataManager(
        alpaca_key=alpaca_key,
        alpaca_secret=alpaca_secret,
        polygon_key=polygon_key,
        enable_caching=True
    )

    # Check available sources
    available = data_manager.get_available_sources()
    logger.info(f"Available data sources: {available}")

    # Health check
    health = data_manager.health_check()
    logger.info(f"Health status: {health}")

    return data_manager


def example_2_historical_data(data_manager: UnifiedDataManager):
    """Example 2: Fetch historical stock data."""
    logger.info("\n=== Example 2: Historical Data ===")

    # Fetch 3 months of daily data for tech stocks
    symbols = ["AAPL", "MSFT", "GOOGL"]
    end = datetime.now()
    start = end - timedelta(days=90)

    logger.info(f"Fetching historical data for {symbols}")
    df = data_manager.get_historical_data(
        symbols=symbols,
        start=start,
        end=end,
        timeframe="1Day"
    )

    if not df.empty:
        logger.info(f"Retrieved {len(df)} rows")
        logger.info(f"\nLast 5 days:\n{df.tail()}")

        # Calculate simple statistics
        for symbol in symbols:
            try:
                symbol_data = df.xs(symbol, level='symbol')
                avg_close = symbol_data['close'].mean()
                latest_close = symbol_data['close'].iloc[-1]
                logger.info(f"{symbol}: Latest=${latest_close:.2f}, Avg=${avg_close:.2f}")
            except Exception as e:
                logger.warning(f"Could not process {symbol}: {e}")
    else:
        logger.warning("No data retrieved")

    return df


def example_3_realtime_quotes(data_manager: UnifiedDataManager):
    """Example 3: Get real-time quotes."""
    logger.info("\n=== Example 3: Real-Time Quotes ===")

    symbols = ["AAPL", "TSLA", "SPY"]

    logger.info(f"Fetching latest prices for {symbols}")
    prices = data_manager.get_latest_prices(symbols)

    if not prices.empty:
        logger.info("Latest prices:")
        for symbol, price in prices.items():
            logger.info(f"  {symbol}: ${price:.2f}")
    else:
        logger.warning("No prices retrieved")

    return prices


def example_4_options_chain(data_manager: UnifiedDataManager):
    """Example 4: Retrieve options chain."""
    logger.info("\n=== Example 4: Options Chain ===")

    # Get options chain for AAPL
    underlying = "AAPL"

    # Get price first
    prices = data_manager.get_latest_prices([underlying])
    if prices.empty:
        logger.warning("Could not get underlying price")
        return pd.DataFrame()

    current_price = prices[underlying]
    logger.info(f"{underlying} current price: ${current_price:.2f}")

    # Get options expiring in next 30 days, near the money
    try:
        chain = data_manager.get_options_chain(
            underlying_symbol=underlying,
            expiration_date=None,  # All expirations
            strike_price=None,     # All strikes
            option_type=None       # Both calls and puts
        )

        if not chain.empty:
            logger.info(f"Retrieved {len(chain)} option contracts")

            # Filter to near-the-money strikes (within 10% of current price)
            near_money = chain[
                (chain['strike'] >= current_price * 0.9) &
                (chain['strike'] <= current_price * 1.1)
            ]

            logger.info(f"\nNear-the-money contracts ({len(near_money)}):")
            logger.info(f"\n{near_money[['ticker', 'strike', 'expiry', 'type']].head(10)}")
        else:
            logger.warning("No options data available (requires Polygon API)")

    except Exception as e:
        logger.warning(f"Options chain not available: {e}")
        return pd.DataFrame()

    return chain


def example_5_crypto_data(data_manager: UnifiedDataManager):
    """Example 5: Fetch cryptocurrency data."""
    logger.info("\n=== Example 5: Cryptocurrency Data ===")

    try:
        end = datetime.now()
        start = end - timedelta(days=30)

        logger.info("Fetching BTC/USD data")
        crypto_df = data_manager.get_crypto_data(
            from_currency="BTC",
            to_currency="USD",
            start=start,
            end=end,
            timeframe="1Day"
        )

        if not crypto_df.empty:
            logger.info(f"Retrieved {len(crypto_df)} days of BTC data")
            latest = crypto_df['close'].iloc[-1]
            avg = crypto_df['close'].mean()
            logger.info(f"Latest: ${latest:,.0f}, 30-day avg: ${avg:,.0f}")
        else:
            logger.warning("No crypto data available (requires Polygon API)")

    except Exception as e:
        logger.warning(f"Crypto data not available: {e}")


def example_6_trading_workflow(data_manager: UnifiedDataManager):
    """Example 6: Complete trading workflow with Alpaca."""
    logger.info("\n=== Example 6: Trading Workflow ===")

    alpaca_key, alpaca_secret, _ = setup_credentials()

    if not alpaca_key or not alpaca_secret:
        logger.warning("Alpaca credentials required for trading")
        return

    # Initialize broker
    broker = AlpacaBroker(
        api_key=alpaca_key,
        secret_key=alpaca_secret,
        paper_trading=True  # Always use paper trading for examples!
    )

    if not broker.connect():
        logger.error("Failed to connect to Alpaca")
        return

    # Get account info
    account = broker.get_account()
    logger.info(f"Account: ${account['equity']:.2f} equity, ${account['buying_power']:.2f} buying power")

    # Get current positions
    positions = broker.get_positions()
    logger.info(f"Current positions: {len(positions)}")

    # Example: Buy 1 share of SPY
    symbol = "SPY"

    # Get current price
    prices = data_manager.get_latest_prices([symbol])
    if prices.empty:
        logger.warning("Could not get price")
        return

    current_price = prices[symbol]
    logger.info(f"\n{symbol} current price: ${current_price:.2f}")

    # Check if we have enough buying power
    cost = current_price * 1.01  # Add 1% buffer
    if cost > account['buying_power']:
        logger.warning(f"Insufficient buying power (need ${cost:.2f})")
        return

    # Place order (commented out for safety)
    logger.info(f"\n[DEMO] Would place order: BUY 1 {symbol} @ market")
    logger.info("Uncomment the following lines to actually place the order:")
    logger.info(f"# order = broker.submit_order(symbol='{symbol}', qty=1, side='buy', order_type='market')")
    logger.info("# logger.info(f'Order placed: {order}')")

    # Uncomment to actually trade:
    # order = broker.submit_order(
    #     symbol=symbol,
    #     qty=1,
    #     side="buy",
    #     order_type="market"
    # )
    # logger.info(f"Order placed: {order}")

    broker.disconnect()


def example_7_options_analysis(data_manager: UnifiedDataManager):
    """Example 7: Options analysis with Greeks."""
    logger.info("\n=== Example 7: Options Analysis ===")

    # Create option asset
    underlying_symbol = "AAPL"

    # Get current price
    prices = data_manager.get_latest_prices([underlying_symbol])
    if prices.empty:
        logger.warning("Could not get underlying price")
        return

    current_price = prices[underlying_symbol]
    logger.info(f"{underlying_symbol} current price: ${current_price:.2f}")

    # Create a call option expiring in 30 days
    expiry = datetime.now() + timedelta(days=30)
    strike = round(current_price * 1.05)  # 5% OTM call

    option = OptionAsset(
        symbol=f"{underlying_symbol}_CALL_{strike}_{expiry.strftime('%Y%m%d')}",
        underlying_symbol=underlying_symbol,
        strike=strike,
        expiry=expiry,
        option_type=OptionType.CALL
    )

    logger.info(f"\nAnalyzing option: {strike} strike call expiring {expiry.date()}")

    # Calculate theoretical price
    implied_vol = 0.30  # 30% IV assumption
    theo_price = option.black_scholes_price(
        underlying_price=current_price,
        volatility=implied_vol,
        risk_free_rate=0.05
    )

    logger.info(f"Theoretical price: ${theo_price:.2f}")
    logger.info(f"Intrinsic value: ${option.intrinsic_value(current_price):.2f}")
    logger.info(f"Days to expiry: {option.days_to_expiry():.0f}")

    # Calculate Greeks
    greeks = option.calculate_greeks(
        underlying_price=current_price,
        volatility=implied_vol,
        risk_free_rate=0.05
    )

    logger.info(f"\nGreeks:")
    logger.info(f"  Delta: {greeks.delta:.3f}")
    logger.info(f"  Gamma: {greeks.gamma:.4f}")
    logger.info(f"  Theta: ${greeks.theta:.2f}/day")
    logger.info(f"  Vega: ${greeks.vega:.2f}/1% IV")
    logger.info(f"  Rho: ${greeks.rho:.2f}/1% rate")


def example_8_caching_performance():
    """Example 8: Demonstrate caching performance."""
    logger.info("\n=== Example 8: Caching Performance ===")

    alpaca_key, alpaca_secret, polygon_key = setup_credentials()

    # Create manager with caching
    data_manager = UnifiedDataManager(
        alpaca_key=alpaca_key,
        alpaca_secret=alpaca_secret,
        polygon_key=polygon_key,
        enable_caching=True
    )

    symbols = ["AAPL", "MSFT"]
    end = datetime.now()
    start = end - timedelta(days=30)

    # First fetch (cache miss)
    import time
    t1 = time.time()
    df1 = data_manager.get_historical_data(symbols, start, end)
    t2 = time.time()

    logger.info(f"First fetch: {t2-t1:.2f}s")

    # Second fetch (cache hit)
    t3 = time.time()
    df2 = data_manager.get_historical_data(symbols, start, end)
    t4 = time.time()

    logger.info(f"Second fetch (cached): {t4-t3:.4f}s")
    logger.info(f"Speedup: {(t2-t1)/(t4-t3):.1f}x")

    # Show cache stats
    stats = data_manager.get_cache_stats()
    logger.info(f"\nCache statistics:")
    logger.info(f"  Hits: {stats['cache_hits']}")
    logger.info(f"  Misses: {stats['cache_misses']}")
    logger.info(f"  Hit rate: {stats['hit_rate']:.1%}")


def example_9_news_sentiment(data_manager: UnifiedDataManager):
    """Example 9: Get news and sentiment data."""
    logger.info("\n=== Example 9: News & Sentiment ===")

    try:
        # Get news for specific symbol
        symbol = "TSLA"
        news = data_manager.get_news(symbol=symbol, limit=5)

        if news:
            logger.info(f"Latest news for {symbol}:")
            for article in news:
                logger.info(f"\n  Title: {article['title']}")
                logger.info(f"  Published: {article['published_utc']}")
                logger.info(f"  URL: {article['article_url']}")
        else:
            logger.warning("No news available (requires Polygon API)")

    except Exception as e:
        logger.warning(f"News not available: {e}")


def main():
    """Run all examples."""
    logger.info("=" * 60)
    logger.info("Alpaca + Polygon Integration Examples")
    logger.info("=" * 60)

    # Setup
    data_manager = example_1_basic_setup()

    # Data examples
    example_2_historical_data(data_manager)
    example_3_realtime_quotes(data_manager)
    example_4_options_chain(data_manager)
    example_5_crypto_data(data_manager)

    # Analysis examples
    example_7_options_analysis(data_manager)
    example_9_news_sentiment(data_manager)

    # Performance
    example_8_caching_performance()

    # Trading (demo only)
    example_6_trading_workflow(data_manager)

    logger.info("\n" + "=" * 60)
    logger.info("Examples complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
