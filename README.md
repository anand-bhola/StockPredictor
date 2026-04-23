# Stock Predictor - LLM-Driven Sentiment Analysis & LSTM Price Prediction

A comprehensive Python application that combines LLM-based sentiment analysis of financial news with technical analysis and LSTM deep learning to predict stock price ranges in 5-minute windows.

## Features

### Part 1: Sentiment & Fundamental Analysis
- **News Fetching**: Automatically retrieves financial news from multiple RSS feeds (CNBC, Reuters, MarketWatch) and web scraping (Yahoo Finance)
- **LLM-Based Sentiment Analysis**: Uses OpenAI API (GPT-3.5/GPT-4) to analyze news sentiment for individual stocks, sectors, and market
- **Periodic Updates**: Automatically fetches and analyzes news every 5-15 minutes
- **Aggregation**: Calculates sector and market-wide sentiment from individual stock sentiments

### Part 2: Technical Analysis & LSTM Prediction
- **Technical Indicators**: Computes RSI, MACD, Bollinger Bands, SMA (20/50/200), EMA (12/26), ATR
- **LSTM Deep Learning**: 2-3 layer LSTM neural network that combines technical indicators with sentiment scores
- **Price Range Prediction**: Predicts the high and low prices for the next 5-minute trading window
- **Confidence Scoring**: Provides confidence metrics based on model training status and feature variance

### Integration
- **SQLite Database**: Persistent storage of stocks, sentiments, predictions, and price history
- **CLI Interface**: Full-featured command-line tool for monitoring, training, and analysis
- **Scheduled Updates**: APScheduler-based background scheduler for continuous monitoring

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key (for GPT sentiment analysis)
- Internet connection for fetching news and price data

### Setup

1. **Clone/Navigate to Repository**
   ```bash
   cd c:\Users\anand\Repos\StockPrediction
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Application**

   Create `.env` file with your API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=sk-...
   ```

   The configuration files are already set up:
   - `config/stocks.yaml` - Stock list and sectors
   - `config/settings.yaml` - Application settings

5. **Initialize Database**
   ```bash
   python app.py debug init-stocks
   ```

## Usage

### Monitor Stocks (Watch Mode)
Continuously monitor stocks with automatic sentiment and price updates every 5-15 minutes:

```bash
python app.py watch
# Or monitor specific stocks:
python app.py watch --stocks AAPL,MSFT,TSLA
```

### Get Sentiment for a Stock
```bash
python app.py sentiment --stock AAPL
```

### Predict Price Range
```bash
python app.py predict --stock AAPL
```

### Train LSTM Model
Train or retrain the model for a stock:

```bash
python app.py train --stock AAPL
# Force retraining:
python app.py train --stock AAPL --force
```

### Health Check
View current status of all stocks, models, and system health:

```bash
python app.py health
```

### Debug Commands

**Initialize stocks database:**
```bash
python app.py debug init-stocks
```

**Fetch and display news:**
```bash
python app.py debug fetch-news --stock AAPL
```

**Fetch news and analyze sentiment:**
```bash
python app.py debug analyze-news --stock AAPL
```

**Show latest data for a stock:**
```bash
python app.py debug show-latest --stock AAPL
```

**Show configuration:**
```bash
python app.py debug show-config
```

**Run a single update cycle:**
```bash
python app.py debug run-cycle
```

## Architecture

