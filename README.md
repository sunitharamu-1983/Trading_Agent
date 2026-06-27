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
├── config/
│   └── settings.py     # Non-secret config: watch list, Tavily defaults, loop interval
├── .env.example        # Template — copy to .env and fill in keys
├── requirements.txt    # Pinned dependencies
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
