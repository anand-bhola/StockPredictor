"""
Data loader for technical analysis.
Fetches OHLCV data and merges with sentiment scores.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads and prepares data for technical analysis and LSTM prediction."""

    def __init__(self, config: Dict):
        """
        Initialize DataLoader.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.lookback = config.get('technical', {}).get('lookback_period', 100)

    def fetch_price_data(self, symbol: str, interval: str = '5m', period: str = '7d') -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from Yahoo Finance.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Interval ('1m', '5m', '15m', '1h', '1d')
            period: Period ('1d', '5d', '7d', '1mo', '3mo', '1y')

        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            logger.info(f"Fetching {interval} data for {symbol} ({period})")

            ticker = yf.Ticker(symbol)
            df = ticker.history(interval=interval, period=period)

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Rename columns to lowercase for consistency
            df.columns = df.columns.str.lower()

            # Convert to proper types
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

            # Remove rows with NaN prices
            df = df.dropna(subset=['open', 'high', 'low', 'close'])

            # Sort by index (chronological)
            df = df.sort_index()

            logger.info(f"Fetched {len(df)} candles for {symbol}")

            return df

        except Exception as e:
            logger.error(f"Error fetching price data for {symbol}: {e}")
            return None

    def fetch_recent_candles(self, symbol: str, candle_count: int = 100, 
                            interval: str = '5m') -> Optional[pd.DataFrame]:
        """
        Fetch the most recent N candles.

        Args:
            symbol: Stock symbol
            candle_count: Number of candles to fetch
            interval: Interval ('5m', '15m', etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Estimate period needed
            if interval == '5m':
                # Roughly 100 candles = 500 minutes = ~8 hours, 1 trading day
                period = '7d'
            elif interval == '15m':
                period = '7d'
            elif interval == '1h':
                period = '60d'
            else:
                period = '1y'

            df = self.fetch_price_data(symbol, interval=interval, period=period)

            if df is None or len(df) == 0:
                return None

            # Return most recent N candles
            return df.tail(candle_count).copy()

        except Exception as e:
            logger.error(f"Error fetching recent candles: {e}")
            return None

    def create_training_windows(self, df: pd.DataFrame, lookback: int = 20, 
                               step: int = 1) -> Tuple[List[List[float]], List[Tuple[float, float]]]:
        """
        Create sliding windows for LSTM training.

        Args:
            df: DataFrame with price data and indicators
            lookback: Number of historical candles to use
            step: Step size for sliding window

        Returns:
            Tuple of (X, y) where X is list of windows and y is list of (low, high) targets
        """
        X = []
        y = []

        # Need at least lookback + 1 rows
        if len(df) < lookback + 1:
            logger.warning(f"Not enough data for windows. Need {lookback + 1}, got {len(df)}")
            return [], []

        for i in range(0, len(df) - lookback, step):
            # Input: lookback candles
            window = df.iloc[i:i + lookback]
            X.append(self._prepare_window_features(window))

            # Target: next candle's low and high
            next_candle = df.iloc[i + lookback]
            target_low = next_candle['low']
            target_high = next_candle['high']
            y.append((target_low, target_high))

        logger.info(f"Created {len(X)} training windows from {len(df)} candles")

        return X, y

    def _prepare_window_features(self, window_df: pd.DataFrame) -> List[float]:
        """Prepare feature vector from a window of data."""
        features = []

        # Add normalized price data
        closes = window_df['close'].values
        if len(closes) > 0:
            # Normalize by dividing by first close (relative changes)
            normalized_closes = closes / closes[0]
            features.extend(normalized_closes.tolist())

        # Add indicator data
        indicator_cols = [col for col in window_df.columns if col.endswith('_norm')]
        for col in sorted(indicator_cols):
            values = window_df[col].fillna(0).values
            features.extend(values.tolist())

        return features

    def merge_with_sentiment(self, price_df: pd.DataFrame, sentiment_score: float) -> pd.DataFrame:
        """
        Add sentiment score to price data.

        Args:
            price_df: DataFrame with price and technical data
            sentiment_score: Latest sentiment score (-1 to 1)

        Returns:
            DataFrame with sentiment column added
        """
        df = price_df.copy()

        # Add sentiment column (constant for all rows - latest sentiment)
        df['sentiment'] = sentiment_score
        df['sentiment_norm'] = (sentiment_score + 1) / 2  # Normalize to [0, 1]

        return df

    def validate_data_integrity(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate data integrity.

        Args:
            df: DataFrame to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if df is None or df.empty:
            return False, "DataFrame is empty"

        required_cols = ['open', 'high', 'low', 'close']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return False, f"Missing columns: {missing}"

        # Check for price anomalies
        if (df['high'] < df['low']).any():
            return False, "High < Low detected (data error)"

        if (df['close'] > df['high']).any() or (df['close'] < df['low']).any():
            return False, "Close outside high/low range"

        # Check for reasonable price ranges
        price_range = df['close'].max() / df['close'].min()
        if price_range > 10:
            logger.warning(f"Large price range detected: {price_range}x")

        return True, "Data valid"

    def get_latest_candle(self, df: pd.DataFrame) -> Optional[Dict]:
        """Get the latest candle as a dictionary."""
        if df.empty:
            return None

        latest = df.iloc[-1]
        return {
            'timestamp': df.index[-1],
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'volume': latest.get('volume', 0),
        }

    def resample_to_interval(self, df: pd.DataFrame, interval: str = '15min') -> pd.DataFrame:
        """
        Resample OHLCV data to different interval.

        Args:
            df: DataFrame with OHLCV data
            interval: Target interval ('5min', '15min', '1h', '1d')

        Returns:
            Resampled DataFrame
        """
        try:
            resampled = df.resample(interval).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })

            # Remove rows with NaN
            resampled = resampled.dropna()

            return resampled

        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            return df
