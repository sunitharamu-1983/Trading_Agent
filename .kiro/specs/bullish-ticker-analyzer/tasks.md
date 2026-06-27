# Implementation Plan: Bullish Ticker Analyzer

## Overview

Build a two-tier web application with a FastAPI backend that computes technical indicators (RSI, SMA, MACD, Volume) and ranks tickers by bullishness score, and a React + CloudScape frontend that accepts ticker input and displays ranked results. The backend is implemented first to enable incremental validation; the frontend follows once the API contract is stable.

## Tasks

- [ ] 1. Backend scaffold — project structure, models, health endpoint
  - [ ] 1.1 Create `backend/` directory structure and `requirements.txt`
    - Create `backend/`, `backend/tests/`, `backend/__init__.py`, `backend/tests/__init__.py`
    - Write `backend/requirements.txt` with pinned versions: `fastapi==0.111.0`, `uvicorn==0.29.0`, `yfinance==0.2.40`, `pandas==2.2.2`, `numpy==1.26.4`, `pydantic==2.7.1`, `httpx==0.27.0`, `pytest==8.2.0`, `hypothesis==6.100.0`
    - _Requirements: 7.2_

  - [ ] 1.2 Implement `backend/models.py` with Pydantic schemas
    - Define `AnalyzeRequest` with `tickers: list[str]` and a `field_validator` that rejects an empty list
    - Define `TickerResult` with fields: `ticker`, `score`, `signal`, `rsi_rule`, `sma_rule`, `macd_rule`, `volume_rule`, `error: Optional[str]`
    - `signal` is computed as: score 4 → "Strong Buy", score 3 → "Bullish", score 1–2 → "Neutral", score 0 → "Bearish"
    - Define `AnalyzeResponse` with `results: list[TickerResult]`
    - _Requirements: 2.1, 2.3, 5.5, 6.5_

  - [ ] 1.3 Implement `backend/main.py` with CORS and health endpoint
    - Create FastAPI `app` instance with title "Bullish Ticker Analyzer"
    - Add `CORSMiddleware` allowing origins `http://localhost:3000` and `http://localhost:5173`, methods GET and POST, header Content-Type
    - Implement `GET /api/health` returning `{"status": "ok"}`
    - _Requirements: 7.1, 7.3, 7.4_

