"""
Cryptocurrency asset implementation.
"""

from typing import Dict, Any, Optional
from alphalens.assets.base import BaseAsset, AssetType
from loguru import logger


class CryptoAsset(BaseAsset):
    """
    Cryptocurrency asset (spot or perpetual).
    """

    def __init__(
        self,
        symbol: str,
        base_currency: str,
        quote_currency: str = "USD",
        exchange: str = "Binance",
        is_perpetual: bool = False,
        min_order_size: float = 0.001,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize crypto asset.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSD")
            base_currency: Base currency (e.g., "BTC")
            quote_currency: Quote currency (e.g., "USD")
            exchange: Exchange name
            is_perpetual: Whether this is a perpetual future
            min_order_size: Minimum order size
            metadata: Additional metadata
        """
        metadata = metadata or {}
        metadata.update({
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "is_perpetual": is_perpetual,
            "min_order_size": min_order_size
        })

        super().__init__(
            symbol=symbol,
            asset_type=AssetType.CRYPTO,
            exchange=exchange,
            metadata=metadata
        )

        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.is_perpetual = is_perpetual
        self.min_order_size = min_order_size

        # Crypto-specific attributes
        self.maker_fee: Optional[float] = None  # Maker fee (as decimal)
        self.taker_fee: Optional[float] = None  # Taker fee (as decimal)
        self.funding_rate: Optional[float] = None  # For perpetuals

    def get_identifier(self) -> str:
        """Get unique identifier."""
        suffix = "-PERP" if self.is_perpetual else ""
        return f"{self.base_currency}/{self.quote_currency}{suffix}@{self.exchange}"

    def is_tradeable(self) -> bool:
        """Crypto trades 24/7."""
        return True

    def get_lot_size(self) -> float:
        """Get minimum order size."""
        return self.min_order_size

    def calculate_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate position value in quote currency.

        Args:
            quantity: Amount in base currency
            price: Price in quote currency (current price if None)

        Returns:
            Value in quote currency
        """
        if price is None:
            price = self.get_current_price()
            if price is None:
                raise ValueError(f"No price available for {self.symbol}")

        return quantity * price

    def set_fees(self, maker_fee: float, taker_fee: float) -> None:
        """
        Set trading fees.

        Args:
            maker_fee: Maker fee (as decimal, e.g., 0.001 for 0.1%)
            taker_fee: Taker fee (as decimal)
        """
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

    def get_trading_cost(self, quantity: float, price: float, is_maker: bool = False) -> float:
        """
        Calculate trading cost.

        Args:
            quantity: Trade quantity
            price: Trade price
            is_maker: Whether this is a maker order

        Returns:
            Trading cost in quote currency
        """
        value = self.calculate_value(quantity, price)
        fee_rate = self.maker_fee if is_maker else self.taker_fee

        if fee_rate is None:
            # Use default estimates
            fee_rate = 0.001 if is_maker else 0.002

        return value * fee_rate

    def set_funding_rate(self, funding_rate: float) -> None:
        """
        Set funding rate for perpetuals.

        Args:
            funding_rate: Funding rate (as decimal per 8 hours)
        """
        if not self.is_perpetual:
            logger.warning(f"{self.symbol} is not a perpetual, funding rate not applicable")

        self.funding_rate = funding_rate

    def get_funding_rate(self) -> Optional[float]:
        """Get funding rate (for perpetuals)."""
        return self.funding_rate if self.is_perpetual else None

    def calculate_funding_cost(self, position_value: float, hours: int = 8) -> Optional[float]:
        """
        Calculate funding cost for perpetual position.

        Args:
            position_value: Position value in quote currency
            hours: Number of hours (default 8 for one funding period)

        Returns:
            Funding cost (positive = pay, negative = receive)
        """
        if not self.is_perpetual or self.funding_rate is None:
            return None

        periods = hours / 8
        return position_value * self.funding_rate * periods

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "is_perpetual": self.is_perpetual,
            "min_order_size": self.min_order_size,
            "maker_fee": self.maker_fee,
            "taker_fee": self.taker_fee
        })

        if self.is_perpetual:
            data["funding_rate"] = self.funding_rate

        return data
