"""
Prediction engine for stock price ranges.
Uses LSTM model and technical indicators to predict price ranges.
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import numpy as np

from src.technical.indicators import TechnicalIndicators
from src.technical.data_loader import DataLoader
from src.technical.lstm_model import LSTMModel

logger = logging.getLogger(__name__)


class PricePredictor:
    """Predicts stock price range for next 5-min window using LSTM and sentiment."""

    def __init__(self, config: Dict, model_path: Optional[str] = None):
        """
        Initialize PricePredictor.

        Args:
            config: Configuration dictionary
            model_path: Path to LSTM model
        """
        self.config = config
        self.indicators = TechnicalIndicators(config)
        self.data_loader = DataLoader(config)
        self.lstm_model = LSTMModel(config, model_path=model_path)
        self.lookback_window = config.get('lstm', {}).get('lookback_window', 20)
        self.min_confidence = config.get('prediction', {}).get('min_confidence', 0.5)

    def predict(self, symbol: str, sentiment_score: float = 0.0, 
                price_df: Optional[object] = None) -> Optional[Dict]:
        """
        Predict price range for next 5-min window.

        Args:
            symbol: Stock symbol
            sentiment_score: Sentiment score (-1 to 1)
            price_df: Optional pre-loaded price DataFrame

        Returns:
            Dict with predicted_low, predicted_high, confidence, or None if error
        """
        try:
            # Fetch price data if not provided
            if price_df is None:
                price_df = self.data_loader.fetch_recent_candles(
                    symbol,
                    candle_count=self.lookback_window + 10,
                    interval='5m'
                )

            if price_df is None or len(price_df) < self.lookback_window:
                logger.warning(f"Insufficient price data for {symbol}")
                return None

            # Validate data
            is_valid, msg = self.data_loader.validate_data_integrity(price_df)
            if not is_valid:
                logger.warning(f"Data validation failed for {symbol}: {msg}")
                return None

            # Compute technical indicators
            price_df = self.indicators.compute_all_indicators(price_df)

            # Normalize indicators
            price_df = self.indicators.normalize_indicators(price_df)

            # Merge sentiment
            price_df = self.data_loader.merge_with_sentiment(price_df, sentiment_score)

            # Get feature vector
            feature_vector = self.indicators.get_feature_vector(price_df, sentiment_score)

            if feature_vector is None:
                logger.warning(f"Failed to create feature vector for {symbol}")
                return None

            # Make prediction
            prediction = self.lstm_model.predict_single(feature_vector)

            if prediction is None:
                logger.warning(f"LSTM prediction failed for {symbol}")
                return None

            predicted_low, predicted_high = prediction

            # Calculate confidence based on model state and feature variance
            confidence = self._calculate_confidence(feature_vector, price_df)

            # Get current price for reference
            current_price = price_df.iloc[-1]['close']

            # Validate prediction sanity
            if predicted_low > current_price or predicted_high < current_price:
                logger.debug(f"Prediction sanity check warning for {symbol}")
                confidence *= 0.8  # Reduce confidence for unusual predictions

            result = {
                'symbol': symbol,
                'predicted_low': float(predicted_low),
                'predicted_high': float(predicted_high),
                'current_price': float(current_price),
                'confidence': float(confidence),
                'sentiment_score': sentiment_score,
                'predicted_at': datetime.now().isoformat(),
                'model_trained': self.lstm_model.is_trained,
            }

            logger.info(f"Prediction for {symbol}: ${predicted_low:.2f}-${predicted_high:.2f} (confidence: {confidence:.2f})")

            return result

        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {e}")
            return None

    def _calculate_confidence(self, feature_vector: np.ndarray, 
                             price_df: object) -> float:
        """
        Calculate confidence score for prediction.

        Args:
            feature_vector: Feature vector used for prediction
            price_df: DataFrame with price data

        Returns:
            Confidence score (0 to 1)
        """
        base_confidence = 0.5

        if not self.lstm_model.is_trained:
            base_confidence = 0.3  # Lower confidence if model not trained

        # Adjust based on feature variance (more variance = more confidence in trend)
        try:
            feature_variance = np.var(feature_vector)
            variance_factor = min(1.0, feature_variance / 0.5)
            base_confidence += variance_factor * 0.3
        except:
            pass

        # Adjust based on volume (higher volume = more confidence)
        try:
            if 'volume' in price_df.columns:
                recent_volume = price_df.iloc[-5:]['volume'].mean()
                historical_volume = price_df.iloc[:-5]['volume'].mean()
                if historical_volume > 0:
                    volume_ratio = recent_volume / historical_volume
                    if volume_ratio > 1.5:
                        base_confidence += 0.1
        except:
            pass

        return min(1.0, base_confidence)

    def train_model(self, symbol: str, data_df: Optional[object] = None,
                   retrain: bool = False) -> bool:
        """
        Train LSTM model for a specific stock.

        Args:
            symbol: Stock symbol
            data_df: Optional pre-loaded data
            retrain: Force retraining

        Returns:
            True if training successful, False otherwise
        """
        try:
            logger.info(f"Training LSTM model for {symbol}")

            # Fetch historical data (1-2 weeks for 5-min candles)
            if data_df is None:
                data_df = self.data_loader.fetch_price_data(symbol, interval='5m', period='7d')

            if data_df is None or len(data_df) < 100:
                logger.warning(f"Not enough data for training {symbol}")
                return False

            # Compute indicators
            data_df = self.indicators.compute_all_indicators(data_df)
            data_df = self.indicators.normalize_indicators(data_df)

            # Create training windows
            lookback = self.config.get('lstm', {}).get('lookback_window', 20)
            X, y = self.data_loader.create_training_windows(data_df, lookback=lookback, step=1)

            if not X or not y:
                logger.warning(f"No training windows created for {symbol}")
                return False

            # Convert to numpy arrays
            X_train = np.array(X, dtype=np.float32)
            y_train = np.array(y, dtype=np.float32)

            logger.info(f"Training data shape: X={X_train.shape}, y={y_train.shape}")

            # Train model
            history = self.lstm_model.train(X_train, y_train)

            if history is None:
                logger.warning("Model training failed")
                return False

            logger.info(f"Training completed for {symbol}")

            return True

        except Exception as e:
            logger.error(f"Error training model for {symbol}: {e}")
            return False

    def get_prediction_metadata(self) -> Dict:
        """Get metadata about prediction capability."""
        return {
            'model_trained': self.lstm_model.is_trained,
            'lookback_window': self.lookback_window,
            'min_confidence': self.min_confidence,
            'prediction_window_minutes': self.config.get('prediction', {}).get('window_minutes', 5),
            'indicators_available': self.indicators.indicators,
        }
