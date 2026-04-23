"""
LSTM model for stock price range prediction.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pickle
import os

logger = logging.getLogger(__name__)


class LSTMModel:
    """LSTM model for predicting stock price range (low, high)."""

    def __init__(self, config: Dict, model_path: Optional[str] = None):
        """
        Initialize LSTMModel.

        Args:
            config: Configuration dictionary
            model_path: Path to load existing model
        """
        self.config = config
        self.lstm_config = config.get('lstm', {})
        self.model = None
        self.scaler_params = {}
        self.history = None
        self.is_trained = False

        # Delay model building/loading until first use
        self._model_initialized = False

        if model_path and os.path.exists(model_path):
            # We'll load the model later when needed
            self._pending_model_path = model_path
        else:
            self._pending_model_path = None

    def _ensure_model(self):
        """Ensure the model is built or loaded before use."""
        if not self._model_initialized:
            if self._pending_model_path:
                self.load_model(self._pending_model_path)
            else:
                self._build_model()
            self._model_initialized = True


    def _ensure_tensorflow(self):
        """Ensure TensorFlow is imported when needed."""
        if not hasattr(self, '_tensorflow_imported'):
            try:
                import tensorflow as tf
                from tensorflow import keras
                from tensorflow.keras import layers
                self.tf = tf
                self.keras = keras
                self.layers = layers
                self._tensorflow_imported = True
                # Configure TensorFlow to use less verbose logging
                tf.get_logger().setLevel('ERROR')
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
            except ImportError:
                raise ImportError("TensorFlow is required for LSTM model functionality")

    def _build_model(self):
        """Build LSTM architecture."""
        self._ensure_tensorflow()

        try:
            units_per_layer = self.lstm_config.get('units_per_layer', [128, 64, 32])
            dropout_rate = self.lstm_config.get('dropout_rate', 0.2)

            model = self.keras.Sequential()

            # LSTM layers
            for i, units in enumerate(units_per_layer):
                return_sequences = i < len(units_per_layer) - 1
                model.add(self.layers.LSTM(
                    units=units,
                    return_sequences=return_sequences,
                    activation='relu'
                ))
                if dropout_rate > 0:
                    model.add(self.layers.Dropout(dropout_rate))

            # Output layer (predicts low and high prices)
            model.add(self.layers.Dense(64, activation='relu'))
            model.add(self.layers.Dense(2))  # Output: [predicted_low, predicted_high]

            # Compile
            model.compile(
                optimizer=self.keras.optimizers.Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )

            self.model = model
            logger.info("LSTM model built successfully")
            logger.debug(f"Model summary:\n{model.summary()}")

        except Exception as e:
            logger.error(f"Error building LSTM model: {e}")

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None) -> Optional[Dict]:
        """
        Train the LSTM model.

        Args:
            X_train: Training features (3D array: samples, timesteps, features)
            y_train: Training targets (2D array: samples, 2 for low/high)
            X_val: Validation features
            y_val: Validation targets

        Returns:
            Training history or None if error
        """
        self._ensure_model()

        if self.model is None:
            logger.error("Model not initialized")
            return None

        self._ensure_tensorflow()

        try:
            # Convert to numpy arrays
            X_train = np.array(X_train, dtype=np.float32)
            y_train = np.array(y_train, dtype=np.float32)

            if X_val is not None:
                X_val = np.array(X_val, dtype=np.float32)
                y_val = np.array(y_val, dtype=np.float32)

            # Reshape for LSTM (samples, timesteps, features)
            if len(X_train.shape) == 2:
                X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
            if X_val is not None and len(X_val.shape) == 2:
                X_val = X_val.reshape((X_val.shape[0], 1, X_val.shape[1]))

            logger.info(f"Training LSTM with {len(X_train)} samples")
            logger.info(f"Input shape: {X_train.shape}")

            # Early stopping
            early_stopping = self.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=self.lstm_config.get('early_stopping_patience', 5),
                restore_best_weights=True
            )

            # Train
            epochs = self.lstm_config.get('epochs', 50)
            batch_size = self.lstm_config.get('batch_size', 32)

            if X_val is not None and y_val is not None:
                validation_data = (X_val, y_val)
            else:
                validation_data = None
                validation_split = self.lstm_config.get('validation_split', 0.2)

            history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=validation_data,
                validation_split=validation_split if validation_data is None else None,
                callbacks=[early_stopping],
                verbose=1
            )

            self.history = history
            self.is_trained = True
            logger.info("Model training completed")

            return history.history

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None

    def predict(self, X: np.ndarray) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Make predictions on input data.

        Args:
            X: Input features (2D or 3D array)

        Returns:
            Tuple of (predicted_low, predicted_high) or None if error
        """
        self._ensure_model()

        if self.model is None:
            logger.error("Model not initialized")
            return None

        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow required for prediction")
            return None

        try:
            X = np.array(X, dtype=np.float32)

            # Reshape if needed
            if len(X.shape) == 2:
                X = X.reshape((X.shape[0], 1, X.shape[1]))

            predictions = self.model.predict(X, verbose=0)

            # Extract low and high predictions
            predicted_low = predictions[:, 0]
            predicted_high = predictions[:, 1]

            return predicted_low, predicted_high

        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return None

    def predict_single(self, X: List[float]) -> Optional[Tuple[float, float]]:
        """
        Make a single prediction.

        Args:
            X: Single input feature vector

        Returns:
            Tuple of (predicted_low, predicted_high) or None
        """
        X_array = np.array([X], dtype=np.float32)
        result = self.predict(X_array)

        if result is None:
            return None

        low, high = result
        return float(low[0]), float(high[0])

    def save_model(self, model_path: str):
        """Save model to disk."""
        self._ensure_model()

        if self.model is None:
            logger.warning("No model to save")
            return

        try:
            Path(model_path).parent.mkdir(parents=True, exist_ok=True)

            # Save Keras model
            model_file = Path(model_path) / 'model.h5'
            self.model.save(str(model_file))

            # Save metadata
            metadata = {
                'is_trained': self.is_trained,
                'config': self.lstm_config,
                'scaler_params': self.scaler_params,
            }
            metadata_file = Path(model_path) / 'metadata.pkl'
            with open(metadata_file, 'wb') as f:
                pickle.dump(metadata, f)

            logger.info(f"Model saved to {model_path}")

        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def load_model(self, model_path: str):
        """Load model from disk."""
        self._ensure_model()

        try:
            model_file = Path(model_path) / 'model.h5'
            metadata_file = Path(model_path) / 'metadata.pkl'

            self._ensure_tensorflow()

            # Load Keras model
            if model_file.exists():
                self.model = self.keras.models.load_model(str(model_file))
                logger.info(f"Model loaded from {model_file}")
            else:
                logger.warning(f"Model file not found: {model_file}")
                self._build_model()

            # Load metadata
            if metadata_file.exists():
                with open(metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                    self.is_trained = metadata.get('is_trained', False)
                    self.scaler_params = metadata.get('scaler_params', {})

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._build_model()

    def get_model_summary(self) -> str:
        """Get model architecture summary."""
        if self.model is None:
            return "Model not initialized"

        try:
            summary = []
            self.model.summary(print_fn=lambda x: summary.append(x))
            return '\n'.join(summary)
        except Exception as e:
            return f"Error getting summary: {e}"

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Optional[Dict]:
        """
        Evaluate model on test data.

        Args:
            X_test: Test features
            y_test: Test targets

        Returns:
            Dict with loss and metrics or None
        """
        if self.model is None:
            logger.error("Model not initialized")
            return None

        try:
            X_test = np.array(X_test, dtype=np.float32)
            y_test = np.array(y_test, dtype=np.float32)

            if len(X_test.shape) == 2:
                X_test = X_test.reshape((X_test.shape[0], 1, X_test.shape[1]))

            loss, mae = self.model.evaluate(X_test, y_test, verbose=0)

            logger.info(f"Test Loss (MSE): {loss:.6f}, MAE: {mae:.6f}")

            return {'loss': loss, 'mae': mae}

        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return None
