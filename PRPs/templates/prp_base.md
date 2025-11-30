# PRP-YYYY-MM-DD-{feature-name}

**Status:** Draft | In Progress | Completed
**Priority:** Low | Medium | High | Critical
**Estimated Effort:** {X} hours
**Target Completion:** YYYY-MM-DD
**Owner:** {developer_name}

---

## Executive Summary

{1-2 sentence description of what this PRP delivers and why it matters}

**CRITICAL RULES:**
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter, or Anthropic Claude
- API keys in `.env` only, never hardcoded
- Maintain backward compatibility with original Alphalens API

---

## Problem Statement

### Current State
{What exists today? What are the limitations?}

### Desired State
{What should exist after this PRP is complete?}

### Success Metrics
- {Metric 1}: {Target value}
- {Metric 2}: {Target value}
- {Metric 3}: {Target value}

---

## Technical Design

### Architecture Overview

```
alphalens/
├── {module_name}/          # New or modified module
│   ├── __init__.py
│   ├── {feature_file}.py   # Core implementation
│   └── {helper_file}.py    # Support functions
└── orchestrator/           # If agent-related
    └── {agent_node}.py     # LangGraph integration
```

### Module: `alphalens.{module_name}`

**Purpose:** {One sentence description}

**Key Classes/Functions:**

```python
class {ClassName}:
    """
    {Class description}

    Args:
        param1: {description}
        param2: {description}
        llm_provider: LLM provider (deepseek, qwen, moonshot, claude) - NO openai!

    Example:
        >>> obj = {ClassName}(config)
        >>> result = obj.process(data)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        llm_provider: str = "deepseek",
    ):
        if llm_provider == "openai":
            raise ValueError("OpenAI not allowed. Use DeepSeek, Qwen, Moonshot, or Claude.")
        self.config = config
        self.llm_provider = llm_provider

    def process(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process data with AI agent."""
        pass
```

### API Changes

**New Public API:**
- `{module}.{function_name}(params) -> ReturnType`
- `{module}.{ClassName}`

**Modified API:**
- `{existing_module}.{existing_function}` - Added parameter: `{new_param}`

**Deprecated API:**
- None (or list deprecated functions with migration path)

### Dependencies

**New Dependencies:**
```toml
# Add to pyproject.toml [project.optional-dependencies]
agents = [
    "new-package>=1.0.0",  # Reason for adding
]
```

**Updated Dependencies:**
- `existing-package>=2.0.0` (was 1.x) - Reason for upgrade

**Verify NO OpenAI:**
```bash
grep -r "openai" pyproject.toml requirements*.txt || echo "✓ Clean"
```

### Database/State Changes

- [ ] No database changes
- [ ] Schema migration required: `migrations/YYYY_MM_DD_{name}.sql`
- [ ] Redis cache keys added: `{key_pattern}`

### Configuration

**Environment Variables (in `.env`):**
```bash
# New configuration
NEW_FEATURE_ENABLED=true
FEATURE_LLM_PROVIDER=deepseek  # deepseek, qwen, moonshot, claude
FEATURE_API_KEY=${DEEPSEEK_API_KEY}  # From .env, never hardcoded
```

**Feature Flags:**
- `alpha_lens.config.ENABLE_{FEATURE}` (default: False)

---

## Implementation Plan

### Phase 1: Core Logic (2-4 hours)

- [ ] Create `alphalens/{module}/{feature_file}.py`
- [ ] Implement `{main_function}` with type hints
- [ ] Add docstrings with examples
- [ ] Implement error handling
- [ ] Add logging at INFO level
- [ ] Validate no OpenAI dependencies

**Acceptance Criteria:**
- Function signature matches design
- Docstring coverage 100%
- No flake8 violations

### Phase 2: Integration (1-2 hours)

- [ ] Update `alphalens/{module}/__init__.py` exports
- [ ] Integrate with orchestrator (if agent feature)
- [ ] Add configuration loading from `.env`
- [ ] Connect to existing data pipelines
- [ ] Add feature flag checks

**Acceptance Criteria:**
- Module imports without errors
- Integration tests pass
- Feature can be toggled via config

### Phase 3: Testing (2-3 hours)

- [ ] Unit tests in `tests/test_{module}/test_{feature}.py`
- [ ] Test edge cases (empty data, invalid config)
- [ ] Test OpenAI rejection (should raise ValueError)
- [ ] Integration tests with mock data
- [ ] Performance benchmarks
- [ ] Agent orchestration tests (if applicable)

**Acceptance Criteria:**
- Coverage >90%
- All tests pass (`pytest tests/`)
- No performance regression
- Latency within targets

### Phase 4: Documentation (1 hour)

