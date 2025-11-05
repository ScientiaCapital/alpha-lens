"""
Example Trading Strategies Using Data Infrastructure

Demonstrates real-world trading strategies using the unified data manager:
1. Mean Reversion Strategy
2. Momentum Strategy
3. Moving Average Crossover
4. RSI Strategy
5. Pairs Trading
6. Options Volatility Strategy

All strategies use paper trading by default.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from loguru import logger

from alphalens.data.unified_data_manager import UnifiedDataManager
from alphalens.brokers.alpaca_broker import AlpacaBroker


class BaseStrategy:
    """Base class for all strategies."""

    def __init__(self, data_manager: UnifiedDataManager, broker: AlpacaBroker):
        self.data_manager = data_manager
        self.broker = broker
        self.positions = {}

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """
        Calculate trading signals.

        Args:
            data: Historical price data

        Returns:
            Dict of symbol -> signal ('buy', 'sell', 'hold')
        """
        raise NotImplementedError

    def execute_signals(self, signals: Dict[str, str]) -> None:
        """Execute trading signals."""
        for symbol, signal in signals.items():
            if signal == "buy":
                self._buy(symbol)
            elif signal == "sell":
                self._sell(symbol)

    def _buy(self, symbol: str, qty: int = 1) -> None:
        """Place buy order."""
        if symbol in self.positions:
            logger.info(f"Already holding {symbol}, skipping buy")
            return

        try:
            order = self.broker.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                order_type="market"
            )
            logger.info(f"BUY {qty} {symbol}: {order}")
            self.positions[symbol] = qty
        except Exception as e:
            logger.error(f"Buy order failed: {e}")

    def _sell(self, symbol: str) -> None:
        """Place sell order."""
        if symbol not in self.positions:
            logger.info(f"Not holding {symbol}, skipping sell")
            return

        qty = self.positions[symbol]

        try:
            order = self.broker.submit_order(
                symbol=symbol,
                qty=qty,
                side="sell",
                order_type="market"
            )
            logger.info(f"SELL {qty} {symbol}: {order}")
            del self.positions[symbol]
        except Exception as e:
            logger.error(f"Sell order failed: {e}")


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy

    Buy when price is below N standard deviations from mean.
    Sell when price returns to mean or exceeds it.
    """

    def __init__(self, data_manager, broker, window=20, num_std=2.0):
        super().__init__(data_manager, broker)
        self.window = window
        self.num_std = num_std

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """Calculate mean reversion signals."""
        signals = {}

        symbols = data.index.get_level_values("symbol").unique()

        for symbol in symbols:
            try:
                symbol_data = data.xs(symbol, level="symbol")

                # Calculate Bollinger Bands
                sma = symbol_data["close"].rolling(self.window).mean()
                std = symbol_data["close"].rolling(self.window).std()

                upper_band = sma + (self.num_std * std)
                lower_band = sma - (self.num_std * std)

                current_price = symbol_data["close"].iloc[-1]
                current_sma = sma.iloc[-1]

                # Generate signals
                if current_price < lower_band.iloc[-1]:
                    # Price below lower band - oversold, buy signal
                    signals[symbol] = "buy"
                    logger.info(f"{symbol}: Oversold at ${current_price:.2f} (mean: ${current_sma:.2f})")

                elif current_price > upper_band.iloc[-1]:
                    # Price above upper band - overbought, sell signal
                    signals[symbol] = "sell"
                    logger.info(f"{symbol}: Overbought at ${current_price:.2f} (mean: ${current_sma:.2f})")

                else:
                    signals[symbol] = "hold"

            except Exception as e:
                logger.error(f"Error calculating signal for {symbol}: {e}")
                signals[symbol] = "hold"

        return signals


