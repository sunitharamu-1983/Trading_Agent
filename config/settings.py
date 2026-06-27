"""
Non-secret configuration — safe to commit.
Secrets (API keys) go in .env only.
"""

# ── Tavily search settings ─────────────────────────────────────────────────
TAVILY_SEARCH_DEPTH = "advanced"   # "basic" | "advanced"
TAVILY_MAX_RESULTS  = 5            # results per query
TAVILY_TIME_RANGE   = "week"       # "day" | "week" | "month" | None
TAVILY_MIN_SCORE    = 0.5          # discard results below this relevance score

# Domains to prioritise for financial news
TAVILY_INCLUDE_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "cnbc.com",
    "marketwatch.com",
    "finance.yahoo.com",
    "seekingalpha.com",
    "investing.com",
]

# ── Default watch-list ─────────────────────────────────────────────────────
WATCH_LIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "SPY"]

# ── Agent loop settings ────────────────────────────────────────────────────
AGENT_LOOP_INTERVAL_SECONDS = 60   # how often the agent re-evaluates
