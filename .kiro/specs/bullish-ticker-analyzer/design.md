# Design Document — Bullish Ticker Analyzer

## Overview

The Bullish Ticker Analyzer is a two-tier web application:

- **Backend** (`backend/`): A FastAPI service that fetches OHLCV data via `yfinance`, computes four technical indicators (RSI, SMA, MACD, Volume), evaluates four bullishness rules, and returns ranked results.
- **Frontend** (`frontend/`): A React + AWS CloudScape SPA that accepts ticker input, calls the backend, and displays ranked results in a structured table.

The two tiers communicate over HTTP. During development both run locally; the backend listens on port 8000, the frontend on port 3000 or 5173.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Browser                                    │
│  ┌───────────────────────────────────────┐  │
│  │  React + CloudScape  (Vite, port 5173)│  │
│  │  ┌─────────────┐  ┌────────────────┐  │  │
│  │  │ TickerInput │  │ ResultsTable   │  │  │
│  │  └──────┬──────┘  └───────▲────────┘  │  │
│  │         │  POST /api/analyze           │  │
│  └─────────┼──────────────────────────────┘  │
└────────────┼──────────────────────────────────┘
             │ HTTP JSON
┌────────────▼──────────────────────────────────┐
│  FastAPI  (uvicorn, port 8000)                 │
│  ┌──────────────┐   ┌────────────────────────┐ │
│  │  /api/analyze│   │  /api/health           │ │
│  └──────┬───────┘   └────────────────────────┘ │
│         │                                       │
│  ┌──────▼──────────────────────────────────┐   │
│  │  analyzer.py                            │   │
│  │  ├─ fetch_ohlcv(ticker) → DataFrame     │   │
│  │  ├─ compute_rsi(series) → float         │   │
│  │  ├─ compute_sma(series, n) → float      │   │
│  │  ├─ compute_macd(series) → MACDResult   │   │
│  │  ├─ compute_volume_avg(series) → float  │   │
│  │  └─ analyze_ticker(ticker) → Result     │   │
│  └─────────────────────────────────────────┘   │
│         │ yfinance                              │
└─────────┼─────────────────────────────────────┘
          ▼
     Yahoo Finance API
```

---

## Directory Layout

```
backend/
├── main.py               # FastAPI app, CORS, routes
├── analyzer.py           # Pure indicator + scoring logic
├── models.py             # Pydantic request/response models
├── requirements.txt      # Pinned backend deps
└── tests/
    ├── test_indicators.py   # Property-based + unit tests
    └── test_api.py          # Endpoint smoke/example tests

frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── TickerInput.tsx   # Text area + validation
│   │   └── ResultsTable.tsx  # CloudScape Table
│   ├── api.ts               # fetch wrapper → POST /api/analyze
│   └── types.ts             # TypeScript interfaces
├── .env.example
├── index.html
├── vite.config.ts
└── package.json
```

---

## Backend Design

### `models.py` — Pydantic Schemas

```python
from pydantic import BaseModel, field_validator
from typing import Optional

class AnalyzeRequest(BaseModel):
    tickers: list[str]

    @field_validator("tickers")
    @classmethod
    def tickers_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("tickers array must not be empty")
        return v

class TickerResult(BaseModel):
    ticker: str
    score: int                   # 0–4
    signal: str                  # "Strong Buy" | "Bullish" | "Neutral" | "Bearish"
    rsi_rule: bool
    sma_rule: bool
    macd_rule: bool
    volume_rule: bool
    error: Optional[str] = None  # set when data fetch/compute fails

class AnalyzeResponse(BaseModel):
    results: list[TickerResult]
```

### `analyzer.py` — Indicator Logic

All functions are pure (no I/O side effects) and operate on pandas Series or plain Python floats. This makes them straightforwardly testable.

```python
import yfinance as yf
import pandas as pd
import numpy as np
from models import TickerResult

# --- Data fetching ---