class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy

    Buy stocks with strong positive momentum.
    Sell when momentum reverses.
    """

    def __init__(self, data_manager, broker, lookback=20, threshold=0.05):
        super().__init__(data_manager, broker)
        self.lookback = lookback
        self.threshold = threshold  # 5% return threshold

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """Calculate momentum signals."""
        signals = {}

        symbols = data.index.get_level_values("symbol").unique()

        for symbol in symbols:
            try:
                symbol_data = data.xs(symbol, level="symbol")

                # Calculate returns over lookback period
                current_price = symbol_data["close"].iloc[-1]
                past_price = symbol_data["close"].iloc[-self.lookback]

                returns = (current_price - past_price) / past_price

                if returns > self.threshold:
                    # Strong positive momentum
                    signals[symbol] = "buy"
                    logger.info(f"{symbol}: Strong momentum {returns:.2%}")

                elif returns < -self.threshold:
                    # Negative momentum
                    signals[symbol] = "sell"
                    logger.info(f"{symbol}: Negative momentum {returns:.2%}")

                else:
                    signals[symbol] = "hold"

            except Exception as e:
                logger.error(f"Error calculating signal for {symbol}: {e}")
                signals[symbol] = "hold"

        return signals


class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy

    Buy when short MA crosses above long MA (golden cross).
    Sell when short MA crosses below long MA (death cross).
    """

    def __init__(self, data_manager, broker, short_window=20, long_window=50):
        super().__init__(data_manager, broker)
        self.short_window = short_window
        self.long_window = long_window

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """Calculate MA crossover signals."""
        signals = {}

        symbols = data.index.get_level_values("symbol").unique()

        for symbol in symbols:
            try:
                symbol_data = data.xs(symbol, level="symbol")

                # Calculate moving averages
                short_ma = symbol_data["close"].rolling(self.short_window).mean()
                long_ma = symbol_data["close"].rolling(self.long_window).mean()

                # Current values
                current_short = short_ma.iloc[-1]
                current_long = long_ma.iloc[-1]

                # Previous values
                prev_short = short_ma.iloc[-2]
                prev_long = long_ma.iloc[-2]

                # Detect crossovers
                if prev_short <= prev_long and current_short > current_long:
                    # Golden cross - buy signal
                    signals[symbol] = "buy"
                    logger.info(f"{symbol}: Golden cross! Short MA: ${current_short:.2f}, Long MA: ${current_long:.2f}")

                elif prev_short >= prev_long and current_short < current_long:
                    # Death cross - sell signal
                    signals[symbol] = "sell"
                    logger.info(f"{symbol}: Death cross! Short MA: ${current_short:.2f}, Long MA: ${current_long:.2f}")

                else:
                    signals[symbol] = "hold"

            except Exception as e:
                logger.error(f"Error calculating signal for {symbol}: {e}")
                signals[symbol] = "hold"

        return signals


class RSIStrategy(BaseStrategy):
    """
    RSI (Relative Strength Index) Strategy

    Buy when RSI < 30 (oversold).
    Sell when RSI > 70 (overbought).
    """

    def __init__(self, data_manager, broker, period=14, oversold=30, overbought=70):
        super().__init__(data_manager, broker)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(self.period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """Calculate RSI signals."""
        signals = {}

        symbols = data.index.get_level_values("symbol").unique()

        for symbol in symbols:
            try:
                symbol_data = data.xs(symbol, level="symbol")

                # Calculate RSI
                rsi = self.calculate_rsi(symbol_data["close"])
                current_rsi = rsi.iloc[-1]

                if current_rsi < self.oversold:
                    # Oversold - buy signal
                    signals[symbol] = "buy"
                    logger.info(f"{symbol}: Oversold, RSI = {current_rsi:.1f}")

                elif current_rsi > self.overbought:
                    # Overbought - sell signal
                    signals[symbol] = "sell"
                    logger.info(f"{symbol}: Overbought, RSI = {current_rsi:.1f}")

                else:
                    signals[symbol] = "hold"

            except Exception as e:
                logger.error(f"Error calculating signal for {symbol}: {e}")
                signals[symbol] = "hold"

        return signals


class PairsTradingStrategy(BaseStrategy):
    """
    Pairs Trading Strategy

    Trade correlated pairs when they diverge.
    """

    def __init__(self, data_manager, broker, pair: Tuple[str, str], threshold=2.0):
        super().__init__(data_manager, broker)
        self.pair = pair
        self.threshold = threshold  # Z-score threshold

    def calculate_signals(self, data: pd.DataFrame) -> Dict[str, str]:
        """Calculate pairs trading signals."""
        signals = {}

        try:
            # Get data for both symbols
            symbol1, symbol2 = self.pair

            data1 = data.xs(symbol1, level="symbol")["close"]
            data2 = data.xs(symbol2, level="symbol")["close"]

            # Calculate spread
            spread = data1 - data2

            # Calculate z-score
            mean = spread.mean()
            std = spread.std()
            z_score = (spread.iloc[-1] - mean) / std

            logger.info(f"Pair {symbol1}/{symbol2} z-score: {z_score:.2f}")

            if z_score > self.threshold:
                # Spread too high - short symbol1, long symbol2
                signals[symbol1] = "sell"
                signals[symbol2] = "buy"
                logger.info(f"Spread diverged high: Sell {symbol1}, Buy {symbol2}")

            elif z_score < -self.threshold:
                # Spread too low - long symbol1, short symbol2
                signals[symbol1] = "buy"
                signals[symbol2] = "sell"
                logger.info(f"Spread diverged low: Buy {symbol1}, Sell {symbol2}")

            else:
                signals[symbol1] = "hold"
                signals[symbol2] = "hold"

        except Exception as e:
            logger.error(f"Error calculating pairs signal: {e}")
            signals[self.pair[0]] = "hold"
            signals[self.pair[1]] = "hold"

        return signals


# Example usage functions

def example_mean_reversion():
    """Run mean reversion strategy example."""
    logger.info("=== Mean Reversion Strategy ===")

    # Setup
    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY")
    )

    broker = AlpacaBroker(
        api_key=os.getenv("ALPACA_API_KEY"),
        secret_key=os.getenv("ALPACA_SECRET_KEY"),
        paper_trading=True
    )
    broker.connect()

    # Create strategy
    strategy = MeanReversionStrategy(data_manager, broker, window=20, num_std=2.0)

    # Get historical data
    symbols = ["SPY", "QQQ", "IWM"]
    end = datetime.now()
    start = end - timedelta(days=60)

    logger.info(f"Fetching data for {symbols}")
    data = data_manager.get_historical_data(symbols, start, end)

    # Calculate signals
    signals = strategy.calculate_signals(data)

    logger.info(f"Signals: {signals}")

    # Execute (commented out for safety)
    logger.info("[DEMO MODE] Would execute: strategy.execute_signals(signals)")
    # strategy.execute_signals(signals)

    broker.disconnect()


