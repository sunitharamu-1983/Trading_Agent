from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import AnalyzeRequest, AnalyzeResponse, TickerResult, WatchlistResponse
from analyzer import analyze_ticker
from watchlist import NIFTY50_TICKERS

app = FastAPI(title="Bullish Ticker Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/watchlist", response_model=WatchlistResponse)
def get_watchlist():
    """Return the Nifty 50 ticker watchlist for auto-population in the UI."""
    return WatchlistResponse(tickers=NIFTY50_TICKERS, label="Nifty 50")


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    results: list[TickerResult] = [
        analyze_ticker(ticker) for ticker in request.tickers
    ]
    # Sort: descending score, ties → alphabetical ticker
    results.sort(key=lambda r: (-r.score, r.ticker))
    return AnalyzeResponse(results=results)
