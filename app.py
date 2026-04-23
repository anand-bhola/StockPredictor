"""
Main entry point for Stock Predictor CLI application.
"""

import logging
import sys
from pathlib import Path

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import ConfigLoader, setup_logging
from src.db import DatabaseManager
from src.integrator import StockPredictorIntegrator
from src.scheduler import SentimentScheduler

# Initialize configuration
config = ConfigLoader(config_dir="./config")
setup_logging(config.settings)
logger = logging.getLogger(__name__)

# Initialize database
db = DatabaseManager(db_path=config.get('database.path', './data/stock_predictor.db'))

# Initialize integrator and scheduler
integrator = StockPredictorIntegrator(config, db)
scheduler = SentimentScheduler(config.settings)


@click.group()
def cli():
    """Stock Predictor CLI - Sentiment Analysis & Technical Analysis for Stock Price Prediction"""
    pass


@cli.command()
@click.option('--stock', required=True, help='Stock symbol (e.g., AAPL)')
def predict(stock: str):
    """Predict stock price range for next 5-min window."""
    click.echo(f"📊 Predicting price range for {stock}...")
    
    results = integrator.predict_prices([stock])
    
    if stock not in results:
        click.echo(f"❌ Error: No result for {stock}", err=True)
        return
    
    result = results[stock]
    
    if result.get('status') == 'success':
        click.echo(f"✅ Prediction successful for {stock}")
        click.echo(f"  Range: ${result['predicted_low']:.2f} - ${result['predicted_high']:.2f}")
        click.echo(f"  Current Price: ${result['current_price']:.2f}")
        click.echo(f"  Confidence: {result['confidence']:.2f}")
    else:
        click.echo(f"⚠️  {stock}: {result.get('status', 'unknown error')}", err=True)


@cli.command()
@click.option('--stock', required=True, help='Stock symbol (e.g., AAPL)')
@click.option('--window', default='24h', help='Time window (e.g., 24h, 7d)')
def sentiment(stock: str, window: str):
    """Show sentiment analysis for a stock."""
    click.echo(f"💭 Sentiment for {stock} ({window})...")
    
    status = integrator.get_stock_status(stock)
    
    if status.get('status') == 'not_found':
        click.echo(f"❌ Stock {stock} not found in database", err=True)
        return
    
    sentiment = status.get('sentiment')
    if sentiment:
        click.echo(f"✅ Sentiment: {sentiment['sentiment'].upper()}")
        click.echo(f"   Score: {sentiment['score']:.2f}")
        click.echo(f"   Articles: {sentiment.get('article_count', 0)}")
        click.echo(f"   Updated: {sentiment['updated_at']}")
    else:
        click.echo(f"⚠️  No sentiment data available for {stock}")


@cli.command()
@click.option('--stock', required=True, help='Stock symbol (e.g., AAPL)')
@click.option('--force', is_flag=True, help='Force retraining')
def train(stock: str, force: bool):
    """Train LSTM model for a stock."""
    click.echo(f"🤖 Training LSTM model for {stock}...")
    if force:
        click.echo("   (Force retraining enabled)")

    success = integrator.price_predictor.train_model(stock, retrain=force)
    
    if success:
        click.echo(f"✅ Model trained successfully for {stock}")
        click.echo(f"   Ready for predictions")
    else:
        click.echo(f"❌ Training failed for {stock}", err=True)


@cli.command()
@click.option('--stocks', default=None, help='Comma-separated stock symbols (e.g., AAPL,MSFT,TSLA)')
@click.option('--duration', default='0', help='Duration to run (e.g., 30m, 2h, or 0 for continuous)')
def watch(stocks: str, duration: str):
    """Monitor stocks with continuous sentiment & price updates."""
    if not stocks:
        stock_list = config.get_stock_symbols()
        click.echo(f"👀 Watching {len(stock_list)} stocks: {', '.join(stock_list)}")
    else:
        stock_list = [s.strip() for s in stocks.split(',')]
        click.echo(f"👀 Watching {len(stock_list)} stocks: {', '.join(stock_list)}")

    if duration and duration != '0':
        click.echo(f"   Duration: {duration}")

    click.echo("⏱️  Starting scheduler...")

    try:
        # Start scheduler with full update cycle
        scheduler.start(lambda: integrator.full_update_cycle())

        # Keep running
        click.echo("✅ Scheduler running. Press Ctrl+C to stop.")
        click.echo("=" * 60)

        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n⏹️  Stopping scheduler...")
            scheduler.stop()
            click.echo("✅ Scheduler stopped")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.command()
