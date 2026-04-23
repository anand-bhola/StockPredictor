# 📊 Stock Predictor - Visual Architecture & Diagrams

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Data Sources"
        RSS["📰 RSS Feeds<br/>CNBC, Reuters, MarketWatch"]
        WS["🌐 Web Scraping<br/>Yahoo Finance"]
        YF["💹 Price Data<br/>Yahoo Finance API"]
    end
    
    subgraph "Data Processing"
        NF["📥 News Fetcher"]
        PD["📊 Price Loader"]
        TD["🔬 Technical Indicators<br/>RSI, MACD, BB, MA"]
    end
    
    subgraph "AI/ML Layer"
        LLM["🧠 OpenAI GPT<br/>Sentiment Analysis"]
        FE["⚙️ Feature Engineering<br/>Normalize & Combine"]
        LSTM["🤖 LSTM Model<br/>3 Layers: 128→64→32"]
    end
    
    subgraph "Storage & Output"
        DB["🗄️ SQLite Database<br/>Stocks, Sentiment, Predictions"]
        CLI["💻 CLI Interface<br/>15 Commands"]
    end
    
    RSS --> NF
    WS --> NF
    YF --> PD
    NF --> LLM
    PD --> TD
    LLM --> FE
    TD --> FE
    FE --> LSTM
    LSTM --> DB
    DB --> CLI
```

---

## Data Flow Pipeline

```mermaid
graph LR
    A["📰 Fetch News<br/>5 articles"] 
    --> B["🧠 LLM Analysis<br/>OpenAI GPT"]
    --> C["📊 Get Sentiment<br/>Score: -1 to +1"]
    --> D["💾 Store Sentiment"]
    
    E["💹 Fetch Price Data<br/>Yahoo Finance"]
    --> F["🔬 Calculate<br/>13 Indicators"]
    --> G["⚙️ Normalize<br/>Features"]
    --> H["🤖 LSTM<br/>Inference"]
    --> I["🎯 Predictions<br/>Low & High Price"]
    --> D
    
    D --> J["📊 Display<br/>CLI Output"]
```

---

## Complete Workflow (Minute by Minute)

```mermaid
gantt
    title Stock Predictor Update Cycle (2-3 minutes)
    dateFormat YYYY-MM-DD HH:mm:ss
    
    section Tasks
    Fetch News           :t1, 2026-04-23 14:00:00, 30s
    OpenAI Analysis      :t2, 2026-04-23 14:00:30, 40s
    Calc Sentiment       :t3, 2026-04-23 14:01:10, 10s
    Fetch Price Data     :t4, 2026-04-23 14:01:20, 20s
    Calc Indicators      :t5, 2026-04-23 14:01:40, 20s
    Normalize Features   :t6, 2026-04-23 14:02:00, 10s
    LSTM Inference       :t7, 2026-04-23 14:02:10, 20s
    Store Predictions    :t8, 2026-04-23 14:02:30, 10s
    Ready for Next       :crit, 2026-04-23 14:02:40, 0s
```

---

## LSTM Model Architecture

```mermaid
graph TD
    Input["📥 Input Layer<br/>(32 dimensions)<br/><br/>• 13 Tech Indicators<br/>• Price Features<br/>• Sentiment Score"]
    
    L1["LSTM Layer 1<br/>128 Units<br/>ReLU Activation"]
    L2["LSTM Layer 2<br/>64 Units<br/>ReLU Activation"]
    L3["LSTM Layer 3<br/>32 Units<br/>ReLU Activation"]
    
    Dense["Dense Output Layer<br/>(2 Units)<br/>Linear Activation"]
    
    PredLow["🎯 Predicted Low<br/>Next 5-min Candle"]
    PredHigh["🎯 Predicted High<br/>Next 5-min Candle"]
    
    Input --> L1
    L1 --> L2
    L2 --> L3
    L3 --> Dense
    Dense --> PredLow
    Dense --> PredHigh
    
    style Input fill:#e1f5ff
    style L1 fill:#fff3e0
    style L2 fill:#fff3e0
    style L3 fill:#fff3e0
    style Dense fill:#f3e5f5
    style PredLow fill:#c8e6c9
    style PredHigh fill:#c8e6c9
