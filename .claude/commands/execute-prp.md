# Alpha-Lens PRP Execution Command

Execute a Production-Ready Plan (PRP) in 6 systematic phases with validation gates.

## CRITICAL RULES
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter, or Anthropic Claude
- API keys in `.env` only, never hardcoded
- Backward compatibility with original Alphalens API is non-negotiable

## Pre-Execution Checklist

Before starting:

- [ ] PRP document reviewed and approved
- [ ] Working branch created: `feature/{prp-name}`
- [ ] All dependencies installed: `pip install -e .[agents,test]`
- [ ] Environment variables configured in `.env`
- [ ] Git status clean (all changes committed)

## Phase 1: Setup & Scaffolding (10-15 min)

### Create file structure
```bash
# Create module files from PRP
mkdir -p alphalens/{module_name}
touch alphalens/{module_name}/__init__.py
touch alphalens/{module_name}/{feature_file}.py

# Create test files
mkdir -p tests/test_{module_name}
touch tests/test_{module_name}/test_{feature_file}.py
```

### Initialize boilerplate
```python
# alphalens/{module}/{file}.py
"""
{Module description from PRP}

CRITICAL: NO OpenAI dependencies. Use DeepSeek/Qwen/Moonshot/Claude.
"""
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Implementation follows...
```

### Update imports
```python
# alphalens/{module}/__init__.py
from .{feature_file} import {public_function}

__all__ = ["{public_function}"]
```

**Phase 1 Gate:** File structure matches PRP, boilerplate compiles without errors.

## Phase 2: Core Implementation (2-4 hours)

### Implement main logic

Follow PRP technical design exactly:

1. **Type hints required** for all functions
2. **Docstrings required** with examples
3. **Error handling** for edge cases
4. **Logging** at INFO level for key operations

### Example structure
```python
def core_function(
    data: pd.DataFrame,
    config: Dict[str, Any],
    llm_provider: str = "deepseek",  # NOT openai!
) -> pd.DataFrame:
    """
    Brief description.

    Args:
        data: Input dataframe with columns [...]
        config: Configuration dict with keys [...]
        llm_provider: LLM provider (deepseek, qwen, moonshot, claude)

    Returns:
        Processed dataframe with columns [...]

    Raises:
        ValueError: If data is empty
        KeyError: If required config keys missing

    Example:
        >>> df = core_function(input_df, {"param": "value"})
        >>> assert "result" in df.columns
    """
    logger.info(f"Processing {len(data)} rows with {llm_provider}")

    # Validate inputs
    if data.empty:
        raise ValueError("Input data cannot be empty")

    # Implementation...

    return result
```

**Phase 2 Gate:** Core function implements PRP design, passes basic smoke test.

## Phase 3: Integration (1-2 hours)

### Connect to existing modules

1. **Import in parent module**
   ```python
   # alphalens/{parent}/__init__.py
   from .{new_module} import {function}
   ```

2. **Update orchestrator** (if agent feature)
   ```python
   # alphalens/orchestrator/graph.py
   from alphalens.agents.{new_agent} import {AgentClass}

   # Add to graph...
   ```

3. **Configuration integration**
   ```python
   # Config in .env
   NEW_FEATURE_ENABLED=true
   LLM_PROVIDER=deepseek  # NOT openai!
   ```

**Phase 3 Gate:** Integration compiles, manual test shows data flows correctly.

## Phase 4: Testing (2-3 hours)

### Unit Tests

```python
# tests/test_{module}/test_{feature}.py
import pytest
from alphalens.{module}.{file} import {function}

class Test{FeatureName}:
    def test_basic_functionality(self):
        """Test happy path."""
        result = {function}(test_data, config)
        assert result is not None
        assert len(result) > 0

    def test_edge_case_empty_input(self):
        """Test with empty dataframe."""
        with pytest.raises(ValueError):
            {function}(pd.DataFrame(), config)

    def test_invalid_llm_provider(self):
        """Test rejects OpenAI (not allowed)."""
        with pytest.raises(ValueError, match="OpenAI not allowed"):
            {function}(data, {"llm_provider": "openai"})

    @pytest.mark.integration
    def test_with_live_data(self):
        """Test with real market data (sandbox)."""
        # Uses Alpaca sandbox...
        pass
```

