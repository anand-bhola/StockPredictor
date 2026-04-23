"""
Unit tests for database module.
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile

from src.db import DatabaseManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(str(db_path))
        yield db


class TestDatabaseManager:
    """Test DatabaseManager functionality."""

    def test_database_initialization(self, temp_db):
        """Test that database initializes with correct schema."""
        assert Path(temp_db.db_path).exists()

    def test_insert_and_get_stock(self, temp_db):
        """Test stock insertion and retrieval."""
        stock_id = temp_db.insert_stock("AAPL", "Technology")
        assert stock_id is not None

        retrieved_id = temp_db.get_stock_id("AAPL")
        assert retrieved_id == stock_id

    def test_get_all_stocks(self, temp_db):
        """Test retrieving all stocks."""
        temp_db.insert_stock("AAPL", "Technology")
        temp_db.insert_stock("MSFT", "Technology")

        stocks = temp_db.get_all_stocks()
        assert len(stocks) >= 2
        symbols = [s['symbol'] for s in stocks]
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_insert_stock_sentiment(self, temp_db):
        """Test sentiment insertion."""
        stock_id = temp_db.insert_stock("AAPL", "Technology")
        temp_db.insert_stock_sentiment(stock_id, "bullish", 0.75, 5)

        sentiment = temp_db.get_latest_stock_sentiment(stock_id)
        assert sentiment is not None
        assert sentiment['sentiment'] == 'bullish'
        assert sentiment['score'] == 0.75
        assert sentiment['article_count'] == 5

    def test_insert_sector_sentiment(self, temp_db):
        """Test sector sentiment insertion."""
        temp_db.insert_sector_sentiment("Technology", "bullish", 0.65)

        sentiment = temp_db.get_latest_sector_sentiment("Technology")
        assert sentiment is not None
        assert sentiment['sentiment'] == 'bullish'
        assert sentiment['score'] == 0.65

    def test_insert_market_sentiment(self, temp_db):
        """Test market sentiment insertion."""
        temp_db.insert_market_sentiment("neutral", 0.05)

        sentiment = temp_db.get_latest_market_sentiment()
        assert sentiment is not None
        assert sentiment['sentiment'] == 'neutral'
        assert sentiment['score'] == 0.05

    def test_insert_prediction(self, temp_db):
        """Test prediction insertion and retrieval."""
        from datetime import datetime

        stock_id = temp_db.insert_stock("AAPL", "Technology")
        now = datetime.now()

        temp_db.insert_prediction(stock_id, 180.0, 185.0, 0.85, now)

        prediction = temp_db.get_latest_prediction(stock_id)
        assert prediction is not None
        assert prediction['predicted_low'] == 180.0
        assert prediction['predicted_high'] == 185.0
        assert prediction['confidence'] == 0.85