```

---

## Feature Vector Composition

```mermaid
graph LR
    subgraph "Technical Indicators (13)"
        TI1["RSI"]
        TI2["MACD"]
        TI3["Bollinger Bands"]
        TI4["SMA 20/50/200"]
        TI5["EMA 12/26"]
        TI6["ATR"]
        TI7["Volume"]
    end
    
    subgraph "Price Features (2)"
        PF1["Price Change Ratio"]
        PF2["Open-Close Delta"]
    end
    
    subgraph "Sentiment (1)"
        SF["Sentiment Score<br/>Normalized -1 to +1"]
    end
    
    TI1 --> FV["Features Vector<br/>(32 dimensions)"]
    TI2 --> FV
    TI3 --> FV
    TI4 --> FV
    TI5 --> FV
    TI6 --> FV
    TI7 --> FV
    PF1 --> FV
    PF2 --> FV
    SF --> FV
    
    style TI1 fill:#fff3e0
    style TI2 fill:#fff3e0
    style TI3 fill:#fff3e0
    style TI4 fill:#fff3e0
    style TI5 fill:#fff3e0
    style TI6 fill:#fff3e0
    style TI7 fill:#fff3e0
    style PF1 fill:#e3f2fd
    style PF2 fill:#e3f2fd
    style SF fill:#f3e5f5
    style FV fill:#c8e6c9
```

---

## Sentiment Analysis Flow

```mermaid
graph TD
    subgraph "News Collection"
        RS["RSS Feeds<br/>CNBC, Reuters, MarketWatch"]
        WS["Web Scraping<br/>Yahoo Finance"]
    end
    
    subgraph "Processing"
        FT["Fetch Latest<br/>5 Articles"]
        DED["Deduplicate<br/>& Filter"]
    end
    
    subgraph "LLM Analysis"
        PREP["Prepare Prompt<br/>with Stock Context"]
        API["Call OpenAI<br/>GPT-3.5-turbo"]
        PARSE["Parse JSON<br/>Response"]
    end
    
    subgraph "Aggregation"
        STOCK["Stock Sentiment<br/>Average"]
        SECT["Sector Sentiment<br/>Mean of Stocks"]
        MKT["Market Sentiment<br/>Overall Average"]
    end
    
    OUTPUT["Store in DB<br/>& Display"]
    
    RS --> FT
    WS --> FT
    FT --> DED
    DED --> PREP
    PREP --> API
    API --> PARSE
    PARSE --> STOCK
    STOCK --> SECT
    SECT --> MKT
    MKT --> OUTPUT
    
    style RS fill:#fff3e0
    style WS fill:#fff3e0
    style FT fill:#e3f2fd
    style DED fill:#e3f2fd
    style PREP fill:#f3e5f5
    style API fill:#f3e5f5
    style PARSE fill:#f3e5f5
    style STOCK fill:#c8e6c9
    style SECT fill:#c8e6c9
    style MKT fill:#c8e6c9
    style OUTPUT fill:#ffccbc
```

---

## Database Schema Relationships

```mermaid
graph LR
    subgraph "Core Entity"
        ST["📦 STOCKS<br/>───────<br/>id (PK)<br/>symbol<br/>sector<br/>created_at"]
    end
    
    subgraph "Sentiment History"
        SS["📊 STOCK_SENTIMENT<br/>───────<br/>id (PK)<br/>stock_id (FK)<br/>sentiment<br/>score<br/>timestamp"]
    end
    
    subgraph "Predictions"
        PP["🎯 PRICE_PREDICTIONS<br/>───────<br/>id (PK)<br/>stock_id (FK)<br/>predicted_low<br/>predicted_high<br/>confidence<br/>timestamp"]
    end
    
    subgraph "News & Articles"
        NA["📰 NEWS_ARTICLES<br/>───────<br/>id (PK)<br/>stock_id (FK)<br/>title<br/>summary<br/>url<br/>fetched_at"]
    end
    
    ST -->|1:M| SS
    ST -->|1:M| PP
    ST -->|1:M| NA
```

---

## Command Hierarchy

```mermaid
graph TB
    Root["python app.py"]
    
    Root --> Predict["predict<br/>--stock AAPL<br/><br/>Get price prediction"]
    Root --> Sentiment["sentiment<br/>--stock MSFT<br/><br/>Get sentiment score"]
    Root --> Train["train<br/>--stock TSLA<br/><br/>Train LSTM model"]
    Root --> Watch["watch<br/><br/>Continuous monitoring"]
    Root --> Health["health<br/><br/>System status"]
    Root --> Debug["debug<br/>Multiple subcommands"]
    
    Debug --> D1["init-stocks<br/>Initialize DB"]
    Debug --> D2["fetch-news<br/>Get latest articles"]
    Debug --> D3["analyze-news<br/>Run LLM analysis"]
    Debug --> D4["show-latest<br/>Display predictions"]
    Debug --> D5["show-config<br/>Configuration info"]
    Debug --> D6["run-cycle<br/>Single update"]
