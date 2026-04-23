"""
Integration tests for the full pipeline.
"""

import pytest
from pathlib import Path
import tempfile

from src.config import ConfigLoader
from src.db import DatabaseManager
from src.integrator import StockPredictorIntegrator


@pytest.fixture
def test_environment():
    """Set up test environment with config and database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create minimal config
        config_dir = tmpdir / 'config'
        config_dir.mkdir()

        import yaml

        stocks_config = {
            'stocks': [{'symbol': 'AAPL', 'sector': 'Technology'}],
            'sectors': {'Technology': ['AAPL']}
        }
        with open(config_dir / 'stocks.yaml', 'w') as f:
            yaml.dump(stocks_config, f)

        settings_config = {
            'app': {'name': 'Test', 'version': '1.0.0'},
            'database': {'path': str(tmpdir / 'test.db')},
            'llm': {'model': 'gpt-3.5-turbo'},
            'news': {'update_interval': 10},
            'technical': {'lookback_period': 100},
            'lstm': {'lookback_window': 20, 'epochs': 5},
            'logging': {'level': 'WARNING'}
        }
        with open(config_dir / 'settings.yaml', 'w') as f:
            yaml.dump(settings_config, f)

        # Create loaders
        config = ConfigLoader(config_dir=str(config_dir))
        db = DatabaseManager(str(tmpdir / 'test.db'))

        yield config, db


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_integrator_initialization(self, test_environment):
        """Test that integrator initializes correctly."""
        config, db = test_environment

        integrator = StockPredictorIntegrator(config, db)
        assert integrator is not None
        assert integrator.config_loader is not None
        assert integrator.db is not None

    def test_get_stock_status(self, test_environment):
        """Test getting stock status."""
        config, db = test_environment

        integrator = StockPredictorIntegrator(config, db)

        # Add some test data
        stock_id = db.insert_stock('AAPL', 'Technology')
        db.insert_stock_sentiment(stock_id, 'bullish', 0.65)

        status = integrator.get_stock_status('AAPL')
        assert status is not None
        assert 'sentiment' in status
        assert status['sentiment']['sentiment'] == 'bullish'

    def test_sentiment_update(self, test_environment):
        """Test sentiment update (mocked)."""
        config, db = test_environment

        integrator = StockPredictorIntegrator(config, db)

        # This will attempt real API calls, so we just test it doesn't crash
        # with missing data gracefully
        results = integrator.update_sentiment(['AAPL'])
        assert results is not None
        assert 'AAPL' in results
