# Alphalens Production Features Guide

Comprehensive guide to all production-ready features added to the autonomous trading system.

## 🎯 Overview

This guide covers the advanced features that make Alphalens ready for production trading:

1. **Broker Integration** - Live trading with Alpaca and Interactive Brokers
2. **Real-Time Data Feeds** - Live market data from multiple sources
3. **Monitoring Dashboard** - Web-based monitoring and control
4. **Enhanced Learning** - Advanced ML algorithms for strategy optimization
5. **Portfolio Optimization** - Modern portfolio theory implementation
6. **Backtesting Framework** - Comprehensive historical testing

---

## 1. Broker Integration

### Supported Brokers

#### Alpaca (Recommended for Getting Started)
- ✅ Commission-free trading
- ✅ Easy API
- ✅ Paper trading support
- ✅ Real-time data included

**Setup:**
```python
from alphalens.brokers import AlpacaBroker

# Initialize broker
broker = AlpacaBroker(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    paper=True  # Use paper trading
)

# Connect
broker.connect()

# Get account info
account = broker.get_account()
print(f"Portfolio value: ${account['portfolio_value']:,.2f}")

# Get positions
positions = broker.get_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']} shares @ ${pos['current_price']}")

# Submit order
order = broker.submit_order(
    symbol="AAPL",
    qty=10,
    side="buy",
    order_type="market"
)
```

#### Interactive Brokers (Professional)
- Professional-grade platform
- Lower costs for high-volume trading
- More asset classes
- Complex order types

### Features

All brokers implement the `BaseBroker` interface:

```python
class BaseBroker:
    def connect() -> bool
    def get_account() -> Dict
    def get_positions() -> List[Dict]
    def submit_order(...) -> Dict
    def cancel_order(order_id) -> bool
    def get_historical_bars(...) -> pd.DataFrame
    def get_latest_quote(symbol) -> Dict
    def is_market_open() -> bool
    def liquidate_position(symbol) -> Dict
    def liquidate_all() -> List[Dict]
```

### Integration with Orchestrator

```python
from alphalens.agents.config import SystemConfig
from alphalens.orchestrator import TradingOrchestrator
from alphalens.brokers import AlpacaBroker

# Set up broker
broker = AlpacaBroker(api_key="...", api_secret="...", paper=True)
broker.connect()

# Configure orchestrator to use broker
config = SystemConfig.from_yaml("config.yaml")
config.orchestrator.enable_auto_trading = True  # Enable live trading

# The execution agent will use the broker
orchestrator = TradingOrchestrator(config)
orchestrator.agents["execution"].broker = broker

# Run
orchestrator.start()
```

---

## 2. Real-Time Data Feeds

### Supported Data Sources

#### Yahoo Finance (Free)
```python
from alphalens.data import YahooDataFeed

feed = YahooDataFeed()
feed.connect()

# Get historical data
data = feed.get_historical_data(
    symbols=["AAPL", "GOOGL", "MSFT"],
    start=datetime(2023, 1, 1),
    end=datetime(2024, 1, 1),
    timeframe="1Day"
)

# Get latest prices
prices = feed.get_latest_prices(["AAPL", "GOOGL"])
```

#### Alpaca Data Feed (Real-Time)
```python
from alphalens.data import AlpacaDataFeed

feed = AlpacaDataFeed(api_key="...", api_secret="...")
feed.connect()

# Get historical data
data = feed.get_historical_data(
    symbols=["AAPL"],
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31),
    timeframe="1Min"  # 1Min, 5Min, 1Hour, 1Day
)

# Subscribe to real-time updates
def on_update(data):
    print(f"{data['symbol']}: ${data['close']}")

feed.subscribe_realtime(["AAPL", "GOOGL"], on_update)
```

### Custom Data Feed

Create your own data feed:

```python
from alphalens.data.base import BaseDataFeed

class MyDataFeed(BaseDataFeed):
    def connect(self):
        # Your connection logic
        return True

    def get_historical_data(self, symbols, start, end, timeframe):
        # Your data retrieval logic
        return pd.DataFrame()

    # Implement other methods...
```

---

## 3. Monitoring Dashboard

### FastAPI REST API

**Start the API server:**
```bash
python -m alphalens.dashboard.api
```

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/status` | GET | Current system status |
| `/performance` | GET | Performance metrics |
| `/start` | POST | Start orchestrator |
| `/pause` | POST | Pause system |
| `/resume` | POST | Resume system |
| `/emergency-stop` | POST | Emergency stop |
| `/agents` | GET | List all agents |
| `/agents/{name}/state` | GET | Get agent state |
| `/memory/global` | GET | Global system state |
| `/factors/successful` | GET | Successful factors |
| `/risk/events` | GET | Risk events |
| `/config` | GET | Current configuration |

**Example usage:**
```python
import requests

