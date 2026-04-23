"""
Unit tests for configuration module.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.config import ConfigLoader


@pytest.fixture
def temp_config():
    """Create temporary config files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Create stocks.yaml
        stocks_config = {
            'stocks': [
                {'symbol': 'AAPL', 'sector': 'Technology'},
                {'symbol': 'MSFT', 'sector': 'Technology'},
                {'symbol': 'TSLA', 'sector': 'Automotive'},
            ],
            'sectors': {
                'Technology': ['AAPL', 'MSFT'],
                'Automotive': ['TSLA']
            }
        }
        with open(config_dir / 'stocks.yaml', 'w') as f:
            yaml.dump(stocks_config, f)

        # Create settings.yaml
        settings_config = {
            'app': {
                'name': 'Stock Predictor',
                'version': '1.0.0'
            },
            'database': {
                'path': './test.db'
            },
            'llm': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.3
            }
        }
        with open(config_dir / 'settings.yaml', 'w') as f:
            yaml.dump(settings_config, f)

        loader = ConfigLoader(config_dir=str(config_dir))
        yield loader


class TestConfigLoader:
    """Test ConfigLoader functionality."""

    def test_config_initialization(self, temp_config):
        """Test config loader initializes correctly."""
        assert temp_config is not None
        assert len(temp_config.stocks) > 0

    def test_get_stock_symbols(self, temp_config):
        """Test retrieving stock symbols."""
        symbols = temp_config.get_stock_symbols()
        assert 'AAPL' in symbols
        assert 'MSFT' in symbols
        assert 'TSLA' in symbols

    def test_get_stock_sector(self, temp_config):
        """Test retrieving stock sector."""
        sector = temp_config.get_stock_sector('AAPL')
        assert sector == 'Technology'

        sector = temp_config.get_stock_sector('TSLA')
        assert sector == 'Automotive'

    def test_get_sector_stocks(self, temp_config):
        """Test retrieving stocks by sector."""
        tech_stocks = temp_config.get_sector_stocks('Technology')
        assert 'AAPL' in tech_stocks
        assert 'MSFT' in tech_stocks
        assert 'TSLA' not in tech_stocks

    def test_get_config_value(self, temp_config):
        """Test retrieving configuration values."""
        name = temp_config.get('app.name')
        assert name == 'Stock Predictor'

        model = temp_config.get('llm.model')
        assert model == 'gpt-3.5-turbo'
