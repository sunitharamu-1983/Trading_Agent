# Requirements Document

## Introduction

The Bullish Ticker Analyzer is a full-stack web application that accepts a list of stock ticker symbols, fetches historical OHLCV (Open, High, Low, Close, Volume) data via `yfinance`, computes a set of technical analysis indicators, and ranks each ticker by a bullishness score representing how many of four defined rules it satisfies. The application consists of a FastAPI backend in `backend/` and a React + AWS CloudScape frontend in `frontend/`, both isolated from the existing `agent/` codebase.

## Glossary

- **Analyzer**: The FastAPI backend service that fetches market data and computes technical indicators.
- **UI**: The React + AWS CloudScape frontend application served to the user's browser.
- **Ticker**: A stock ticker symbol (e.g., AAPL, TSLA) provided by the user.
- **OHLCV Data**: Open, High, Low, Close, Volume time-series data for a given ticker, retrieved via `yfinance`.
- **RSI**: Relative Strength Index — a momentum oscillator measuring the speed and magnitude of recent price changes, calculated over a 14-period window.
- **SMA**: Simple Moving Average — the arithmetic mean of closing prices over a specified number of periods.
- **50-day SMA**: The Simple Moving Average of closing prices over the most recent 50 trading days.
- **MACD**: Moving Average Convergence Divergence — the difference between the 12-period and 26-period exponential moving averages, with a 9-period signal line.
- **MACD Bullish Crossover**: The event where the MACD line crosses above the signal line on the most recent two trading days (MACD was below or equal to signal line on the prior day and is above it on the current day).
- **20-day Volume Average**: The arithmetic mean of daily trading volume over the most recent 20 trading days.
- **Bullishness Score**: An integer from 0 to 4 representing how many of the four defined technical analysis rules a ticker satisfies.
- **Technical Analysis Rules**: The four criteria used to evaluate each ticker: RSI Rule, SMA Rule, MACD Rule, and Volume Rule.
- **RSI Rule**: Satisfied when the most recent RSI value is less than or equal to 40.
- **SMA Rule**: Satisfied when the most recent closing price is strictly greater than the most recent 50-day SMA value.
- **MACD Rule**: Satisfied when a MACD bullish crossover has occurred on the most recent trading day.
- **Volume Rule**: Satisfied when the most recent day's volume is at least 20% greater than the 20-day volume average.
- **Analysis Result**: A structured object for a single ticker containing: ticker symbol, bullishness score, and a boolean flag for each of the four rules indicating whether it was satisfied.
- **Ranked Results**: The list of Analysis Results sorted by bullishness score in descending order; ties are sorted alphabetically by ticker symbol.
- **Bullish Signal**: A human-readable label derived from the bullishness score: score 4 = "Strong Buy", score 3 = "Bullish", score 1–2 = "Neutral", score 0 = "Bearish".
- **NSE/BSE Ticker**: Indian exchange tickers use a suffix notation supported by yfinance — `.NS` for NSE (e.g., `RELIANCE.NS`) and `.BO` for BSE (e.g., `RELIANCE.BO`).
- **Nifty 50**: The benchmark index of the 50 largest companies listed on the NSE. The application ships a static list of Nifty 50 tickers (with `.NS` suffix) in `backend/watchlist.py` for UI auto-population.
- **WatchlistResponse**: A Pydantic response schema containing a `tickers: list[str]` field, returned by the `/api/watchlist` endpoint.
- **Kite Chart URL**: The Zerodha Kite web chart URL for a ticker, constructed by stripping the `.NS` or `.BO` suffix and using the pattern `https://kite.zerodha.com/chart/ext/ciq/NSE:{SYMBOL}/EQ`. No API key or authentication is required to construct this link.

---

## Requirements

### Requirement 1 — Ticker Input

**User Story:** As a user, I want to enter a list of stock tickers as comma-separated values or one per line, so that I can analyze multiple tickers in a single request.

#### Acceptance Criteria

