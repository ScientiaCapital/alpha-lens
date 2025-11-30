# Alpha-Lens Multi-Phase Validation Command

Execute comprehensive validation across all project layers.

## CRITICAL RULES
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter, or Anthropic Claude
- API keys in `.env` only, never hardcoded
- All changes must preserve backward compatibility with original Alphalens API

## Phase 1: Static Analysis

### Code Quality (pytest + flake8)
```bash
# Run linting
flake8 alphalens/ --max-line-length=100 --exclude=__pycache__,*.pyc,.git

# Type checking (if mypy configured)
mypy alphalens/ --ignore-missing-imports

# Run all tests
pytest tests/ -v --cov=alphalens --cov-report=term-missing
```

### Dependency Audit
```bash
# Check for security vulnerabilities
pip list --outdated
pip check

# Verify no OpenAI dependencies
grep -r "openai" requirements*.txt pyproject.toml || echo "✓ No OpenAI dependencies"
```

## Phase 2: Integration Tests

### Agent System
```bash
# Test AI agent orchestration
pytest tests/test_agents/ -v -m "not live_trading"

# Verify LangGraph coordination
pytest tests/test_orchestrator/ -v
```

### Data Providers
```bash
# Test market data integrations (mock mode)
pytest tests/test_data/ -v --mock-api

# Verify broker connections (sandbox)
pytest tests/test_brokers/ -v --sandbox
```

## Phase 3: Performance Benchmarks

### Latency Tests
```bash
# Factor computation performance
python benchmarks/factor_performance.py

# Agent response times
python benchmarks/agent_latency.py
```

### Memory Profiling
```bash
# Check memory usage with large datasets
python -m memory_profiler benchmarks/memory_stress_test.py
```

## Phase 4: Security Audit

### Secret Detection
```bash
# Scan for hardcoded secrets
grep -rn "sk-" alphalens/ && echo "❌ HARDCODED API KEY FOUND" || echo "✓ No hardcoded secrets"
grep -rn "APCA-API" alphalens/ && echo "❌ HARDCODED ALPACA KEY" || echo "✓ No Alpaca keys"

# Verify .env usage
grep -l "os.getenv\|config\." alphalens/**/*.py | wc -l
```

### Dependency Security
```bash
# Check for known vulnerabilities
pip install safety
safety check --json

# Audit dependency licenses
pip-licenses --format=markdown
```

## Phase 5: Documentation Validation

### API Documentation
```bash
# Check docstring coverage
python scripts/check_docstrings.py --min-coverage=80

# Build docs (if Sphinx configured)
cd docs && make html && cd ..
```

### README Accuracy
- Verify installation instructions work in clean venv
- Test all code examples in README.md
- Confirm API examples are up-to-date

## Phase 6: Final Checklist

**Before merging/deploying:**

- [ ] All tests pass (pytest exit code 0)
- [ ] No flake8 violations
- [ ] No hardcoded API keys or secrets
- [ ] No OpenAI dependencies
- [ ] Agent tests pass (LangGraph orchestration)
- [ ] Performance benchmarks within targets
- [ ] Docstring coverage >80%
- [ ] CHANGELOG.md updated
- [ ] Version bumped in pyproject.toml (if release)
- [ ] Git commit messages follow convention

## Validation Success Criteria

| Phase | Success Metric |
|-------|---------------|
| Static | 0 flake8 errors, pytest >90% coverage |
| Integration | All agent/data tests pass |
| Performance | <500ms factor computation, <2s agent response |
| Security | 0 hardcoded secrets, 0 high-severity CVEs |
| Docs | >80% docstring coverage |
| Final | All checkboxes checked |

## Emergency Rollback Plan

If validation fails:
1. Do NOT merge to master
2. Create hotfix branch: `hotfix/validation-failure-YYYYMMDD`
3. Fix issues identified in validation report
4. Re-run validation from Phase 1
5. Only merge when all phases pass

## Usage

```bash
# Run full validation
/validate

# Run specific phase
pytest tests/ -v --phase=integration

# Generate validation report
python scripts/generate_validation_report.py > validation_report.md
```
