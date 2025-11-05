"""
Data feed integrations for real-time and historical data.

Supports:
- Alpaca (real-time and historical)
- Yahoo Finance (free historical data)
- Custom data sources
"""

from alphalens.data.base import BaseDataFeed
from alphalens.data.alpaca_feed import AlpacaDataFeed
from alphalens.data.yahoo_feed import YahooDataFeed

__all__ = ["BaseDataFeed", "AlpacaDataFeed", "YahooDataFeed"]
