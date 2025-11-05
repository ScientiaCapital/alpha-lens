# Alpaca + Polygon.io Integration Guide

Complete guide for setting up and using the Alpaca broker and Polygon.io data feeds with Alphalens.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [API Keys Setup](#api-keys-setup)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Features](#features)
7. [Examples](#examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

This integration provides:

- **Alpaca Broker**: Commission-free stock trading (paper and live)
- **Polygon.io Data**: Comprehensive market data (stocks, options, crypto)
- **Yahoo Finance**: Free fallback for historical data
- **Unified Interface**: Single API for all data sources
- **Intelligent Routing**: Automatic source selection and failover
- **Caching**: Built-in caching for performance and cost savings
- **WebSocket Streaming**: Real-time market data

## Prerequisites

- Python 3.8+
- Alpaca account (free at [alpaca.markets](https://alpaca.markets))
- Polygon.io API key (free tier available at [polygon.io](https://polygon.io))

## API Keys Setup

### 1. Alpaca API Keys

1. Sign up at [alpaca.markets](https://alpaca.markets)
2. Go to "Paper Trading" or "Live Trading" dashboard
3. Navigate to "Your API Keys"
4. Generate new API key and secret
5. **Important**: Keep these secure! Never commit to git

### 2. Polygon API Key

1. Sign up at [polygon.io](https://polygon.io)
2. Go to dashboard
3. Copy your API key from the dashboard
4. **Free tier**: 5 API calls/minute (good for testing)
5. **Paid tiers**: Higher rate limits for production

### 3. Environment Variables

Create a `.env` file in your project root:

```bash
# Alpaca API (Required for trading)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here

# Polygon.io API (Optional but recommended)
POLYGON_API_KEY=your_polygon_key_here

# Anthropic Claude (For AI agents)
ANTHROPIC_API_KEY=your_anthropic_key_here
```

**Important**: Add `.env` to your `.gitignore`!

```bash
echo ".env" >> .gitignore
```

Load environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

alpaca_key = os.getenv("ALPACA_API_KEY")
polygon_key = os.getenv("POLYGON_API_KEY")
```

## Installation

### 1. Install Dependencies

```bash
# Core dependencies
pip install alpaca-py polygon-api-client yfinance

# WebSocket support (for real-time streaming)
pip install websocket-client

# Environment variables
pip install python-dotenv

# Or install all at once
pip install -r requirements-agents.txt
```

### 2. Verify Installation

```python
# Test imports
from alphalens.data.unified_data_manager import UnifiedDataManager
from alphalens.brokers.alpaca_broker import AlpacaBroker
from alphalens.data.polygon_websocket import PolygonWebSocketClient

print("✓ All imports successful!")
```

## Quick Start

### 1. Basic Setup

```python
from alphalens.data.unified_data_manager import UnifiedDataManager
import os

# Initialize data manager
data_manager = UnifiedDataManager(
    alpaca_key=os.getenv("ALPACA_API_KEY"),
    alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
    polygon_key=os.getenv("POLYGON_API_KEY"),
    enable_caching=True
)

# Check available sources
print(data_manager.get_available_sources())
# Output: ['alpaca', 'polygon', 'yahoo']

# Health check
print(data_manager.health_check())
# Output: {'alpaca': True, 'polygon': True, 'yahoo': True}
```

### 2. Fetch Historical Data

```python
from datetime import datetime, timedelta

# Get 30 days of daily data
end = datetime.now()
start = end - timedelta(days=30)

df = data_manager.get_historical_data(
    symbols=["AAPL", "MSFT", "GOOGL"],
    start=start,
    end=end,
    timeframe="1Day"
)

print(df.tail())
```

### 3. Get Real-Time Quotes

```python
# Get latest prices
prices = data_manager.get_latest_prices(["AAPL", "TSLA", "SPY"])

for symbol, price in prices.items():
    print(f"{symbol}: ${price:.2f}")
```

### 4. Trading with Alpaca

```python
from alphalens.brokers.alpaca_broker import AlpacaBroker

# Initialize broker (paper trading)
broker = AlpacaBroker(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    paper_trading=True  # Always start with paper trading!
)

broker.connect()

# Get account info
account = broker.get_account()
print(f"Buying power: ${account['buying_power']:.2f}")

# Place order
order = broker.submit_order(
    symbol="SPY",
    qty=1,
    side="buy",
    order_type="market"
)

print(f"Order placed: {order}")
```

## Features

### Data Sources

#### 1. Polygon.io (Primary)

**Best for:**
- Historical stock data (high quality, adjusted)
- Options chains and Greeks
- Cryptocurrency data
- Technical indicators
- News and sentiment

**Rate Limits:**
- Free: 5 calls/min
- Starter ($29/mo): 100 calls/min
- Developer ($99/mo): 1000 calls/min

```python
# Use Polygon explicitly
df = data_manager.get_historical_data(
    symbols=["AAPL"],
    start=start,
    end=end,
    source="polygon"  # Force Polygon
)
```

#### 2. Alpaca (Real-time Trading Data)

**Best for:**
- Real-time quotes (free for customers)
- Account data
- Order management
- Paper trading

```python
# Alpaca provides real-time data for customers
prices = data_manager.get_latest_prices(
    symbols=["AAPL"],
    source="alpaca"
)
```

#### 3. Yahoo Finance (Free Fallback)

**Best for:**
- Historical data (free, no API key needed)
- Backup when Polygon unavailable

```python
# Automatically falls back to Yahoo if Polygon unavailable
df = data_manager.get_historical_data(
    symbols=["AAPL"],
    start=start,
    end=end
    # No source specified = automatic selection
)
```

### Intelligent Data Routing

The `UnifiedDataManager` automatically selects the best source:

**Historical Data:**
1. Polygon (highest quality)
2. Yahoo Finance (free fallback)

**Real-time Quotes:**
1. Alpaca (free for customers)
2. Polygon
3. Yahoo Finance

**Options Data:**
- Polygon only (exclusive)

**Crypto Data:**
- Polygon only

### Caching System

Built-in caching saves API calls and improves performance:

```python
# Caching is enabled by default
data_manager = UnifiedDataManager(
    alpaca_key=alpaca_key,
    alpaca_secret=alpaca_secret,
    polygon_key=polygon_key,
    enable_caching=True,
    cache_dir=".cache"
)

# First call hits API (slow)
df1 = data_manager.get_historical_data(symbols, start, end)

# Second call uses cache (fast!)
df2 = data_manager.get_historical_data(symbols, start, end)

# Check cache performance
stats = data_manager.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
```

**Cache TTL:**
- Historical data: 24 hours
- Options chains: 5 minutes
- Real-time quotes: No caching

### WebSocket Streaming

Real-time data streaming via WebSocket:

```python
from alphalens.data.polygon_websocket import PolygonWebSocketClient

# Create WebSocket client
client = PolygonWebSocketClient(
    api_key=os.getenv("POLYGON_API_KEY"),
    cluster="stocks"
)

# Connect
client.connect()

# Define callback
def on_trade(msg):
    print(f"{msg['sym']}: ${msg['p']:.2f} x{msg['s']}")

# Subscribe to trades
client.subscribe_trades(["AAPL", "MSFT"], on_trade)

# Stream runs in background
time.sleep(30)

# Disconnect
client.disconnect()
```

## Examples

### Complete Trading Workflow

```python
from datetime import datetime, timedelta
from alphalens.data.unified_data_manager import UnifiedDataManager
from alphalens.brokers.alpaca_broker import AlpacaBroker

# 1. Setup
data_manager = UnifiedDataManager(
    alpaca_key=alpaca_key,
    alpaca_secret=alpaca_secret,
    polygon_key=polygon_key
)

broker = AlpacaBroker(alpaca_key, alpaca_secret, paper_trading=True)
broker.connect()

# 2. Analyze
symbol = "AAPL"

# Get historical data
end = datetime.now()
start = end - timedelta(days=90)
df = data_manager.get_historical_data([symbol], start, end)

# Calculate moving average
df['sma_20'] = df['close'].rolling(20).mean()

# Get current price
current_price = data_manager.get_latest_prices([symbol])[symbol]

# 3. Make decision
last_close = df['close'].iloc[-1]
last_sma = df['sma_20'].iloc[-1]

if current_price > last_sma:
    print(f"{symbol} is above SMA(20), buying signal!")

    # 4. Execute trade
    order = broker.submit_order(
        symbol=symbol,
        qty=1,
        side="buy",
        order_type="market"
    )

    print(f"Order placed: {order}")
else:
    print(f"{symbol} is below SMA(20), no action")
```

### Options Analysis

```python
from alphalens.assets.option import OptionAsset, OptionType

# Get options chain
symbol = "AAPL"
chain = data_manager.get_options_chain(
    underlying_symbol=symbol,
    expiration_date=None,  # All expirations
    option_type="call"     # Calls only
)

# Get current price
current_price = data_manager.get_latest_prices([symbol])[symbol]

# Filter near-the-money calls
near_money = chain[
    (chain['strike'] >= current_price * 0.95) &
    (chain['strike'] <= current_price * 1.05)
]

print(f"Found {len(near_money)} near-the-money calls")

# Analyze specific option
option = OptionAsset(
    symbol=near_money.iloc[0]['ticker'],
    underlying_symbol=symbol,
    strike=near_money.iloc[0]['strike'],
    expiry=near_money.iloc[0]['expiry'],
    option_type=OptionType.CALL
)

# Calculate Greeks
greeks = option.calculate_greeks(
    underlying_price=current_price,
    volatility=0.30
)

print(f"Delta: {greeks.delta:.3f}")
print(f"Theta: ${greeks.theta:.2f}/day")
```

## Best Practices

### 1. Always Use Paper Trading First

```python
# ✓ Good - Paper trading for testing
broker = AlpacaBroker(api_key, secret_key, paper_trading=True)

# ✗ Bad - Live trading without testing
broker = AlpacaBroker(api_key, secret_key, paper_trading=False)
```

### 2. Enable Caching

```python
# ✓ Good - Caching enabled
data_manager = UnifiedDataManager(..., enable_caching=True)

# ✗ Bad - Hitting API every time (slow, expensive)
data_manager = UnifiedDataManager(..., enable_caching=False)
```

### 3. Handle Rate Limits

```python
# ✓ Good - Built-in rate limiting
# UnifiedDataManager handles this automatically

# Monitor cache hit rate
stats = data_manager.get_cache_stats()
if stats['hit_rate'] < 0.5:
    print("Warning: Low cache hit rate, may hit rate limits")
```

### 4. Error Handling

```python
# ✓ Good - Handle errors gracefully
try:
    df = data_manager.get_historical_data(symbols, start, end)
    if df.empty:
        print("No data available")
        # Fall back to alternative
except Exception as e:
    print(f"Error: {e}")
    # Handle error
```

### 5. Secure API Keys

```python
# ✓ Good - Environment variables
import os
api_key = os.getenv("POLYGON_API_KEY")

# ✗ Bad - Hardcoded keys
api_key = "pk_abc123"  # NEVER DO THIS!
```

## Troubleshooting

### Issue: "Not connected to Polygon"

**Solution**: Check your API key and connection:

```python
data_manager = UnifiedDataManager(polygon_key=polygon_key)
health = data_manager.health_check()
print(health)  # Should show polygon: True

# If False, check your API key
```

### Issue: Rate limit exceeded

**Solution**:
1. Enable caching (enabled by default)
2. Reduce request frequency
3. Upgrade to paid Polygon tier

```python
# Check your rate limit tier
from alphalens.data.polygon_feed import PolygonDataFeed

feed = PolygonDataFeed(polygon_key, tier="free")  # 5 calls/min
# or
feed = PolygonDataFeed(polygon_key, tier="starter")  # 100 calls/min
```

### Issue: WebSocket connection fails

**Solution**: Check websocket-client installation:

```bash
pip install websocket-client
```

### Issue: No data returned

**Solution**: Check date range and symbol:

```python
# Verify symbol
prices = data_manager.get_latest_prices(["AAPL"])
if prices.empty:
    print("Symbol may be invalid or market closed")

# Check available sources
print(data_manager.get_available_sources())
```

### Issue: Alpaca order rejected

**Solution**: Check buying power and market hours:

```python
account = broker.get_account()
print(f"Buying power: ${account['buying_power']:.2f}")

# Check if market is open
if account['trading_blocked']:
    print("Trading is currently blocked")
```

## Advanced Usage

### Custom Data Pipeline

```python
# Create custom data pipeline
class CustomDataPipeline:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def fetch_and_process(self, symbols, days=30):
        end = datetime.now()
        start = end - timedelta(days=days)

        # Fetch data
        df = self.data_manager.get_historical_data(
            symbols, start, end
        )

        # Add technical indicators
        for symbol in symbols:
            symbol_data = df.xs(symbol, level='symbol')

            # SMA
            df.loc[(slice(None), symbol), 'sma_20'] = \
                symbol_data['close'].rolling(20).mean()

            # RSI
            delta = symbol_data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            df.loc[(slice(None), symbol), 'rsi'] = 100 - (100 / (1 + rs))

        return df

# Use custom pipeline
pipeline = CustomDataPipeline(data_manager)
df = pipeline.fetch_and_process(["AAPL", "MSFT"])
```

## Resources

- **Alpaca Documentation**: https://alpaca.markets/docs
- **Polygon Documentation**: https://polygon.io/docs
- **Alphalens GitHub**: https://github.com/quantopian/alphalens
- **Example Scripts**: `examples/alpaca_polygon_integration.py`
- **WebSocket Example**: `alphalens/data/polygon_websocket.py`

## Support

For issues or questions:
1. Check this guide first
2. Review example scripts in `examples/`
3. Check Alpaca/Polygon documentation
4. Open an issue on GitHub

---

**Happy Trading! 🚀**

*Remember: Always test with paper trading first!*