1. THE UI SHALL render a text input area that accepts ticker symbols separated by commas, newlines, or a combination of both.
2. WHEN the user submits the input, THE UI SHALL strip whitespace from each token and discard empty tokens before sending them to the Analyzer.
3. IF the user submits an empty or blank input, THEN THE UI SHALL display an inline validation message stating "Please enter at least one ticker symbol." and SHALL NOT submit a request to the Analyzer.
4. THE UI SHALL accept a maximum of 50 ticker symbols per submission; IF the user provides more than 50 symbols, THEN THE UI SHALL display an inline validation message stating "Maximum 50 tickers allowed per request." and SHALL NOT submit a request to the Analyzer.

---

### Requirement 2 — Analysis Endpoint

**User Story:** As the UI, I want to call a single REST endpoint with a list of tickers and receive ranked analysis results, so that the frontend can display scored outcomes to the user.

#### Acceptance Criteria

1. THE Analyzer SHALL expose a POST endpoint at `/api/analyze` that accepts a JSON request body containing a non-empty array of ticker symbol strings.
2. WHEN `/api/analyze` is called with a valid request body, THE Analyzer SHALL return a JSON response containing a `results` array of Analysis Result objects sorted by bullishness score in descending order, with ties sorted alphabetically by ticker symbol.
3. IF the request body is missing the tickers array or the array is empty, THEN THE Analyzer SHALL return HTTP 422 with a JSON error body describing the validation failure.
4. THE Analyzer SHALL process each ticker independently so that a failure for one ticker does not prevent results from being returned for the remaining tickers.
5. WHEN a ticker cannot be resolved or returns insufficient historical data (fewer than 50 trading days), THE Analyzer SHALL include that ticker in the results with a bullishness score of 0, all rule flags set to false, and an `error` field containing a human-readable message.

---

### Requirement 3 — OHLCV Data Fetching

**User Story:** As the Analyzer, I want to fetch sufficient historical OHLCV data for each ticker, so that all four technical indicators can be computed accurately.

#### Acceptance Criteria

1. WHEN computing indicators for a ticker, THE Analyzer SHALL fetch at least 90 calendar days of daily OHLCV data using `yfinance` to ensure at least 50 trading days of data are available.
2. THE Analyzer SHALL use adjusted closing prices for all price-based indicator calculations (RSI, SMA, MACD).
3. IF `yfinance` raises an exception or returns an empty DataFrame for a ticker, THEN THE Analyzer SHALL treat that ticker as having insufficient data and return an Analysis Result with score 0, all rule flags false, and an error message.

---

### Requirement 4 — Technical Indicator Computation

**User Story:** As the Analyzer, I want to compute RSI, 50-day SMA, MACD, and volume metrics for each ticker, so that each of the four bullishness rules can be evaluated.

#### Acceptance Criteria

1. THE Analyzer SHALL compute RSI using a 14-period Wilder's smoothed average gain/loss method applied to daily adjusted close price changes.
2. THE Analyzer SHALL compute the 50-day SMA as the arithmetic mean of the most recent 50 adjusted closing prices.
3. THE Analyzer SHALL compute the MACD line as the difference between the 12-period EMA and the 26-period EMA of adjusted closing prices, and the signal line as the 9-period EMA of the MACD line.
4. THE Analyzer SHALL compute the 20-day volume average as the arithmetic mean of the most recent 20 daily trading volumes.
5. WHEN fewer data points are available than required for a given indicator (e.g., fewer than 26 days for MACD), THE Analyzer SHALL treat that ticker as having insufficient data per Requirement 3, Acceptance Criterion 3.

---

### Requirement 5 — Bullishness Scoring

**User Story:** As the Analyzer, I want to evaluate each ticker against the four technical analysis rules and assign a score, so that tickers can be ranked by their bullish outlook.

#### Acceptance Criteria

1. THE Analyzer SHALL set the RSI Rule flag to true for a ticker WHEN the most recent computed RSI value is less than or equal to 40.
2. THE Analyzer SHALL set the SMA Rule flag to true for a ticker WHEN the most recent adjusted closing price is strictly greater than the most recent 50-day SMA value.
3. THE Analyzer SHALL set the MACD Rule flag to true for a ticker WHEN the MACD line was less than or equal to the signal line on the second-to-last trading day AND the MACD line is strictly greater than the signal line on the most recent trading day.
4. THE Analyzer SHALL set the Volume Rule flag to true for a ticker WHEN the most recent day's trading volume is greater than or equal to 1.2 times the 20-day volume average.
5. THE Analyzer SHALL compute the bullishness score for each ticker as the count of rule flags that are set to true, yielding an integer in the range [0, 4].