### Project Structure
```
StockPrediction/
├── config/
│   ├── stocks.yaml           # Stock symbols and sectors
│   └── settings.yaml         # Application configuration
├── src/
│   ├── app.py                # CLI entry point
│   ├── config.py             # Configuration loader
│   ├── db.py                 # Database module
│   ├── integrator.py         # Orchestrates sentiment + prediction
│   ├── scheduler.py          # APScheduler wrapper
│   ├── sentiment/
│   │   ├── news_fetcher.py   # Fetches RSS feeds and web scrape news
│   │   └── sentiment_analyzer.py  # OpenAI LLM sentiment analysis
│   └── technical/
│       ├── indicators.py     # Technical indicator calculations
│       ├── data_loader.py    # Yahoo Finance data fetching
│       ├── lstm_model.py     # LSTM neural network model
│       └── predictor.py      # Price range prediction engine
├── data/
│   ├── models/               # Trained LSTM models
│   ├── cache/                # Cached data
│   └── stock_predictor.db    # SQLite database
├── tests/                    # Unit and integration tests
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Database Schema

**stocks**: Stock metadata
- id, symbol, sector, created_at

**stock_sentiment**: Individual stock sentiment
- id, stock_id, sentiment, score, article_count, updated_at

**sector_sentiment**: Sector-level aggregate sentiment
- id, sector, sentiment, score, updated_at

**market_sentiment**: Broad market sentiment
- id, sentiment, score, updated_at

**predictions**: Price range predictions
- id, stock_id, predicted_low, predicted_high, confidence, predicted_at, created_at

**price_history_5m**: 5-minute OHLCV candles
- id, stock_id, open, high, low, close, volume, timestamp

**news_cache**: Cached news articles
- id, stock_id, title, summary, content, source, url, published_at, fetched_at

## Configuration

### stocks.yaml
Define the stocks to monitor and their sectors:
```yaml
stocks:
  - symbol: AAPL
    sector: Technology
  - symbol: MSFT
    sector: Technology
  
sectors:
  Technology:
    - AAPL
    - MSFT
```

### settings.yaml
Configure application behavior:
- **llm**: OpenAI API settings (model, temperature, max_tokens)
- **news**: News fetching (update_interval, RSS feeds, max_articles)
- **technical**: Technical indicators and normalization
- **lstm**: Model architecture (layers, units, epochs)
- **prediction**: Prediction settings (window size, confidence threshold)
- **database**: SQLite path and settings

## How It Works

### Sentiment Analysis Pipeline (Part 1)

1. **News Fetching** (every 5-15 min):
   - Fetches latest articles from RSS feeds (CNBC, Reuters, MarketWatch)
   - Optionally scrapes stock-specific news from Yahoo Finance
   - Filters articles by age (< 24 hours) and relevance

2. **Sentiment Analysis**:
   - Sends article text to OpenAI API with prompt: "Analyze sentiment of [news] for [STOCK]"
   - Receives: sentiment (bullish/neutral/bearish), score (-1.0 to 1.0), confidence
   - Stores results in SQLite database

3. **Aggregation**:
   - Sector sentiment = average of constituent stock sentiments
   - Market sentiment = average of all stock sentiments

### Price Prediction Pipeline (Part 2)

1. **Data Preparation**:
   - Fetches last 100 5-min OHLCV candles from Yahoo Finance
   - Computes technical indicators (RSI, MACD, Bollinger Bands, MAs)
   - Normalizes indicators to [0, 1] range
   - Merges latest sentiment score

2. **Feature Creation**:
   - Creates feature vectors combining technical indicators + sentiment
   - Maintains 20-candle lookback window for LSTM

3. **LSTM Prediction**:
   - Passes feature vector through trained LSTM (3 layers: 128 → 64 → 32 units)
   - Outputs: (predicted_low, predicted_high) for next 5-min candle
   - Calculates confidence based on model state and feature variance

4. **Storage**:
   - Stores prediction in database with timestamp and confidence score

## Example Output

### Watch Mode
```
👀 Watching 10 stocks: AAPL, MSFT, GOOGL, TSLA, JPM, XOM, JNJ, PG, V, WMT
⏱️  Starting scheduler...
✅ Scheduler running. Press Ctrl+C to stop.
============================================================

[Update 1] ✅ Sentiment & Predictions Updated (45.2s)
  AAPL: BULLISH (0.67) from 23 articles → $185.20-$186.50 (conf: 0.78)
  MSFT: NEUTRAL (0.02) from 18 articles → $420.10-$422.80 (conf: 0.71)
  TSLA: BEARISH (-0.34) from 31 articles → $245.60-$248.90 (conf: 0.64)
  ...
