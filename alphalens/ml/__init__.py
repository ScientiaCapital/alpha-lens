"""
Advanced machine learning models for trading.

Includes:
- Ensemble methods (XGBoost, LightGBM, CatBoost, Random Forest)
- Deep learning (LSTM, GRU, Transformers)
- AutoML for hyperparameter optimization
"""

from alphalens.ml.ensemble import EnsemblePredictor
from alphalens.ml.deep_learning import LSTMPredictor
from alphalens.ml.automl import AutoMLOptimizer

__all__ = [
    "EnsemblePredictor",
    "LSTMPredictor",
    "AutoMLOptimizer",
]