---

### Requirement 6 — Results Display

**User Story:** As a user, I want to see ranked analysis results in a clear table showing each ticker's score and which rules it passed, so that I can quickly identify the most bullish opportunities.

#### Acceptance Criteria

1. WHEN analysis results are returned by the Analyzer, THE UI SHALL display the results in a CloudScape Table component ranked by bullishness score descending, with ties ordered alphabetically by ticker symbol.
2. THE UI SHALL render the following columns in the results table: Ticker, Signal, Score, RSI ≤ 40, Price > 50-day SMA, MACD Crossover, Volume Surge, View on Kite.
3. THE UI SHALL display each rule column using a CloudScape StatusIndicator showing "success" (green) when the rule is satisfied and "error" (red) when it is not.
4. THE UI SHALL display the bullishness score as a numeric value in the Score column.
5. THE UI SHALL display a Bullish Signal badge in the Signal column using the following mapping: score 4 → "Strong Buy" (green), score 3 → "Bullish" (blue), score 1–2 → "Neutral" (grey), score 0 → "Bearish" (red). This column SHALL be the most visually prominent indicator of actionability.
6. THE UI SHALL render a "View on Kite" icon-link button in each row that opens `https://kite.zerodha.com/chart/ext/ciq/NSE:{SYMBOL}/EQ` in a new browser tab, where `{SYMBOL}` is the ticker with `.NS` or `.BO` suffix stripped. No API key is required for this link.
7. WHILE the Analyzer is processing a request, THE UI SHALL display a CloudScape Spinner or loading state and SHALL disable the Analyze button.
8. IF the Analyzer returns an error field for a ticker, THEN THE UI SHALL display that ticker in the table with score 0, all rule indicators negative, Signal as "Bearish", and an error icon or tooltip showing the error message.
9. IF the Analyzer returns an HTTP error response, THEN THE UI SHALL display a CloudScape Alert of type "error" with a user-readable message and SHALL NOT render the results table.

---

### Requirement 7 — Backend Structure and CORS

**User Story:** As a developer, I want the FastAPI backend to be isolated in the `backend/` subfolder and configured to allow requests from the React frontend, so that both services can run independently during development.

#### Acceptance Criteria

1. THE Analyzer SHALL be structured as a standalone FastAPI application rooted in the `backend/` directory, with no imports from the existing `agent/`, `config/`, or `tests/` modules.
2. THE Analyzer SHALL include a `backend/requirements.txt` listing all backend-specific dependencies with pinned versions, including `fastapi`, `uvicorn`, `yfinance`, `pandas`, and `numpy`.
3. THE Analyzer SHALL configure CORS middleware to allow requests from `http://localhost:3000` and `http://localhost:5173` during development.
4. THE Analyzer SHALL expose a GET endpoint at `/api/health` that returns HTTP 200 with a JSON body `{"status": "ok"}`.
5. THE Analyzer SHALL expose a GET endpoint at `/api/watchlist` that returns HTTP 200 with a `WatchlistResponse` JSON body containing the static Nifty 50 ticker list (e.g. `["RELIANCE.NS", "TCS.NS", ...]`), allowing the UI to auto-populate the ticker input without the user having to type symbols manually.

---

### Requirement 8 — Frontend Structure

**User Story:** As a developer, I want the React frontend to be isolated in the `frontend/` subfolder and use the AWS CloudScape design system, so that the UI is professional and consistent.

#### Acceptance Criteria

1. THE UI SHALL be structured as a standalone React application rooted in the `frontend/` directory, bootstrapped with Vite or Create React App.
2. THE UI SHALL use the `@cloudscape-design/components` and `@cloudscape-design/global-styles` packages for all UI components and base styles.
3. THE UI SHALL apply the CloudScape light theme and SHALL NOT include custom CSS that overrides CloudScape component internals.
4. THE UI SHALL configure the Analyzer API base URL via an environment variable (e.g., `VITE_API_BASE_URL` or `REACT_APP_API_BASE_URL`) with a default of `http://localhost:8000`.
