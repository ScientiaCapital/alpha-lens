# Alpha-Lens - Architecture & Planning

**Project:** ScientiaCapital/alpha-lens
**Last Updated:** 2025-11-30
**Repository:** https://github.com/ScientiaCapital/alpha-lens

---

## Project Vision

Alpha-Lens is an AI-powered quantitative trading platform that extends the original Quantopian Alphalens library with:
- Autonomous AI agents for strategy development
- Multi-asset support (equity, options, crypto, futures)
- Production-ready infrastructure for live trading
- Enterprise-grade monitoring and reliability

**CRITICAL RULES:**
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter, or Anthropic Claude
- API keys in `.env` only, never hardcoded
- Maintain backward compatibility with original Alphalens API

---

## Architecture Overview

### Layer 1: Core Alphalens (Preserved)

Original Quantopian functionality maintained for backward compatibility:

```
alphalens/
├── performance.py      # Factor performance metrics
├── plotting.py         # Visualization and tear sheets
├── utils.py            # Data processing utilities
└── tears.py            # Tear sheet generation
```

**Design Principles:**
- No breaking changes to original API
- All tests from Quantopian still pass
- Docstrings preserved

### Layer 2: AI Agent System (New)

Autonomous trading agents powered by LangGraph orchestration:

```
alphalens/
├── agents/
│   ├── strategy_agent.py       # Strategy development
│   ├── risk_agent.py           # Risk assessment
│   ├── execution_agent.py      # Order placement
│   └── monitoring_agent.py     # System health
├── orchestrator/
│   ├── graph.py                # LangGraph workflow
│   ├── nodes.py                # Agent nodes
│   └── state.py                # Shared state
└── memory/
    ├── vector_store.py         # Embedding search
    └── postgres_store.py       # Persistent state
```

**Design Principles:**
- LLM provider abstraction (no vendor lock-in)
- Use DeepSeek/Qwen/Moonshot for cost efficiency
- Agent responses <2s latency target
- Graceful degradation if LLM unavailable

### Layer 3: Multi-Asset Support (New)

Asset class abstractions for equity, options, crypto, futures:

```
alphalens/
├── assets/
│   ├── base.py                 # BaseAsset interface
│   ├── equity.py               # Stock implementation
│   ├── options.py              # Options chain
│   ├── crypto.py               # Cryptocurrency
│   └── futures.py              # Futures contracts
└── strategies/
    ├── equity_strategies.py
    ├── options_strategies.py
    └── multi_asset_strategies.py
```

**Design Principles:**
- Common interface across all asset types
- Asset-specific validation rules
- Position sizing respects asset conventions

### Layer 4: Data & Infrastructure (New)

Market data integrations and broker execution:

```
alphalens/
├── data/
│   ├── alpaca_provider.py      # Alpaca market data
│   ├── polygon_provider.py     # Polygon.io enterprise data
│   └── yahoo_provider.py       # Yahoo Finance (free tier)
├── brokers/
│   ├── alpaca_broker.py        # Commission-free trading
│   └── paper_broker.py         # Paper trading
├── ml/
│   ├── ensemble.py             # Ensemble models
│   ├── deep_learning.py        # Neural networks
│   └── automl.py               # AutoML pipelines
└── monitoring/
    ├── health_check.py         # System health
    └── data_feed_monitor.py    # Feed uptime
```

**Design Principles:**
- API keys in `.env` only
- Rate limiting and retry logic
- Sandbox testing before production
- Monitoring for data quality

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Core | Python | 3.8+ | Runtime |
| Agents | LangGraph | 0.0.20+ | Orchestration |
| Agents | LangChain | 0.1.0+ | Agent framework |
| LLM | Anthropic Claude | Latest | High-quality reasoning |
| LLM | DeepSeek | Latest | Cost-efficient |
| LLM | Qwen | Latest | Alternative |
| Data | Alpaca | Latest | Market data + trading |
| Data | Polygon.io | Latest | Enterprise data |
| Storage | PostgreSQL | 14+ | Persistent state |
| Cache | Redis | 7+ | Fast state access |
| UI | Streamlit | 1.28+ | Dashboard |
| Testing | pytest | 7.0+ | Test framework |
| Linting | flake8 | 6.0+ | Code quality |

**NO OpenAI in this stack!**

---

## Data Flow Architecture

### 1. Market Data Ingestion

```
External API (Alpaca/Polygon)
    → Rate Limiter
    → Validation Layer
    → Redis Cache
    → PostgreSQL Storage
    → Agent Consumption
```

**Key Design Decisions:**
- Cache frequently accessed data (1-min bars)
- Store historical data in PostgreSQL
- Validate data quality before storage

### 2. Agent Decision Flow

