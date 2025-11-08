# Alpha-Lens

**AI-Powered Multi-Asset Alpha Factor Analysis Platform**

Alpha-Lens is ScientiaCapital's next-generation quantitative trading platform that combines traditional alpha factor analysis with autonomous AI agents, multi-asset support, and enterprise-grade infrastructure.

## Overview

Built on the foundation of predictive alpha factor analysis, Alpha-Lens extends beyond equities to support options, cryptocurrencies, and futures trading. The platform integrates Claude AI agents for autonomous factor discovery, risk management, and trade execution, providing institutional-grade capabilities for systematic trading strategies.

## Key Features

**Core Analysis**
- Factor performance analysis with returns, IC, and turnover metrics
- Multi-timeframe forward returns analysis
- Sector and industry-based grouping analytics
- Comprehensive tear sheet visualizations

**AI Agent System**
- Autonomous factor discovery and validation
- Dynamic risk management and position sizing
- Market regime detection and adaptation
- Backtesting with walk-forward analysis

**Multi-Asset Support**
- Equities (traditional alpha factors)
- Options (Greeks-aware strategies)
- Cryptocurrencies (24/7 market coverage)
- Futures (commodity and index exposure)

**Data Integration**
- Alpaca Markets (commission-free trading)
- Polygon.io (real-time and historical data)
- Yahoo Finance (market data fallback)
- WebSocket streaming for live prices

**Production Infrastructure**
- Real-time monitoring dashboard (Streamlit)
- PostgreSQL for persistent storage
- Redis for caching and state management
- Docker-ready deployment configuration

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ScientiaCapital/alpha-lens.git
cd alpha-lens

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements-agents.txt

# Run example
python example_usage_lite.py
```

## Documentation

- [Agent Architecture](AGENT_ARCHITECTURE.md) - AI agent system design
- [Multi-Asset Guide](MULTI_ASSET_ARCHITECTURE.md) - Trading multiple asset classes
- [Data Integration](ALPACA_POLYGON_SETUP.md) - Setting up data feeds
- [Production Deployment](PRODUCTION_READY.md) - Enterprise deployment guide

## Requirements

- Python 3.8+
- Anthropic API key (for Claude AI agents)
- Alpaca API credentials (for trading)
- Polygon.io API key (for market data)

## License

Apache License 2.0. Originally based on Quantopian/Alphalens, extensively enhanced by ScientiaCapital.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/ScientiaCapital/alpha-lens/issues).