```

---

## Indicator Calculation Timeline

```mermaid
timeline
    title Technical Indicators Calculation Order
    section Fast Indicators (< 5 ms each)
        RSI : Relative Strength Index
        SMA : Simple Moving Average
        EMA : Exponential Moving Average
        Volume : Volume Analysis
    section Medium Indicators (5-10 ms each)
        MACD : Moving Average Convergence
        Bollinger : Bollinger Bands
        ATR : Average True Range
    section Complete Feature Vector (5 ms)
        Normalize : Scale to 0-1
    section Total Time
        All Indicators : < 100 ms total
```

---

## Sentiment Score Interpretation

```mermaid
graph LR
    VB["Very Bullish<br/>+0.75 to +1.0<br/>🚀 Strong Buy"]
    B["Bullish<br/>+0.25 to +0.75<br/>📈 Buy"]
    N["Neutral<br/>-0.25 to +0.25<br/>➡️ Hold"]
    BR["Bearish<br/>-0.75 to -0.25<br/>📉 Sell"]
    VBR["Very Bearish<br/>-1.0 to -0.75<br/>⚠️ Strong Sell"]
    
    VB --> Range["Sentiment Range: -1.0 to +1.0"]
    B --> Range
    N --> Range
    BR --> Range
    VBR --> Range
    
    style VB fill:#a5d6a7
    style B fill:#c8e6c9
    style N fill:#ffe0b2
    style BR fill:#ffccbc
    style VBR fill:#ef9a9a
```

---

## Model Training Process

```mermaid
graph TD
    subgraph "Data Preparation"
        DP["Fetch historical data<br/>100-200 candles"]
        CI["Calculate indicators<br/>13+ features"]
        NM["Normalize features<br/>Scale 0-1"]
        SEQ["Create sequences<br/>Time windows"]
    end
    
    subgraph "Model Training"
        SPLIT["Train/Val Split<br/>80/20"]
        TRAIN["Train LSTM<br/>MSE Loss"]
        ES["Early Stopping<br/>Patience=10"]
    end
    
    subgraph "Evaluation"
        VAL["Validate on test set<br/>Calculate RMSE"]
        SAVE["Save model<br/>to disk"]
    end
    
    subgraph "Deployment"
        LOAD["Load model<br/>inference mode"]
        INF["Run inference<br/>< 2 sec"]
        PRED["Generate predictions<br/>Low & High"]
    end
    
    DP --> CI
    CI --> NM
    NM --> SEQ
    SEQ --> SPLIT
    SPLIT --> TRAIN
    TRAIN --> ES
    ES --> VAL
    VAL --> SAVE
    SAVE --> LOAD
    LOAD --> INF
    INF --> PRED
```

---

## Error Handling & Recovery

```mermaid
graph TD
    Try["Execute Task"]
    
    Try -->|Success| Save["Save Results"]
    Try -->|API Error| Retry["Retry (3x)<br/>with backoff"]
    Try -->|Network| Retry
    Try -->|Data Error| Log["Log Error<br/>& Continue"]
    
    Retry -->|Still Fails| Cache["Use Cached<br/>Data"]
    Retry -->|Success| Save
    
    Log --> Skip["Skip Stock<br/>Next Cycle"]
    Cache --> Skip
    
    Save --> Next["Ready for<br/>Next Update"]
    Skip --> Next
    
    style Try fill:#e3f2fd
    style Save fill:#c8e6c9
    style Retry fill:#fff9c4
    style Cache fill:#ffccbc
    style Log fill:#ffccbc
    style Skip fill:#ef9a9a
    style Next fill:#a5d6a7
```

---

## Performance Metrics Dashboard

```mermaid
graph LR
    subgraph "Real-Time Metrics"
        TS["Sentiment Score<br/>-1.0 to +1.0"]
        TC["Sentiment Trend<br/>📈📉➡️"]
        TR["RSI<br/>0-100"]
        TM["MACD<br/>Histogram"]
    end
    
    subgraph "Predictions"
        PL["Predicted Low<br/>Price"]
        PH["Predicted High<br/>Price"]
        PC["Confidence<br/>0-100%"]
    end
    
    subgraph "Portfolio Level"
        SS["Sector Sentiment<br/>Aggregated"]
        MS["Market Sentiment<br/>Overall"]
        TP["Top Performers<br/>Ranked"]
    end
    
    TS --> Dashboard["📊 Live Dashboard"]
    TC --> Dashboard
    TR --> Dashboard
    TM --> Dashboard
    PL --> Dashboard
    PH --> Dashboard
    PC --> Dashboard
    SS --> Dashboard
    MS --> Dashboard
    TP --> Dashboard
    
    style TS fill:#fff3e0
    style TC fill:#fff3e0
    style TR fill:#fff3e0
    style TM fill:#fff3e0
    style PL fill:#e3f2fd
    style PH fill:#e3f2fd
    style PC fill:#e3f2fd
    style SS fill:#f3e5f5
    style MS fill:#f3e5f5
    style TP fill:#f3e5f5