def fetch_ohlcv(ticker: str) -> pd.DataFrame:
    """Fetch 90 calendar days of daily OHLCV data. Returns DataFrame or raises."""
    df = yf.download(ticker, period="90d", auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for {ticker}")
    return df

# --- Indicator computations (pure functions) ---

def compute_rsi(close: pd.Series, period: int = 14) -> float:
    """Wilder's smoothed RSI. Returns the most recent RSI value."""
    delta = close.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing: initial avg = simple mean of first `period` values,
    # then EWM with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def compute_sma(close: pd.Series, period: int = 50) -> float:
    """Arithmetic mean of the most recent `period` closing prices."""
    return float(close.iloc[-period:].mean())

class MACDResult:
    def __init__(self, macd_prev: float, signal_prev: float,
                 macd_curr: float, signal_curr: float):
        self.macd_prev = macd_prev
        self.signal_prev = signal_prev
        self.macd_curr = macd_curr
        self.signal_curr = signal_curr

def compute_macd(close: pd.Series,
                 fast: int = 12, slow: int = 26, signal: int = 9) -> MACDResult:
    """Returns MACD and signal values for the last two trading days."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return MACDResult(
        macd_prev=float(macd_line.iloc[-2]),
        signal_prev=float(signal_line.iloc[-2]),
        macd_curr=float(macd_line.iloc[-1]),
        signal_curr=float(signal_line.iloc[-1]),
    )

def compute_volume_avg(volume: pd.Series, period: int = 20) -> float:
    """Arithmetic mean of the most recent `period` daily volumes."""
    return float(volume.iloc[-period:].mean())

# --- Rule evaluation (pure functions) ---

def eval_rsi_rule(rsi: float) -> bool:
    return rsi <= 40.0

def eval_sma_rule(close_last: float, sma: float) -> bool:
    return close_last > sma

def eval_macd_rule(m: MACDResult) -> bool:
    return m.macd_prev <= m.signal_prev and m.macd_curr > m.signal_curr

def eval_volume_rule(volume_last: float, volume_avg: float) -> bool:
    return volume_last >= 1.2 * volume_avg

# --- Per-ticker orchestration ---

MIN_ROWS = 50

def analyze_ticker(ticker: str) -> TickerResult:
    """Fetch data, compute indicators, evaluate rules, return TickerResult."""
    try:
        df = fetch_ohlcv(ticker)
        if len(df) < MIN_ROWS:
            raise ValueError(f"Insufficient data: {len(df)} rows (need {MIN_ROWS})")

        close  = df["Close"]
        volume = df["Volume"]

        rsi        = compute_rsi(close)
        sma        = compute_sma(close)
        macd_res   = compute_macd(close)
        vol_avg    = compute_volume_avg(volume)

        rsi_rule    = eval_rsi_rule(rsi)
        sma_rule    = eval_sma_rule(float(close.iloc[-1]), sma)
        macd_rule   = eval_macd_rule(macd_res)
        volume_rule = eval_volume_rule(float(volume.iloc[-1]), vol_avg)

        score = sum([rsi_rule, sma_rule, macd_rule, volume_rule])

        signal = (
            "Strong Buy" if score == 4 else
            "Bullish"    if score == 3 else
            "Neutral"    if score >= 1 else
            "Bearish"
        )

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
```

### `main.py` — FastAPI Application

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import AnalyzeRequest, AnalyzeResponse, TickerResult
from analyzer import analyze_ticker

app = FastAPI(title="Bullish Ticker Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    results: list[TickerResult] = [
        analyze_ticker(t) for t in request.tickers
    ]
    # Sort: descending score, ties → alphabetical ticker
    results.sort(key=lambda r: (-r.score, r.ticker))
    return AnalyzeResponse(results=results)
```

### Error Handling

| Scenario | Behaviour |
|---|---|
| `tickers` array missing or empty | FastAPI / Pydantic returns HTTP 422 automatically |
| `yfinance` raises exception | `analyze_ticker` catches, returns `TickerResult` with `score=0`, `error=<msg>` |
| Insufficient rows (< 50) | Same as above |
| Any other unhandled exception inside `analyze_ticker` | Caught by the bare `except Exception` — other tickers continue |

### Backend Dependencies (`backend/requirements.txt`)

```
fastapi==0.111.0
uvicorn==0.29.0
yfinance==0.2.40
pandas==2.2.2
numpy==1.26.4
pydantic==2.7.1
httpx==0.27.0       # for TestClient in tests
pytest==8.2.0
hypothesis==6.100.0
```

---

## Frontend Design

### Component Tree

```
App
└── ContentLayout (CloudScape)
    ├── Header (CloudScape Header)
    ├── TickerInput
    │   ├── Textarea (CloudScape)
    │   ├── Button "Analyze" (CloudScape)
    │   └── FormField (for validation messages)
    └── ResultsTable
        ├── Table (CloudScape)
        │   └── per-row: StatusIndicator for each rule
        └── Alert (CloudScape, shown on API error)
```

### `types.ts`

```typescript
export interface TickerResult {
  ticker: string;
  score: number;
  signal: string;        // "Strong Buy" | "Bullish" | "Neutral" | "Bearish"
  rsi_rule: boolean;
  sma_rule: boolean;
  macd_rule: boolean;
  volume_rule: boolean;
  error?: string;
}

export interface AnalyzeResponse {
  results: TickerResult[];
}
```

### `api.ts`

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function analyzeTickers(tickers: string[]): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tickers }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<AnalyzeResponse>;
}
```

### `TickerInput.tsx` — Parsing and Validation

The core parsing logic is a pure function, making it independently testable:

```typescript
/** Parse raw textarea value into clean, deduplicated ticker tokens. */
export function parseTickers(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map(t => t.trim().toUpperCase())
    .filter(t => t.length > 0);
}
```

Validation rules (evaluated before submitting):
1. `parseTickers(raw).length === 0` → show "Please enter at least one ticker symbol."
2. `parseTickers(raw).length > 50` → show "Maximum 50 tickers allowed per request."

### `ResultsTable.tsx` — Column Definitions

```typescript
// Bullish Signal badge mapping
const SIGNAL_CONFIG: Record<string, { color: string; type: string }> = {
  "Strong Buy": { color: "#1a7f37", type: "success" },
  "Bullish":    { color: "#0972d3", type: "info" },
  "Neutral":    { color: "#8d99a8", type: "stopped" },
  "Bearish":    { color: "#d91515", type: "error" },
};

// Strip .NS / .BO suffix for Kite URL
function toKiteUrl(ticker: string): string {
  const symbol = ticker.replace(/\.(NS|BO)$/i, "");
  return `https://kite.zerodha.com/chart/ext/ciq/NSE:${symbol}/EQ`;
}

const columnDefinitions = [
  { id: "ticker",  header: "Ticker",          cell: (r) => r.ticker },
  { id: "signal",  header: "Signal",          cell: (r) => (
      <StatusIndicator type={SIGNAL_CONFIG[r.signal]?.type ?? "stopped"}>
        {r.signal}
      </StatusIndicator>
    )
  },
  { id: "score",   header: "Score",           cell: (r) => r.error
      ? <StatusIndicator type="error" title={r.error}>Error</StatusIndicator>
      : `${r.score} / 4` },
  { id: "rsi",     header: "RSI ≤ 40",        cell: ruleCell("rsi_rule") },
  { id: "sma",     header: "Price > 50d SMA", cell: ruleCell("sma_rule") },
  { id: "macd",    header: "MACD Crossover",  cell: ruleCell("macd_rule") },
  { id: "volume",  header: "Volume Surge",    cell: ruleCell("volume_rule") },
  { id: "kite",    header: "View on Kite",    cell: (r) => (
      <Link href={toKiteUrl(r.ticker)} external target="_blank">
        Kite Chart ↗
      </Link>
    )
  },
];

function ruleCell(key: keyof TickerResult) {
  return (r: TickerResult) => (
    <StatusIndicator type={r[key] ? "success" : "error"}>
      {r[key] ? "Yes" : "No"}
    </StatusIndicator>
  );
}
```

---

## Data Flow

```
User types tickers
       │
       ▼
parseTickers(raw) ──→ validate (empty? >50?)
       │                       │
       │                  show error, stop
       │
       ▼
POST /api/analyze  { tickers: [...] }
       │
       ▼  (for each ticker, independently)
fetch_ohlcv(ticker)
       │
compute_rsi / compute_sma / compute_macd / compute_volume_avg
       │
eval_rsi_rule / eval_sma_rule / eval_macd_rule / eval_volume_rule
       │
score = sum of flags
       │
       ▼
sort results (score DESC, ticker ASC)
       │
       ▼
JSON response → ResultsTable renders
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

**Property reflection:** After reviewing all prework items, properties 5.1–5.4 (individual rule threshold checks) can each stand alone because they test orthogonal pure functions. Properties 4.2 and 4.4 (SMA and volume avg as means) are structurally identical patterns but operate on different series and different periods, so both are kept. Properties 1.2 and 1.4 (ticker parsing) complement each other — 1.2 tests token cleanliness, 1.4 tests the upper-bound enforcement. No redundancy remains after this reflection.

---

### Property 1: Ticker token parsing strips whitespace and discards empty tokens

*For any* raw input string composed of ticker symbols interspersed with arbitrary combinations of commas, spaces, tabs, and newlines (including leading/trailing whitespace on individual tokens and consecutive delimiters), the parsed output shall contain only non-empty strings with no leading or trailing whitespace.

**Validates: Requirements 1.2**

---

### Property 2: Ticker count limit enforcement

*For any* raw input string whose parsed token count exceeds 50, the frontend validation function shall reject the input; and for any raw input string whose parsed token count is between 1 and 50 inclusive, the validation function shall accept the input.

**Validates: Requirements 1.4**

---

### Property 3: Result list sort order invariant

*For any* list of TickerResult objects (with arbitrary scores and ticker symbols), the sort applied before returning the API response shall produce a list where no element has a higher score than any element that precedes it, and among elements with equal scores the ticker symbols appear in lexicographic ascending order.

**Validates: Requirements 2.2**

---

### Property 4: Independent ticker processing — valid tickers unaffected by failures

*For any* request containing a mix of resolvable tickers and unresolvable (invalid) tickers, the response shall include a result entry for every ticker in the input, and the result entries for the resolvable tickers shall have `error` absent (or null), while the result entries for unresolvable tickers shall have `score=0`, all rule flags false, and a non-empty `error` string.

**Validates: Requirements 2.4, 2.5**

---

### Property 5: RSI is always in the range [0, 100]

*For any* price series of sufficient length (≥ 15 data points), the computed RSI value shall be a finite float in the closed interval [0.0, 100.0].

**Validates: Requirements 4.1**

---

### Property 6: 50-day SMA equals the arithmetic mean of the last 50 closes

*For any* closing price series of length ≥ 50, `compute_sma(close, 50)` shall return a value equal to `mean(close[-50:])` within floating-point tolerance.

**Validates: Requirements 4.2**

---

### Property 7: 20-day volume average equals the arithmetic mean of the last 20 volumes

*For any* volume series of length ≥ 20, `compute_volume_avg(volume, 20)` shall return a value equal to `mean(volume[-20:])` within floating-point tolerance.

**Validates: Requirements 4.4**

---

### Property 8: RSI rule threshold is exactly ≤ 40

*For any* RSI value `r`, `eval_rsi_rule(r)` shall return `True` if and only if `r <= 40.0`.

**Validates: Requirements 5.1**

---

### Property 9: SMA rule threshold is strictly close > SMA

*For any* pair `(close, sma)`, `eval_sma_rule(close, sma)` shall return `True` if and only if `close > sma`.

**Validates: Requirements 5.2**

---

### Property 10: MACD crossover rule detects exactly the bullish crossover condition

*For any* four-tuple `(macd_prev, signal_prev, macd_curr, signal_curr)`, `eval_macd_rule` shall return `True` if and only if `macd_prev <= signal_prev` and `macd_curr > signal_curr`.

**Validates: Requirements 5.3**

---

### Property 11: Volume rule threshold is ≥ 1.2× average

*For any* pair `(volume_last, volume_avg)` with `volume_avg > 0`, `eval_volume_rule(volume_last, volume_avg)` shall return `True` if and only if `volume_last >= 1.2 * volume_avg`.

**Validates: Requirements 5.4**

---

### Property 12: Bullishness score equals the count of true rule flags and is always in [0, 4]

*For any* combination of four boolean rule flags `(rsi_rule, sma_rule, macd_rule, volume_rule)`, the computed bullishness score shall equal `sum([rsi_rule, sma_rule, macd_rule, volume_rule])` and shall therefore be an integer in the closed interval [0, 4].

**Validates: Requirements 5.5**

---

## Testing Strategy

### Backend unit + property tests (`backend/tests/test_indicators.py`)

Use [Hypothesis](https://hypothesis.readthedocs.io/) for property tests; pytest for examples and edge cases.

```python
# Example property test sketch
from hypothesis import given, settings
from hypothesis import strategies as st
from analyzer import (
    compute_rsi, compute_sma, compute_volume_avg,
    eval_rsi_rule, eval_sma_rule, eval_macd_rule,
    eval_volume_rule, MACDResult
)
import pandas as pd

@given(
    prices=st.lists(st.floats(min_value=1.0, max_value=10000.0,
                              allow_nan=False, allow_infinity=False),
                    min_size=15)
)
@settings(max_examples=200)
def test_rsi_always_in_range(prices):
    """Property 5: RSI ∈ [0, 100] for any valid price series."""
    rsi = compute_rsi(pd.Series(prices))
    assert 0.0 <= rsi <= 100.0
```

Each property test is tagged with `# Property N: <title>` to maintain traceability.

### API example/smoke tests (`backend/tests/test_api.py`)

```python
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

def test_invalid_ticker_returns_error_entry():
    r = client.post("/api/analyze", json={"tickers": ["XXXXINVALID999"]})
    assert r.status_code == 200
    result = r.json()["results"][0]
    assert result["score"] == 0
    assert result["error"] is not None
```

### Frontend unit tests

Use Vitest + Testing Library for `parseTickers` and validation logic, which are pure functions that do not require a DOM.

```typescript
// Property 1 — token cleanliness
import { parseTickers } from "./TickerInput";

test("strips whitespace and ignores empty tokens", () => {
  const result = parseTickers("  AAPL , TSLA\n\nGOOGL,  ");
  expect(result).toEqual(["AAPL", "TSLA", "GOOGL"]);
});

// Property 2 — 50-ticker limit
test("accepts exactly 50 tickers", () => {
  const raw = Array.from({ length: 50 }, (_, i) => `T${i}`).join(",");
  expect(parseTickers(raw).length).toBe(50);
});
```

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev          # Vite default: http://localhost:5173

# Tests
cd backend
pytest tests/ -v

cd frontend
npx vitest run
```