def example_momentum():
    """Run momentum strategy example."""
    logger.info("\n=== Momentum Strategy ===")

    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY")
    )

    broker = AlpacaBroker(
        api_key=os.getenv("ALPACA_API_KEY"),
        secret_key=os.getenv("ALPACA_SECRET_KEY"),
        paper_trading=True
    )
    broker.connect()

    strategy = MomentumStrategy(data_manager, broker, lookback=20, threshold=0.05)

    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    end = datetime.now()
    start = end - timedelta(days=60)

    data = data_manager.get_historical_data(symbols, start, end)
    signals = strategy.calculate_signals(data)

    logger.info(f"Signals: {signals}")

    broker.disconnect()


def example_ma_crossover():
    """Run MA crossover strategy example."""
    logger.info("\n=== Moving Average Crossover Strategy ===")

    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY")
    )

    broker = AlpacaBroker(
        api_key=os.getenv("ALPACA_API_KEY"),
        secret_key=os.getenv("ALPACA_SECRET_KEY"),
        paper_trading=True
    )
    broker.connect()

    strategy = MovingAverageCrossoverStrategy(data_manager, broker, short_window=20, long_window=50)

    symbols = ["SPY", "DIA"]
    end = datetime.now()
    start = end - timedelta(days=100)  # Need more data for long MA

    data = data_manager.get_historical_data(symbols, start, end)
    signals = strategy.calculate_signals(data)

    logger.info(f"Signals: {signals}")

    broker.disconnect()


def example_rsi():
    """Run RSI strategy example."""
    logger.info("\n=== RSI Strategy ===")

    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY")
    )

    broker = AlpacaBroker(
        api_key=os.getenv("ALPACA_API_KEY"),
        secret_key=os.getenv("ALPACA_SECRET_KEY"),
        paper_trading=True
    )
    broker.connect()

    strategy = RSIStrategy(data_manager, broker, period=14, oversold=30, overbought=70)

    symbols = ["AAPL", "TSLA", "NVDA"]
    end = datetime.now()
    start = end - timedelta(days=60)

    data = data_manager.get_historical_data(symbols, start, end)
    signals = strategy.calculate_signals(data)

    logger.info(f"Signals: {signals}")

    broker.disconnect()


def example_pairs_trading():
    """Run pairs trading strategy example."""
    logger.info("\n=== Pairs Trading Strategy ===")

    data_manager = UnifiedDataManager(
        alpaca_key=os.getenv("ALPACA_API_KEY"),
        alpaca_secret=os.getenv("ALPACA_SECRET_KEY"),
        polygon_key=os.getenv("POLYGON_API_KEY")
    )

    broker = AlpacaBroker(
        api_key=os.getenv("ALPACA_API_KEY"),
        secret_key=os.getenv("ALPACA_SECRET_KEY"),
        paper_trading=True
    )
    broker.connect()

    # Trade the pair: SPY and QQQ (correlated ETFs)
    pair = ("SPY", "QQQ")
    strategy = PairsTradingStrategy(data_manager, broker, pair=pair, threshold=2.0)

    end = datetime.now()
    start = end - timedelta(days=90)

    data = data_manager.get_historical_data(list(pair), start, end)
    signals = strategy.calculate_signals(data)

    logger.info(f"Signals: {signals}")

    broker.disconnect()


def main():
    """Run all strategy examples."""
    logger.info("=" * 60)
    logger.info("Trading Strategy Examples")
    logger.info("=" * 60)

    examples = [
        example_mean_reversion,
        example_momentum,
        example_ma_crossover,
        example_rsi,
        example_pairs_trading,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            logger.error(f"Example failed: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("All strategy examples complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