```

### Prediction Output
```
📊 Predicting price range for AAPL...
✅ Prediction successful for AAPL
  Range: $185.20 - $186.50
  Current Price: $185.75
  Confidence: 0.78
```

## Technical Details

### LSTM Model Architecture
- **Input**: 32-dim feature vector (technical indicators + sentiment)
- **Layer 1**: LSTM (128 units) + Dropout (0.2)
- **Layer 2**: LSTM (64 units) + Dropout (0.2)
- **Layer 3**: LSTM (32 units)
- **Dense**: 64 units (ReLU)
- **Output**: 2 units (predicted_low, predicted_high)
- **Loss**: Mean Squared Error (MSE)
- **Optimizer**: Adam (lr=0.001)

### Training Strategy
- **Data**: Last 7 days of 5-min candles per stock
- **Lookback**: 20 candles → predict 1 candle ahead
- **Epochs**: 50 with early stopping (patience=5)
- **Batch Size**: 32
- **Validation Split**: 20%

### Sentiment Scoring
- **Range**: -1.0 (most bearish) to +1.0 (most bullish)
- **Neutral**: -0.1 to 0.1
- **Aggregation**: Simple average of article-level sentiments

## Advanced Features

### Retraining
Models are automatically retrained weekly, or manually with:
```bash
python app.py train --stock AAPL --force
```

### Custom Stock List
Edit `config/stocks.yaml` to add/remove stocks and sectors.

### Tuning
Adjust LSTM hyperparameters in `config/settings.yaml`:
- Change layers, units, dropout, epochs
- Modify technical indicators
- Adjust sentiment update frequency

## Testing

Run unit tests (when available):
```bash
pytest tests/
pytest --cov=src tests/
```

## Troubleshooting

### No News Found
- Check RSS feed URLs are accessible
- Verify internet connection
- Try `python app.py debug fetch-news --stock AAPL`

### API Errors
- Verify OpenAI API key in `.env`
- Check API rate limits and quota
- Fallback to neutral sentiment if API fails

### Insufficient Data
- Models need 100+ 5-min candles to train
- Wait 1-2 hours for enough historical data
- Check Yahoo Finance data availability for stock

### Model Not Trained
- LSTM model needs initial training before predictions
- Run: `python app.py train --stock AAPL`
- Predictions have lower confidence until model is trained

## Performance

- **News Fetching**: ~10-20s for 50 articles (cached)
- **Sentiment Analysis**: ~30-60s for 50 articles (OpenAI API calls)
- **Price Prediction**: ~1-2s per stock (LSTM inference)
- **Full Cycle**: ~2-3 minutes for 10 stocks

## Future Enhancements

- [ ] Backtesting module to validate predictions against historical prices
- [ ] Multi-model ensemble (LSTM + XGBoost + Statistical models)
- [ ] Real-time WebSocket data feed instead of polling
- [ ] Django/FastAPI REST API wrapper
- [ ] Web dashboard with real-time charts
- [ ] Trade signal generation and alerts
- [ ] Risk management and portfolio optimization
- [ ] Support for cryptocurrency and forex

## Dependencies

Key libraries:
- **Data**: yfinance, pandas, numpy
- **ML/DL**: tensorflow, scikit-learn
- **LLM**: openai
- **Data Fetching**: feedparser, requests, beautifulsoup4
- **Technical Indicators**: ta
- **Scheduling**: APScheduler
- **CLI**: click
- **Configuration**: pyyaml, pydantic

## License

MIT License - feel free to use, modify, and distribute.

## Support

For issues, questions, or feature requests, refer to the plan document (`/memories/session/plan.md`) or modify the application as needed.

---

**Last Updated**: April 23, 2026
**Version**: 1.0.0 (Initial Release)
