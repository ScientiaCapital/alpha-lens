# Alphalens Autonomous Trading System

An AI-powered autonomous trading system built on top of Alphalens, using **Claude SDK** for complex reasoning and **LangGraph** for orchestration. The system is self-learning through backtesting and makes decisions based on risk/opportunity analysis.

## 🎯 Overview

This system extends Alphalens from a factor analysis library into a fully autonomous trading system with:

- **AI-Powered Factor Discovery**: Uses Claude to discover novel alpha factors
- **Self-Learning**: Learns from backtests and adapts strategies over time
- **Risk Management**: Multi-layer safety system with automatic circuit breakers
- **Autonomous Decision Making**: Makes trading decisions based on risk/opportunity analysis
- **State Machine Orchestration**: LangGraph coordinates all agents with memory and state
- **Market Regime Detection**: Adapts strategies to market conditions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Central Orchestrator                      │
│                  (LangGraph State Machine)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┬──────────────┐
    │             │             │             │              │
    ▼             ▼             ▼             ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
│Factor  │  │Backtest  │  │  Risk   │  │Execution │  │ Market   │
│Discovery│  │& Learn   │  │Management│  │ Agent    │  │ Regime   │
│ Agent  │  │  Agent   │  │  Agent  │  │          │  │  Agent   │
└────┬───┘  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬─────┘
     │           │             │            │             │
     └───────────┴─────────────┴────────────┴─────────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │   Shared Memory &  │
                   │  State Management  │
                   │    (PostgreSQL +   │
                   │   Redis + Vector)  │
                   └────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL (for persistent storage)
- Redis (for state cache)
- Anthropic API key (for Claude)

### 2. Installation

```bash
# Install base Alphalens dependencies
pip install -r requirements.txt

# Install agent system dependencies
pip install -r requirements-agents.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and database credentials
```

### 3. Database Setup

```bash
# Start PostgreSQL (if not running)
# Start Redis (if not running)

# Create database
createdb alphalens_agents
```

### 4. Configuration

Edit `config.yaml` to customize:
- Risk limits
- Trading parameters
- Learning settings
- Agent behavior

### 5. Run Example

```bash
python example_usage.py
```

## 📚 Core Components

### Agents

#### 1. Factor Discovery Agent
- Discovers new alpha factors using Claude's reasoning
- Learns from historical factor performance
- Generates factor combinations
- Economic intuition + statistical patterns

**Key Methods:**
```python
factor_agent.execute(context={
    "market_data": prices_df,
    "existing_factors": [...],
    "focus_area": "momentum"  # optional
})
```

#### 2. Backtesting Agent
- Tests factors using Alphalens
- Calculates IC, Sharpe, turnover, etc.
- Self-learning: adjusts factor weights based on results
- Makes use/reject decisions

**Key Methods:**
```python
backtest_agent.execute(context={
    "factor": factor_series,
    "prices": prices_df,
    "factor_name": "momentum_5d"
})
```

#### 3. Risk Management Agent
- Monitors portfolio risk metrics
- Enforces position limits
- Detects violations
- Triggers emergency stops

**Risk Limits** (configurable):
- Max daily loss: 2%
- Max position size: 10%
- Max drawdown: 20%
- Max leverage: 1.0x

#### 4. Execution Agent
- Optimizes trade execution
- Minimizes market impact
- Calculates slippage and costs

#### 5. Market Regime Agent
- Detects market conditions
- Classifies regimes (bull/bear, high/low vol)
- Adapts strategies per regime

### Orchestrator (LangGraph State Machine)

The orchestrator coordinates all agents through a state machine:

**State Flow:**
```
IDLE → Regime Detection → Factor Discovery → Backtesting
     → Risk Assessment → Decision Making → Execution → Learning → IDLE
```

**Usage:**
```python
from alphalens.agents.config import SystemConfig
from alphalens.orchestrator import TradingOrchestrator

config = SystemConfig.from_yaml("config.yaml")
orchestrator = TradingOrchestrator(config)

# Run one iteration
result = orchestrator.start(market_data=prices_df)

# Check status
status = orchestrator.get_state()

# Emergency stop
orchestrator.emergency_stop()
```

### Memory & State Management

**Three-tier memory system:**

1. **Redis**: Real-time state cache (fast access)
2. **PostgreSQL**: Persistent storage for historical data
3. **Vector DB**: Semantic search over learnings (future)

**Key Features:**
- Agent state persistence
- Global system state
- Learning memory (strategy results)
- Factor performance history
- Risk event logs

**Usage:**
```python
from alphalens.memory import MemoryStore

memory = MemoryStore(config)

# Store learning
memory.store_learning(
    strategy_id="momentum_strategy_v1",
    strategy_type="factor",
    description="5-day momentum factor",
    parameters={"lookback": 5},
    performance_metrics={"sharpe_ratio": 1.5, "ic_mean": 0.03},
    outcome="success",
    confidence_score=0.8
)

# Retrieve successful strategies
strategies = memory.get_successful_strategies(
    strategy_type="factor",
    market_regime="bull",
    limit=10
)
```

