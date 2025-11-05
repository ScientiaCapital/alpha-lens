"""
AutoML for hyperparameter optimization.
"""

from typing import Dict, Any, Optional
import pandas as pd
from loguru import logger

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not installed. Run: pip install optuna")


class AutoMLOptimizer:
    """
    AutoML optimizer using Optuna.

    Automatically finds best hyperparameters for your models.
    """

    def __init__(self, n_trials: int = 100):
        """
        Initialize AutoML optimizer.

        Args:
            n_trials: Number of optimization trials
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna is required. Run: pip install optuna")

        self.n_trials = n_trials
        self.study: Optional[optuna.Study] = None

        logger.info(f"AutoML optimizer initialized with {n_trials} trials")

    def optimize_ensemble(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        model_type: str = "xgboost"
    ) -> Dict[str, Any]:
        """
        Optimize hyperparameters for ensemble model.

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            model_type: Model to optimize

        Returns:
            Best hyperparameters
        """
        def objective(trial):
            if model_type == "xgboost":
                import xgboost as xgb

                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "min_child_weight": trial.suggest_int("min_child_weight", 1, 7),
                    "gamma": trial.suggest_float("gamma", 0, 0.5),
                    "reg_alpha": trial.suggest_float("reg_alpha", 0, 1.0),
                    "reg_lambda": trial.suggest_float("reg_lambda", 0, 1.0)
                }

                model = xgb.XGBRegressor(**params, random_state=42)

            elif model_type == "lightgbm":
                import lightgbm as lgb

                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 3, 10),
                    "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3),
                    "num_leaves": trial.suggest_int("num_leaves", 20, 150),
                    "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
                    "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                    "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                    "reg_alpha": trial.suggest_float("reg_alpha", 0, 1.0),
                    "reg_lambda": trial.suggest_float("reg_lambda", 0, 1.0)
                }

                model = lgb.LGBMRegressor(**params, random_state=42, verbose=-1)

            else:
                raise ValueError(f"Unknown model type: {model_type}")

            # Train and evaluate
            model.fit(X_train, y_train)
            predictions = model.predict(X_val)

            from sklearn.metrics import mean_squared_error
            mse = mean_squared_error(y_val, predictions)

            return mse

        # Run optimization
        self.study = optuna.create_study(direction="minimize")
        self.study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        logger.info(f"Best MSE: {self.study.best_value:.6f}")
        logger.info(f"Best params: {self.study.best_params}")

        return self.study.best_params
