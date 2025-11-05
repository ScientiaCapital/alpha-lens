"""
Base broker interface for all broker integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from loguru import logger


class BaseBroker(ABC):
    """
    Abstract base class for broker integrations.

    All broker implementations must inherit from this class.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize broker connection.

        Args:
            config: Broker-specific configuration
        """
        self.config = config
        self.connected = False
        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to broker API.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from broker API."""
        pass

    @abstractmethod
    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            Dictionary with account details:
            - cash: Available cash
            - portfolio_value: Total portfolio value
            - buying_power: Available buying power
            - positions: Current positions
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.

        Returns:
            List of position dictionaries with:
            - symbol: Asset symbol
            - quantity: Number of shares
            - avg_entry_price: Average entry price
            - current_price: Current market price
            - market_value: Current market value
            - unrealized_pl: Unrealized P&L
        """
        pass

    @abstractmethod
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get orders.

        Args:
            status: Filter by status (open, filled, canceled, etc.)

        Returns:
            List of order dictionaries
        """
        pass

    @abstractmethod
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
        """
        Submit an order.

        Args:
            symbol: Asset symbol
            qty: Quantity
            side: "buy" or "sell"
            order_type: "market", "limit", "stop", "stop_limit"
            time_in_force: "day", "gtc", "ioc", "fok"
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Order confirmation dictionary
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime
    ) -> pd.DataFrame:
        """
        Get historical price data.

        Args:
            symbol: Asset symbol
            timeframe: Bar timeframe (1Min, 5Min, 1Hour, 1Day, etc.)
            start: Start datetime
            end: End datetime

        Returns:
            DataFrame with OHLCV data
        """
        pass

    @abstractmethod
    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Dictionary with bid, ask, last price, volume, etc.
        """
        pass

    @abstractmethod
    def is_market_open(self) -> bool:
        """
        Check if market is currently open.

        Returns:
            True if market is open
        """
        pass

    def get_buying_power(self) -> float:
        """
        Get available buying power.

        Returns:
            Available buying power
        """
        account = self.get_account()
        return account.get("buying_power", 0)

    def get_portfolio_value(self) -> float:
        """
        Get total portfolio value.

        Returns:
            Total portfolio value
        """
        account = self.get_account()
        return account.get("portfolio_value", 0)

    def liquidate_position(self, symbol: str) -> Dict[str, Any]:
        """
        Liquidate a position (sell all shares).

        Args:
            symbol: Asset symbol

        Returns:
            Order confirmation
        """
        positions = self.get_positions()
        position = next((p for p in positions if p["symbol"] == symbol), None)

        if not position:
            raise ValueError(f"No position found for {symbol}")

        return self.submit_order(
            symbol=symbol,
            qty=abs(position["quantity"]),
            side="sell" if position["quantity"] > 0 else "buy",
            order_type="market"
        )

    def liquidate_all(self) -> List[Dict[str, Any]]:
        """
        Liquidate all positions.

        Returns:
            List of order confirmations
        """
        results = []
        for position in self.get_positions():
            try:
                result = self.liquidate_position(position["symbol"])
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to liquidate {position['symbol']}: {e}")

        return results
