# Alpha-Lens - Current Tasks

**Last Updated:** 2025-11-30
**Sprint:** Q4 2025 - Week 48

---

## Active Tasks

### High Priority

#### 1. Options Trading Strategies (PRP-2025-11-25-options)
**Status:** In Progress (Phase 3/6 - Testing)
**Owner:** Development Team
**Due:** 2025-12-05

**Progress:**
- [x] Core options chain data structure
- [x] Integration with Alpaca options API
- [x] Basic covered call strategy
- [ ] Unit tests for options pricing
- [ ] Integration tests with sandbox
- [ ] Documentation and examples

**Blockers:**
- None

**Next Steps:**
1. Complete unit tests for `alphalens/assets/options.py`
2. Test covered call strategy in Alpaca sandbox
3. Add examples to `examples/options_covered_call.py`

---

#### 2. Ensemble ML Models (PRP-2025-11-28-ensemble)
**Status:** In Progress (Phase 2/6 - Core Implementation)
**Owner:** Development Team
**Due:** 2025-12-10

**Progress:**
- [x] Ensemble architecture design
- [x] Random Forest model integration
- [ ] XGBoost model integration
- [ ] Voting ensemble logic
- [ ] Backtesting integration
- [ ] Performance benchmarks

**Blockers:**
- None

**Next Steps:**
1. Implement `alphalens/ml/ensemble.py` XGBoost wrapper
2. Add voting logic with configurable weights
3. Benchmark against single models

---

### Medium Priority

#### 3. Advanced Risk Metrics (PRP-2025-11-30-risk)
**Status:** Planning
**Owner:** Development Team
**Due:** 2025-12-15

**Tasks:**
- [ ] Create PRP document
- [ ] Design risk metric API
- [ ] Implement VaR (Value at Risk)
- [ ] Implement CVaR (Conditional VaR)
- [ ] Add portfolio-level risk aggregation
- [ ] Integration with risk agent

**Blockers:**
- Waiting for PRP approval

**Next Steps:**
1. Review existing risk implementations
2. Draft PRP using `/generate-prp`
3. Get stakeholder approval

---

#### 4. Dashboard Performance Optimization
**Status:** Planned
**Owner:** Development Team
**Due:** 2025-12-12

**Tasks:**
- [ ] Profile Streamlit dashboard load times
- [ ] Optimize Redis caching strategy
- [ ] Reduce database query count
- [ ] Add lazy loading for charts
- [ ] Target: <2s initial load time

**Blockers:**
- None

**Next Steps:**
1. Run profiler on current dashboard
2. Identify top 3 bottlenecks
3. Create optimization PRP if needed

---

### Low Priority

#### 5. Documentation Improvements
**Status:** Ongoing
**Owner:** Development Team
**Due:** Continuous

**Tasks:**
- [ ] Add more examples to `examples/`
- [ ] Improve docstring coverage (target: 95%)
- [ ] Create video tutorials
- [ ] Write blog post on AI agents

**Blockers:**
- None

**Next Steps:**
1. Review docstring coverage report
2. Add examples for new features
3. Plan video tutorial outline

---

## Backlog

### Research & Exploration

- [ ] **Crypto asset support** - Research Binance API integration
- [ ] **Futures trading** - Evaluate futures data providers
- [ ] **Reinforcement learning** - Explore RL for strategy optimization
- [ ] **Alternative data** - Investigate sentiment data sources

### Technical Debt

- [ ] **Python 3.12 upgrade** - Test compatibility with Python 3.12
- [ ] **Dependency audit** - Update all dependencies to latest stable
- [ ] **Test refactoring** - Reduce test duplication
- [ ] **Type hint coverage** - Add type hints to legacy code

### Infrastructure

- [ ] **CI/CD improvements** - Add automated deployment
- [ ] **Monitoring dashboard** - Set up Grafana for metrics
- [ ] **Alerting system** - Integrate PagerDuty for critical alerts
- [ ] **Backup strategy** - Automated PostgreSQL backups

---

## Completed (Last 30 Days)

- ✅ **2025-11-28:** LangGraph agent orchestration implemented
- ✅ **2025-11-25:** Alpaca broker integration complete
- ✅ **2025-11-22:** PostgreSQL + Redis infrastructure deployed
- ✅ **2025-11-20:** Streamlit dashboard v1 launched
- ✅ **2025-11-18:** Validation command system created
- ✅ **2025-11-15:** PRP workflow established

---

## Blocked Tasks

**None currently**

---

## Sprint Goals (Current Week)

### Week of 2025-11-30

**Primary Goal:** Complete options trading strategies (PRP-2025-11-25-options)

**Tasks:**
1. ✅ Design options data structures
2. ✅ Integrate Alpaca options API
3. 🔄 Write unit tests for options pricing
4. ⬜ Test covered call strategy in sandbox
5. ⬜ Add documentation and examples

**Stretch Goal:** Start ensemble ML implementation

---

## Quick Commands

```bash
# Check task status
cat TASK.md

# Update task status
# Edit this file and commit changes

# Generate new PRP for task
/generate-prp

# Execute active PRP
/execute-prp PRPs/PRP-2025-11-25-options.md

# Run validation
/validate
```

---

## Task Management Rules

1. **Update daily** - Keep task status current
2. **Link PRPs** - Every task should reference a PRP
3. **Track blockers** - Document blockers immediately
4. **Celebrate wins** - Move completed tasks to "Completed" section
5. **Limit WIP** - Max 3 "In Progress" tasks at once

---

## Critical Reminders

- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot, or Claude
- **API keys in `.env` only** - Never hardcode
- **Backward compatibility** - Don't break original Alphalens API
- **Test first** - Sandbox before production
- **Document everything** - Update docs with every feature

---

## Next Review

**Date:** 2025-12-07 (Weekly sprint review)
**Agenda:**
1. Review completed tasks
2. Adjust priorities based on stakeholder feedback
3. Plan next sprint goals
4. Update roadmap in PLANNING.md
