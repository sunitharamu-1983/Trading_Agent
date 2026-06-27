"""
test_api.py — Smoke and example tests for the FastAPI endpoints.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_empty_tickers_returns_422():
    r = client.post("/api/analyze", json={"tickers": []})
    assert r.status_code == 422


def test_missing_tickers_field_returns_422():
    r = client.post("/api/analyze", json={})
    assert r.status_code == 422


def test_invalid_ticker_returns_error_entry():
    """An unresolvable ticker must come back with score=0 and an error message."""
    r = client.post("/api/analyze", json={"tickers": ["XXXXINVALID999"]})
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 1
    result = results[0]
    assert result["score"] == 0
    assert result["signal"] == "Bearish"
    assert result["error"] is not None
    assert result["rsi_rule"] is False
    assert result["sma_rule"] is False
    assert result["macd_rule"] is False
    assert result["volume_rule"] is False


def test_mixed_valid_invalid_tickers():
    """A bad ticker must not block the rest of the results."""
    r = client.post("/api/analyze", json={"tickers": ["XXXXINVALID999", "YYYYBAD888"]})
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 2
    for result in results:
        assert result["score"] == 0
        assert result["error"] is not None


def test_response_has_required_fields():
    """Every result must include all required fields."""
    r = client.post("/api/analyze", json={"tickers": ["XXXXINVALID999"]})
    assert r.status_code == 200
    result = r.json()["results"][0]
    for field in ["ticker", "score", "signal", "rsi_rule", "sma_rule", "macd_rule", "volume_rule"]:
        assert field in result


def test_results_are_sorted_by_score_desc():
    """Results must be ordered by score descending."""
    r = client.post("/api/analyze", json={"tickers": ["XXXXINVALID999", "YYYYBAD888"]})
    assert r.status_code == 200
    results = r.json()["results"]
    scores = [res["score"] for res in results]
    assert scores == sorted(scores, reverse=True)