def health():
    """Show application health and latest data."""
    click.echo("🏥 Stock Predictor Health Check")
    click.echo("=" * 60)

    # Check database
    try:
        stocks = db.get_all_stocks()
        click.echo(f"✅ Database: OK ({len(stocks)} stocks)")
    except Exception as e:
        click.echo(f"❌ Database: FAILED ({e})")
        return

    # Check each stock
    if stocks:
        for stock in stocks[:5]:
            symbol = stock['symbol']
            sector = stock.get('sector', 'N/A')
            
            status = integrator.get_stock_status(symbol)
            sentiment = status.get('sentiment')
            prediction = status.get('prediction')

            status_icon = "✅" if sentiment else "⚠️"
            click.echo(f"\n{status_icon} {symbol} ({sector})")
            
            if sentiment:
                click.echo(f"   Sentiment: {sentiment['sentiment'].upper()} ({sentiment['score']:.2f})")
                click.echo(f"   Articles: {sentiment.get('article_count', 0)}")
                click.echo(f"   Updated: {sentiment['updated_at']}")
            else:
                click.echo(f"   Sentiment: No data")
                
            if prediction:
                click.echo(f"   Prediction: ${prediction['predicted_low']:.2f} - ${prediction['predicted_high']:.2f}")
                click.echo(f"   Confidence: {prediction.get('confidence', 0):.2f}")
            else:
                click.echo(f"   Predictions: No data")

    # Show model info
    click.echo("\n" + "=" * 60)
    click.echo("🤖 Model Status:")
    metadata = integrator.price_predictor.get_prediction_metadata()
    click.echo(f"   Trained: {'Yes' if metadata['model_trained'] else 'No'}")
    click.echo(f"   Lookback Window: {metadata['lookback_window']} candles")
    
    click.echo("\n💡 Tip: Run 'python app.py watch' to start live monitoring")


@cli.group()
def debug():
    """Debug utilities (for development)"""
    pass


@debug.command()
def init_stocks():
    """Initialize stocks in database from config."""
    click.echo("📦 Initializing stocks database...")
    stock_symbols = config.get_stock_symbols()
    count = 0
    for symbol in stock_symbols:
        sector = config.get_stock_sector(symbol)
        db.insert_stock(symbol, sector)
        count += 1
    click.echo(f"✅ Initialized {count} stocks")
    for symbol in stock_symbols[:3]:
        click.echo(f"   - {symbol}")
    if len(stock_symbols) > 3:
        click.echo(f"   ... and {len(stock_symbols) - 3} more")


@debug.command()
@click.option('--stock', required=True, help='Stock symbol')
def fetch_news(stock: str):
    """Fetch and display latest news for a stock."""
    click.echo(f"📰 Fetching news for {stock}...")
    
    articles = integrator.news_fetcher.fetch_news([stock])
    
    if not articles:
        click.echo(f"❌ No news found for {stock}", err=True)
        return
    
    click.echo(f"✅ Found {len(articles)} articles:\n")
    
    for i, article in enumerate(articles[:5], 1):
        click.echo(f"{i}. {article['title']}")
        click.echo(f"   Source: {article['source']}")
        if article.get('summary'):
            summary = article['summary'][:100] + "..." if len(article['summary']) > 100 else article['summary']
            click.echo(f"   Summary: {summary}")
        click.echo()