- [ ] Update README.md with feature description
- [ ] Add usage example to `examples/{feature}_example.py`
- [ ] Update CHANGELOG.md
- [ ] Add API documentation
- [ ] Document configuration options

**Acceptance Criteria:**
- Examples run without errors
- Documentation builds cleanly
- All public APIs documented

### Phase 5: Validation (30-60 min)

- [ ] Run `/validate` command (all 6 phases)
- [ ] No hardcoded secrets
- [ ] No OpenAI dependencies
- [ ] Backward compatibility verified
- [ ] Performance benchmarks pass

**Acceptance Criteria:**
- All validation phases pass
- No critical issues in report

### Phase 6: Deployment (30 min)

- [ ] Create PR with descriptive title
- [ ] Link PRP in PR description
- [ ] Request code review
- [ ] Address review feedback
- [ ] Merge to master
- [ ] Tag release (if applicable)
- [ ] Update TASK.md and PLANNING.md

**Acceptance Criteria:**
- PR approved by reviewer
- CI/CD passes
- Deployed to production (if applicable)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_{module}/test_{feature}.py
import pytest
from alphalens.{module}.{file} import {function}

class Test{FeatureName}:
    """Test suite for {feature}."""

    def test_basic_functionality(self):
        """Test happy path."""
        result = {function}(test_data)
        assert result is not None

    def test_rejects_openai(self):
        """Verify OpenAI is rejected."""
        with pytest.raises(ValueError, match="OpenAI not allowed"):
            {function}(data, llm_provider="openai")

    def test_empty_input(self):
        """Test with empty dataframe."""
        with pytest.raises(ValueError):
            {function}(pd.DataFrame())
```

### Integration Tests

```python
@pytest.mark.integration
def test_with_live_alpaca_sandbox():
    """Test with live Alpaca sandbox API."""
    # Uses sandbox credentials from .env
    result = {function}(live_data, sandbox=True)
    assert result.success
```

### Performance Benchmarks

```python
def test_latency_target():
    """Verify response time <2s for agent."""
    start = time.time()
    result = agent.process(data)
    duration = time.time() - start
    assert duration < 2.0, f"Too slow: {duration}s"
```

---

## Rollback Plan

### Pre-Deployment Snapshot
```bash
# Tag current stable version
git tag -a v1.0.9 -m "Pre-{feature} stable"
git push origin v1.0.9
```

### Rollback Procedure

**If issues found within 24 hours:**
```bash
# Revert commit
git revert {commit_hash}
git push origin master

# Or restore from tag
git checkout v1.0.9 -- alphalens/{module}/
git commit -m "hotfix: rollback {feature}"
```

**If database migration applied:**
```bash
# Run down migration
python scripts/migrate.py down YYYY_MM_DD_{name}
```

**If in production with live trading:**
1. Disable feature flag immediately: `ENABLE_{FEATURE}=false`
2. Revert code changes
3. Notify users of rollback
4. Investigate in staging environment

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance regression | Medium | High | Benchmarks in Phase 3 |
| Breaking API change | Low | Critical | Backward compat tests |
| Data corruption | Low | Critical | Sandbox testing first |
| {Custom risk} | {L/M/H} | {L/M/H} | {Mitigation} |

---

## Success Criteria

**Must Have:**
- [ ] All tests pass (pytest >90% coverage)
- [ ] No OpenAI dependencies
- [ ] No hardcoded API keys
- [ ] Backward compatible with Alphalens 0.x
- [ ] Documentation complete
- [ ] All 6 validation phases pass

**Nice to Have:**
- [ ] Performance improvement over baseline
- [ ] Additional examples in `examples/`
- [ ] Blog post or tutorial

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Core Logic | 2-4 hrs | YYYY-MM-DD | YYYY-MM-DD |
| Integration | 1-2 hrs | YYYY-MM-DD | YYYY-MM-DD |
| Testing | 2-3 hrs | YYYY-MM-DD | YYYY-MM-DD |
| Documentation | 1 hr | YYYY-MM-DD | YYYY-MM-DD |
| Validation | 1 hr | YYYY-MM-DD | YYYY-MM-DD |
| Deployment | 30 min | YYYY-MM-DD | YYYY-MM-DD |

**Total Estimated:** {X-Y} hours
**Target Completion:** YYYY-MM-DD

---

## References

- Original Alphalens docs: https://github.com/quantopian/alphalens
- LangGraph docs: https://langchain-ai.github.io/langgraph/
- Project PLANNING.md: `../PLANNING.md`
- Related PRPs: {list related PRPs}

---

## Approval

**Reviewed By:** {name}
**Approved:** Yes / No
**Date:** YYYY-MM-DD
**Comments:** {feedback}