- [ ] 2. Indicator computation functions
  - [ ] 2.1 Implement `fetch_ohlcv` in `backend/analyzer.py`
    - Use `yf.download(ticker, period="90d", auto_adjust=True, progress=False)`
    - Raise `ValueError` if the returned DataFrame is None or empty
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 2.2 Implement `compute_rsi` (Wilder's smoothed RSI, 14-period)
    - Compute `delta = close.diff().dropna()`, clip into gains and losses
    - Apply EWM with `alpha=1/period, adjust=False` to gains and losses
    - Return `float(rsi.iloc[-1])`; RSI must be finite and in [0, 100]
    - _Requirements: 4.1_

  - [ ]* 2.3 Write property test for `compute_rsi` — Property 5
    - **Property 5: RSI is always in the range [0, 100]**
    - Use `@given(st.lists(st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False), min_size=15))`
    - Assert `0.0 <= compute_rsi(pd.Series(prices)) <= 100.0`
    - Tag with `# Property 5: RSI ∈ [0, 100]`
    - **Validates: Requirements 4.1**

  - [ ] 2.4 Implement `compute_sma` (50-period arithmetic mean)
    - Return `float(close.iloc[-period:].mean())`
    - _Requirements: 4.2_

  - [ ]* 2.5 Write property test for `compute_sma` — Property 6
    - **Property 6: 50-day SMA equals arithmetic mean of last 50 closes**
    - Use `@given(st.lists(st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False), min_size=50))`
    - Assert `compute_sma(pd.Series(prices), 50) == pytest.approx(np.mean(prices[-50:]))`
    - Tag with `# Property 6: SMA = mean(close[-50:])`
    - **Validates: Requirements 4.2**

  - [ ] 2.6 Implement `compute_macd` and `MACDResult`
    - Define `MACDResult` dataclass/class with `macd_prev`, `signal_prev`, `macd_curr`, `signal_curr`
    - Compute EMA fast (span=12), EMA slow (span=26), MACD line, signal line (span=9), all with `adjust=False`
    - Return `MACDResult` using `.iloc[-2]` and `.iloc[-1]`
    - _Requirements: 4.3_

  - [ ] 2.7 Implement `compute_volume_avg` (20-period arithmetic mean)
    - Return `float(volume.iloc[-period:].mean())`
    - _Requirements: 4.4_

  - [ ]* 2.8 Write property test for `compute_volume_avg` — Property 7
    - **Property 7: 20-day volume average equals arithmetic mean of last 20 volumes**
    - Use `@given(st.lists(st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False), min_size=20))`
    - Assert `compute_volume_avg(pd.Series(vols), 20) == pytest.approx(np.mean(vols[-20:]))`
    - Tag with `# Property 7: volume_avg = mean(volume[-20:])`
    - **Validates: Requirements 4.4**

- [ ] 3. Rule evaluation functions
  - [ ] 3.1 Implement `eval_rsi_rule`, `eval_sma_rule`, `eval_macd_rule`, `eval_volume_rule` in `backend/analyzer.py`
    - `eval_rsi_rule(rsi)`: return `rsi <= 40.0`
    - `eval_sma_rule(close_last, sma)`: return `close_last > sma`
    - `eval_macd_rule(m: MACDResult)`: return `m.macd_prev <= m.signal_prev and m.macd_curr > m.signal_curr`
    - `eval_volume_rule(volume_last, volume_avg)`: return `volume_last >= 1.2 * volume_avg`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 3.2 Write property tests for rule evaluation — Properties 8, 9, 10, 11
    - **Property 8: RSI rule threshold is exactly ≤ 40** — `@given(st.floats(allow_nan=False, allow_infinity=False))` → `eval_rsi_rule(r) == (r <= 40.0)`
    - **Property 9: SMA rule is strictly close > SMA** — `@given(st.floats(...), st.floats(...))` → `eval_sma_rule(c, s) == (c > s)`
    - **Property 10: MACD crossover detects exactly the bullish condition** — `@given(four floats)` → `eval_macd_rule(m) == (m.macd_prev <= m.signal_prev and m.macd_curr > m.signal_curr)`
    - **Property 11: Volume rule threshold is ≥ 1.2× average** — `@given(st.floats(min_value=0), st.floats(min_value=0.001))` → `eval_volume_rule(v, a) == (v >= 1.2 * a)`
    - Tag each with `# Property N: <title>`
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [ ] 4. Scoring and analysis orchestration
  - [ ] 4.1 Implement `analyze_ticker` in `backend/analyzer.py`
    - Call `fetch_ohlcv`, check `len(df) >= MIN_ROWS (50)`, raise `ValueError` if not
    - Call all four compute functions, all four eval functions
    - Compute `score = sum([rsi_rule, sma_rule, macd_rule, volume_rule])`
    - Compute `signal`: score 4 → "Strong Buy", score 3 → "Bullish", score 1–2 → "Neutral", score 0 → "Bearish"
    - Return `TickerResult` with all fields populated including `signal`; on any exception return `TickerResult` with `score=0`, `signal="Bearish"`, all flags false, `error=str(exc)`
    - _Requirements: 2.4, 2.5, 3.1, 3.2, 3.3, 4.5, 5.5, 6.5_

  - [ ]* 4.2 Write property test for bullishness score — Property 12
    - **Property 12: Score equals count of true rule flags and is always in [0, 4]**
    - Use `@given(st.booleans(), st.booleans(), st.booleans(), st.booleans())`
    - Assert `score == sum([rsi_rule, sma_rule, macd_rule, volume_rule])` and `0 <= score <= 4`
    - Tag with `# Property 12: score = count(true flags) ∈ [0, 4]`
    - **Validates: Requirements 5.5**

- [ ] 5. `POST /api/analyze` endpoint and result sorting
  - [ ] 5.1 Wire `analyze_ticker` into `POST /api/analyze` in `backend/main.py`
    - Accept `AnalyzeRequest`, call `analyze_ticker(t)` for each ticker in `request.tickers`
    - Sort results by `(-r.score, r.ticker)` (descending score, then alphabetical)
    - Return `AnalyzeResponse(results=results)`
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 5.2 Write property test for result sort order — Property 3
    - **Property 3: Result list sort order invariant**
    - Use `@given(st.lists(st.builds(TickerResult, ...), min_size=1))`
    - After sorting, assert no element has a higher score than its predecessor; among equal scores assert ticker symbols are in ascending lexicographic order
    - Tag with `# Property 3: sort order invariant`
    - **Validates: Requirements 2.2**

- [ ] 6. Backend tests — API smoke tests
  - [ ] 6.1 Write `backend/tests/test_api.py` with endpoint smoke tests
    - Use `fastapi.testclient.TestClient`
    - `test_health`: GET `/api/health` → 200, `{"status": "ok"}`
    - `test_empty_tickers_returns_422`: POST `{"tickers": []}` → 422
    - `test_missing_tickers_returns_422`: POST `{}` → 422
    - `test_invalid_ticker_returns_error_entry`: POST `{"tickers": ["XXXXINVALID999"]}` → 200, `results[0].score == 0`, `results[0].error` is not None
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 7.4_

- [ ] 7. Checkpoint — backend complete
  - Ensure all backend tests pass (`pytest backend/tests/ -v`), ask the user if any questions arise.

- [ ] 8. Frontend scaffold — Vite + React + CloudScape
  - [ ] 8.1 Initialise `frontend/` with Vite React-TS template
    - Run `npm create vite@latest frontend -- --template react-ts` (user runs this manually)
    - Add to `frontend/package.json` dependencies: `@cloudscape-design/components`, `@cloudscape-design/global-styles`
    - Add to devDependencies: `vitest`, `@vitest/ui` (or confirm they are bundled with template)
    - Create `frontend/.env.example` with `VITE_API_BASE_URL=http://localhost:8000`
    - _Requirements: 8.1, 8.2, 8.4_

  - [ ] 8.2 Configure `frontend/vite.config.ts` and apply CloudScape global styles in `frontend/src/main.tsx`
    - Import `@cloudscape-design/global-styles/index.css` in `main.tsx`
    - Ensure no custom CSS overrides CloudScape component internals
    - _Requirements: 8.2, 8.3_

  - [ ] 8.3 Define `frontend/src/types.ts`
    - Export `TickerResult` interface: `ticker`, `score`, `signal`, `rsi_rule`, `sma_rule`, `macd_rule`, `volume_rule`, `error?`
    - Export `AnalyzeResponse` interface: `results: TickerResult[]`
    - _Requirements: 2.2, 6.2_

- [ ] 9. Frontend components
  - [ ] 9.1 Implement `parseTickers` utility and `TickerInput` component in `frontend/src/components/TickerInput.tsx`
    - Export pure function `parseTickers(raw: string): string[]` — split on `/[\s,]+/`, trim, uppercase, filter empty
    - Render CloudScape `FormField` > `Textarea` for input
    - Validate on submit: empty → "Please enter at least one ticker symbol."; >50 → "Maximum 50 tickers allowed per request."
    - Render CloudScape `Button` labelled "Analyze"; disable while `loading` prop is true
    - Accept props: `onSubmit(tickers: string[]): void`, `loading: boolean`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 9.2 Write Vitest unit tests for `parseTickers` — Properties 1 and 2
    - **Property 1: Parsed tokens have no leading/trailing whitespace and no empty tokens** — test with mixed commas, spaces, tabs, newlines, consecutive delimiters
    - **Property 2: Ticker count limit enforcement** — exactly 50 tokens accepted; 51 tokens makes `parseTickers(raw).length > 50` (validation logic test)
    - Place tests in `frontend/src/components/TickerInput.test.ts`
    - **Validates: Requirements 1.2, 1.4**

  - [ ] 9.3 Implement `ResultsTable` component in `frontend/src/components/ResultsTable.tsx`
    - Render CloudScape `Table` with column definitions: Ticker, Signal, Score, RSI ≤ 40, Price > 50d SMA, MACD Crossover, Volume Surge, View on Kite
    - **Signal column** (most prominent): use CloudScape `StatusIndicator` with type `success` for "Strong Buy", `info` for "Bullish", `stopped` for "Neutral", `error` for "Bearish"
    - Rule columns use `StatusIndicator type="success"` ("Yes") / `type="error"` ("No")
    - Score column: display as `{score} / 4`; if `error` is set render `StatusIndicator type="error"` with error tooltip
    - **View on Kite column**: render a CloudScape `Link` with `external` prop that opens `https://kite.zerodha.com/chart/ext/ciq/NSE:{SYMBOL}/EQ` in a new tab; strip `.NS`/`.BO` suffix from ticker to get `{SYMBOL}`
    - Accept props: `results: TickerResult[]`, `loading: boolean`, `apiError: string | null`
    - Show CloudScape `Spinner` when `loading` is true
    - Show CloudScape `Alert type="error"` with `apiError` message when `apiError` is non-null; do not render the table in that state
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

- [ ] 10. API integration and App wiring
  - [ ] 10.1 Implement `frontend/src/api.ts`
    - Read `BASE_URL` from `import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"`
    - Export `analyzeTickers(tickers: string[]): Promise<AnalyzeResponse>`
    - POST to `${BASE_URL}/api/analyze` with `Content-Type: application/json`
    - On non-OK response, parse body and throw `Error(body?.detail ?? \`HTTP ${res.status}\`)`
    - _Requirements: 2.1, 8.4_

  - [ ] 10.2 Wire everything together in `frontend/src/App.tsx`
    - Manage state: `results: TickerResult[]`, `loading: boolean`, `apiError: string | null`
    - On `TickerInput` submit: set `loading=true`, `apiError=null`, call `analyzeTickers`, update `results` on success, set `apiError` on catch, always set `loading=false`
    - Render CloudScape `ContentLayout` with a `Header` ("Bullish Ticker Analyzer"), `TickerInput`, and `ResultsTable`
    - _Requirements: 6.1, 6.5, 6.7_

- [ ] 11. Final checkpoint — full stack complete
  - Ensure backend tests pass: `pytest backend/tests/ -v`
  - Ensure frontend tests pass: `npx vitest run` (run from `frontend/`)
  - Ensure both dev servers start without errors (user runs `uvicorn main:app --reload --port 8000` and `npm run dev` manually)
  - Ask the user if any questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests are tagged with their property number from the design document for full traceability
- Checkpoints validate incremental progress before moving to the next layer
- The backend must be runnable before starting frontend work (Tasks 1–7 first)
- `parseTickers` is a pure function exported separately from the component to make it directly unit-testable without a DOM
- The `backend/` and `frontend/` directories are fully isolated from the existing `agent/` codebase per Requirement 7.1

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1", "2.4", "2.6", "2.7"] },
    { "id": 3, "tasks": ["2.2", "3.1"] },
    { "id": 4, "tasks": ["2.3", "2.5", "2.8", "3.2", "4.1"] },
    { "id": 5, "tasks": ["4.2", "5.1"] },
    { "id": 6, "tasks": ["5.2", "6.1"] },
    { "id": 7, "tasks": ["8.1"] },
    { "id": 8, "tasks": ["8.2", "8.3"] },
    { "id": 9, "tasks": ["9.1", "9.3"] },
    { "id": 10, "tasks": ["9.2", "10.1"] },
    { "id": 11, "tasks": ["10.2"] }
  ]
}
```
