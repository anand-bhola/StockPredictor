"""
Technical analysis indicators module.
Computes standard technical indicators like RSI, MACD, Bollinger Bands, moving averages.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from ta import momentum, trend, volatility, volume

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Computes technical indicators from OHLCV data."""

    def __init__(self, config: Dict):
        """
        Initialize TechnicalIndicators.

        Args:
            config: Configuration dictionary with technical settings
        """
        self.config = config
        self.indicators = config.get('indicators', [
            'RSI', 'MACD', 'Bollinger Bands', 'SMA 20', 'SMA 50', 'SMA 200', 'EMA 12'
        ])
        self.lookback = config.get('lookback_period', 100)
        self.normalize = config.get('normalize', True)

    def compute_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all configured technical indicators.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()

        # Ensure we have minimum data
        if len(df) < 14:
            logger.warning(f"Not enough data for indicators. Need 14 bars, got {len(df)}")
            return df

        try:
            # RSI (Relative Strength Index)
            if 'RSI' in self.indicators:
                df['RSI'] = momentum.rsi(df['close'], window=14)

            # MACD (Moving Average Convergence Divergence)
            if 'MACD' in self.indicators:
                macd = trend.macd(df['close'], window_fast=12, window_slow=26, window_sign=9)
                df['MACD'] = macd
                df['MACD_Signal'] = trend.macd_signal(df['close'], window_fast=12, window_slow=26, window_sign=9)
                df['MACD_Diff'] = trend.macd_diff(df['close'], window_fast=12, window_slow=26, window_sign=9)

            # Bollinger Bands
            if 'Bollinger Bands' in self.indicators:
                bb_high = volatility.bollinger_hband(df['close'], window=20, window_dev=2)
                bb_low = volatility.bollinger_lband(df['close'], window=20, window_dev=2)
                bb_mid = volatility.bollinger_mavg(df['close'], window=20)
                df['BB_High'] = bb_high
                df['BB_Mid'] = bb_mid
                df['BB_Low'] = bb_low

            # Simple Moving Averages
            if 'SMA 20' in self.indicators:
                df['SMA_20'] = df['close'].rolling(window=20).mean()
            if 'SMA 50' in self.indicators:
                df['SMA_50'] = df['close'].rolling(window=50).mean()
            if 'SMA 200' in self.indicators:
                df['SMA_200'] = df['close'].rolling(window=200).mean()

            # Exponential Moving Averages
            if 'EMA 12' in self.indicators:
                df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
            if 'EMA 26' in self.indicators:
                df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()

            # Additional useful indicators
            # ATR (Average True Range)
            df['ATR'] = self._calculate_atr(df)

            # Volume indicators
            if 'volume' in df.columns:
                df['SMA_Volume'] = df['volume'].rolling(window=20).mean()

            logger.debug(f"Computed {len(df.columns)} indicator columns")

        except Exception as e:
            logger.error(f"Error computing indicators: {e}")

        return df

    def normalize_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize indicators to [0, 1] range for ML models.

        Args:
            df: DataFrame with computed indicators

        Returns:
            DataFrame with normalized indicators
        """
        if not self.normalize:
            return df

        df = df.copy()
        indicator_cols = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]

        for col in indicator_cols:
            if col in df.columns and df[col].notna().any():
                try:
                    min_val = df[col].min()
                    max_val = df[col].max()

                    if max_val > min_val:
                        df[f'{col}_norm'] = (df[col] - min_val) / (max_val - min_val)
                    else:
                        df[f'{col}_norm'] = 0.5  # Constant value case

                except Exception as e:
                    logger.debug(f"Error normalizing {col}: {e}")

        return df

    def get_feature_vector(self, df: pd.DataFrame, sentiment_score: float = 0.0) -> Optional[np.ndarray]:
        """
        Create a feature vector for ML models from the latest row.

        Args:
            df: DataFrame with computed indicators
            sentiment_score: Latest sentiment score (-1 to 1)

        Returns:
            Feature vector as numpy array
        """
        if df.empty:
            return None

        latest = df.iloc[-1]
        features = []

        # Add normalized indicators
        normalized_cols = [col for col in df.columns if col.endswith('_norm')]
        for col in sorted(normalized_cols):
            val = latest[col] if col in latest else 0.0
            features.append(val if not np.isnan(val) else 0.0)

        # Add price-based features (normalized)
        if 'close' in df.columns and 'open' in df.columns:
            if not df['close'].empty:
                # Price change ratio
                close = latest['close']
                open_price = latest['open']
                price_change = (close - open_price) / open_price if open_price != 0 else 0
                features.append(np.clip(price_change, -1, 1))  # Clip to [-1, 1]

        # Add sentiment score (scaled to [0, 1])
        sentiment_normalized = (sentiment_score + 1) / 2  # Convert from [-1, 1] to [0, 1]
        features.append(sentiment_normalized)

        return np.array(features, dtype=np.float32)

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close']

        # True range
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Average True Range
        atr = tr.rolling(window=period).mean()

        return atr

    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate that data has minimum requirements for indicators.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if df.empty:
            return False, "DataFrame is empty"

        required_cols = ['open', 'high', 'low', 'close']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return False, f"Missing required columns: {missing}"

        if len(df) < 14:
            return False, f"Not enough data. Need 14+ rows, got {len(df)}"

        # Check for NaN values in required columns
        if df[required_cols].isna().all().any():
            return False, "All values are NaN in some columns"

        return True, "Valid"

    def get_indicator_info(self) -> Dict[str, str]:
        """Get descriptions of computed indicators."""
        info = {
            'RSI': 'Relative Strength Index (0-100, > 70 overbought, < 30 oversold)',
            'MACD': 'MACD line (momentum indicator)',
            'MACD_Signal': 'MACD signal line (exponential moving average)',
            'MACD_Diff': 'MACD histogram (difference)',
            'BB_High': 'Bollinger Band upper limit',
            'BB_Mid': 'Bollinger Band middle (20-day MA)',
            'BB_Low': 'Bollinger Band lower limit',
            'SMA_20': 'Simple Moving Average 20-day',
            'SMA_50': 'Simple Moving Average 50-day',
            'SMA_200': 'Simple Moving Average 200-day',
            'EMA_12': 'Exponential Moving Average 12-day',
            'EMA_26': 'Exponential Moving Average 26-day',
            'ATR': 'Average True Range (volatility measure)',
        }
        return info
