"""
agent/tools.py
──────────────
Tool definitions the agent can invoke during its decision loop.
Each tool is a plain function that accepts structured input and returns
a string (or dict) the agent can reason over.
"""

from __future__ import annotations

import logging
from typing import Optional

from agent.tavily_search import (
    TavilySearchClient,
    SearchResponse,
    search_market_news,
    search_topic,
    search_company,
    batch_search,
)

logger = logging.getLogger(__name__)


def get_news_for_ticker(
    client: TavilySearchClient,
    ticker: str,
    time_range: str = "week",
) -> str:
    """
    Agent tool: fetch and format recent news for a single ticker.
    Returns a context string ready for LLM consumption.
    """
    response = search_market_news(client, [ticker], time_range=time_range)
    sr: SearchResponse = response.get(ticker)
    if sr is None or sr.error:
        return f"Could not retrieve news for {ticker}: {getattr(sr, 'error', 'unknown error')}"
    if not sr.results:
        return f"No relevant news found for {ticker} in the last {time_range}."
    return sr.as_context_string(max_results=3)


def get_macro_context(
    client: TavilySearchClient,
    topics: list[str] | None = None,
) -> str:
    """
    Agent tool: fetch macro-economic context across several topics.
    Returns a combined context string.
    """
    if topics is None:
        topics = [
            "Federal Reserve interest rate decision",
            "US inflation CPI report",
            "S&P 500 market outlook",
        ]
    responses = batch_search(client, topics, time_range="week")
    sections = []
    for resp in responses:
        if resp.error:
            sections.append(f"[{resp.query}] ERROR: {resp.error}")
        else:
            sections.append(resp.as_context_string(max_results=2))
    return "\n\n---\n\n".join(sections)


def get_company_deep_dive(
    client: TavilySearchClient,
    ticker: str,
) -> str:
    """
    Agent tool: deep-dive company research (earnings, ratings, filings).
    Returns a context string.
    """
    resp = search_company(client, ticker)
    if resp.error:
        return f"Deep-dive failed for {ticker}: {resp.error}"
    if not resp.results:
        return f"No deep-dive results found for {ticker}."
    return resp.as_context_string(max_results=5)
