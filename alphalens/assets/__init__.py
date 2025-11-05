"""
Multi-asset framework for trading system.

Supports:
- Equities (stocks, ETFs)
- Options (calls, puts, spreads)
- Crypto (spot, perpetuals)
- Futures (index, commodity, currency)
"""

from alphalens.assets.base import BaseAsset, AssetType
from alphalens.assets.equity import EquityAsset
from alphalens.assets.option import OptionAsset, OptionType, OptionStyle
from alphalens.assets.crypto import CryptoAsset
from alphalens.assets.future import FutureAsset

__all__ = [
    "BaseAsset",
    "AssetType",
    "EquityAsset",
    "OptionAsset",
    "OptionType",
    "OptionStyle",
    "CryptoAsset",
    "FutureAsset",
]
