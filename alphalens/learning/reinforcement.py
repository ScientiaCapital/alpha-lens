"""
Reinforcement learning algorithms for strategy selection.
"""

import numpy as np
from typing import Dict, Any, List, Tuple
from collections import defaultdict
from loguru import logger


class QLearningAgent:
    """
    Q-Learning agent for strategy selection.

    Learns optimal strategy selection based on:
    - Market regime
    - Historical performance
    - Risk metrics
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 0.2,
        exploration_decay: float = 0.995
    ):
        """
        Initialize Q-Learning agent.

        Args:
            learning_rate: Learning rate (alpha)
            discount_factor: Discount factor (gamma)
            exploration_rate: Epsilon for epsilon-greedy
            exploration_decay: Decay rate for exploration
        """
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.epsilon_decay = exploration_decay

        # Q-table: Q[state][action] = value
        self.q_table = defaultdict(lambda: defaultdict(float))

        # Experience buffer
        self.experiences = []

        logger.info("Q-Learning agent initialized")

    def get_state_key(self, state: Dict[str, Any]) -> str:
        """Convert state dict to hashable key."""
        regime = state.get("market_regime", "unknown")
        risk_level = state.get("risk_level", "medium")
        return f"{regime}_{risk_level}"

    def select_action(self, state: Dict[str, Any], available_actions: List[str]) -> str:
        """
        Select action using epsilon-greedy policy.

        Args:
            state: Current state
            available_actions: List of available actions (strategy names)

        Returns:
            Selected action
        """
        state_key = self.get_state_key(state)

        # Exploration
        if np.random.random() < self.epsilon:
            action = np.random.choice(available_actions)
            logger.debug(f"Exploring: selected {action}")
            return action

        # Exploitation - select best action
        q_values = [self.q_table[state_key][a] for a in available_actions]

        if all(q == 0 for q in q_values):
            # All actions have same Q-value, choose randomly
            action = np.random.choice(available_actions)
        else:
            # Choose action with highest Q-value
            best_idx = np.argmax(q_values)
            action = available_actions[best_idx]

        logger.debug(f"Exploiting: selected {action} (Q={q_values[best_idx]:.3f})")
        return action

    def update(
        self,
        state: Dict[str, Any],
        action: str,
        reward: float,
        next_state: Dict[str, Any],
        done: bool = False
    ) -> None:
        """
        Update Q-values based on experience.

        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
        """
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)

        # Current Q-value
        current_q = self.q_table[state_key][action]

        # Max Q-value for next state
        if done:
            max_next_q = 0
        else:
            max_next_q = max(self.q_table[next_state_key].values() or [0])

        # Q-learning update
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q

        # Decay exploration
        self.epsilon *= self.epsilon_decay

        # Store experience
        self.experiences.append({
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done
        })

        logger.debug(f"Q-update: {action} {current_q:.3f} -> {new_q:.3f} (reward={reward:.3f})")

    def get_best_action(self, state: Dict[str, Any], available_actions: List[str]) -> str:
        """Get best action without exploration."""
        state_key = self.get_state_key(state)
        q_values = {a: self.q_table[state_key][a] for a in available_actions}
        return max(q_values, key=q_values.get)


class BanditLearner:
    """
    Multi-armed bandit learner for strategy selection.

    Uses Thompson Sampling for exploration/exploitation.
    """

    def __init__(self, num_arms: int = 10):
        """
        Initialize bandit learner.

        Args:
            num_arms: Number of arms (strategies)
        """
        self.num_arms = num_arms

        # Beta distribution parameters (successes, failures)
        self.alpha = np.ones(num_arms)  # Successes + 1
        self.beta = np.ones(num_arms)   # Failures + 1

        # Track pulls and rewards
        self.pulls = np.zeros(num_arms)
        self.rewards = np.zeros(num_arms)

        logger.info(f"Bandit learner initialized with {num_arms} arms")

    def select_arm(self) -> int:
        """
        Select arm using Thompson Sampling.

        Returns:
            Selected arm index
        """
        # Sample from Beta distribution for each arm
        samples = np.random.beta(self.alpha, self.beta)

        # Select arm with highest sample
        arm = np.argmax(samples)

        return arm

    def update(self, arm: int, reward: float) -> None:
        """
        Update arm statistics.

        Args:
            arm: Arm index
            reward: Reward received (0-1)
        """
        self.pulls[arm] += 1
        self.rewards[arm] += reward

        # Update Beta parameters
        if reward > 0.5:  # Success
            self.alpha[arm] += 1
        else:  # Failure
            self.beta[arm] += 1

        logger.debug(f"Bandit update: arm={arm}, reward={reward:.3f}")

    def get_arm_stats(self) -> Dict[int, Dict[str, float]]:
        """Get statistics for each arm."""
        stats = {}
        for arm in range(self.num_arms):
            if self.pulls[arm] > 0:
                mean_reward = self.rewards[arm] / self.pulls[arm]
            else:
                mean_reward = 0

            stats[arm] = {
                "pulls": int(self.pulls[arm]),
                "mean_reward": mean_reward,
                "alpha": self.alpha[arm],
                "beta": self.beta[arm],
                "estimated_prob": self.alpha[arm] / (self.alpha[arm] + self.beta[arm])
            }

        return stats
