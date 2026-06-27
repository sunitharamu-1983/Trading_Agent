"""
agent/prompts.py
────────────────
System and user prompt templates for the trading agent.
"""

SYSTEM_PROMPT = """\
You are a disciplined, risk-aware trading analyst assistant.
You receive real-time market news and research gathered from the web.
Your job is to:
1. Summarise the most relevant information for each ticker.
2. Identify bullish or bearish signals from the news.
3. Suggest a brief action note: BUY / SELL / HOLD / WATCH, with a one-sentence rationale.
Always caveat that this is for educational purposes only — not financial advice.
"""

def build_analysis_prompt(ticker: str, news_context: str, macro_context: str) -> str:
    return f"""\
Ticker: {ticker}

=== Recent News ===
{news_context}

=== Macro Context ===
{macro_context}

Based on the above, provide:
- A 2–3 sentence news summary for {ticker}
- Key bullish signals (if any)
- Key bearish signals (if any)
- Suggested action: BUY / SELL / HOLD / WATCH with a one-line rationale
"""
