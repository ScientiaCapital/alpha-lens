"""
Ensemble machine learning models.

Implements:
- XGBoost
- LightGBM
- CatBoost
- Random Forest
- Stacking ensemble
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from loguru import logger

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not installed. Run: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not installed. Run: pip install lightgbm")

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    logger.warning("CatBoost not installed. Run: pip install catboost")

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple gradient boosting models.

    Use this as the **first step** into advanced ML - excellent for:
    - Factor ranking
    - Strategy selection
    - Risk prediction
    - Entry/exit signals
    """

    def __init__(
        self,
        task: str = "classification",  # or "regression"
        models: Optional[List[str]] = None,
        voting: str = "soft"  # "soft" or "hard"
    ):
        """
        Initialize ensemble predictor.

        Args:
            task: "classification" or "regression"
            models: List of models to use (None = all available)
            voting: Voting method for ensemble
        """
        self.task = task
        self.voting = voting
        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        self.feature_names: Optional[List[str]] = None
        self.is_fitted = False

        # Select models
        if models is None:
            models = []
            if XGBOOST_AVAILABLE:
                models.append("xgboost")
            if LIGHTGBM_AVAILABLE:
                models.append("lightgbm")
            if CATBOOST_AVAILABLE:
                models.append("catboost")
            models.append("random_forest")

        self.model_names = models
        logger.info(f"Ensemble predictor initialized with models: {models}")

    def _create_models(self) -> Dict[str, Any]:
        """Create model instances."""
        models = {}

        for name in self.model_names:
            if name == "xgboost" and XGBOOST_AVAILABLE:
                if self.task == "classification":
                    models[name] = xgb.XGBClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        random_state=42
                    )
                else:
                    models[name] = xgb.XGBRegressor(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        random_state=42
                    )

            elif name == "lightgbm" and LIGHTGBM_AVAILABLE:
                if self.task == "classification":
                    models[name] = lgb.LGBMClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        random_state=42,
                        verbose=-1
                    )
                else:
                    models[name] = lgb.LGBMRegressor(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        random_state=42,
                        verbose=-1
                    )

            elif name == "catboost" and CATBOOST_AVAILABLE:
                if self.task == "classification":
                    models[name] = cb.CatBoostClassifier(
                        iterations=100,
                        depth=6,
                        learning_rate=0.1,
                        random_state=42,
                        verbose=False
                    )
                else:
                    models[name] = cb.CatBoostRegressor(
                        iterations=100,
                        depth=6,
                        learning_rate=0.1,
                        random_state=42,
                        verbose=False
                    )

            elif name == "random_forest":
                if self.task == "classification":
                    models[name] = RandomForestClassifier(
                        n_estimators=100,
                        max_depth=6,
                        random_state=42
                    )
                else:
                    models[name] = RandomForestRegressor(
                        n_estimators=100,
                        max_depth=6,
                        random_state=42
                    )

        return models

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validation_split: float = 0.2,
        time_series: bool = True
    ) -> Dict[str, float]:
        """
        Train ensemble models.

        Args:
            X: Feature matrix
            y: Target variable
            validation_split: Validation set size
            time_series: Whether to use time series split

        Returns:
            Validation scores for each model
        """
        logger.info(f"Training ensemble on {len(X)} samples with {len(X.columns)} features")

        self.feature_names = list(X.columns)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

        # Split data
        if time_series:
            # Time series split (no shuffling)
            split_idx = int(len(X) * (1 - validation_split))
            X_train = X_scaled.iloc[:split_idx]
            X_val = X_scaled.iloc[split_idx:]
            y_train = y.iloc[:split_idx]
            y_val = y.iloc[split_idx:]
        else:
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=validation_split, random_state=42
            )

        # Create and train models
        self.models = self._create_models()
        scores = {}

        for name, model in self.models.items():
            logger.info(f"Training {name}...")

            # Train
            model.fit(X_train, y_train)

            # Validate
            y_pred = model.predict(X_val)

            if self.task == "classification":
                score = accuracy_score(y_val, y_pred)
                scores[name] = score
                logger.info(f"{name} accuracy: {score:.4f}")
            else:
                from sklearn.metrics import r2_score
                score = r2_score(y_val, y_pred)
                scores[name] = score
                logger.info(f"{name} R²: {score:.4f}")

        self.is_fitted = True
        logger.info("Ensemble training complete")

        return scores

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using ensemble.

        Args:
            X: Feature matrix

        Returns:
            Predictions (averaged across models)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # Scale features
        X_scaled = self.scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

        # Get predictions from each model
        predictions = []
        for name, model in self.models.items():
            pred = model.predict(X_scaled)
            predictions.append(pred)

        # Average predictions
        ensemble_pred = np.mean(predictions, axis=0)

        if self.task == "classification":
            # Round to nearest class
            ensemble_pred = np.round(ensemble_pred).astype(int)

        return ensemble_pred

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities (classification only).

        Args:
            X: Feature matrix

        Returns:
            Probability predictions
        """
        if self.task != "classification":
            raise ValueError("predict_proba only available for classification")

        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        # Scale features
        X_scaled = self.scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

        # Get probabilities from each model
        probas = []
        for name, model in self.models.items():
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X_scaled)
                probas.append(proba)

        # Average probabilities
        ensemble_proba = np.mean(probas, axis=0)

        return ensemble_proba

    def get_feature_importance(self, top_k: int = 20) -> pd.DataFrame:
        """
        Get feature importance across models.

        Args:
            top_k: Number of top features to return

        Returns:
            DataFrame with feature importances
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        importance_dict = {}

        for name, model in self.models.items():
            if hasattr(model, "feature_importances_"):
                importance_dict[name] = model.feature_importances_

        if not importance_dict:
            logger.warning("No feature importances available")
            return pd.DataFrame()

        importance_df = pd.DataFrame(importance_dict, index=self.feature_names)

        # Average importance across models
        importance_df["mean"] = importance_df.mean(axis=1)
        importance_df = importance_df.sort_values("mean", ascending=False)

        return importance_df.head(top_k)

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model performance.

        Args:
            X: Feature matrix
            y: True labels

        Returns:
            Performance metrics
        """
        predictions = self.predict(X)

        if self.task == "classification":
            return {
                "accuracy": accuracy_score(y, predictions),
                "precision": precision_score(y, predictions, average="weighted"),
                "recall": recall_score(y, predictions, average="weighted"),
                "f1": f1_score(y, predictions, average="weighted")
            }
        else:
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

            return {
                "mse": mean_squared_error(y, predictions),
                "mae": mean_absolute_error(y, predictions),
                "r2": r2_score(y, predictions)
            }
