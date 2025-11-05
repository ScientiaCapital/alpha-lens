"""
Trading strategies for multi-asset system.
"""

from alphalens.strategies.options import (
    CoveredCall,
    ProtectivePut,
    VerticalSpread,
    IronCondor,
    Straddle,
    Strangle
)

__all__ = [
    "CoveredCall",
    "ProtectivePut",
    "VerticalSpread",
    "IronCondor",
    "Straddle",
    "Strangle",
]
