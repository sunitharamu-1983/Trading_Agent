# Trading Agent

Weekend class project exploring agentic/vibe coding techniques applied to automated trading.

The agent fetches real-time financial news via Tavily, builds analysis prompts per ticker, and optionally routes them through an OpenAI LLM for a structured market outlook. It runs without an LLM key too — it just returns the assembled context for manual inspection.

---

## Quick Start

```bash
# 1. Clone and enter the project
cd "Sunitha - Trading_Agent"

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up secrets
cp .env.example .env
# Edit .env and add your API keys
```

---

## Usage

### Run full analysis (default watch list)

```bash
python main.py
```

Analyses all tickers in `config/settings.py → WATCH_LIST` (default: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, SPY).

### Analyse specific tickers

```bash
python main.py analyse --tickers AAPL TSLA NVDA
```

### Ad-hoc Tavily search

Useful for quick lookups during development — no LLM key required.

```bash
python main.py search "Fed rate cut impact on tech stocks"
```

---

## Project Structure

```
Trading_Agent/
├── main.py             # Entry point — CLI with analyse and search sub-commands
├── agent/
│   ├── agent.py        # run_analysis(): orchestrates Tavily + LLM analysis
│   ├── tavily_search.py# TavilySearchClient and high-level search helpers
│   ├── tools.py        # Tool functions: get_news_for_ticker, get_macro_context, etc.
│   └── prompts.py      # System prompt and per-ticker prompt builder
├── backend/            # Bullish Ticker Analyzer — FastAPI service
│   ├── main.py         # FastAPI app, CORS config, /api/health, /api/watchlist, /api/analyze
│   ├── analyzer.py     # OHLCV fetch, RSI/SMA/MACD/Volume indicators, scoring
│   ├── models.py       # Pydantic request/response schemas (incl. WatchlistResponse)
│   ├── watchlist.py    # Nifty 50 ticker list in yfinance (.NS) format
│   ├── requirements.txt# Pinned backend dependencies (isolated from root)
│   └── tests/          # pytest + hypothesis property tests
├── config/
│   └── settings.py     # Non-secret config: watch list, Tavily defaults, loop interval
├── .env.example        # Template — copy to .env and fill in keys
├── requirements.txt    # Pinned dependencies (agent)
└── README.md
```

---

## Configuration

Non-secret settings live in `config/settings.py` and are safe to commit:

| Setting | Default | Description |
|---|---|---|
| `WATCH_LIST` | 7 tickers | Tickers analysed by default |
| `TAVILY_SEARCH_DEPTH` | `"advanced"` | Tavily search depth (`"basic"` or `"advanced"`) |
| `TAVILY_MAX_RESULTS` | `5` | Results fetched per query |
| `TAVILY_TIME_RANGE` | `"week"` | Recency filter (`"day"`, `"week"`, `"month"`) |
| `TAVILY_MIN_SCORE` | `0.5` | Minimum relevance score to keep a result |
| `AGENT_LOOP_INTERVAL_SECONDS` | `60` | Re-evaluation interval (for continuous mode) |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys. Never commit `.env`.

| Variable | Required | Description |
|---|---|---|
| `TAVILY_API_KEY` | Yes | [Tavily](https://app.tavily.com) search API key |
| `OPENAI_API_KEY` | Optional | GPT-4o-mini analysis. Without it, raw context is printed instead |
| `ALPACA_API_KEY` | Optional | Alpaca paper trading API key |
| `ALPACA_SECRET_KEY` | Optional | Alpaca paper trading secret |
| `ALPACA_BASE_URL` | Optional | Defaults to paper trading endpoint |

---

## Bullish Ticker Analyzer (Frontend)

A React + TypeScript + Vite UI built with [AWS CloudScape](https://cloudscape.design/) components.

### Setup

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if backend runs on a non-default port
npm run dev
```

The dev server starts at `http://localhost:5173` by default.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

Copy `frontend/.env.example` to `frontend/.env` and override `VITE_API_BASE_URL` if your backend runs on a different host or port.

### Run frontend tests

```bash
cd frontend
npx vitest run
```

---

## Bullish Ticker Analyzer (Backend)

A standalone FastAPI service that accepts a list of tickers and returns them ranked by bullishness score using four technical indicators.

### Run the backend

```bash
cd backend

# Install backend-specific dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

The API is then available at `http://localhost:8000`.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness check — returns `{"status": "ok"}` |
| `GET` | `/api/watchlist` | Returns the Nifty 50 ticker list (`tickers`, `label`) for UI auto-population |
| `POST` | `/api/analyze` | Accepts `{"tickers": ["AAPL", "TSLA"]}`, returns ranked results |

### Scoring

Each ticker is scored 0–4 based on these rules:

| Rule | Condition |
|---|---|
| RSI ≤ 40 | 14-period Wilder RSI below oversold threshold |
| Price > 50d SMA | Last close above 50-day simple moving average |
| MACD Crossover | MACD line crossed above signal line in last bar |
| Volume Surge | Last volume ≥ 1.2× 20-day average volume |

Scores map to signals: **4 → Strong Buy**, **3 → Bullish**, **1–2 → Neutral**, **0 → Bearish**.

### Backend dependencies

Minimum-version bounds are used to support Python 3.14+ (avoids source compilation issues with pre-release wheels).

| Package | Min Version | Purpose |
|---|---|---|
| `fastapi` | ≥ 0.111.0 | API framework |
| `uvicorn` | ≥ 0.29.0 | ASGI server |
| `yfinance` | ≥ 0.2.40 | OHLCV market data |
| `pandas` | ≥ 2.2.0 | Data processing |
| `numpy` | ≥ 1.26.0 | Numerical utilities |
| `pydantic` | ≥ 2.7.0 | Request/response validation |
| `httpx` | ≥ 0.27.0 | Async HTTP client |
| `pytest` | ≥ 8.0.0 | Test runner |
| `hypothesis` | ≥ 6.100.0 | Property-based testing |

### Run backend tests

```bash
pytest backend/tests/ -v
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `tavily-python` | 0.5.1 | Financial news search |
| `openai` | 1.40.0 | LLM analysis (optional) |
| `python-dotenv` | 1.0.1 | Secret management via `.env` |
| `yfinance` | 0.2.40 | Market data |
| `pandas` | 2.2.2 | Data processing |
| `numpy` | 1.26.4 | Numerical utilities |
| `requests` | 2.32.3 | HTTP client |
