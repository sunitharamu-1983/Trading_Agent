"""
agent/agent.py
──────────────
Main agent loop — ties together Tavily search, tools, and LLM analysis.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from agent.tavily_search import TavilySearchClient
from agent.tools import get_news_for_ticker, get_macro_context, get_company_deep_dive
from agent.prompts import SYSTEM_PROMPT, build_analysis_prompt
from config.settings import WATCH_LIST

load_dotenv()
logger = logging.getLogger(__name__)


def run_analysis(tickers: list[str] | None = None) -> dict[str, str]:
    """
    Run a single analysis pass for the given tickers.

    1. Initialise Tavily client
    2. Fetch macro context once (shared across all tickers)
    3. For each ticker: fetch news, build prompt, optionally call LLM

    Returns:
        Dict mapping ticker → analysis text (or context string if no LLM key).
    """
    tickers = tickers or WATCH_LIST

    # ── Tavily client ──────────────────────────────────────────────────────
    try:
        tavily = TavilySearchClient()
    except EnvironmentError as e:
        logger.error(e)
        raise

    # ── Macro context (fetched once) ───────────────────────────────────────
    logger.info("Fetching macro context…")
    macro_context = get_macro_context(tavily)

    results: dict[str, str] = {}

    for ticker in tickers:
        logger.info("Analysing %s…", ticker)
        news_context = get_news_for_ticker(tavily, ticker)
        prompt       = build_analysis_prompt(ticker, news_context, macro_context)

        # ── Optional LLM analysis ──────────────────────────────────────────
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import OpenAI
                llm    = OpenAI(api_key=openai_key)
                resp   = llm.chat.completions.create(
                    model    = "gpt-4o-mini",
                    messages = [
                        {"role": "system",  "content": SYSTEM_PROMPT},
                        {"role": "user",    "content": prompt},
                    ],
                    max_tokens  = 400,
                    temperature = 0.2,
                )
                analysis = resp.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning("LLM call failed for %s: %s", ticker, exc)
                analysis = prompt  # fall back to raw context
        else:
            # No LLM key — return the assembled context for manual inspection
            analysis = prompt

        results[ticker] = analysis

    return results