```

---

## Integration Points

```mermaid
graph TB
    APIExt["External APIs"]
    OpenAI["🔗 OpenAI API<br/>Sentiment Analysis"]
    YahooF["🔗 Yahoo Finance<br/>Price Data"]
    RSS["🔗 RSS Feeds<br/>News Sources"]
    
    Core["Core Application"]
    Config["⚙️ Configuration<br/>YAML Files"]
    Cache["💾 Cache<br/>Local Storage"]
    
    Output["Output Channels"]
    CLI["💻 CLI Commands"]
    DB["🗄️ SQLite DB"]
    
    APIExt --> OpenAI
    APIExt --> YahooF
    APIExt --> RSS
    
    OpenAI --> Core
    YahooF --> Core
    RSS --> Core
    
    Config --> Core
    Cache --> Core
    
    Core --> CLI
    Core --> DB
    
    style APIExt fill:#ffebee
    style Core fill:#e3f2fd
    style Output fill:#c8e6c9
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        VS["Visual Studio Code<br/>Python 3.13"]
        Git["Git Repository<br/>Version Control"]
    end
    
    subgraph "Environment"
        Venv["Virtual Environment<br/>Isolated Python"]
        Deps["Dependencies<br/>requirements.txt"]
    end
    
    subgraph "Data"
        DB["SQLite Database<br/>Local Storage"]
        Models["LSTM Models<br/>Serialized"]
        Cache["Cache Files<br/>News & Prices"]
    end
    
    subgraph "Execution"
        Scheduler["APScheduler<br/>Background Tasks"]
        CLI["Click CLI<br/>User Interface"]
    end
    
    VS --> Git
    Git --> Venv
    Deps --> Venv
    Venv --> Scheduler
    Venv --> CLI
    Scheduler --> DB
    Scheduler --> Models
    CLI --> Models
```

---

## Key Success Factors

```mermaid
graph LR
    subgraph "Data Quality"
        DQ1["✓ Real-time feeds"]
        DQ2["✓ Multiple sources"]
        DQ3["✓ Deduplication"]
    end
    
    subgraph "Analysis Quality"
        AQ1["✓ LLM accuracy"]
        AQ2["✓ Proper indicators"]
        AQ3["✓ Feature engineering"]
    end
    
    subgraph "Model Quality"
        MQ1["✓ LSTM architecture"]
        MQ2["✓ Early stopping"]
        MQ3["✓ Confidence scoring"]
    end
    
    subgraph "System Reliability"
        SR1["✓ Error handling"]
        SR2["✓ Retry logic"]
        SR3["✓ Caching"]
    end
    
    DQ1 --> Success["✅ Reliable<br/>Predictions"]
    DQ2 --> Success
    DQ3 --> Success
    AQ1 --> Success
    AQ2 --> Success
    AQ3 --> Success
    MQ1 --> Success
    MQ2 --> Success
    MQ3 --> Success
    SR1 --> Success
    SR2 --> Success
    SR3 --> Success
    
    style Success fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
```

---

## Next Steps & Roadmap

```mermaid
timeline
    title Project Roadmap
    section Phase 1: Current
        Version 1.0 : ✅ Complete
        : • Core sentiment analysis
        : • Technical indicators
        : • LSTM model
        : • SQLite storage
        : • CLI interface
    
    section Phase 2: Planned
        Q3 2026 : 🔄 In Progress
        : • Crypto support
        : • WebSocket feeds
        : • Ensemble models
        : • API endpoint
    
    section Phase 3: Future
        Q4 2026 : 📋 Planned
        : • Automated trading
        : • Portfolio optimization
        : • Risk management
        : • Cloud deployment
    
    section Phase 4: Vision
        2027+ : 🌟 Long-term
        : • Multi-language NLP
        : • Reinforcement learning
        : • Social sentiment
        : • Real-time execution
```

---

*These diagrams provide a visual understanding of the Stock Predictor system architecture and data flows.*