## 🧠 Self-Learning System

The system learns through a feedback loop:

1. **Backtest** factor/strategy
2. **Analyze** performance metrics
3. **Compare** to historical results
4. **Update** factor scoring model
5. **Store** learnings in memory
6. **Adapt** future factor discovery

**Learning Mechanisms:**
- Factor weight adjustment (reinforcement learning style)
- Strategy performance tracking by market regime
- Risk event pattern recognition
- Execution quality improvement

## 🛡️ Safety & Risk Management

### Circuit Breakers
- Daily loss limit
- Position size limits
- Drawdown limits
- Correlation limits

### Human Oversight
- Auto-trading disabled by default
- All decisions logged
- Emergency stop capability
- Explainable AI (Claude provides reasoning)

### Testing Protocol
1. Paper trading (default mode)
2. Limited live trading
3. Graduated scale-up
4. Continuous monitoring

## 📊 Configuration

### Risk Limits (`config.yaml`)

```yaml
risk_limits:
  max_daily_loss_pct: 2.0
  max_position_size_pct: 10.0
  max_leverage: 1.0
  max_drawdown_pct: 20.0
  stop_loss_pct: 5.0
```

### Trading Settings

```yaml
trading:
  mode: "paper"  # paper, live, backtest
  initial_capital: 1000000.0
  commission_rate: 0.001
  factor_quantiles: 5
```

### Learning Settings

```yaml
learning:
  learning_rate: 0.01
  exploration_rate: 0.2
  confidence_threshold: 0.6
  memory_retention_days: 730
```

### Orchestrator Settings

```yaml
orchestrator:
  enable_auto_trading: false  # IMPORTANT: Set to true for autonomous trading
  enable_learning: true
  enable_factor_discovery: true
```

## 🔧 Advanced Usage

### Custom Agents

Create your own agent by extending `BaseAgent`:

```python
from alphalens.agents.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def _initialize_state(self):
        return {"my_state": "initial"}

    def execute(self, context):
        # Your agent logic
        result = self.reason("What should I do?")
        self.log_action("my_action", {"result": result})
        return {"output": result}
```

### Custom Workflow

Modify the orchestrator's state machine:

```python
from langgraph.graph import StateGraph

workflow = StateGraph(TradingState)
workflow.add_node("my_custom_stage", my_function)
workflow.add_edge("discover_factors", "my_custom_stage")
# ... etc
```

### Using Claude for Complex Decisions

Every agent has access to Claude for reasoning:

```python
response = agent.reason(
    prompt="Should I trade this factor given...",
    system="You are a risk-averse quantitative trader"
)
```

## 📈 Monitoring

### Performance Metrics

```python
# Get performance summary
performance = orchestrator.get_performance()

# Get learning summary
learning_summary = memory.get_learning_summary()

# Get agent status
status = orchestrator.get_state()
```

### Logs

- Orchestrator logs: `logs/orchestrator.log`
- Example logs: `logs/example_*.log`

## 🔬 Development Roadmap

### Phase 1: Foundation ✅
- [x] State management
- [x] Agent framework
- [x] Orchestrator with LangGraph
- [x] Basic agents

### Phase 2: Enhanced Intelligence (Next)
- [ ] Advanced factor discovery with Claude
- [ ] Multi-agent collaboration
- [ ] Ensemble strategies
- [ ] Vector memory for semantic search

### Phase 3: Production Ready
- [ ] Broker integration (Interactive Brokers, Alpaca)
- [ ] Real-time data feeds
- [ ] Advanced execution algorithms
- [ ] Monitoring dashboards

### Phase 4: Advanced Features
- [ ] Multi-asset support
- [ ] Options strategies
- [ ] Portfolio optimization
- [ ] Tax-loss harvesting

## 🤝 Contributing

This is an experimental system. Contributions welcome!

Areas for improvement:
- More sophisticated learning algorithms
- Better regime detection
- Advanced execution strategies
- Integration with live data sources
- Monitoring dashboards

## ⚠️ Disclaimers

1. **Paper Trading Only**: Default mode is paper trading. Enable live trading at your own risk.
2. **No Guarantees**: Past performance doesn't guarantee future results.
3. **Use at Your Own Risk**: This is experimental software.
4. **Test Thoroughly**: Test extensively before any live deployment.
5. **Regulatory Compliance**: Ensure compliance with all applicable regulations.

## 📝 License

Apache 2.0 (same as Alphalens)

## 🙏 Credits

Built on top of:
- **Alphalens** by Quantopian
- **Claude SDK** by Anthropic
- **LangGraph** by LangChain
- **Empyrical** for financial metrics

---

**Questions?** Check out:
- [Architecture Document](AGENT_ARCHITECTURE.md) for detailed design
- [Example Usage](example_usage.py) for code examples
- [Configuration Guide](config.yaml) for all settings
