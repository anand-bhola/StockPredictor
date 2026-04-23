# SETUP & INSTALLATION GUIDE

## Quick Start

### 1. Prerequisites
Ensure you have Python 3.11+ installed. If not, download from https://www.python.org/

### 2. Install Dependencies

```bash
cd D:\StockPredictor
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure OpenAI API

Create `.env` file with your OpenAI API key:

```bash
# Copy example file
copy .env.example .env

# Edit .env and add:
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. Initialize Database

```bash
python app.py debug init-stocks
```

### 5. Run Application

#### Option A: Watch Mode (Continuous Monitoring)
```bash
python app.py watch
```

#### Option B: Single Update Cycle
```bash
python app.py debug run-cycle
```

#### Option C: Check Status
```bash
python app.py health
```

## Detailed Installation

### Windows

1. **Install Python 3.11+** from https://www.python.org/downloads/

2. **Clone the repository**
   ```powershell
   cd D:\StockPredictor
   ```

3. **Create virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   
   If you get an execution policy error, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure API key**
   ```powershell
   copy .env.example .env
   # Edit .env with your OpenAI API key
   notepad .env
   ```

6. **Initialize**
   ```powershell
   python app.py debug init-stocks
   ```

### macOS/Linux

1. **Install Python 3.10+**
   ```bash
   # macOS with Homebrew
   brew install python@3.10
   
   # Or from https://www.python.org/downloads/
   ```

2. **Clone repository**
   ```bash
   cd ~/repos/StockPrediction
   ```

3. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   nano .env
   ```

6. **Initialize**
   ```bash
   python app.py debug init-stocks
   ```

## Verification

After installation, verify everything works:

```bash
# Check configuration
python app.py debug show-config

# Initialize stocks
python app.py debug init-stocks

# Test news fetching
python app.py debug fetch-news --stock AAPL

# Check health
python app.py health
```

## Troubleshooting

### Python not found
- Ensure Python is installed from https://www.python.org/
- Check `python --version` in terminal
- On Windows, restart terminal or add Python to PATH

### OpenAI API errors
- Verify API key is correctly set in `.env`
- Check API quota and rate limits at https://platform.openai.com/account/billing/overview
- Ensure API key has correct permissions

### No news found
- Internet connection may be blocked
- Try accessing feeds directly: https://feeds.cnbc.com/cnbcnews
- Check firewall/proxy settings

### TensorFlow installation issues
- On Windows: May need Visual C++ redistributables
- Try: `pip install tensorflow --upgrade`
- Consider using CPU-only version if GPU is unavailable

### Database errors
- Ensure `data/` directory exists and is writable
- Try deleting `data/stock_predictor.db` and reinitializing
- Check file permissions

## Next Steps

1. **Initial Training**: Train LSTM models for stocks
   ```bash
   python app.py train --stock AAPL
   python app.py train --stock MSFT
   ```

2. **Add More Stocks**: Edit `config/stocks.yaml`

3. **Monitor Live**: Start watch mode
   ```bash
   python app.py watch
   ```

4. **Customize Settings**: Edit `config/settings.yaml`
   - Adjust news update interval
   - Modify LSTM hyperparameters
   - Add custom RSS feeds

## Support

For issues:
1. Check README.md for detailed documentation
2. Review logs: `logs/stock_predictor.log`
3. Test components individually:
   - `python app.py debug fetch-news --stock AAPL`
   - `python app.py debug analyze-news --stock AAPL`
   - `python app.py debug show-latest --stock AAPL`

---

**Installation Checklist:**
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API key configured in `.env`
- [ ] Stocks initialized (`python app.py debug init-stocks`)
- [ ] Health check passes (`python app.py health`)
- [ ] Can fetch news (`python app.py debug fetch-news --stock AAPL`)
