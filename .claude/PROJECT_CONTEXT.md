# alpha-lens

**Branch**: master | **Updated**: 2025-11-30

## Status
Independent fork of Quantopian's Alphalens, extended with autonomous AI agents, multi-asset support, and enterprise infrastructure. Production-ready AI-powered quantitative trading platform.

## Today's Focus
1. [ ] Test AI agent system integration
2. [ ] Validate multi-asset support
3. [ ] Review broker execution adapters

## Done (This Session)
- (none yet)

## Critical Rules
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter
- API keys in `.env` only, never hardcoded
- Follow PEP 8 style guidelines
- Type hints for new code
- Unit tests for critical functionality

## Blockers
(none)

## Quick Commands
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements-agents.txt

# Run setup
./setup.sh

# Run tests
pytest tests/ -v
```

## Tech Stack
- **Primary Language**: Python 3.8+
- **AI Framework**: LangGraph-based agent orchestration
- **AI Provider**: Anthropic Claude (autonomous agents)
- **Data Sources**: Alpaca, Polygon.io, Yahoo Finance
- **Database**: PostgreSQL (persistent storage)
- **Cache**: Redis (state management)
- **Dashboard**: Streamlit monitoring interface
- **ML**: Ensemble, deep learning, AutoML models
