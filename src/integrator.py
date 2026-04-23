"""
Integrator module that orchestrates sentiment analysis and price predictions.
Coordinates between Part 1 (sentiment) and Part 2 (technical).
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.db import DatabaseManager
from src.config import ConfigLoader
from src.sentiment.news_fetcher import NewsFetcher
from src.sentiment.sentiment_analyzer import SentimentAnalyzer
from src.technical.predictor import PricePredictor

logger = logging.getLogger(__name__)


class StockPredictorIntegrator:
    """Integrates sentiment analysis and technical prediction."""

    def __init__(self, config_loader: ConfigLoader, db: DatabaseManager):
        """
        Initialize integrator.

        Args:
            config_loader: Configuration loader
            db: Database manager
        """
        self.config_loader = config_loader
        self.config = config_loader.settings
        self.db = db

        # Initialize components
        self.news_fetcher = NewsFetcher(self.config.get('news', {}))
        self.sentiment_analyzer = SentimentAnalyzer(self.config)
        self.price_predictor = PricePredictor(self.config)

        # Initialize stocks in database
        self._initialize_stocks()

    def _initialize_stocks(self):
        """Initialize stock list in database."""
        stock_symbols = self.config_loader.get_stock_symbols()
        for symbol in stock_symbols:
            sector = self.config_loader.get_stock_sector(symbol)
            self.db.insert_stock(symbol, sector)
        logger.info(f"Initialized {len(stock_symbols)} stocks in database")

    def update_sentiment(self, stocks: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Fetch news and update sentiment for stocks.

        Args:
            stocks: List of stock symbols to update (None = all)

        Returns:
            Dict mapping symbol to sentiment update result
        """
        if stocks is None:
            stocks = self.config_loader.get_stock_symbols()

        logger.info(f"Updating sentiment for {len(stocks)} stocks")

        results = {}

        for stock_symbol in stocks:
            try:
                # Get stock ID
                stock_id = self.db.get_stock_id(stock_symbol)
                if not stock_id:
                    stock_id = self.db.insert_stock(stock_symbol, self.config_loader.get_stock_sector(stock_symbol))

                # Fetch news for stock
                articles = self.news_fetcher.fetch_news([stock_symbol])

                if not articles:
                    logger.warning(f"No news found for {stock_symbol}")
                    results[stock_symbol] = {'status': 'no_news', 'articles': 0}
                    continue

                # Analyze sentiment
                sentiment_result = self.sentiment_analyzer.analyze_batch_sentiment(
                    articles,
                    context=stock_symbol
                )

                if sentiment_result is None:
                    results[stock_symbol] = {'status': 'error', 'articles': len(articles)}
                    continue

                # Store in database
                self.db.insert_stock_sentiment(
                    stock_id,
                    sentiment_result['sentiment'],
                    sentiment_result['score'],
                    article_count=sentiment_result.get('article_count', len(articles))
                )

                logger.info(
                    f"{stock_symbol}: {sentiment_result['sentiment'].upper()} "
                    f"({sentiment_result['score']:.2f}) from {len(articles)} articles"
                )

                results[stock_symbol] = {
                    'status': 'success',
                    'sentiment': sentiment_result['sentiment'],
                    'score': sentiment_result['score'],
                    'confidence': sentiment_result.get('confidence', 0),
                    'articles': len(articles)
                }

            except Exception as e:
                logger.error(f"Error updating sentiment for {stock_symbol}: {e}")
                results[stock_symbol] = {'status': 'error', 'error': str(e)}

        return results

    def update_sector_sentiment(self, sectors: Optional[List[str]] = None):
        """
        Calculate and update sector-level sentiment.

        Args:
            sectors: List of sectors to update (None = all)
        """
        if sectors is None:
            sectors = set(self.config_loader.config.get('stocks', {}).__class__.__dict__.get('sectors', {}).keys())
            if not sectors:
                sectors = list(set(self.config_loader.config.get('sectors', {}).keys()))

        logger.info(f"Updating sentiment for {len(sectors)} sectors")

        for sector in sectors:
            try:
                # Get stocks in sector
                stocks_in_sector = self.config_loader.get_sector_stocks(sector)

                if not stocks_in_sector:
                    logger.warning(f"No stocks found for sector {sector}")
                    continue

                # Get latest sentiment for each stock
                sentiments = []
                scores = []

                for stock_symbol in stocks_in_sector:
                    stock_id = self.db.get_stock_id(stock_symbol)
                    if stock_id:
                        sentiment = self.db.get_latest_stock_sentiment(stock_id)
                        if sentiment:
                            sentiments.append(sentiment['sentiment'])
                            scores.append(sentiment['score'])

                if scores:
                    # Calculate average sentiment
                    avg_score = sum(scores) / len(scores)
                    overall_sentiment = self.sentiment_analyzer.score_to_sentiment(avg_score)

                    # Store in database
                    self.db.insert_sector_sentiment(sector, overall_sentiment, avg_score)

                    logger.info(f"{sector}: {overall_sentiment.upper()} ({avg_score:.2f})")

            except Exception as e:
                logger.error(f"Error updating sector sentiment for {sector}: {e}")

    def update_market_sentiment(self):
        """Calculate and update market-wide sentiment."""
        try:
            logger.info("Updating market-wide sentiment")

            # Get all stocks
            stocks = self.db.get_all_stocks()

            # Collect sentiments
            scores = []
            for stock in stocks:
                sentiment = self.db.get_latest_stock_sentiment(stock['id'])
                if sentiment:
                    scores.append(sentiment['score'])

            if scores:
                avg_score = sum(scores) / len(scores)
                overall_sentiment = self.sentiment_analyzer.score_to_sentiment(avg_score)

                self.db.insert_market_sentiment(overall_sentiment, avg_score)

                logger.info(f"Market: {overall_sentiment.upper()} ({avg_score:.2f})")

        except Exception as e:
            logger.error(f"Error updating market sentiment: {e}")

    def predict_prices(self, stocks: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Predict prices for stocks.

        Args:
            stocks: List of stock symbols to predict (None = all)

        Returns:
            Dict mapping symbol to prediction result
        """
        if stocks is None:
            stocks = self.config_loader.get_stock_symbols()

        logger.info(f"Predicting prices for {len(stocks)} stocks")

        results = {}

        for stock_symbol in stocks:
            try:
                stock_id = self.db.get_stock_id(stock_symbol)
                if not stock_id:
                    results[stock_symbol] = {'status': 'not_found'}
                    continue

                # Get latest sentiment
                sentiment = self.db.get_latest_stock_sentiment(stock_id)
                sentiment_score = sentiment['score'] if sentiment else 0.0

                # Make prediction
                prediction = self.price_predictor.predict(stock_symbol, sentiment_score=sentiment_score)

                if prediction is None:
                    results[stock_symbol] = {'status': 'prediction_failed'}
                    continue

                # Store in database
                self.db.insert_prediction(
                    stock_id,
                    prediction['predicted_low'],
                    prediction['predicted_high'],
                    prediction['confidence'],
                    datetime.fromisoformat(prediction['predicted_at'])
                )

                logger.info(
                    f"{stock_symbol}: ${prediction['predicted_low']:.2f} - ${prediction['predicted_high']:.2f} "
                    f"(confidence: {prediction['confidence']:.2f})"
                )

                results[stock_symbol] = {
                    'status': 'success',
                    'predicted_low': prediction['predicted_low'],
                    'predicted_high': prediction['predicted_high'],
                    'confidence': prediction['confidence'],
                    'current_price': prediction['current_price'],
                }

            except Exception as e:
                logger.error(f"Error predicting price for {stock_symbol}: {e}")
                results[stock_symbol] = {'status': 'error', 'error': str(e)}

        return results

    def full_update_cycle(self) -> Dict:
        """
        Run a complete update cycle: sentiment -> sector -> market -> predictions.

        Returns:
            Dict with results from each step
        """
        logger.info("=" * 60)
        logger.info("Starting full update cycle")
        logger.info("=" * 60)

        cycle_start = datetime.now()

        try:
            # Step 1: Update stock sentiments
            sentiment_results = self.update_sentiment()

            # Step 2: Update sector sentiments
            self.update_sector_sentiment()

            # Step 3: Update market sentiment
            self.update_market_sentiment()

            # Step 4: Make price predictions
            prediction_results = self.predict_prices()

            cycle_duration = (datetime.now() - cycle_start).total_seconds()

            summary = {
                'cycle_start': cycle_start.isoformat(),
                'cycle_duration_seconds': cycle_duration,
                'sentiment_updates': sentiment_results,
                'prediction_results': prediction_results,
                'status': 'completed'
            }

            logger.info(f"Update cycle completed in {cycle_duration:.2f}s")

            return summary

        except Exception as e:
            logger.error(f"Error in full update cycle: {e}")
            return {
                'cycle_start': cycle_start.isoformat(),
                'status': 'error',
                'error': str(e)
            }

    def get_stock_status(self, symbol: str) -> Dict:
        """Get current status (sentiment, prediction) for a stock."""
        try:
            stock_id = self.db.get_stock_id(symbol)
            if not stock_id:
                return {'status': 'not_found'}

            sentiment = self.db.get_latest_stock_sentiment(stock_id)
            prediction = self.db.get_latest_prediction(stock_id)
            prices = self.db.get_price_history(stock_id, limit=5)

            return {
                'symbol': symbol,
                'sentiment': sentiment,
                'prediction': prediction,
                'recent_prices': prices,
            }

        except Exception as e:
            logger.error(f"Error getting stock status: {e}")
            return {'status': 'error', 'error': str(e)}
