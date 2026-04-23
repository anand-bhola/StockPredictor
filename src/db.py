"""
Database module for Stock Predictor application.
Handles SQLite connections, schema creation, and CRUD operations.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: str = "./data/stock_predictor.db"):
        """
        Initialize DatabaseManager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _initialize_schema(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Stocks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    sector TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Stock sentiment table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    sentiment TEXT NOT NULL,
                    score REAL NOT NULL,
                    article_count INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks(id),
                    UNIQUE(stock_id, updated_at)
                )
            """)

            # Sector sentiment table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sector_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    score REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sector, updated_at)
                )
            """)

            # Market sentiment table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sentiment TEXT NOT NULL,
                    score REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    predicted_low REAL NOT NULL,
                    predicted_high REAL NOT NULL,
                    confidence REAL,
                    predicted_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks(id)
                )
            """)

            # Price history (5-min candles)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history_5m (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (stock_id) REFERENCES stocks(id),
                    UNIQUE(stock_id, timestamp)
                )
            """)

            # News cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_id INTEGER,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT,
                    source TEXT,
                    url TEXT UNIQUE,
                    published_at TIMESTAMP,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_id) REFERENCES stocks(id)
                )
            """)

            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_sentiment_stock_id ON stock_sentiment(stock_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_sentiment_updated_at ON stock_sentiment(updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_stock_id ON predictions(stock_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_stock_id ON price_history_5m(stock_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history_5m(timestamp)")

            logger.info("Database schema initialized successfully")

    # Stock CRUD operations
    def insert_stock(self, symbol: str, sector: str) -> int:
        """Insert a new stock."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO stocks (symbol, sector) VALUES (?, ?)",
                (symbol, sector)
            )
            cursor.execute("SELECT id FROM stocks WHERE symbol = ?", (symbol,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_stock_id(self, symbol: str) -> Optional[int]:
        """Get stock ID by symbol."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM stocks WHERE symbol = ?", (symbol,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """Get all stocks."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, symbol, sector FROM stocks")
            return [dict(row) for row in cursor.fetchall()]

    # Sentiment CRUD operations
    def insert_stock_sentiment(self, stock_id: int, sentiment: str, score: float, article_count: int = 1):
        """Insert stock sentiment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO stock_sentiment (stock_id, sentiment, score, article_count, updated_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (stock_id, sentiment, score, article_count)
            )

    def get_latest_stock_sentiment(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """Get latest sentiment for a stock."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT sentiment, score, article_count, updated_at FROM stock_sentiment
                   WHERE stock_id = ? ORDER BY updated_at DESC LIMIT 1""",
                (stock_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def insert_sector_sentiment(self, sector: str, sentiment: str, score: float):
        """Insert sector sentiment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO sector_sentiment (sector, sentiment, score, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (sector, sentiment, score)
            )

    def get_latest_sector_sentiment(self, sector: str) -> Optional[Dict[str, Any]]:
        """Get latest sentiment for a sector."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT sentiment, score, updated_at FROM sector_sentiment
                   WHERE sector = ? ORDER BY updated_at DESC LIMIT 1""",
                (sector,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def insert_market_sentiment(self, sentiment: str, score: float):
        """Insert market sentiment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO market_sentiment (sentiment, score, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (sentiment, score)
            )

    def get_latest_market_sentiment(self) -> Optional[Dict[str, Any]]:
        """Get latest market sentiment."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT sentiment, score, updated_at FROM market_sentiment
                   ORDER BY updated_at DESC LIMIT 1"""
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    # Prediction CRUD operations
    def insert_prediction(self, stock_id: int, predicted_low: float, predicted_high: float,
                         confidence: float, predicted_at: datetime):
        """Insert a price prediction."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO predictions (stock_id, predicted_low, predicted_high, confidence, predicted_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (stock_id, predicted_low, predicted_high, confidence, predicted_at)
            )

    def get_latest_prediction(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """Get latest prediction for a stock."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT predicted_low, predicted_high, confidence, predicted_at, created_at
                   FROM predictions WHERE stock_id = ? ORDER BY created_at DESC LIMIT 1""",
                (stock_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_recent_predictions(self, stock_id: int, hours: int = 24) -> List[Dict[str, Any]]:
        """Get predictions from last N hours."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT predicted_low, predicted_high, confidence, predicted_at, created_at
                   FROM predictions 
                   WHERE stock_id = ? AND created_at >= datetime('now', '-' || ? || ' hours')
                   ORDER BY created_at DESC""",
                (stock_id, hours)
            )
            return [dict(row) for row in cursor.fetchall()]

    # Price history CRUD operations
    def insert_price_candle(self, stock_id: int, open_price: float, high: float, low: float,
                           close: float, volume: int, timestamp: datetime):
        """Insert a 5-min price candle."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO price_history_5m
                   (stock_id, open, high, low, close, volume, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (stock_id, open_price, high, low, close, volume, timestamp)
            )

    def get_price_history(self, stock_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent price candles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT open, high, low, close, volume, timestamp
                   FROM price_history_5m WHERE stock_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (stock_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    # News cache CRUD operations
    def insert_news(self, title: str, summary: str, content: str, source: str, url: str,
                    published_at: datetime, stock_id: Optional[int] = None):
        """Insert a news article."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR IGNORE INTO news_cache
                   (stock_id, title, summary, content, source, url, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (stock_id, title, summary, content, source, url, published_at)
            )

    def get_recent_news(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent news articles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT stock_id, title, summary, source, url, published_at
                   FROM news_cache 
                   WHERE published_at >= datetime('now', '-' || ? || ' hours')
                   ORDER BY published_at DESC LIMIT ?""",
                (hours, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stock_news(self, stock_id: int, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent news for a specific stock."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT title, summary, source, url, published_at
                   FROM news_cache
                   WHERE stock_id = ? AND published_at >= datetime('now', '-' || ? || ' hours')
                   ORDER BY published_at DESC LIMIT ?""",
                (stock_id, hours, limit)
            )
            return [dict(row) for row in cursor.fetchall()]
