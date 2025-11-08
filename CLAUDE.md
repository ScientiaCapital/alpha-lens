# Alpha-Lens Project Context

## Project Overview

Alpha-Lens is ScientiaCapital's AI-powered quantitative trading platform. This is an independent fork of Quantopian's Alphalens library, significantly extended with autonomous AI agents, multi-asset support, and enterprise infrastructure.

## Project Status

**Repository:** ScientiaCapital/alpha-lens (independent, not a fork)
**Primary Language:** Python 3.8+
**Architecture:** Modular agent-based system with AI orchestration

## Core Components

### Original Alphalens (Preserved)
- `alphalens/performance.py` - Factor performance metrics
- `alphalens/plotting.py` - Visualization and tear sheets
- `alphalens/utils.py` - Data processing utilities
- `alphalens/tears.py` - Tear sheet generation

### AI Agent System (New)
- `alphalens/agents/` - Autonomous trading agents powered by Claude
- `alphalens/orchestrator/` - LangGraph-based agent coordination
- `alphalens/memory/` - Persistent state and learning memory

### Multi-Asset Support (New)
- `alphalens/assets/` - Base classes for equity, options, crypto, futures
- `alphalens/strategies/` - Asset-specific trading strategies

### Data & Infrastructure (New)
- `alphalens/data/` - Alpaca, Polygon.io, Yahoo Finance integrations
- `alphalens/brokers/` - Broker execution adapters
- `alphalens/dashboard/` - Streamlit monitoring interface
- `alphalens/ml/` - Machine learning models (ensemble, deep learning, AutoML)
- `alphalens/monitoring/` - System health and data feed monitoring

## Development Guidelines

### Code Standards
- Follow PEP 8 style guidelines
- Type hints for new code
- Docstrings for public APIs
- Unit tests for critical functionality

### API Keys & Secrets
- NEVER hardcode API keys in code
- ALL secrets go in `.env` file (never committed)
- Use `.env.example` as template

### Git Workflow
- Main branch: `master`
- Feature branches: descriptive names
- Commit messages: Clear, descriptive
- Push regularly to backup work

### Dependencies
- Core: `requirements-agents.txt`
- Keep dependencies minimal and documented
- Pin versions for production stability

## Key Integrations

**Claude AI:** Autonomous agent intelligence (Anthropic API)
**Alpaca:** Commission-free trading execution
**Polygon.io:** Enterprise market data feeds
**PostgreSQL:** Persistent storage
**Redis:** Caching and state management

## Project Goals

1. Provide institutional-grade alpha factor analysis
2. Enable autonomous AI-driven trading strategies
3. Support multiple asset classes (equity, options, crypto, futures)
4. Maintain production-ready reliability and monitoring
5. Scale to handle real-time market data and execution

## Attribution

Originally based on Quantopian/Alphalens (Apache 2.0 License). Significantly extended and enhanced by ScientiaCapital with AI agents, multi-asset support, and production infrastructure.
