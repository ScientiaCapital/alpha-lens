"""
Deep learning models for time series prediction.

Implements:
- LSTM (Long Short-Term Memory)
- GRU (Gated Recurrent Unit)
- Temporal Convolutional Networks
"""

from typing import Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from loguru import logger

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. Run: pip install torch")


if PYTORCH_AVAILABLE:
    class LSTMModel(nn.Module):
        """LSTM neural network for time series."""

        def __init__(
            self,
            input_size: int,
            hidden_size: int,
            num_layers: int,
            output_size: int,
            dropout: float = 0.2
        ):
            super(LSTMModel, self).__init__()

            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout if num_layers > 1 else 0,
                batch_first=True
            )

            self.fc = nn.Linear(hidden_size, output_size)

        def forward(self, x):
            # Initialize hidden state
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

            # Forward propagate LSTM
            out, _ = self.lstm(x, (h0, c0))

            # Get last output
            out = self.fc(out[:, -1, :])

            return out


    class TimeSeriesDataset(Dataset):
        """Dataset for time series sequences."""

        def __init__(self, X: np.ndarray, y: np.ndarray):
            self.X = torch.FloatTensor(X)
            self.y = torch.FloatTensor(y)

        def __len__(self):
            return len(self.X)

        def __getitem__(self, idx):
            return self.X[idx], self.y[idx]


class LSTMPredictor:
    """
    LSTM predictor for time series forecasting.

    **Phase 2** of advanced ML - use after ensemble methods.

    Best for:
    - Price prediction
    - Market regime detection
    - Sequential pattern recognition
    """

    def __init__(
        self,
        sequence_length: int = 60,
        hidden_size: int = 128,
        num_layers: int = 2,
        learning_rate: float = 0.001,
        dropout: float = 0.2
    ):
        """
        Initialize LSTM predictor.

        Args:
            sequence_length: Length of input sequences
            hidden_size: Number of LSTM hidden units
            num_layers: Number of LSTM layers
            learning_rate: Learning rate for optimizer
            dropout: Dropout rate
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required. Run: pip install torch")

        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.dropout = dropout

        self.model: Optional[LSTMModel] = None
        self.scaler = MinMaxScaler()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"LSTM predictor initialized (device: {self.device})")

    def create_sequences(
        self,
        data: np.ndarray,
        target: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Create sequences for LSTM training.

        Args:
            data: Input data (n_samples, n_features)
            target: Target data (n_samples,)

        Returns:
            Tuple of (X_sequences, y_sequences)
        """
        X = []
        y = [] if target is not None else None

        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])

            if target is not None:
                y.append(target[i + self.sequence_length])

        X = np.array(X)
        y = np.array(y) if y is not None else None

        return X, y

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> List[float]:
        """
        Train LSTM model.

        Args:
            X: Feature matrix
            y: Target variable
            epochs: Number of training epochs
            batch_size: Batch size
            validation_split: Validation set size

        Returns:
            Training loss history
        """
        logger.info(f"Training LSTM on {len(X)} samples")

        # Scale data
        X_scaled = self.scaler.fit_transform(X)

        # Create sequences
        X_seq, y_seq = self.create_sequences(X_scaled, y.values)

        logger.info(f"Created {len(X_seq)} sequences of length {self.sequence_length}")

        # Split into train/val
        split_idx = int(len(X_seq) * (1 - validation_split))
        X_train, X_val = X_seq[:split_idx], X_seq[split_idx:]
        y_train, y_val = y_seq[:split_idx], y_seq[split_idx:]

        # Create datasets
        train_dataset = TimeSeriesDataset(X_train, y_train)
        val_dataset = TimeSeriesDataset(X_val, y_val)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Create model
        input_size = X.shape[1]
        output_size = 1

        self.model = LSTMModel(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            output_size=output_size,
            dropout=self.dropout
        ).to(self.device)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training loop
        train_losses = []

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0.0

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device).unsqueeze(1)

                # Forward pass
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            epoch_loss /= len(train_loader)
            train_losses.append(epoch_loss)

            # Validation
            if (epoch + 1) % 10 == 0:
                val_loss = self._validate(val_loader, criterion)
                logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {epoch_loss:.6f}, Val Loss: {val_loss:.6f}")

        logger.info("LSTM training complete")
        return train_losses

    def _validate(self, val_loader, criterion) -> float:
        """Validate model."""
        self.model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device).unsqueeze(1)

                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()

        val_loss /= len(val_loader)
        return val_loss

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Feature matrix

        Returns:
            Predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")

        # Scale data
        X_scaled = self.scaler.transform(X)

        # Create sequences
        X_seq, _ = self.create_sequences(X_scaled)

        # Predict
        self.model.eval()
        predictions = []

        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_seq).to(self.device)
            outputs = self.model(X_tensor)
            predictions = outputs.cpu().numpy().flatten()

        return predictions

    def save(self, path: str) -> None:
        """Save model."""
        if self.model is None:
            raise ValueError("No model to save")

        torch.save({
            "model_state_dict": self.model.state_dict(),
            "scaler": self.scaler,
            "config": {
                "sequence_length": self.sequence_length,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers
            }
        }, path)

        logger.info(f"Model saved to {path}")

    def load(self, path: str) -> None:
        """Load model."""
        checkpoint = torch.load(path)

        # Load config
        config = checkpoint["config"]
        self.sequence_length = config["sequence_length"]
        self.hidden_size = config["hidden_size"]
        self.num_layers = config["num_layers"]

        # Load scaler
        self.scaler = checkpoint["scaler"]

        # Recreate model
        self.model = LSTMModel(
            input_size=self.scaler.n_features_in_,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            output_size=1
        ).to(self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])

        logger.info(f"Model loaded from {path}")
