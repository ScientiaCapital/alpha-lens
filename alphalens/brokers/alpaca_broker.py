"""
Alpaca broker integration.

Alpaca is great for getting started:
- Commission-free trading
- Easy API
- Paper trading support
- Good documentation
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from loguru import logger

from alphalens.brokers.base import BaseBroker

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("Alpaca SDK not installed. Run: pip install alpaca-py")


class AlpacaBroker(BaseBroker):
    """
    Alpaca broker implementation.

    Requires:
    - pip install alpaca-py
    - Alpaca API key and secret
    """

    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        """
        Initialize Alpaca broker.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Use paper trading (default True)
        """
        if not ALPACA_AVAILABLE:
            raise ImportError("Alpaca SDK not installed. Run: pip install alpaca-py")

        config = {
            "api_key": api_key,
            "api_secret": api_secret,
            "paper": paper
        }
        super().__init__(config)

        self.paper = paper
        self.trading_client = None
        self.data_client = None

    def connect(self) -> bool:
        """Connect to Alpaca API."""
        try:
            self.trading_client = TradingClient(
                api_key=self.config["api_key"],
                secret_key=self.config["api_secret"],
                paper=self.paper
            )

            self.data_client = StockHistoricalDataClient(
                api_key=self.config["api_key"],
                secret_key=self.config["api_secret"]
            )

            # Test connection
            account = self.trading_client.get_account()
            self.connected = True

            logger.info(f"Connected to Alpaca ({'paper' if self.paper else 'live'} trading)")
            logger.info(f"Account status: {account.status}")
            logger.info(f"Portfolio value: ${float(account.portfolio_value):,.2f}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from Alpaca API."""
        self.connected = False
        logger.info("Disconnected from Alpaca")

    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        account = self.trading_client.get_account()

        return {
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "status": account.status,
            "pattern_day_trader": account.pattern_day_trader,
            "trading_blocked": account.trading_blocked,
            "transfers_blocked": account.transfers_blocked
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        positions = self.trading_client.get_all_positions()

        return [
            {
                "symbol": p.symbol,
                "quantity": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "side": p.side
            }
            for p in positions
        ]

    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        from alpaca.trading.enums import QueryOrderStatus

        status_filter = None
        if status == "open":
            status_filter = QueryOrderStatus.OPEN
        elif status == "closed":
            status_filter = QueryOrderStatus.CLOSED

        orders = self.trading_client.get_orders(filter={"status": status_filter} if status_filter else None)

        return [
            {
                "id": o.id,
                "symbol": o.symbol,
                "qty": float(o.qty),
                "filled_qty": float(o.filled_qty),
                "side": o.side.value,
                "type": o.type.value,
                "time_in_force": o.time_in_force.value,
                "status": o.status.value,
                "created_at": o.created_at,
                "filled_at": o.filled_at,
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "stop_price": float(o.stop_price) if o.stop_price else None
            }
            for o in orders
        ]

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Submit an order."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        # Convert side
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

        # Convert time in force
        tif_map = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK
        }
        tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)

        # Create order request
        if order_type.lower() == "market":
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=tif
            )
        elif order_type.lower() == "limit":
            if limit_price is None:
                raise ValueError("limit_price required for limit orders")

            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=tif,
                limit_price=limit_price
            )
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        # Submit order
        order = self.trading_client.submit_order(order_request)

        logger.info(f"Order submitted: {side} {qty} {symbol} @ {order_type}")

        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": float(order.qty),
            "side": order.side.value,
            "type": order.type.value,
            "status": order.status.value,
            "created_at": order.created_at
        }

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order canceled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        """Get historical price data."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        # Map timeframe string to Alpaca TimeFrame
        tf_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, "Min"),
            "15Min": TimeFrame(15, "Min"),
            "1Hour": TimeFrame.Hour,
            "1Day": TimeFrame.Day
        }

        tf = tf_map.get(timeframe, TimeFrame.Day)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=end
        )

        bars = self.data_client.get_stock_bars(request)

        # Convert to DataFrame
        df = bars.df

        if not df.empty and isinstance(df.index, pd.MultiIndex):
            # Reset index and pivot if multi-index
            df = df.reset_index()
            df = df[df['symbol'] == symbol]
            df = df.set_index('timestamp')

        return df

    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Get latest quote."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        from alpaca.data.requests import StockLatestQuoteRequest

        request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quote = self.data_client.get_stock_latest_quote(request)[symbol]

        return {
            "symbol": symbol,
            "bid_price": float(quote.bid_price),
            "bid_size": int(quote.bid_size),
            "ask_price": float(quote.ask_price),
            "ask_size": int(quote.ask_size),
            "timestamp": quote.timestamp
        }

    def is_market_open(self) -> bool:
        """Check if market is open."""
        if not self.connected:
            raise RuntimeError("Not connected to broker")

        clock = self.trading_client.get_clock()
        return clock.is_open
