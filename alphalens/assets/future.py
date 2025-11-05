"""
Futures asset implementation.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from alphalens.assets.base import BaseAsset, AssetType
from loguru import logger


class FutureAsset(BaseAsset):
    """
    Futures contract.

    Supports:
    - Index futures (ES, NQ)
    - Commodity futures (CL, GC)
    - Currency futures
    """

    def __init__(
        self,
        symbol: str,
        underlying_symbol: str,
        expiry: datetime,
        contract_size: float,
        tick_size: float,
        tick_value: float,
        exchange: str = "CME",
        margin_requirement: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize futures contract.

        Args:
            symbol: Futures symbol (e.g., "ESH23")
            underlying_symbol: Underlying asset
            expiry: Contract expiration date
            contract_size: Contract multiplier
            tick_size: Minimum price movement
            tick_value: Value of one tick
            exchange: Exchange
            margin_requirement: Initial margin requirement
            metadata: Additional metadata
        """
        metadata = metadata or {}
        metadata.update({
            "underlying": underlying_symbol,
            "expiry": expiry.isoformat(),
            "contract_size": contract_size,
            "tick_size": tick_size,
            "tick_value": tick_value,
            "margin_requirement": margin_requirement
        })

        super().__init__(
            symbol=symbol,
            asset_type=AssetType.FUTURE,
            exchange=exchange,
            metadata=metadata
        )

        self.underlying_symbol = underlying_symbol
        self.expiry = expiry
        self.contract_size = contract_size
        self.tick_size = tick_size
        self.tick_value = tick_value
        self.margin_requirement = margin_requirement

    def get_identifier(self) -> str:
        """Get unique identifier."""
        return f"{self.symbol}@{self.exchange}"

    def is_tradeable(self) -> bool:
        """Check if contract is tradeable (not expired)."""
        return datetime.now() < self.expiry

    def get_lot_size(self) -> float:
        """Futures trade in contracts of 1."""
        return 1.0

    def calculate_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate futures position value.

        Args:
            quantity: Number of contracts
            price: Futures price (current price if None)

        Returns:
            Notional value (quantity * price * contract_size)
        """
        if price is None:
            price = self.get_current_price()
            if price is None:
                raise ValueError(f"No price available for {self.symbol}")

        return quantity * price * self.contract_size

    def days_to_expiry(self) -> float:
        """Calculate days until expiration."""
        now = datetime.now()
        if now >= self.expiry:
            return 0.0

        delta = self.expiry - now
        return delta.total_seconds() / (24 * 3600)

    def calculate_pnl(self, entry_price: float, exit_price: float, quantity: float) -> float:
        """
        Calculate P&L for a futures trade.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            quantity: Number of contracts (positive for long, negative for short)

        Returns:
            P&L in dollars
        """
        price_change = exit_price - entry_price
        ticks = price_change / self.tick_size
        pnl = ticks * self.tick_value * quantity

        return pnl

    def get_margin_requirement(self) -> Optional[float]:
        """Get initial margin requirement per contract."""
        return self.margin_requirement

    def calculate_margin(self, quantity: float) -> float:
        """
        Calculate margin requirement for position.

        Args:
            quantity: Number of contracts

        Returns:
            Total margin requirement
        """
        if self.margin_requirement is None:
            # Estimate as 5% of notional value if not specified
            price = self.get_current_price()
            if price:
                notional = self.calculate_value(abs(quantity), price)
                return notional * 0.05
            return 0

        return abs(quantity) * self.margin_requirement

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "underlying": self.underlying_symbol,
            "expiry": self.expiry.isoformat(),
            "days_to_expiry": self.days_to_expiry(),
            "contract_size": self.contract_size,
            "tick_size": self.tick_size,
            "tick_value": self.tick_value,
            "margin_requirement": self.margin_requirement
        })
        return data
