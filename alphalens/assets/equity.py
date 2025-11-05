"""
Equity asset implementation (stocks, ETFs).
"""

from typing import Dict, Any, Optional
from alphalens.assets.base import BaseAsset, AssetType
from loguru import logger


class EquityAsset(BaseAsset):
    """
    Equity asset (stock or ETF).
    """

    def __init__(
        self,
        symbol: str,
        exchange: str = "NYSE",
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        market_cap: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize equity asset.

        Args:
            symbol: Stock ticker (e.g., "AAPL")
            exchange: Exchange (NYSE, NASDAQ, etc.)
            sector: Sector classification
            industry: Industry classification
            market_cap: Market capitalization
            metadata: Additional metadata
        """
        metadata = metadata or {}
        metadata.update({
            "sector": sector,
            "industry": industry,
            "market_cap": market_cap
        })

        super().__init__(
            symbol=symbol,
            asset_type=AssetType.EQUITY,
            exchange=exchange,
            metadata=metadata
        )

        self.sector = sector
        self.industry = industry
        self.market_cap = market_cap

    def get_identifier(self) -> str:
        """Get unique identifier (symbol for equities)."""
        return f"{self.symbol}"

    def is_tradeable(self) -> bool:
        """Check if equity is tradeable."""
        # Basic check - could enhance with market hours, halts, etc.
        return True

    def get_lot_size(self) -> float:
        """Equities trade in units of 1 share."""
        return 1.0

    def calculate_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate position value.

        Args:
            quantity: Number of shares
            price: Price per share (current price if None)

        Returns:
            Total value (quantity * price)
        """
        if price is None:
            price = self.get_current_price()
            if price is None:
                raise ValueError(f"No price available for {self.symbol}")

        return quantity * price

    def get_dividend_yield(self) -> Optional[float]:
        """Get dividend yield if available."""
        return self.metadata.get("dividend_yield")

    def get_pe_ratio(self) -> Optional[float]:
        """Get P/E ratio if available."""
        return self.metadata.get("pe_ratio")

    def is_etf(self) -> bool:
        """Check if this is an ETF."""
        return self.metadata.get("is_etf", False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "is_etf": self.is_etf()
        })
        return data


class ETFAsset(EquityAsset):
    """
    Exchange-Traded Fund asset.
    """

    def __init__(
        self,
        symbol: str,
        exchange: str = "NYSE",
        expense_ratio: Optional[float] = None,
        aum: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ETF asset.

        Args:
            symbol: ETF ticker
            exchange: Exchange
            expense_ratio: Annual expense ratio (as decimal)
            aum: Assets under management
            metadata: Additional metadata
        """
        metadata = metadata or {}
        metadata.update({
            "is_etf": True,
            "expense_ratio": expense_ratio,
            "aum": aum
        })

        super().__init__(
            symbol=symbol,
            exchange=exchange,
            metadata=metadata
        )

        self.expense_ratio = expense_ratio
        self.aum = aum

    def get_expense_ratio(self) -> Optional[float]:
        """Get annual expense ratio."""
        return self.expense_ratio

    def get_aum(self) -> Optional[float]:
        """Get assets under management."""
        return self.aum
