"""
Factor Discovery Agent - Discovers and generates new alpha factors using Claude's reasoning.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger

from alphalens.agents.base import BaseAgent
from alphalens.agents.config import SystemConfig
from alphalens.memory.memory_store import MemoryStore


class FactorDiscoveryAgent(BaseAgent):
    """
    Discovers and generates new alpha factors.

    Uses Claude SDK to:
    - Analyze market patterns
    - Generate factor hypotheses
    - Combine existing factors in novel ways
    - Learn from historical factor performance
    """

    def __init__(self, config: SystemConfig, memory: MemoryStore):
        super().__init__(
            name="factor_discovery",
            config=config,
            memory=memory,
            description="an expert quantitative researcher specializing in alpha factor discovery"
        )

    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize factor discovery agent state."""
        return {
            "factors_discovered": 0,
            "factors_tested": 0,
            "successful_factors": [],
            "failed_factors": [],
            "current_hypotheses": [],
            "last_discovery_run": None,
            "action_history": []
        }

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute factor discovery process.

        Args:
            context: Must contain:
                - market_data: DataFrame with price/volume data
                - existing_factors: List of existing factors (optional)
                - focus_area: Area to focus on (optional)

        Returns:
            Dictionary with:
                - new_factors: List of newly discovered factors
                - factor_ideas: List of factor ideas for testing
        """
        logger.info(f"Agent {self.name} executing factor discovery")

        market_data = context.get("market_data")
        existing_factors = context.get("existing_factors", [])
        focus_area = context.get("focus_area")

        if market_data is None:
            logger.warning("No market data provided to factor discovery agent")
            return {"new_factors": [], "factor_ideas": []}

        # Get market regime for context
        market_regime = self.get_global_state().get("current_regime", "unknown")

        # Get historical factor performance to learn from
        factor_history = self.memory.get_factor_history(limit=50)

        # Generate factor ideas using Claude
        factor_ideas = self._generate_factor_ideas(
            market_data=market_data,
            market_regime=market_regime,
            existing_factors=existing_factors,
            factor_history=factor_history,
            focus_area=focus_area
        )

        # Validate and refine factor ideas
        validated_factors = self._validate_factor_ideas(factor_ideas, market_data)

        # Update state
        self.update_state({
            "factors_discovered": self.get_state("factors_discovered") + len(validated_factors),
            "current_hypotheses": [f["name"] for f in validated_factors],
            "last_discovery_run": datetime.utcnow().isoformat()
        })

        self.log_action("factor_discovery", {
            "ideas_generated": len(factor_ideas),
            "factors_validated": len(validated_factors),
            "market_regime": market_regime
        })

        return {
            "new_factors": validated_factors,
            "factor_ideas": factor_ideas
        }

    def _generate_factor_ideas(
        self,
        market_data: pd.DataFrame,
        market_regime: str,
        existing_factors: List[str],
        factor_history: List[Dict],
        focus_area: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate factor ideas using Claude's reasoning.

        Args:
            market_data: Market data for analysis
            market_regime: Current market regime
            existing_factors: List of existing factors
            factor_history: Historical factor performance
            focus_area: Optional focus area (e.g., "momentum", "value")

        Returns:
            List of factor ideas
        """
        # Analyze what's worked historically
        successful_factors = [
            f for f in factor_history
            if f.get("ic_mean", 0) > 0.02  # Good IC threshold
        ]

        # Build context for Claude
        prompt = self._build_discovery_prompt(
            market_regime=market_regime,
            existing_factors=existing_factors,
            successful_factors=successful_factors,
            focus_area=focus_area,
            data_shape=market_data.shape
        )

        # Get Claude's reasoning
        response = self.reason(prompt)

        # Parse Claude's response into factor ideas
        factor_ideas = self._parse_factor_response(response)

        logger.info(f"Generated {len(factor_ideas)} factor ideas")
        return factor_ideas

    def _build_discovery_prompt(
        self,
        market_regime: str,
        existing_factors: List[str],
        successful_factors: List[Dict],
        focus_area: Optional[str],
        data_shape: tuple
    ) -> str:
        """Build the prompt for Claude to generate factor ideas."""
        prompt = f"""You are a quantitative researcher discovering new alpha factors for stock trading.

**Current Context:**
- Market Regime: {market_regime}
- Data Available: {data_shape[0]} stocks, {data_shape[1]} days of history
- Existing Factors: {len(existing_factors)} factors already in use

**Historical Performance:**
We have tested {len(successful_factors)} factors that showed strong predictive power (IC > 0.02):
"""

        # Add top performing factors as examples
        for i, factor in enumerate(successful_factors[:5], 1):
            prompt += f"\n{i}. {factor.get('factor_name', 'Unknown')}: IC={factor.get('ic_mean', 0):.4f}, Returns={factor.get('returns_5d', 0):.2%}"

        if focus_area:
            prompt += f"\n\n**Focus Area:** {focus_area}"

        prompt += """

**Your Task:**
Generate 5-7 novel alpha factor ideas that could predict future stock returns. For each factor:

1. **Name**: Clear, descriptive name
2. **Category**: momentum, value, quality, volatility, or combination
3. **Formula**: Mathematical expression or calculation method
4. **Rationale**: Why this factor might predict returns (economic intuition)
5. **Expected IC**: Estimated information coefficient (0-0.1 scale)
6. **Risk Considerations**: Potential failure modes or when it might not work

**Guidelines:**
- Factors should be implementable with standard price/volume/fundamental data
- Prefer factors that work in the current market regime
- Build on successful patterns from history but add novel twists
- Consider factor combinations and interactions
- Think about economic reasoning, not just statistical patterns

**Format your response as:**
```
FACTOR 1:
Name: [factor name]
Category: [category]
Formula: [mathematical formula or description]
Rationale: [why it works]
Expected IC: [0.XX]
Risks: [when it might fail]

FACTOR 2:
...
```
"""

        return prompt

    def _parse_factor_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse Claude's factor suggestions into structured format.

        Args:
            response: Claude's text response

        Returns:
            List of factor dictionaries
        """
        factors = []
        current_factor = {}

        lines = response.split('\n')
        for line in lines:
            line = line.strip()

            if line.startswith('FACTOR ') and current_factor:
                factors.append(current_factor)
                current_factor = {}

            elif line.startswith('Name:'):
                current_factor['name'] = line.replace('Name:', '').strip()
            elif line.startswith('Category:'):
                current_factor['category'] = line.replace('Category:', '').strip()
            elif line.startswith('Formula:'):
                current_factor['formula'] = line.replace('Formula:', '').strip()
            elif line.startswith('Rationale:'):
                current_factor['rationale'] = line.replace('Rationale:', '').strip()
            elif line.startswith('Expected IC:'):
                ic_str = line.replace('Expected IC:', '').strip()
                try:
                    current_factor['expected_ic'] = float(ic_str)
                except:
                    current_factor['expected_ic'] = 0.02
            elif line.startswith('Risks:'):
                current_factor['risks'] = line.replace('Risks:', '').strip()

        # Add last factor
        if current_factor:
            factors.append(current_factor)

        # Ensure all factors have required fields
        validated_factors = []
        for factor in factors:
            if 'name' in factor and 'formula' in factor:
                validated_factors.append(factor)

        return validated_factors

    def _validate_factor_ideas(
        self,
        factor_ideas: List[Dict[str, Any]],
        market_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Validate that factor ideas are implementable.

        Args:
            factor_ideas: List of factor ideas
            market_data: Market data for validation

        Returns:
            List of validated factors
        """
        validated = []

        for factor in factor_ideas:
            # Basic validation
            if not factor.get('name') or not factor.get('formula'):
                logger.warning(f"Skipping invalid factor: {factor}")
                continue

            # Add metadata
            factor['discovered_at'] = datetime.utcnow().isoformat()
            factor['discovered_by'] = self.name
            factor['status'] = 'awaiting_backtest'

            validated.append(factor)

        logger.info(f"Validated {len(validated)} factors")
        return validated

    def get_top_factors(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing factors from history.

        Args:
            limit: Number of top factors to return

        Returns:
            List of top factors
        """
        all_factors = self.memory.get_factor_history(limit=limit * 2)

        # Sort by IC
        sorted_factors = sorted(
            all_factors,
            key=lambda x: x.get('ic_mean', 0),
            reverse=True
        )

        return sorted_factors[:limit]

    def suggest_factor_combinations(
        self,
        factors: List[Dict],
        n_combinations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest combinations of existing factors.

        Args:
            factors: List of existing factors
            n_combinations: Number of combinations to suggest

        Returns:
            List of factor combination ideas
        """
        if len(factors) < 2:
            return []

        prompt = f"""You have {len(factors)} proven alpha factors. Suggest {n_combinations} ways to combine them into more powerful composite factors.

**Existing Factors:**
"""
        for i, factor in enumerate(factors[:10], 1):
            prompt += f"\n{i}. {factor.get('factor_name', 'Unknown')}: {factor.get('factor_formula', 'N/A')}"

        prompt += """

For each combination, provide:
1. Name: Descriptive name
2. Components: Which factors to combine
3. Method: How to combine them (average, product, z-score, etc.)
4. Rationale: Why this combination might be stronger

Format as:
COMBINATION 1:
Name: [name]
Components: [factor1, factor2, ...]
Method: [combination method]
Rationale: [why it works]
"""

        response = self.reason(prompt)
        combinations = self._parse_factor_response(response)  # Reuse parser

        return combinations
