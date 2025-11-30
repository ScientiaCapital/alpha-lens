# Alpha-Lens PRP Generation Command

Generate a Production-Ready Plan (PRP) for implementing new features or changes.

## CRITICAL RULES
- **NO OpenAI models** - Use DeepSeek, Qwen, Moonshot via OpenRouter, or Anthropic Claude
- API keys in `.env` only, never hardcoded
- All features must maintain backward compatibility with original Alphalens API

## PRP Generation Process

### Step 1: Discovery Questions

Ask the user to clarify:

1. **Feature Scope**
   - What problem does this solve?
   - Which module(s) will be affected? (agents, data, strategies, ml, etc.)
   - Is this a new feature, enhancement, or bugfix?

2. **Technical Requirements**
   - Does it require new dependencies?
   - Will it affect existing API contracts?
   - Does it need database migrations?

3. **AI/Agent Considerations**
   - Does this involve AI agents or LangGraph orchestration?
   - Which LLM provider? (DeepSeek, Qwen, Moonshot, Claude)
   - Expected latency/performance targets?

4. **Risk Assessment**
   - Could this break existing strategies?
   - Does it impact production trading systems?
   - Rollback plan needed?

### Step 2: Create PRP Document

Use the template at `PRPs/templates/prp_base.md` and fill in:

```markdown
# PRP-YYYY-MM-DD-{feature-name}

## Executive Summary
[1-2 sentence description]

## Problem Statement
[What problem are we solving?]

## Proposed Solution
[High-level approach]

## Technical Design

### Architecture Changes
- Module: `alphalens/{module}/`
- New files: `{filename}.py`
- Modified files: `{existing_file}.py`

### API Changes
```python
# New public API
def new_function(param: Type) -> ReturnType:
    """Docstring with examples."""
    pass
```

### Dependencies
- New: `package>=1.0.0` (reason)
- Updated: `existing-package>=2.0.0` (reason)

### Database Changes
- None / Schema migration needed

## Implementation Plan

### Phase 1: Core Logic (2-4 hours)
- [ ] Create `alphalens/{module}/{filename}.py`
- [ ] Implement core function
- [ ] Add type hints
- [ ] Write docstrings

### Phase 2: Integration (1-2 hours)
- [ ] Integrate with existing modules
- [ ] Update `__init__.py` exports
- [ ] Add configuration options

### Phase 3: Testing (2-3 hours)
- [ ] Unit tests in `tests/test_{module}/`
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Agent orchestration tests (if applicable)

### Phase 4: Documentation (1 hour)
- [ ] Update README.md
- [ ] Add examples to `examples/`
- [ ] Update CHANGELOG.md

## Testing Strategy

### Unit Tests
```python
def test_new_function():
    result = new_function(test_input)
    assert result == expected_output
```

### Integration Tests
- Test with live data (Alpaca sandbox)
- Test with agent orchestration
- Test error handling

### Performance Benchmarks
- Target: {latency_target}ms
- Memory: {memory_target}MB max
- Throughput: {throughput_target} ops/sec

## Rollback Plan
1. Git revert commit: `git revert {commit_hash}`
2. Restore previous version from tag
3. Emergency hotfix if in production

## Success Criteria
- [ ] All tests pass (pytest >90% coverage)
- [ ] No performance regression
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Validation phases 1-6 pass

## Timeline
- Estimated: {total_hours} hours
- Target completion: {date}
```

### Step 3: Validation Checklist

Before finalizing PRP:

- [ ] All discovery questions answered
- [ ] Technical design is concrete (not abstract)
- [ ] Implementation plan has clear tasks
- [ ] Testing strategy covers edge cases
- [ ] Rollback plan is realistic
- [ ] No OpenAI dependencies introduced
- [ ] API keys remain in `.env` only
- [ ] Backward compatibility maintained

### Step 4: Save PRP

```bash
# Save to PRPs directory with date prefix
cp PRP_draft.md PRPs/PRP-2025-11-30-{feature-name}.md

# Update PLANNING.md to reference this PRP
echo "- [PRP-2025-11-30-{feature-name}](PRPs/PRP-2025-11-30-{feature-name}.md)" >> PLANNING.md
```

## PRP Templates

### For AI Agent Features
Use when adding/modifying agents, orchestration, or LLM integrations.

**Key sections:**
- LLM provider selection (DeepSeek/Qwen/Moonshot/Claude)
- Latency targets (<2s agent response)
- Prompt engineering approach
- Memory/state management

### For Data Integration Features
Use when adding market data providers or broker connections.

**Key sections:**
- API authentication (keys in .env)
- Rate limiting strategy
- Error handling for API failures
- Sandbox testing plan

### For ML Model Features
Use when adding machine learning models or ensemble strategies.

**Key sections:**
- Training data requirements
- Model performance metrics
- Inference latency targets
- Model versioning strategy

## Usage

```bash
# Generate PRP for new feature
/generate-prp

# Generate from template
/generate-prp --template=agent

# Review existing PRP
/generate-prp --review PRPs/PRP-2025-11-30-feature.md
```

## Example PRPs

See existing examples:
- `PRPs/PRP-2025-11-15-multi-asset-support.md`
- `PRPs/PRP-2025-11-20-langgraph-orchestration.md`
- `PRPs/PRP-2025-11-25-alpaca-integration.md`