# Get status
response = requests.get("http://localhost:8000/status")
status = response.json()
print(f"System is {status['current_stage']}")

# Start orchestrator
requests.post("http://localhost:8000/start")

# Emergency stop
requests.post("http://localhost:8000/emergency-stop")
```

### Streamlit Dashboard

**Start the dashboard:**
```bash
streamlit run alphalens/dashboard/streamlit_app.py
```

**Features:**
- 📊 Real-time system overview
- 💰 Portfolio performance tracking
- 🧠 Learning statistics
- 🤖 Agent status monitoring
- 🎯 Successful factors display
- ⚠️ Risk event alerts
- ⚙️ Control panel (Start/Pause/Stop)
- 🔄 Auto-refresh every 5 seconds

**Screenshots:**
The dashboard provides a comprehensive view of:
- System status (running/paused/idle)
- Current stage and iteration
- Portfolio value and positions
- Learning success rate
- Agent health
- Recent factors and their performance
- Risk events

---

## 4. Enhanced Learning Algorithms

### Q-Learning Agent

Reinforcement learning for strategy selection:

```python
from alphalens.learning import QLearningAgent

# Initialize agent
agent = QLearningAgent(
    learning_rate=0.1,
    discount_factor=0.95,
    exploration_rate=0.2
)

# Select strategy based on market regime
state = {"market_regime": "bull", "risk_level": "low"}
strategies = ["momentum", "value", "quality"]

strategy = agent.select_action(state, strategies)

# After strategy execution, update Q-values
reward = 0.15  # Strategy return
next_state = {"market_regime": "bull", "risk_level": "medium"}

agent.update(state, strategy, reward, next_state)
```

**How it works:**
- Learns optimal strategy for each market regime
- Balances exploration (trying new strategies) and exploitation (using best known)
- Adapts over time based on results

### Multi-Armed Bandit

Thompson Sampling for strategy allocation:

```python
from alphalens.learning import BanditLearner

# Initialize bandit with 5 strategies
bandit = BanditLearner(num_arms=5)

# Select strategy
strategy_idx = bandit.select_arm()

# Execute and get reward
reward = execute_strategy(strategy_idx)  # Returns 0-1

# Update
bandit.update(strategy_idx, reward)

# Get statistics
stats = bandit.get_arm_stats()
for arm, stat in stats.items():
    print(f"Strategy {arm}: {stat['mean_reward']:.2%} success rate")
```

### Meta-Learning (Future)

Learn how to learn - optimize the learning process itself.

---

## 5. Portfolio Optimization

### Mean-Variance Optimization (Markowitz)

Find optimal portfolio weights:

```python
from alphalens.optimization import MeanVarianceOptimizer
import pandas as pd

# Load returns data
returns = pd.DataFrame({
    'AAPL': [...],
    'GOOGL': [...],
    'MSFT': [...]
})

# Initialize optimizer
optimizer = MeanVarianceOptimizer(
    risk_free_rate=0.02,
    max_position=0.30,  # Max 30% per stock
    min_position=0.05   # Min 5% per stock
)

# Optimize for maximum Sharpe ratio
weights = optimizer.optimize(returns)
print("Optimal weights:", weights)

# Optimize for target return
weights = optimizer.optimize(returns, target_return=0.12)

# Calculate efficient frontier
frontier = optimizer.efficient_frontier(returns, n_points=50)
```

**Output:**
```python
{
    'AAPL': 0.35,
    'GOOGL': 0.40,
    'MSFT': 0.25
}
```

### Risk Parity (Future)

Equal risk contribution from each asset.

### Black-Litterman (Future)

Combine market equilibrium with investor views.

---

## 6. Testing & Deployment

### Lightweight Testing (No Database Required)

```bash
# Run lite example
python example_usage_lite.py
```

Uses in-memory storage - perfect for quick testing without PostgreSQL/Redis.

### Full Setup with Docker

```bash
# Start databases
docker-compose up -d

# Run setup script
./setup.sh

# Run full example
python example_usage.py
```

### Production Deployment

**1. Set up infrastructure:**
```bash
# PostgreSQL and Redis (production-grade)
# Use AWS RDS, GCP Cloud SQL, or self-hosted

# Environment variables
cp .env.example .env
# Edit .env with production credentials
```

**2. Configure system:**
```yaml
# config.yaml
trading:
  mode: "live"  # Switch to live trading
  initial_capital: 100000.0