@debug.command()
@click.option('--stock', required=True, help='Stock symbol')
def analyze_news(stock: str):
    """Fetch news and analyze sentiment for a stock."""
    click.echo(f"📰 Fetching news for {stock}...")
    
    articles = integrator.news_fetcher.fetch_news([stock])
    
    if not articles:
        click.echo(f"❌ No news found for {stock}", err=True)
        return
    
    click.echo(f"✅ Found {len(articles)} articles")
    click.echo(f"💭 Analyzing sentiment...\n")
    
    sentiment_result = integrator.sentiment_analyzer.analyze_batch_sentiment(articles, context=stock)
    
    click.echo(f"Sentiment: {sentiment_result['sentiment'].upper()}")
    click.echo(f"Score: {sentiment_result['score']:.2f}")
    click.echo(f"Confidence: {sentiment_result.get('confidence', 0):.2f}")
    click.echo(f"Summary: {sentiment_result.get('summary', 'N/A')}")


@debug.command()
@click.option('--stock', required=True, help='Stock symbol')
def show_latest(stock: str):
    """Show latest data for a stock."""
    stock_id = db.get_stock_id(stock)
    if not stock_id:
        click.echo(f"❌ Stock {stock} not found")
        return

    click.echo(f"📋 Latest data for {stock}")
    click.echo("=" * 60)

    # Get complete status
    status = integrator.get_stock_status(stock)
    
    # Sentiment
    sentiment = status.get('sentiment')
    if sentiment:
        click.echo(f"💭 Sentiment: {sentiment['sentiment'].upper()} ({sentiment['score']:.2f})")
        click.echo(f"   Articles: {sentiment.get('article_count', 0)}")
        click.echo(f"   Updated: {sentiment['updated_at']}")
    else:
        click.echo("💭 Sentiment: No data")

    # Price history
    prices = status.get('recent_prices', [])
    if prices:
        click.echo(f"\n📈 Recent Prices (last 5 candles):")
        for price in prices:
            click.echo(
                f"   {price['timestamp']}: "
                f"O={price['open']:.2f} H={price['high']:.2f} "
                f"L={price['low']:.2f} C={price['close']:.2f}"
            )
    else:
        click.echo("\n📈 Price History: No data")

    # Predictions
    prediction = status.get('prediction')
    if prediction:
        click.echo(f"\n🎯 Latest Prediction:")
        click.echo(f"   Range: ${prediction['predicted_low']:.2f} - ${prediction['predicted_high']:.2f}")
        click.echo(f"   Confidence: {prediction.get('confidence', 0):.2f}")
        click.echo(f"   Created: {prediction['created_at']}")
    else:
        click.echo("\n🎯 Predictions: No data")


@debug.command()
def show_config():
    """Show loaded configuration."""
    click.echo("⚙️  Application Configuration")
    click.echo("=" * 60)
    click.echo(f"App: {config.get('app.name')} v{config.get('app.version')}")
    click.echo(f"Database: {config.get('database.path')}")
    click.echo(f"LLM Provider: {config.get('llm.provider')}")
    click.echo(f"LLM Model: {config.get('llm.model')}")
    click.echo(f"News Update Interval: {config.get('news.update_interval')} min")
    click.echo(f"LSTM Lookback Window: {config.get('lstm.lookback_window')} candles")
    click.echo(f"Prediction Window: {config.get('prediction.window_minutes')} minutes")
    
    stock_list = config.get_stock_symbols()
    click.echo(f"\n📊 Monitored Stocks ({len(stock_list)}):")
    for symbol in stock_list[:10]:
        sector = config.get_stock_sector(symbol)
        click.echo(f"   - {symbol} ({sector})")
    if len(stock_list) > 10:
        click.echo(f"   ... and {len(stock_list) - 10} more")


@debug.command()
def run_cycle():
    """Run a single sentiment/prediction update cycle."""
    click.echo("⚙️  Running update cycle...")
    
    result = integrator.full_update_cycle()
    
    click.echo("\n✅ Cycle completed!")
    click.echo(f"   Duration: {result.get('cycle_duration_seconds', 0):.2f}s")
    
    sentiment_results = result.get('sentiment_updates', {})
    successful = sum(1 for r in sentiment_results.values() if r.get('status') == 'success')
    click.echo(f"   Sentiments updated: {successful}/{len(sentiment_results)}")
    
    prediction_results = result.get('prediction_results', {})
    pred_success = sum(1 for r in prediction_results.values() if r.get('status') == 'success')
    click.echo(f"   Predictions made: {pred_success}/{len(prediction_results)}")


cli.add_command(debug)

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
