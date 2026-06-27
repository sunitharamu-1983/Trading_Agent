"""
tests/test_tavily_search.py
────────────────────────────
Unit tests for the Tavily search module.
Uses mocking so no real API calls are made during CI.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from agent.tavily_search import (
    TavilySearchClient,
    SearchResult,
    SearchResponse,
    search_market_news,
    search_topic,
    search_company,
    batch_search,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

MOCK_RAW_RESULTS = [
    {"title": "AAPL beats earnings", "url": "https://reuters.com/aapl", "content": "Apple reported...", "score": 0.92},
    {"title": "AAPL supply chain",   "url": "https://wsj.com/aapl-sc", "content": "Supply issues...", "score": 0.41},  # below min_score
]

MOCK_TAVILY_RESPONSE = {
    "results": MOCK_RAW_RESULTS,
    "answer":  "Apple beat Q3 expectations by a wide margin.",
}


@pytest.fixture
def mock_client():
    """Return a TavilySearchClient with the underlying TavilyClient mocked."""
    with patch("agent.tavily_search.TavilyClient") as MockTavily:
        instance = MockTavily.return_value
        instance.search.return_value = MOCK_TAVILY_RESPONSE

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            client = TavilySearchClient(min_score=0.5)
            client._client = instance   # inject mock
            yield client


# ── Tests ──────────────────────────────────────────────────────────────────

class TestTavilySearchClient:

    def test_search_returns_response(self, mock_client):
        resp = mock_client.search("AAPL earnings")
        assert isinstance(resp, SearchResponse)
        assert resp.query == "AAPL earnings"

    def test_score_filter_applied(self, mock_client):
        """Result with score 0.41 should be filtered out (min_score=0.5)."""
        resp = mock_client.search("AAPL earnings")
        assert len(resp.results) == 1
        assert resp.results[0].score == 0.92

    def test_answer_captured(self, mock_client):
        resp = mock_client.search("AAPL earnings")
        assert "Apple beat" in resp.answer

    def test_top_result(self, mock_client):
        resp = mock_client.search("AAPL earnings")
        assert resp.top is not None
        assert resp.top.title == "AAPL beats earnings"

    def test_error_on_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            # Ensure TAVILY_API_KEY is not in environment
            import os
            os.environ.pop("TAVILY_API_KEY", None)
            with pytest.raises(EnvironmentError, match="TAVILY_API_KEY"):
                TavilySearchClient()

    def test_as_context_string(self, mock_client):
        resp = mock_client.search("AAPL earnings")
        ctx  = resp.as_context_string()
        assert "AAPL earnings" in ctx
        assert "Apple beat" in ctx   # answer
        assert "reuters.com" in ctx


class TestHighLevelRoutines:

    def test_search_market_news(self, mock_client):
        results = search_market_news(mock_client, ["AAPL"])
        assert "AAPL" in results
        assert isinstance(results["AAPL"], SearchResponse)

    def test_search_topic(self, mock_client):
        resp = search_topic(mock_client, "Federal Reserve rate cut")
        assert isinstance(resp, SearchResponse)

    def test_search_company(self, mock_client):
        resp = search_company(mock_client, "TSLA")
        assert isinstance(resp, SearchResponse)

    def test_batch_search(self, mock_client):
        queries   = ["inflation", "tech selloff", "oil prices"]
        responses = batch_search(mock_client, queries)
        assert len(responses) == 3
        assert all(isinstance(r, SearchResponse) for r in responses)
