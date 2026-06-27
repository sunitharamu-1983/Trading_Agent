"""
analyzer.py — Pure indicator computation, rule evaluation, and per-ticker orchestration.

All indicator functions are pure (no I/O side effects) and operate on pandas Series
or plain Python floats, making them straightforwardly unit-testable.
"""

import yfinance as yf
import pandas as pd
import numpy as np

from models import TickerResult

# Minimum number of trading-day rows required for all indicators (50-day SMA is the bottleneck)
MIN_ROWS = 50


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_ohlcv(ticker: str) -> pd.DataFrame:
    """Fetch 90 calendar days of daily OHLCV data via yfinance.

    Supports NSE tickers (e.g. RELIANCE.NS) and BSE tickers (e.g. RELIANCE.BO).
    Returns a DataFrame or raises ValueError if no data is available.
    """
    df = yf.download(ticker, period="90d", auto_adjust=True, progress=False, multi_level_index=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for '{ticker}'. Check the ticker symbol.")
    return df


# ---------------------------------------------------------------------------
# Indicator computations (pure functions)
# ---------------------------------------------------------------------------

def compute_rsi(close: pd.Series, period: int = 14) -> float:
    """Wilder's smoothed RSI over `period` days.

    Returns the most recent RSI value as a float in [0, 100].
    """
    delta = close.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing uses EWM with alpha = 1/period, adjust=False
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


def compute_sma(close: pd.Series, period: int = 50) -> float:
    """Arithmetic mean of the most recent `period` closing prices."""
    return float(close.iloc[-period:].mean())


class MACDResult:
    """Holds MACD and signal line values for the two most recent trading days."""

    def __init__(
        self,
        macd_prev: float,
        signal_prev: float,
        macd_curr: float,
        signal_curr: float,
    ) -> None:
        self.macd_prev = macd_prev
        self.signal_prev = signal_prev
        self.macd_curr = macd_curr
        self.signal_curr = signal_curr


def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> MACDResult:
    """Compute MACD line and signal line using standard EMA parameters.

    Returns a MACDResult with values for the last two trading days, which is
    the minimum needed to detect a bullish crossover.
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return MACDResult(
        macd_prev=float(macd_line.iloc[-2]),
        signal_prev=float(signal_line.iloc[-2]),
        macd_curr=float(macd_line.iloc[-1]),
        signal_curr=float(signal_line.iloc[-1]),
    )


def compute_volume_avg(volume: pd.Series, period: int = 20) -> float:
    """Arithmetic mean of the most recent `period` daily trading volumes."""
    return float(volume.iloc[-period:].mean())


# ---------------------------------------------------------------------------
# Rule evaluation (pure functions — each returns a single bool)
# ---------------------------------------------------------------------------

def eval_rsi_rule(rsi: float) -> bool:
    """RSI ≤ 40 — oversold / bullish reversal signal."""
    return rsi <= 40.0


def eval_sma_rule(close_last: float, sma: float) -> bool:
    """Price strictly above 50-day SMA — uptrend confirmation."""
    return close_last > sma


def eval_macd_rule(m: MACDResult) -> bool:
    """MACD bullish crossover: MACD was ≤ signal yesterday, now > signal today."""
    return m.macd_prev <= m.signal_prev and m.macd_curr > m.signal_curr


def eval_volume_rule(volume_last: float, volume_avg: float) -> bool:
    """Volume ≥ 120% of 20-day average — demand / momentum confirmation."""
    return volume_last >= 1.2 * volume_avg


# ---------------------------------------------------------------------------
# Signal label
# ---------------------------------------------------------------------------

def score_to_signal(score: int) -> str:
    """Map a bullishness score (0–4) to a human-readable signal label."""
    if score == 4:
        return "Strong Buy"
    if score == 3:
        return "Bullish"
    if score >= 1:
        return "Neutral"
    return "Bearish"


# ---------------------------------------------------------------------------
# Per-ticker orchestration
# ---------------------------------------------------------------------------

def analyze_ticker(ticker: str) -> TickerResult:
    """Fetch OHLCV data, compute indicators, evaluate rules, and return a TickerResult.

    Failures are caught per-ticker so a bad symbol does not block others.
    """
    try:
        df = fetch_ohlcv(ticker)

        if len(df) < MIN_ROWS:
            raise ValueError(
                f"Insufficient historical data: only {len(df)} trading days available "
                f"(need at least {MIN_ROWS})."
            )

        close = df["Close"].squeeze()
        volume = df["Volume"].squeeze()

        rsi = compute_rsi(close)
        sma = compute_sma(close)
        macd_res = compute_macd(close)
        vol_avg = compute_volume_avg(volume)

        rsi_rule = eval_rsi_rule(rsi)
        sma_rule = eval_sma_rule(float(close.iloc[-1]), sma)
        macd_rule = eval_macd_rule(macd_res)
        volume_rule = eval_volume_rule(float(volume.iloc[-1]), vol_avg)

        score = int(sum([rsi_rule, sma_rule, macd_rule, volume_rule]))
        signal = score_to_signal(score)

        return TickerResult(
            ticker=ticker.upper(),
            score=score,
            signal=signal,
            rsi_rule=rsi_rule,
            sma_rule=sma_rule,
            macd_rule=macd_rule,
            volume_rule=volume_rule,
        )

    except Exception as exc:
        return TickerResult(
            ticker=ticker.upper(),
            score=0,
            signal="Bearish",
            rsi_rule=False,
            sma_rule=False,
            macd_rule=False,
            volume_rule=False,
            error=str(exc),
        )