### Run tests
```bash
# Unit tests
pytest tests/test_{module}/ -v

# With coverage
pytest tests/test_{module}/ --cov=alphalens.{module} --cov-report=term-missing

# Integration tests
pytest tests/test_{module}/ -v -m integration
```

**Phase 4 Gate:** All tests pass, coverage >90%, no flake8 violations.

## Phase 5: Documentation (1 hour)

### Update documentation

1. **README.md**
   ```markdown
   ## New Feature: {Feature Name}

   {Brief description}

   ### Usage
   ```python
   from alphalens.{module} import {function}
   result = {function}(data, config)
   ```

   ### Configuration
   Set in `.env`:
   ```
   NEW_FEATURE_ENABLED=true
   ```
   ```

2. **Examples**
   ```python
   # examples/{feature}_example.py
   """
   Example usage of {feature}.

   CRITICAL: Uses DeepSeek, not OpenAI.
   """
   from alphalens.{module} import {function}

   # Example code...
   ```

3. **CHANGELOG.md**
   ```markdown
   ## [Unreleased]

   ### Added
   - {Feature description} ({PRP-YYYY-MM-DD-name})
   ```

**Phase 5 Gate:** Documentation builds without errors, examples run successfully.

## Phase 6: Validation & Review (30 min - 1 hour)

### Run full validation

```bash
# Run complete validation suite
/validate

# Should pass all 6 validation phases
```

### Pre-merge checklist

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No flake8 violations (`flake8 alphalens/`)
- [ ] Coverage >90% (`pytest --cov`)
- [ ] No hardcoded secrets (`grep -r "sk-" alphalens/`)
- [ ] No OpenAI dependencies (`grep -r "openai" requirements*.txt`)
- [ ] Documentation complete
- [ ] CHANGELOG.md updated
- [ ] Examples work
- [ ] Git commit messages descriptive

### Create Pull Request

```bash
# Commit changes
git add .
git commit -m "feat({module}): {brief description}

Implements PRP-YYYY-MM-DD-{name}

- {change 1}
- {change 2}
- {change 3}

Closes #{issue_number}"

# Push to remote
git push origin feature/{prp-name}

# Create PR (via GitHub CLI or web)
gh pr create --title "feat({module}): {description}" --body "$(cat PRPs/PRP-YYYY-MM-DD-{name}.md)"
```

**Phase 6 Gate:** All validation checks pass, PR created.

## Post-Execution

### Monitor deployment

1. **Tag release** (if merging to master)
   ```bash
   git tag -a v1.1.0 -m "Release {feature}"
   git push origin v1.1.0
   ```

2. **Update TASK.md**
   ```markdown
   ## Completed
   - [x] {Feature name} (PRP-YYYY-MM-DD-{name})
   ```

3. **Update PLANNING.md**
   ```markdown
   ## Completed Features
   - {Feature name} - {date} (PRP-YYYY-MM-DD-{name})
   ```

## Rollback Procedure

If issues found post-merge:

```bash
# Create hotfix branch
git checkout -b hotfix/{issue}

# Revert problematic commit
git revert {commit_hash}

# Or restore from tag
git checkout v1.0.9 -- alphalens/{module}/

# Test, commit, create emergency PR
git commit -m "hotfix: rollback {feature} due to {issue}"
```

## Usage

```bash
# Execute PRP
/execute-prp PRPs/PRP-2025-11-30-feature.md

# Execute specific phase only
/execute-prp PRPs/PRP-2025-11-30-feature.md --phase=3

# Dry-run (show what would be executed)
/execute-prp PRPs/PRP-2025-11-30-feature.md --dry-run
```

## Success Metrics

| Phase | Duration | Success Criteria |
|-------|----------|------------------|
| 1. Setup | 10-15 min | Files created, imports work |
| 2. Core | 2-4 hours | Function implements PRP spec |
| 3. Integration | 1-2 hours | Connects to existing modules |
| 4. Testing | 2-3 hours | >90% coverage, all pass |
| 5. Docs | 1 hour | Examples run, README updated |
| 6. Validation | 30-60 min | All validation phases pass |

**Total:** 6-10 hours for typical feature PRP
