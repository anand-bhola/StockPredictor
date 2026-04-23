"""
Configuration loader for Stock Predictor application.
Loads settings from YAML and environment variables.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseSettings

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage application configuration."""

    def __init__(self, config_dir: str = "./config"):
        """
        Initialize ConfigLoader.

        Args:
            config_dir: Path to config directory
        """
        self.config_dir = Path(config_dir)
        self.settings = {}
        self.stocks = {}
        self.sectors = {}
        self._load_configs()

    def _load_configs(self):
        """Load all YAML configuration files."""
        # Load settings.yaml
        settings_path = self.config_dir / "settings.yaml"
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                self.settings = yaml.safe_load(f) or {}
            self._substitute_env_vars(self.settings)
            logger.info(f"Loaded settings from {settings_path}")
        else:
            logger.warning(f"Settings file not found: {settings_path}")

        # Load stocks.yaml
        stocks_path = self.config_dir / "stocks.yaml"
        if stocks_path.exists():
            with open(stocks_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                self.stocks = {s['symbol']: s for s in config.get('stocks', [])}
                self.sectors = config.get('sectors', {})
            logger.info(f"Loaded {len(self.stocks)} stocks from {stocks_path}")
        else:
            logger.warning(f"Stocks file not found: {stocks_path}")

    def _substitute_env_vars(self, obj: Any):
        """Recursively substitute ${VAR} with environment variables."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    obj[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._substitute_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                    env_var = item[2:-1]
                    obj[i] = os.getenv(env_var, item)
                elif isinstance(item, (dict, list)):
                    self._substitute_env_vars(item)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated path."""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_stock_symbols(self) -> list:
        """Get all stock symbols."""
        return list(self.stocks.keys())

    def get_stock_sector(self, symbol: str) -> Optional[str]:
        """Get sector for a stock symbol."""
        stock = self.stocks.get(symbol)
        return stock.get('sector') if stock else None

    def get_sector_stocks(self, sector: str) -> list:
        """Get all stocks in a sector."""
        return self.sectors.get(sector, [])


def setup_logging(config: Dict[str, Any]):
    """Set up application logging."""
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file')

    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )

    # Suppress verbose logging from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('feedparser').setLevel(logging.WARNING)

    logger.info(f"Logging configured at level: {log_level}")