```
User Request
    → Strategy Agent (analyzes market)
    → Risk Agent (assesses position)
    → Execution Agent (places order)
    → Monitoring Agent (tracks result)
```

**Key Design Decisions:**
- Each agent is stateless (state in shared store)
- Orchestrator manages agent coordination
- Human-in-the-loop for high-risk decisions

### 3. Trading Execution Flow

```
Agent Signal
    → Order Validator
    → Broker Adapter (Alpaca)
    → Execution
    → Position Tracking
    → Performance Analysis
```

**Key Design Decisions:**
- Paper trading first (test strategies)
- Position limits enforced by validator
- Execution failures logged and alerted

---

## Development Workflow

### 1. Feature Development

```bash
# Create PRP (Production-Ready Plan)
/generate-prp

# Execute PRP in phases
/execute-prp PRPs/PRP-YYYY-MM-DD-feature.md

# Validate before merge
/validate
```

### 2. Testing Strategy

| Test Type | Coverage Target | Tools |
|-----------|----------------|-------|
| Unit | >90% | pytest, pytest-cov |
| Integration | Critical paths | pytest, mock APIs |
| Performance | Latency targets | pytest-benchmark |
| Security | No hardcoded secrets | grep, safety |

### 3. CI/CD Pipeline

```yaml
# GitHub Actions
on: [push, pull_request]
jobs:
  test:
    - run: pytest tests/ --cov
    - run: flake8 alphalens/
    - run: safety check
  deploy:
    - if: branch == master
    - run: docker build && push
```

---

## Configuration Management

### Environment Variables (`.env`)

```bash
# LLM Providers (NO OpenAI!)
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=...
QWEN_API_KEY=...

# Market Data
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
POLYGON_API_KEY=...

# Infrastructure
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379

# Feature Flags
ENABLE_LIVE_TRADING=false
ENABLE_OPTIONS_TRADING=false
```

**Never commit `.env` to Git!**

### Feature Flags

- `ENABLE_LIVE_TRADING` - Production trading (default: false)
- `ENABLE_OPTIONS_TRADING` - Options strategies (default: false)
- `ENABLE_CRYPTO_TRADING` - Crypto assets (default: false)

---

## Security & Compliance

### Secret Management
- All API keys in `.env` only
- `.env` in `.gitignore`
- Use `.env.example` as template
- Rotate keys quarterly

### Code Security
- `safety check` in CI/CD
- No hardcoded credentials
- Dependencies pinned for reproducibility
- Regular security audits

### Trading Compliance
- Position limits enforced
- Risk checks before execution
- Audit trail for all trades
- Human approval for large positions

---

## Monitoring & Observability

### System Health Metrics
- Agent response latency (<2s target)
- Data feed uptime (>99.9% target)
- Order execution success rate
- Redis cache hit rate

### Alerts
- Trading errors (immediate Slack alert)
- Data feed outage (5-min SLA)
- Agent crashes (auto-restart + alert)
- Position limit breaches (trading halt)

---

## Roadmap

### Completed Features
- ✅ Core Alphalens functionality (preserved)
- ✅ LangGraph agent orchestration
- ✅ Alpaca data + broker integration
- ✅ PostgreSQL + Redis infrastructure
- ✅ Streamlit dashboard

### In Progress (Current PRPs)
- [ ] Options trading strategies (PRP-2025-11-25-options)
- [ ] Ensemble ML models (PRP-2025-11-28-ensemble)
- [ ] Advanced risk metrics (PRP-2025-11-30-risk)

### Planned (Next Quarter)
- [ ] Crypto asset support
- [ ] Futures trading
- [ ] Multi-agent collaboration
- [ ] Advanced backtesting engine
- [ ] Mobile notifications

### Research (Future)
- Reinforcement learning agents
- Portfolio optimization algorithms
- Alternative data sources
- Decentralized trading (DeFi)

---

## Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Agent latency | <2s | 1.5s | ✅ |
| Data refresh | <1s | 0.8s | ✅ |
| Order execution | <500ms | 400ms | ✅ |
| Dashboard load | <3s | 2.5s | ✅ |
| Test coverage | >90% | 92% | ✅ |

---

## Related Documents

- [TASK.md](TASK.md) - Current tasks and priorities
- [CLAUDE.md](CLAUDE.md) - Project context for Claude
- [PRPs/templates/prp_base.md](PRPs/templates/prp_base.md) - PRP template
- `.claude/commands/validate.md` - Validation process
- `.claude/commands/execute-prp.md` - Execution guide

---

## Contact & Support

**Repository:** https://github.com/ScientiaCapital/alpha-lens
**Issues:** https://github.com/ScientiaCapital/alpha-lens/issues
**Maintainer:** ScientiaCapital

For questions about this architecture, create an issue or PR.
