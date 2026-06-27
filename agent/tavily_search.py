"""
agent/tavily_search.py
──────────────────────
Tavily connection and search routines for the Trading Agent.

Provides:
  - TavilySearchClient  : thin wrapper around tavily-python with config defaults
  - search_market_news  : search financial news for one or more ticker symbols
  - search_topic        : free-form topic search (macro events, sector trends, etc.)
  - search_company      : company-specific research (earnings, sentiment, filings)
  - batch_search        : run multiple queries and merge results
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from tavily import TavilyClient

from config.settings import (
    TAVILY_SEARCH_DEPTH,
    TAVILY_MAX_RESULTS,
    TAVILY_TIME_RANGE,
    TAVILY_MIN_SCORE,
    TAVILY_INCLUDE_DOMAINS,
)

# ── Logging ────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── Load .env secrets ──────────────────────────────────────────────────────
load_dotenv()


# ── Data classes ───────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """A single normalised search result."""
    title:   str
    url:     str
    content: str
    score:   float
    query:   str = ""

    def __repr__(self) -> str:
        return f"SearchResult(score={self.score:.2f}, title={self.title!r})"


@dataclass
class SearchResponse:
    """Aggregated response from a Tavily search call."""
    query:    str
    results:  list[SearchResult] = field(default_factory=list)
    answer:   Optional[str]      = None   # Tavily's AI-generated summary (if returned)
    error:    Optional[str]      = None

    @property
    def top(self) -> Optional[SearchResult]:
        """Return the highest-scored result, or None if empty."""
        return self.results[0] if self.results else None

    def as_context_string(self, max_results: int = 3) -> str:
        """
        Render results as a compact string suitable for injection into
        an LLM prompt.
        """
        lines = [f"Query: {self.query}"]
        if self.answer:
            lines.append(f"Summary: {self.answer}")
        for i, r in enumerate(self.results[:max_results], 1):
            lines.append(f"[{i}] {r.title} (score={r.score:.2f})")
            lines.append(f"    {r.url}")
            lines.append(f"    {r.content[:300]}...")
        return "\n".join(lines)


# ── Client ─────────────────────────────────────────────────────────────────

class TavilySearchClient:
    """
    Thin wrapper around TavilyClient that applies project-level defaults
    and enforces score filtering.

    Usage:
        client = TavilySearchClient()
        response = client.search("NVDA earnings beat")
    """

    def __init__(
        self,
        api_key:        Optional[str] = None,
        search_depth:   str           = TAVILY_SEARCH_DEPTH,
        max_results:    int           = TAVILY_MAX_RESULTS,
        time_range:     Optional[str] = TAVILY_TIME_RANGE,
        min_score:      float         = TAVILY_MIN_SCORE,
        include_domains: list[str]    = TAVILY_INCLUDE_DOMAINS,
    ):
        resolved_key = api_key or os.getenv("TAVILY_API_KEY")
        if not resolved_key:
            raise EnvironmentError(
                "TAVILY_API_KEY is not set. "
                "Add it to your .env file or pass api_key= explicitly."
            )

        self._client         = TavilyClient(api_key=resolved_key)
        self.search_depth    = search_depth
        self.max_results     = max_results
        self.time_range      = time_range
        self.min_score       = min_score
        self.include_domains = include_domains
        logger.info("TavilySearchClient initialised (depth=%s, max=%d)", search_depth, max_results)

    # ── Core search ────────────────────────────────────────────────────────

    def search(
        self,
        query:           str,
        search_depth:    Optional[str]       = None,
        max_results:     Optional[int]       = None,
        time_range:      Optional[str]       = None,
        include_domains: Optional[list[str]] = None,
        include_answer:  bool                = True,
    ) -> SearchResponse:
        """
        Execute a Tavily search and return a normalised SearchResponse.

        Args:
            query:           The search query string.
            search_depth:    Override instance default ("basic" or "advanced").
            max_results:     Override instance default.
            time_range:      Override instance default ("day", "week", "month").
            include_domains: Override instance default domain allowlist.
            include_answer:  Whether to request Tavily's AI summary answer.

        Returns:
            SearchResponse with filtered, scored results.
        """
        params = {
            "query":          query,
            "search_depth":   search_depth   or self.search_depth,
            "max_results":    max_results    or self.max_results,
            "include_answer": include_answer,
        }

        # Only pass optional fields when they have a value
        resolved_time_range = time_range if time_range is not None else self.time_range
        if resolved_time_range:
            params["time_range"] = resolved_time_range

        resolved_domains = include_domains if include_domains is not None else self.include_domains
        if resolved_domains:
            params["include_domains"] = resolved_domains

        try:
            logger.debug("Tavily search: %r", query)
            raw = self._client.search(**params)
        except Exception as exc:
            logger.error("Tavily search failed for %r: %s", query, exc)
            return SearchResponse(query=query, error=str(exc))

        results = self._parse_results(raw.get("results", []), query)
        answer  = raw.get("answer")

        logger.info(
            "Search %r → %d results (after score filter ≥ %.2f)",
            query, len(results), self.min_score,
        )
        return SearchResponse(query=query, results=results, answer=answer)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _parse_results(self, raw_results: list[dict], query: str) -> list[SearchResult]:
        """Parse raw Tavily result dicts, filter by score, sort descending."""
        parsed = []
        for r in raw_results:
            score = float(r.get("score", 0.0))
            if score < self.min_score:
                continue
            parsed.append(SearchResult(
                title   = r.get("title",   ""),
                url     = r.get("url",     ""),
                content = r.get("content", ""),
                score   = score,
                query   = query,
            ))
        return sorted(parsed, key=lambda x: x.score, reverse=True)


# ── High-level search routines ─────────────────────────────────────────────

def search_market_news(
    client:  TavilySearchClient,
    tickers: list[str],
    time_range: str = "week",
) -> dict[str, SearchResponse]:
    """
    Search for recent market news for each ticker in the list.

    Args:
        client:     Initialised TavilySearchClient.
        tickers:    List of ticker symbols, e.g. ["AAPL", "NVDA"].
        time_range: Recency filter ("day", "week", "month").

    Returns:
        Dict mapping ticker → SearchResponse.
    """
    responses: dict[str, SearchResponse] = {}
    for ticker in tickers:
        query = f"{ticker} stock news earnings market outlook"
        responses[ticker] = client.search(
            query      = query,
            time_range = time_range,
        )
        logger.info("Market news for %s: %d results", ticker, len(responses[ticker].results))
    return responses


def search_topic(
    client:      TavilySearchClient,
    topic:       str,
    time_range:  Optional[str] = "week",
    max_results: int           = 5,
) -> SearchResponse:
    """
    Free-form topic search — macroeconomic events, sector trends, Fed policy, etc.

    Args:
        client:      Initialised TavilySearchClient.
        topic:       Natural-language topic, e.g. "Federal Reserve interest rate decision".
        time_range:  Recency filter.
        max_results: Number of results to fetch.

    Returns:
        SearchResponse.
    """
    return client.search(
        query       = topic,
        time_range  = time_range,
        max_results = max_results,
    )


def search_company(
    client:  TavilySearchClient,
    ticker:  str,
    aspects: list[str] | None = None,
) -> SearchResponse:
    """
    Deep company research — earnings, analyst sentiment, recent filings.

    Args:
        client:  Initialised TavilySearchClient.
        ticker:  Ticker symbol, e.g. "TSLA".
        aspects: Optional list of topics to focus on.
                 Defaults to ["earnings", "analyst rating", "SEC filing"].

    Returns:
        SearchResponse.
    """
    if aspects is None:
        aspects = ["earnings", "analyst rating", "SEC filing", "revenue guidance"]
    aspect_str = " ".join(aspects)
    query = f"{ticker} {aspect_str}"
    return client.search(
        query        = query,
        search_depth = "advanced",
        time_range   = "month",
        max_results  = 8,
    )


def batch_search(
    client:  TavilySearchClient,
    queries: list[str],
    time_range: Optional[str] = None,
) -> list[SearchResponse]:
    """
    Run multiple independent queries and return a list of SearchResponses
    in the same order as the input queries.

    Args:
        client:     Initialised TavilySearchClient.
        queries:    List of query strings.
        time_range: Optional time filter applied to all queries.

    Returns:
        List of SearchResponse objects.
    """
    responses = []
    for query in queries:
        responses.append(client.search(query=query, time_range=time_range))
    return responses