orchestrator:
  enable_auto_trading: true  # Enable autonomous trading
  enable_learning: true

risk_limits:
  max_daily_loss_pct: 1.0  # Tighter limits for production
  max_drawdown_pct: 10.0
```

**3. Start services:**
```bash
# Start API server
uvicorn alphalens.dashboard.api:app --host 0.0.0.0 --port 8000

# Start Streamlit dashboard
streamlit run alphalens/dashboard/streamlit_app.py --server.port 8501

# Start orchestrator (automated or manual)
python run_production.py
```

---

## 7. Advanced Features

### Multi-Asset Support (Coming Soon)

- Stocks
- ETFs
- Options
- Futures
- Crypto

### Options Strategies (Coming Soon)

- Covered calls
- Protective puts
- Spreads
- Iron condors

### Tax-Loss Harvesting (Coming Soon)

Automatically realize losses for tax benefits while maintaining exposure.

---

## 8. Safety & Risk Management

### Circuit Breakers

Automatic safeguards:
- Daily loss limit (default: 2%)
- Position size limits (default: 10%)
- Drawdown limits (default: 20%)
- Leverage limits (default: 1.0x)

### Emergency Procedures

**Manual Emergency Stop:**
```python
orchestrator.emergency_stop()
```

**Via API:**
```bash
curl -X POST http://localhost:8000/emergency-stop
```

**Via Dashboard:**
Click the "🛑 Emergency Stop" button

### Monitoring & Alerts

- Real-time risk monitoring
- Email/SMS alerts for violations
- Slack/Discord integration
- Prometheus metrics export

---

## 9. Performance & Scaling

### Optimization Tips

1. **Use Redis for caching** - 10-100x faster than PostgreSQL
2. **Batch operations** - Process multiple symbols together
3. **Async processing** - Use Celery for background tasks
4. **Data caching** - Cache historical data locally

### Scaling Horizontally

- Run multiple orchestrator instances
- Load balance API requests
- Shared Redis/PostgreSQL backend
- Distributed task queue

---

## 10. Example Production Workflow

```python
from alphalens.agents.config import SystemConfig
from alphalens.orchestrator import TradingOrchestrator
from alphalens.brokers import AlpacaBroker
from alphalens.data import AlpacaDataFeed

# 1. Initialize configuration
config = SystemConfig.from_yaml("production_config.yaml")

# 2. Set up broker
broker = AlpacaBroker(
    api_key=config.broker_api_key,
    api_secret=config.broker_api_secret,
    paper=False  # LIVE TRADING
)
broker.connect()

# 3. Set up data feed
data_feed = AlpacaDataFeed(
    api_key=config.data_api_key,
    api_secret=config.data_api_secret
)
data_feed.connect()

# 4. Initialize orchestrator
orchestrator = TradingOrchestrator(config)

# 5. Attach broker and data feed
orchestrator.agents["execution"].broker = broker
orchestrator.data_feed = data_feed

# 6. Run production loop
while True:
    # Get latest market data
    market_data = data_feed.get_latest_prices(config.universe)

    # Run orchestrator iteration
    result = orchestrator.start(market_data=market_data)

    # Log results
    logger.info(f"Iteration {result['iteration']} complete")
    logger.info(f"Factors: {len(result['successful_factors'])}")
    logger.info(f"Trades: {len(result['executed_trades'])}")

    # Wait for next iteration
    time.sleep(config.iteration_interval)
```

---

## 11. Troubleshooting

### Common Issues

**PostgreSQL connection failed**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**Redis connection failed**
```bash
# Check if Redis is running
redis-cli ping

# Restart Redis
sudo systemctl restart redis
```

**Claude API errors**
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API usage limits
- Review error logs in `logs/`

**Import errors**
```bash
# Reinstall dependencies
pip install -r requirements-agents.txt
```

---

## 12. Next Steps

1. ✅ Test in paper trading mode
2. ✅ Review all generated factors
3. ✅ Monitor risk metrics daily
4. ✅ Backtest thoroughly (6+ months)
5. ✅ Start with small capital
6. ✅ Gradually increase position sizes
7. ✅ Continuous monitoring and improvement

---

## 13. Resources

- **Documentation**: See `AGENTS_README.md` for core concepts
- **Architecture**: See `AGENT_ARCHITECTURE.md` for system design
- **API Reference**: http://localhost:8000/docs (when server running)
- **Dashboard**: http://localhost:8501 (when Streamlit running)

---

**Remember**: Always start with paper trading and test extensively before deploying with real capital!
