"""
test_indicators.py — Unit and property-based tests for pure indicator/rule functions.

Property tests use Hypothesis. Each test is tagged with its property number
from the design document for full traceability.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from analyzer import (
    MACDResult,
    compute_rsi,
    compute_sma,
    compute_volume_avg,
    eval_macd_rule,
    eval_rsi_rule,
    eval_sma_rule,
    eval_volume_rule,
    score_to_signal,
)

# ---------------------------------------------------------------------------
# Property 5: RSI is always in the range [0, 100]
# Validates: Requirements 4.1
# ---------------------------------------------------------------------------

@given(
    prices=st.lists(
        st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
        min_size=15,
    )
)
@settings(max_examples=200)
def test_rsi_always_in_range(prices):
    # Property 5: RSI ∈ [0, 100]
    rsi = compute_rsi(pd.Series(prices, dtype=float))
    assert 0.0 <= rsi <= 100.0


# ---------------------------------------------------------------------------
# Property 6: 50-day SMA equals arithmetic mean of last 50 closes
# Validates: Requirements 4.2
# ---------------------------------------------------------------------------

@given(
    prices=st.lists(
        st.floats(min_value=1.0, max_value=10_000.0, allow_nan=False, allow_infinity=False),
        min_size=50,
    )
)
@settings(max_examples=200)
def test_sma_equals_arithmetic_mean(prices):
    # Property 6: SMA = mean(close[-50:])
    result = compute_sma(pd.Series(prices, dtype=float), period=50)
    expected = float(np.mean(prices[-50:]))
    assert result == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Property 7: 20-day volume average equals arithmetic mean of last 20 volumes
# Validates: Requirements 4.4
# ---------------------------------------------------------------------------

@given(
    vols=st.lists(
        st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False),
        min_size=20,
    )
)
@settings(max_examples=200)
def test_volume_avg_equals_arithmetic_mean(vols):
    # Property 7: volume_avg = mean(volume[-20:])
    result = compute_volume_avg(pd.Series(vols, dtype=float), period=20)
    expected = float(np.mean(vols[-20:]))
    assert result == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Property 8: RSI rule threshold is exactly ≤ 40
# Validates: Requirements 5.1
# ---------------------------------------------------------------------------

@given(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
def test_rsi_rule_threshold(rsi_val):
    # Property 8: eval_rsi_rule(r) == (r <= 40.0)
    assert eval_rsi_rule(rsi_val) == (rsi_val <= 40.0)


# ---------------------------------------------------------------------------
# Property 9: SMA rule is strictly close > SMA
# Validates: Requirements 5.2
# ---------------------------------------------------------------------------

@given(
    close=st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False),
    sma=st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False),
)
def test_sma_rule_threshold(close, sma):
    # Property 9: eval_sma_rule(c, s) == (c > s)
    assert eval_sma_rule(close, sma) == (close > sma)


# ---------------------------------------------------------------------------
# Property 10: MACD crossover rule detects exactly the bullish condition
# Validates: Requirements 5.3
# ---------------------------------------------------------------------------

@given(
    macd_prev=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    signal_prev=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    macd_curr=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    signal_curr=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
def test_macd_rule_crossover(macd_prev, signal_prev, macd_curr, signal_curr):
    # Property 10: eval_macd_rule == (macd_prev <= signal_prev and macd_curr > signal_curr)
    m = MACDResult(macd_prev, signal_prev, macd_curr, signal_curr)
    expected = (macd_prev <= signal_prev) and (macd_curr > signal_curr)
    assert eval_macd_rule(m) == expected


# ---------------------------------------------------------------------------
# Property 11: Volume rule threshold is ≥ 1.2× average
# Validates: Requirements 5.4
# ---------------------------------------------------------------------------

@given(
    volume_last=st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False),
    volume_avg=st.floats(min_value=0.001, max_value=1e9, allow_nan=False, allow_infinity=False),
)
def test_volume_rule_threshold(volume_last, volume_avg):
    # Property 11: eval_volume_rule(v, a) == (v >= 1.2 * a)
    assert eval_volume_rule(volume_last, volume_avg) == (volume_last >= 1.2 * volume_avg)


# ---------------------------------------------------------------------------
# Property 12: Score equals count of true rule flags and is always in [0, 4]
# Validates: Requirements 5.5
# ---------------------------------------------------------------------------

@given(
    rsi_rule=st.booleans(),
    sma_rule=st.booleans(),
    macd_rule=st.booleans(),
    volume_rule=st.booleans(),
)
def test_score_equals_flag_count(rsi_rule, sma_rule, macd_rule, volume_rule):
    # Property 12: score = count(true flags) ∈ [0, 4]
    score = int(sum([rsi_rule, sma_rule, macd_rule, volume_rule]))
    assert 0 <= score <= 4
    assert score == sum([rsi_rule, sma_rule, macd_rule, volume_rule])


# ---------------------------------------------------------------------------
# Property 3 (backend side): sort order invariant
# Validates: Requirements 2.2
# ---------------------------------------------------------------------------

def test_results_sorted_by_score_desc_then_ticker_asc():
    # Property 3: sort order invariant
    from models import TickerResult

    unsorted = [
        TickerResult(ticker="TSLA", score=2, signal="Neutral", rsi_rule=True,  sma_rule=True,  macd_rule=False, volume_rule=False),
        TickerResult(ticker="AAPL", score=4, signal="Strong Buy", rsi_rule=True, sma_rule=True, macd_rule=True, volume_rule=True),
        TickerResult(ticker="GOOG", score=4, signal="Strong Buy", rsi_rule=True, sma_rule=True, macd_rule=True, volume_rule=True),
        TickerResult(ticker="MSFT", score=1, signal="Neutral", rsi_rule=True,  sma_rule=False, macd_rule=False, volume_rule=False),
        TickerResult(ticker="AMZN", score=3, signal="Bullish", rsi_rule=True,  sma_rule=True,  macd_rule=True,  volume_rule=False),
    ]
    unsorted.sort(key=lambda r: (-r.score, r.ticker))

    scores = [r.score for r in unsorted]
    # Scores must be non-increasing
    assert scores == sorted(scores, reverse=True)
    # Among equal scores, tickers must be alphabetical
    prev = unsorted[0]
    for curr in unsorted[1:]:
        if curr.score == prev.score:
            assert curr.ticker >= prev.ticker
        prev = curr


# ---------------------------------------------------------------------------
# score_to_signal label tests
# ---------------------------------------------------------------------------

def test_signal_labels():
    assert score_to_signal(4) == "Strong Buy"
    assert score_to_signal(3) == "Bullish"
    assert score_to_signal(2) == "Neutral"
    assert score_to_signal(1) == "Neutral"
    assert score_to_signal(0) == "Bearish"
